from django.urls import path
from .views import my_view , HistoryAPIView , NewChatAPIView , ChatAPIView , StoreChat

urlpatterns = [
    path('', my_view, name='my_view'),  
    path('history/', HistoryAPIView.as_view(), name='history'),
    path('new_chat/', NewChatAPIView.as_view(), name='new_chat'),
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('store_chat/', StoreChat.as_view(), name='store_chat'),
]