from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.load import load, dumpd
from langgraph.checkpoint.memory import MemorySaver

from rag_legal.graph.graph import create_workflow
from rag_legal.graph.state import State
from rag_legal.utils.persistence import save_state, get_state
from rag_legal.graph.summary_graph import create_summary_workflow
from rag_legal.services.message_service import MessageService

from rich.console import Console
from asgiref.sync import sync_to_async

console = Console()

class ChatService:
    @staticmethod
    async def process_message(message: str, conversation_id: str, user=None) -> dict:
        """
        Procesa un mensaje y retorna la respuesta del chatbot.
        
        Args:
            message: El mensaje del usuario
            conversation_id: ID de la conversación
            user: Usuario autenticado (opcional)
            
        Returns:
            dict: Respuesta del chatbot con información de tokens
        """
        config = RunnableConfig(
            recursion_limit=10,
            configurable={
                "thread_id": conversation_id
            }
        )
        
        # Crear el workflow con el memory_saver
        workflow, memory_saver = await create_workflow(config=config)
        
        state_history = len(list(workflow.get_state_history(config)))
        
        initial_state = State(
            messages=[HumanMessage(content=message)],
            token_info={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0
            }
        )
        
        if state_history == 0:
            console.print("No hay State en memoria", style="bold yellow")
            try:
                summary, messages, token_info = await sync_to_async(get_state)(conversation_id)

                if messages:
                    console.print("Hay historial de base de datos", style="bold red")
                    messages = load(messages)
                    summary = load(summary)

                    initial_state = State(
                        messages=messages + [HumanMessage(content=message)],
                        summary=summary,
                        token_info=token_info
                    )
            except Exception as e:
                console.print(f"Error al obtener el estado de la base de datos: {str(e)}", style="bold red")

        # Procesar el mensaje y obtener el estado
        result = await workflow.ainvoke(initial_state, config)
        
        # Guardar el estado en la base de datos
        state = workflow.get_state(config)
        
        messages = state.values.get('messages', [])
        summary = state.values.get('summary', {})
        token_info = state.values.get('token_info', {})
        
        messages_data = dumpd(messages)
        summary_data = dumpd(summary)
        token_info_data = dumpd(token_info)

        await sync_to_async(save_state)(
            conversation_id,
            messages_data,
            summary_data,
            token_info_data
        )
        
        response = result["messages"][-1]
        
        # Guardar el mensaje del usuario y la respuesta del asistente en la base de datos
        # Solo si el usuario está autenticado
        if user and user.is_authenticated:
            try:
                await MessageService.save_conversation(
                    user=user,
                    user_message=message,
                    assistant_response=response.content
                )
            except Exception as e:
                console.print(f"Error al guardar la conversación: {str(e)}", style="bold red")
        else:
            console.print("Usuario no autenticado, no se guarda la conversación", style="bold yellow")
        
        # Iniciar el proceso de resumen en segundo plano si es necesario
        if state.values.get("create_summary", False):
            console.print("Llamando a resumen", style="bold red")
            await ChatService._generate_summary(config, state, conversation_id, memory_saver)
        
        return {
            "response": response.content,
            "token_info": result["token_info"]
        }
    
    @staticmethod
    async def _generate_summary(config: RunnableConfig, state: State, conversation_id: str, memory_saver: MemorySaver) -> None:
        """
        Genera un resumen de la conversación en segundo plano.
        
        Args:
            config: Configuración del proceso de ejecución
            state: Estado actual de la conversación
            conversation_id: ID de la conversación
            memory_saver: Objeto para guardar el estado en memoria
        """
        try:
            summary_workflow = await create_summary_workflow(memory_saver=memory_saver)
            
            await summary_workflow.ainvoke(state.values, config)
            
            state = summary_workflow.get_state(config)
            
            messages = state.values.get('messages', [])
            summary = state.values.get('summary', {})
            token_info = state.values.get('token_info', {})
            
            messages_data = dumpd(messages)
            summary_data = dumpd(summary)
            token_info_data = dumpd(token_info)
            
            await sync_to_async(save_state)(
                conversation_id,
                messages_data,
                summary_data,
                token_info_data
            )

        except Exception as e:
            console.print(f"Error al generar el resumen: {str(e)}", style="bold red") 