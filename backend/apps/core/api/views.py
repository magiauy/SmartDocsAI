from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses.builders import api_success
from apps.llm.services.provider_factory import ProviderFactory


class HealthView(APIView):
    def get(self, request):
        services = {
            "mysql": bool(getattr(settings, "DATABASES", {}).get("default")),
            "redis": bool(getattr(settings, "CELERY_BROKER_URL", "")),
            "qdrant": bool(getattr(settings, "QDRANT_URL", "")),
        }
        return Response(api_success({"services": services}), status=status.HTTP_200_OK)


class ProviderListView(APIView):
    def get(self, request):
        factory = ProviderFactory(settings)
        return Response(api_success({"providers": factory.describe()}), status=status.HTTP_200_OK)


class ProviderTestView(APIView):
    def post(self, request):
        provider = request.data.get("provider", "mock")
        factory = ProviderFactory(settings)
        client = factory.build(provider)
        return Response(
            api_success(
                {
                    "provider": provider,
                    "resolved_provider": client.provider_name,
                    "mode": "live" if client.provider_name == provider else "mock",
                }
            ),
            status=status.HTTP_200_OK,
        )
