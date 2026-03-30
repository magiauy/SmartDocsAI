def test_demo_page_renders_main_workflow(api_client):
    response = api_client.get("/demo/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "SmartDocsAI Demo" in content
    assert "Document Upload" in content
    assert "Conversation Setup" in content
    assert "Chat Console" in content
    assert "demo/demo.js" in content
