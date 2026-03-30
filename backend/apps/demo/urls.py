from django.urls import path

from .views import DemoPageView

urlpatterns = [
    path("", DemoPageView.as_view(), name="demo-page"),
]
