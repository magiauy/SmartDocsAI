from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses.builders import api_success
from apps.retrieval.services.search_service import SearchService


class RetrievalSearchView(APIView):
    def get(self, request):
        query = request.query_params.get("query", "")
        raw_ids = request.query_params.getlist("document_ids")
        document_ids = [int(value) for value in raw_ids if str(value).isdigit()]
        hits = SearchService().search(query=query, document_ids=document_ids, limit=5)
        return Response(api_success({"hits": hits}))
