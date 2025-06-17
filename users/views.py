from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from pymongo import MongoClient
from django.conf import settings
from .forms import UserRegistrationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.sessions.models import Session
from django.db import close_old_connections


def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')


def register(request):
    """Register a new user"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile in MongoDB
            try:
                client = MongoClient(settings.MONGODB_URI)
                db = client.get_database()
                db.user_profiles.insert_one({
                    'user_id': user.id,
                    'username': user.username,
                    'date_joined': user.date_joined
                })
                client.close()
            except Exception as e:
                print(f"Error creating MongoDB profile: {e}")
            
            # Log the user in
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    """User profile view showing account details and usage statistics"""
    try:
        # Connect to MongoDB to get usage statistics
        client = MongoClient(settings.MONGODB_URI)
        db = client.get_database()
        conversations = db.chat_history
        
        # Count total conversations
        total_conversations = conversations.count_documents({'user_id': str(request.user.id)})
        
        # Count by provider
        provider_counts = {}
        pipeline = [
            {'$match': {'user_id': str(request.user.id)}},
            {'$group': {'_id': '$provider', 'count': {'$sum': 1}}}
        ]
        provider_results = conversations.aggregate(pipeline)
        
        for result in provider_results:
            provider_counts[result['_id']] = result['count']
        
        client.close()
        
        context = {
            'total_conversations': total_conversations,
            'provider_counts': provider_counts,
        }
        
        return render(request, 'users/profile.html', context)
        
    except Exception as e:
        print(f"Error retrieving profile statistics: {e}")
        messages.error(request, 'Error retrieving profile statistics. Please try again.')
        return render(request, 'users/profile.html', {
            'total_conversations': 0,
            'provider_counts': {}
        })


def logout_view(request):
    try:
        # Close any old database connections
        close_old_connections()
        
        # Store session key before logout
        session_key = request.session.session_key
        
        # Perform logout
        logout(request)
        
        # Clear Django session
        if session_key:
            Session.objects.filter(session_key=session_key).delete()
        
        # Clear session data
        request.session.flush()
        
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home')
        
    except Exception as e:
        print(f"Error during logout: {e}")
        messages.error(request, 'An error occurred during logout. Please try again.')
        return redirect('home')