# AI Platform

A Django-based platform for interacting with various AI models.

## Features

- Integration with OpenAI and Google AI models
- User authentication and session management
- Conversation history storage in MongoDB
- Safe prompt checking with FastAPI microservice

## Setup

1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with the following variables:

```
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
MONGODB_URI=mongodb://mongodb:27017/ai_platform
```

5. Run migrations: `python manage.py migrate`
6. Start the development server: `python manage.py runserver`

## Docker Setup

1. Make sure Docker and Docker Compose are installed
2. Create a `.env` file as described above
3. Build and run the containers:

```bash
docker compose up --build
```

The application will be available at http://localhost:8000

## Project Structure

- `ai_platform/`: Main Django project settings
- `ai_models/`: AI model integration and API endpoints
- `core/`: Core application views and templates
- `users/`: User authentication and management
- `safe_prompt_api/`: FastAPI microservice for prompt safety checks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.