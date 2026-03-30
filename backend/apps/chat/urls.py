from django.urls import path

from .views import (
    ConversationDetailView,
    ConversationDocumentUpdateView,
    ConversationListCreateView,
    ConversationMessageView,
    ConversationStatusView,
)

urlpatterns = [
    path("", ConversationListCreateView.as_view(), name="conversation-list"),
    path("<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("<int:pk>/status/", ConversationStatusView.as_view(), name="conversation-status"),
    path("<int:pk>/documents/", ConversationDocumentUpdateView.as_view(), name="conversation-documents"),
    path("<int:pk>/messages/", ConversationMessageView.as_view(), name="conversation-messages"),
]
