from django.urls import path
from . import views

urlpatterns = [
    path('models/', views.list_models, name='list_models'),
    path('generate/', views.generate_response, name='generate_response'),
]