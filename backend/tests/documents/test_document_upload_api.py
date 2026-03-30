from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_upload_endpoint_accepts_multiple_files(api_client, mocker):
    from apps.documents.models import Document

    mocked_delay = mocker.patch("apps.documents.services.upload_service.process_document.delay")

    file_a = SimpleUploadedFile("a.txt", b"alpha", content_type="text/plain")
    file_b = SimpleUploadedFile("b.txt", b"beta", content_type="text/plain")

    response = api_client.post(
        "/api/documents/upload/",
        {"files": [file_a, file_b]},
        format="multipart",
    )

    assert response.status_code == 201
    payload = response.json()["data"]["documents"]
    assert len(payload) == 2
    assert Document.objects.count() == 2
    assert mocked_delay.call_count == 2
    assert all(Path(item["file_path"]).suffix == ".txt" for item in payload)
