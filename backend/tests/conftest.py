import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()
