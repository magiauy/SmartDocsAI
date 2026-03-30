import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage


class StorageService:
    def save(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix
        storage_name = f"uploads/{uuid.uuid4().hex}{extension}"
        saved_path = default_storage.save(storage_name, uploaded_file)
        return os.path.join(settings.MEDIA_ROOT, saved_path)
