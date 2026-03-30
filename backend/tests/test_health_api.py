def test_health_endpoint_returns_dependency_flags(api_client):
    response = api_client.get("/api/health/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "mysql" in payload["data"]["services"]
    assert "qdrant" in payload["data"]["services"]


def test_provider_list_returns_config_readiness(api_client):
    response = api_client.get("/api/providers/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"]["providers"], list)
