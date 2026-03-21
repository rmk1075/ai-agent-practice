from django.urls import path

from chat.views import chat_stream

urlpatterns = [
    path("stream/", chat_stream)
]