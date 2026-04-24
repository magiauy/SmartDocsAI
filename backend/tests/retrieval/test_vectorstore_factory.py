from types import SimpleNamespace


def test_factory_returns_qdrant_store_by_default(mocker):
    from apps.retrieval.vectorstores.factory import get_retrieval_store

    mocked_store = object()
    mocked_ctor = mocker.patch("apps.retrieval.vectorstores.factory.QdrantStore", return_value=mocked_store)
    settings_obj = SimpleNamespace(RETRIEVAL_STORE_BACKEND="qdrant")

    resolved = get_retrieval_store(settings_obj=settings_obj)

    assert resolved is mocked_store
    mocked_ctor.assert_called_once_with(settings_obj, embedding_service=None)


def test_factory_returns_neo4j_store_when_configured(mocker):
    from apps.retrieval.vectorstores.factory import get_retrieval_store

    mocked_store = object()
    mocked_ctor = mocker.patch("apps.retrieval.vectorstores.factory.Neo4jStore", return_value=mocked_store)
    settings_obj = SimpleNamespace(RETRIEVAL_STORE_BACKEND="neo4j")

    resolved = get_retrieval_store(settings_obj=settings_obj)

    assert resolved is mocked_store
    mocked_ctor.assert_called_once_with(settings_obj, embedding_service=None)


def test_factory_raises_for_unsupported_backend():
    from apps.retrieval.vectorstores.factory import get_retrieval_store

    settings_obj = SimpleNamespace(RETRIEVAL_STORE_BACKEND="unsupported")

    try:
        get_retrieval_store(settings_obj=settings_obj)
        assert False, "Expected ValueError for unsupported backend"
    except ValueError as exc:
        assert "Unsupported RETRIEVAL_STORE_BACKEND" in str(exc)