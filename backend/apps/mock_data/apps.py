from django.apps import AppConfig


class MockDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mock_data"
