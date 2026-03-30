from django.urls import path

from conversation.views import ConversationDetailView, ConversationView

urlpatterns = [
    path('', ConversationView.as_view()),
    path('<int:conversation_id>/', ConversationDetailView.as_view()),
]
