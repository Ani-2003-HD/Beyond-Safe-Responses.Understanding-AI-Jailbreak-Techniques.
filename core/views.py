from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json
import pytz

from ai_models.models import AI_MODELS


def home(request):
    """Home page view - redirects to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard(request):
    """Main dashboard for interacting with AI models"""
    context = {
        'models': AI_MODELS,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def history(request):
    """View conversation history for the logged-in user"""
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client.get_database()
        
        # Convert ObjectId to string for JSON serialization
        def convert_objectid(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, dict):
                d = {k: convert_objectid(v) for k, v in obj.items()}
                # Convert timezone-aware datetime to IST
                if 'timestamp' in d and isinstance(d['timestamp'], datetime):
                    ist = pytz.timezone('Asia/Kolkata')
                    if d['timestamp'].tzinfo is None:
                        # If timestamp is naive, assume it's UTC and convert to IST
                        d['timestamp'] = pytz.UTC.localize(d['timestamp']).astimezone(ist)
                    else:
                        # If timestamp already has timezone info, convert to IST
                        d['timestamp'] = d['timestamp'].astimezone(ist)
                return d
            elif isinstance(obj, list):
                return [convert_objectid(item) for item in obj]
            return obj
        
        # Get history and convert ObjectIds and timestamps
        history = list(db.chat_history.find({'user_id': str(request.user.id)}).sort('timestamp', -1))
        history = convert_objectid(history)
        
        # Add timezone info to context
        timezone_info = {
            'name': 'IST',
            'offset': '+5:30',
            'timezone': 'Asia/Kolkata'
        }
        
        client.close()
        return render(request, 'core/history.html', {
            'history': history,
            'timezone': timezone_info
        })
    except Exception as e:
        print(f"Error retrieving history from MongoDB: {e}")
        return render(request, 'core/history.html', {
            'history': [], 
            'error': str(e),
            'timezone': {'name': 'IST', 'offset': '+5:30', 'timezone': 'Asia/Kolkata'}
        })


@login_required
def chat(request, chat_id):
    """View a specific chat conversation"""
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client.get_database()
        
        # Convert string ID to ObjectId for MongoDB query
        chat = db.chat_history.find_one({
            '_id': ObjectId(chat_id),
            'user_id': str(request.user.id)
        })
        
        if chat:
            # Convert ObjectId to string for JSON serialization
            chat['_id'] = str(chat['_id'])
        
        client.close()
        return render(request, 'core/chat.html', {'chat': chat})
    except Exception as e:
        print(f"Error retrieving chat from MongoDB: {e}")
        return render(request, 'core/chat.html', {'chat': None, 'error': str(e)})