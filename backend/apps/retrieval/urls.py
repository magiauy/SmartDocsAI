from django.urls import path

from .views import RetrievalSearchView

urlpatterns = [
    path("search/", RetrievalSearchView.as_view(), name="retrieval-search"),
]
