from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import serializers

import logging
import asyncio
import threading
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.load import load, dumpd

from langgraph.checkpoint.memory import MemorySaver

from chat_rag.rag_legal.graph import create_workflow
from chat_rag.rag_legal.state import State
from chat_rag.models import State as StateModel

from chat_rag.rag_legal.summary_graph import create_summary_workflow

from rich.console import Console
from rich.logging import RichHandler

from asgiref.sync import async_to_sync, sync_to_async

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)
logger = logging.getLogger("rich")
# Create your views here.
class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    conversation_id = serializers.CharField()

class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    token_info = serializers.DictField()

# memory_saver = MemorySaver()

def save_state(conversation_id: str, state_data: dict) -> None:
    """
    Guarda el estado de la conversación en la base de datos.
    
    Args:
        conversation_id: ID de la conversación
        state_data: Datos del estado a guardar
    """
    StateModel.objects.update_or_create(
        conversation_id=conversation_id,
        defaults={'state': state_data}
    )

def get_state(conversation_id: str) -> dict:
    """
    Obtiene el estado de la conversación desde la base de datos.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        dict: Estado de la conversación o None si no existe
    """
    try:
        state_obj = StateModel.objects.get(conversation_id=conversation_id)
        return state_obj.state
    except StateModel.DoesNotExist:
        return None

class RAGLegalView(APIView):
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
        
        # Crear el workflow con el memory_saver
        workflow, memory_saver = await create_workflow(config=config)
        
        state_history = len(list(workflow.get_state_history(config)))
        
        initial_state = State(
            messages=[HumanMessage(content=chat_request['message'])],
            token_info={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0
                }
            )
        
        if state_history == 0:
            console.print("No hay State en memoria", style="bold yellow")
            state = await sync_to_async(get_state)(chat_request['conversation_id'])
            if state:
                console.print("Hay historial de base de datos", style="bold red")
                # Actualizar el estado con el nuevo mensaje
                messages_data = state.get('messages', [])
                messages = load(messages_data)
                summary_data = state.get('summary', '')
                summary = load(summary_data)
                token_info = state.get('token_info', {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0
                })
                initial_state = State(
                    messages=messages + [HumanMessage(content=chat_request['message'])],
                    summary=summary,
                    token_info=token_info
                    )

        # Procesar el mensaje y obtener el estado
        result = await workflow.ainvoke(initial_state, config)
        
        # Guardar el estado en la base de datos
        state = workflow.get_state(config)

        serializable_state = dumpd(state.values)
        
        # Ejecutar la función síncrona en un contexto asíncrono
        await sync_to_async(save_state)(
            chat_request['conversation_id'],
            serializable_state
        )
        
        response = result["messages"][-1]

        response_data = {
            "response": response.content,
            "token_info": result["token_info"]
        }

        # Enviar la respuesta inmediatamente
        response = Response(
            ChatResponseSerializer(response_data).data, 
            status=status.HTTP_200_OK
        )
        
        def background_summary():
            asyncio.run(self._generate_summary(config, state, chat_request['conversation_id'], memory_saver))
        
        if state.values.get("create_summary", False):
            console.print("Llamando a resumen", style="bold red")

            threading.Thread(target=background_summary).start()

        return response

    async def _generate_summary(self, config: RunnableConfig, state: State, conversation_id: str, memory_saver: MemorySaver) -> None:
        try:
            summary_workflow = await create_summary_workflow(memory_saver=memory_saver)
            await summary_workflow.ainvoke(state.values, config)
            state = summary_workflow.get_state(config)
            serializable_state = dumpd(state.values)
            
            await sync_to_async(save_state)(
                conversation_id,
                serializable_state
            )

        except Exception as e:
            console.print(f"Error al generar el resumen: {str(e)}", style="bold red")
            