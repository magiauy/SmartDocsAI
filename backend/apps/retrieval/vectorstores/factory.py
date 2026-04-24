from django.conf import settings as django_settings

from apps.retrieval.vectorstores.neo4j_store import Neo4jStore
from apps.retrieval.vectorstores.qdrant_store import QdrantStore


def get_retrieval_store(settings_obj=None, embedding_service=None):
    resolved_settings = settings_obj or django_settings
    backend = str(getattr(resolved_settings, "RETRIEVAL_STORE_BACKEND", "qdrant")).strip().lower()

    if backend == "qdrant":
        return QdrantStore(resolved_settings, embedding_service=embedding_service)
    if backend == "neo4j":
        return Neo4jStore(resolved_settings, embedding_service=embedding_service)

    raise ValueError(f"Unsupported RETRIEVAL_STORE_BACKEND: {backend}")