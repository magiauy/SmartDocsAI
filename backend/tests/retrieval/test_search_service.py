def test_search_service_returns_hits_in_expected_shape(mocker):
    from apps.retrieval.services.search_service import SearchService

    adapter = mocker.Mock()
    adapter.search.return_value = [{"content": "hit", "score": 0.88, "metadata": {"document_id": 1}}]

    service = SearchService(adapter)
    hits = service.search("policy", [1], limit=3)

    assert isinstance(hits, list)
    assert hits[0]["metadata"]["document_id"] == 1
