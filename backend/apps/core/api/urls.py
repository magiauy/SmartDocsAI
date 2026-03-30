from django.urls import path

from .views import HealthView, ProviderListView, ProviderTestView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("providers/", ProviderListView.as_view(), name="providers"),
    path("providers/test/", ProviderTestView.as_view(), name="providers-test"),
]
