"""AI Models configuration and constants"""

# Available AI models that users can select from
AI_MODELS = [
    {
        'id': 'openai',
        'name': 'ChatGPT (OpenAI)',
        'description': 'Advanced language models from OpenAI',
        'color': '#10a37f',  # OpenAI green
        'icon': 'message-square',
        'models': [
            {'id': 'gpt-4', 'name': 'GPT-4 (Most Capable)'},
            {'id': 'gpt-4-turbo-preview', 'name': 'GPT-4 Turbo (Latest)'},
            {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo (Fast & Efficient)'}
        ]
    },
    {
        'id': 'google',
        'name': 'Gemini (Google)',
        'description': 'Gemini models from Google',
        'color': '#4285f4',  # Google blue
        'icon': 'zap',
        'models': [
            {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
            {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash'},
            {'id': 'gemini-1.0-pro', 'name': 'Gemini 1.0 Pro'}
        ]
    }
]