from django.urls import path

from conversation.views import (
    ConversationDetailView,
    ConversationMessagesView,
    ConversationView,
)

urlpatterns = [
    path("", ConversationView.as_view()),
    path("<int:conversation_id>/", ConversationDetailView.as_view()),
    path("<int:conversation_id>/messages/", ConversationMessagesView.as_view()),
]
