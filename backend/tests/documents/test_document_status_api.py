import pytest


@pytest.mark.django_db
def test_document_status_endpoint_returns_processing_fields(api_client):
    from apps.documents.models import Document

    document = Document.objects.create(
        title="Policy",
        original_filename="policy.txt",
        file_path="media/policy.txt",
        mime_type="text/plain",
        size_bytes=12,
        source="upload",
        status="uploaded",
        processing_status="uploaded",
        summary_status="pending",
    )

    response = api_client.get(f"/api/documents/{document.id}/status/")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["processing_status"] == "uploaded"
    assert payload["summary_status"] == "pending"
