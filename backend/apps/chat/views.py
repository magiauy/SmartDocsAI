from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses.builders import api_error, api_success

from .models import Conversation, Message
from .serializers import ConversationSerializer, ConversationStatusSerializer, MessageSerializer
from .services.conversation_service import ConversationService
from .services.message_service import MessageService


class ConversationListCreateView(generics.ListCreateAPIView):
    queryset = Conversation.objects.order_by("-created_at")
    serializer_class = ConversationSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(api_success({"conversations": serializer.data}))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = ConversationService().create_conversation(serializer.validated_data)
        return Response(api_success(ConversationSerializer(conversation).data), status=201)


class ConversationDetailView(generics.RetrieveAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(api_success(serializer.data))


class ConversationStatusView(generics.RetrieveAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationStatusSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(api_success(serializer.data))


class ConversationDocumentUpdateView(APIView):
    def patch(self, request, pk):
        conversation = Conversation.objects.get(pk=pk)
        document_ids = request.data.get("document_ids", [])
        ConversationService().replace_documents(conversation, document_ids)
        return Response(api_success(ConversationSerializer(conversation).data))


class ConversationMessageView(APIView):
    def get(self, request, pk):
        messages = Message.objects.filter(conversation_id=pk).order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(api_success({"messages": serializer.data}))

    def post(self, request, pk):
        result, status_code = MessageService().send_message(pk, request.data)
        # Keep 409 as success payload so frontend can poll/read "ready_for_chat" gracefully.
        if status_code == 409:
            return Response(api_success(result), status=status_code)
        if status_code >= 400:
            return Response(api_error(result.get("message", "Request failed"), result), status=status_code)
        return Response(api_success(result), status=status_code)
