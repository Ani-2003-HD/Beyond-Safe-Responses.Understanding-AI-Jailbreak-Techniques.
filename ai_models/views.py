from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
from openai import OpenAI
import google.generativeai as genai
from .models import AI_MODELS
import requests
from bson.objectid import ObjectId
import pytz

def check_prompt_safety(prompt: str, base_url: str = "http://safe-prompt-api:8001") -> dict:
    """
    Check if a prompt is safe using the Prompt Safety API.
    
    Args:
        prompt: The text prompt to check
        base_url: The base URL of the API (default: http://safe-prompt-api:8001)
        
    Returns:
        Dictionary containing the safety assessment or None if there's an error
    """
    url = f"{base_url}/check-safety"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking prompt safety: {e}")
        return {'safe': True, 'error': str(e)}  # Default to safe if API is unavailable

# Configure the API clients
client = OpenAI(api_key=settings.OPENAI_API_KEY)
genai.configure(api_key=settings.GOOGLE_API_KEY)

def check_mongodb_connection():
    """Test MongoDB connection and return status"""
    try:
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise an exception if connection fails
        print("MongoDB connection successful")
        return True
    except Exception as e:
        print(f"MongoDB connection error: {str(e)}")
        return False

@api_view(['GET'])
@login_required
def list_models(request):
    """Return a list of available AI models"""
    # Check MongoDB connection
    db_status = check_mongodb_connection()
    if not db_status:
        return JsonResponse({'error': 'Database connection error'}, status=500)
    return JsonResponse({'models': AI_MODELS})

@api_view(['POST'])
@login_required
def generate_response(request):
    """Generate a response from the selected AI model"""
    try:
        data = request.data
        
        provider = data.get('provider')
        model = data.get('model')
        prompt = data.get('prompt')
        
        if not all([provider, model, prompt]):
            return Response({
                'error': 'Missing required fields: provider, model, and prompt are required'
            }, status=400)

        # Check prompt safety
        safety_result = check_prompt_safety(prompt)
        if not safety_result.get('safe', True):
            return Response({
                'response': "This prompt has been flagged as potentially unsafe. Please rephrase your request.",
                'model': model,
                'provider': provider,
                'safety_error': safety_result.get('error')
            })
        
        # Generate response based on the selected provider
        if provider == 'openai':
            response = generate_openai_response(model, prompt)
        elif provider == 'google':
            response = generate_google_response(model, prompt)
        else:
            return Response({'error': f'Unknown provider: {provider}'}, status=400)
        
        # Create response data
        response_data = {
            'response': response,
            'model': model,
            'provider': provider
        }
        
        # Save the conversation in MongoDB
        if not save_conversation(request, response_data):
            print("Warning: Failed to save conversation to MongoDB")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return Response({'error': str(e)}, status=500)

def generate_openai_response(model, prompt):
    """Generate a response using OpenAI's API"""
    try:
        # Set temperature based on model
        temperature = 0.7 if model == 'gpt-3.5-turbo' else 0.5
        
        # Create system message based on model
        system_message = (
            "You are a helpful, friendly, and knowledgeable AI assistant. "
            "You provide clear, accurate, and well-structured responses. "
            "When appropriate, you can use markdown formatting to improve readability."
        )
        
        # Create the messages list
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        # Make the API call with error handling
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            if not completion.choices:
                return "Error: No response generated from OpenAI API"
                
            return completion.choices[0].message.content
            
        except Exception as api_error:
            print(f"OpenAI API error: {str(api_error)}")
            if "api_key" in str(api_error).lower():
                return "Error: Invalid OpenAI API key. Please check your configuration."
            elif "rate limit" in str(api_error).lower():
                return "Error: OpenAI API rate limit exceeded. Please try again later."
            else:
                return f"Error communicating with OpenAI API: {str(api_error)}"
        
    except Exception as e:
        print(f"Unexpected error in generate_openai_response: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def generate_google_response(model, prompt):
    """Generate a response using Google's Generative AI API"""
    try:
        model = genai.GenerativeModel(model_name=model)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Google API error: {str(e)}")
        return f"Error with Google API: {str(e)}"

def save_conversation(request, response_data):
    """Save conversation to MongoDB"""
    try:
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.get_database()
        
        # Get IST timezone and current time
        utc_time = datetime.utcnow()
        current_time = utc_time + timedelta(hours=5, minutes=30)
        
        # Create conversation document
        conversation = {
            'user_id': str(request.user.id),
            'timestamp': current_time,
            'prompt': request.data.get('prompt'),
            'response': response_data['response'],
            'model': response_data['model'],
            'provider': response_data['provider']
        }
        
        # Insert into MongoDB
        result = db.chat_history.insert_one(conversation)
        client.close()
        return True
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return False

def get_conversation_history(request):
    """Get conversation history for the current user"""
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client.get_database()
        
        # Convert ObjectId to string for JSON serialization
        def convert_objectid(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_objectid(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_objectid(item) for item in obj]
            return obj
        
        # Get history and convert ObjectIds
        history = list(db.chat_history.find({'user_id': str(request.user.id)}).sort('timestamp', -1))
        history = convert_objectid(history)
        
        client.close()
        return JsonResponse({'history': history}, safe=False)
    except Exception as e:
        print(f"Error retrieving from MongoDB: {e}")
        return JsonResponse({'error': str(e)}, status=500)