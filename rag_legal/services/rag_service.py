import asyncio
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.load import load, dumpd

from rag_legal.graph.state import State
from rag_legal.models import TokenCost
from rag_legal.utils.persistence import save_state, get_state
from rag_legal.services.message_persistent import MessageService
from rag_legal.rag_graph import workflow, workflow_summary

from rich.console import Console
from asgiref.sync import sync_to_async

console = Console()

class RagService:
    @staticmethod
    async def process_message(input: str, config: RunnableConfig, user=None) -> dict:
        """
        Procesa un mensaje y retorna la respuesta del chatbot.
        
        Args:
            message: El mensaje del usuario
            conversation_id: ID de la conversación
            user: Usuario autenticado (opcional)
            
        Returns:
            dict: Respuesta del chatbot con información de tokens
        """
        
        # Crear el workflow con el memory_saver
        # Obtener los valores de credits y total_cost del usuario actual
        try:
            token_cost = await sync_to_async(TokenCost.objects.get)(user=user)
            credits = token_cost.credits
            total_cost = token_cost.total_cost
            ratio = total_cost/credits*100
            if ratio > 100:
                return {
                    "response": "No tienes suficientes créditos para continuar. Por favor, actualiza tu plan.",
                    "token_cost": 0
                }
        except TokenCost.DoesNotExist:
            credits = 0.5  # Valor por defecto
            total_cost = 0.45
        
        
        state_history = len(list(workflow.get_state_history(config)))
        
        initial_state = State(
            messages=[HumanMessage(content=input)]
        )
        
        if state_history == 0:
            console.print("No hay State en memoria", style="bold yellow")
            try:
                state_result = await sync_to_async(get_state)(user)
                
                if state_result is not None:
                    summary, messages, token_cost = state_result
                    console.print("Hay historial de base de datos", style="bold red")
                    messages = load(messages)
                    summary = load(summary)

                    initial_state = State(
                        messages=messages + [HumanMessage(content=input)],
                        summary=summary,
                        token_cost=token_cost
                    )
            except Exception as e:
                console.print(f"Error al obtener el estado de la base de datos: {str(e)}", style="bold red")

        # Procesar el mensaje y obtener el estado
        result = await workflow.ainvoke(initial_state, config)

        state = workflow.get_state(config)
        
        messages = state.values.get('messages', [])
        summary = state.values.get('summary', {})
        
        messages_data = dumpd(messages)
        summary_data = dumpd(summary)
        token_cost_data = dumpd(state.values.get("token_cost", 0))
        
        await sync_to_async(save_state)(
            user,
            messages_data,
            summary_data,
            token_cost_data
            )
        
        response = result["messages"][-1]
                    
        # Crear la tarea asíncrona sin esperar su resultado
        # asyncio.create_task(
        #     RagService._generate_summary(config, state, user)
        # )
        
        # Crear la tarea asíncrona esperando el resultado
        await RagService._save_and_summary(config, state, user)
    
        return {
            "response": response.content,
            "token_cost": state.values.get("token_cost", 0)
        }
    
    @staticmethod
    async def _save_and_summary(config: RunnableConfig, state: State, user: str) -> None:
        """
        Genera un resumen de la conversación en segundo plano.
        
        Args:
            config: Configuración del proceso de ejecución
            state: Estado actual de la conversación
            conversation_id: ID de la conversación
            memory_saver: Objeto para guardar el estado en memoria
        """
        
        try:
            console.print("Llamando a resumen", style="bold green")
            
            # console.print(state.values.get("token_cost", 0), style="bold green")
            await workflow_summary.ainvoke(state.values, config)
            
            state = workflow_summary.get_state(config)
            
            messages = state.values.get('messages', [])
            summary = state.values.get('summary', {})
            token_cost = state.values.get('token_cost', 0)
            
            messages_data = dumpd(messages)
            summary_data = dumpd(summary)
            token_cost_data = dumpd(token_cost)
            
            await sync_to_async(save_state)(
                user,
                messages_data,
                summary_data,
                token_cost_data
            )
            
            # Guardar el mensaje del usuario y la respuesta del asistente en la base de datos
            # Solo si el usuario está autenticado
            if user and user.is_authenticated:
                try:
                    await MessageService.save_conversation(
                        user=user,
                        user_message=messages[-2].content,
                        assistant_response=messages[-1].content,
                        token_cost=token_cost
                    )
                except Exception as e:
                    console.print(f"Error al guardar la conversación: {str(e)}", style="bold red")
            else:
                console.print("Usuario no autenticado, no se guarda la conversación", style="bold yellow")

        except Exception as e:
            console.print(f"Error al generar el resumen: {str(e)}", style="bold red") 