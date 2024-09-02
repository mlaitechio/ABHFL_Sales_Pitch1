from django.urls import path
from .views import ChatAPIView ,my_view

urlpatterns = [
    path('', my_view, name='my_view'),
    path('chat/', ChatAPIView.as_view(), name='chat_api'),
]