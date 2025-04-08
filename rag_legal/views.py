from asgiref.sync import async_to_sync

from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from rag_legal.services.rag_service import RagService
from langchain_core.runnables import RunnableConfig

from rich.console import Console

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    conversation_id = serializers.CharField()

class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    token_cost = serializers.FloatField()

class RAGLegalView(APIView):
    # Cambiamos temporalmente a AllowAny para depuración
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    
    console = Console()
    
    def post(self, request):
        return async_to_sync(self._post_async)(request)

    async def _post_async(self, request: Request) -> Response:
        # Validamos la entrada
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        chat_request = serializer.validated_data
        
        config = RunnableConfig(
            recursion_limit=10,
            configurable={
                "thread_id": chat_request['conversation_id']
            }
        )

        # Procesamos el mensaje usando el servicio
        response_data = await RagService.process_message(
            input=chat_request['message'],
            config=config,
            user=request.user
        )
        
        # Enviamos la respuesta
        return Response(
            ChatResponseSerializer(response_data).data, 
            status=status.HTTP_200_OK
        )
            