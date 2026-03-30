def test_django_settings_load(settings):
    assert "rest_framework" in settings.INSTALLED_APPS
    assert settings.ROOT_URLCONF == "app.urls"
