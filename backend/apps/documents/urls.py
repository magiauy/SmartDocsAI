from django.urls import path

from .views import (
    DocumentBulkIndexView,
    DocumentDetailView,
    DocumentIndexView,
    DocumentListView,
    DocumentStatusView,
    DocumentUploadView,
)

urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
    path("index/bulk/", DocumentBulkIndexView.as_view(), name="document-index-bulk"),
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<int:pk>/index/", DocumentIndexView.as_view(), name="document-index"),
    path("<int:pk>/status/", DocumentStatusView.as_view(), name="document-status"),
]
