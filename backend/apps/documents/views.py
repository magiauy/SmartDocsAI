from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses.builders import api_success

from .models import Document
from .serializers import DocumentSerializer, DocumentStatusSerializer, DocumentUploadSerializer
from .services.upload_service import UploadService
from apps.jobs.tasks.document_tasks import process_document


class DocumentListView(generics.ListAPIView):
    queryset = Document.objects.order_by("-created_at")
    serializer_class = DocumentSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(api_success({"documents": serializer.data}))


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(api_success(serializer.data))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(api_success(message="Deleted"), status=status.HTTP_200_OK)


class DocumentStatusView(generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentStatusSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(api_success(serializer.data))


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data={"files": request.FILES.getlist("files")})
        serializer.is_valid(raise_exception=True)
        documents = UploadService().create_documents_from_files(serializer.validated_data["files"])
        payload = DocumentSerializer(documents, many=True).data
        return Response(api_success({"documents": payload}), status=status.HTTP_201_CREATED)


class DocumentIndexView(APIView):
    def post(self, request, pk):
        process_document.delay(pk)
        return Response(api_success({"document_id": pk, "queued": True}), status=status.HTTP_202_ACCEPTED)


class DocumentBulkIndexView(APIView):
    def post(self, request):
        document_ids = request.data.get("document_ids", [])
        for document_id in document_ids:
            process_document.delay(document_id)
        return Response(api_success({"document_ids": document_ids, "queued": True}), status=status.HTTP_202_ACCEPTED)
