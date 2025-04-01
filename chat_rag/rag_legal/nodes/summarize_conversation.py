from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from langchain_core.messages import SystemMessage

from chat_rag.utils.token_counter import TokenCounterCallback
from chat_rag.rag_legal.configuration import Configuration
from chat_rag.rag_legal.state import State

from rich.console import Console
console = Console()

token_counter = TokenCounterCallback(
        model_name=Configuration.llm_chat_model
        )

async def summarize_conversation(state: State, *, config: RunnableConfig) -> State:
    """
    Genera un resumen de la conversación actual.
    
    Args:
        state: Estado actual de la conversación
        config: Configuración del proceso de ejecución
    """
    console.print("---summarize_conversation---", style="bold magenta")
    
    # Obtener el resumen existente si hay uno
    current_summary = state.get("summary", "")
    
    # Crear el prompt para el resumen
    if current_summary:
        summary_prompt = (
            f"""Este es el resumen actual de la conversación:
            {current_summary}
            
            Por favor, actualiza el resumen con la información más reciente de la conversación.
            Mantén el formato y estructura del resumen existente.
            """
        )
    else:
        summary_prompt = """Por favor, genera un resumen de la conversación actual.
        Incluye los puntos principales discutidos y cualquier información relevante.
        """
    
    # Crear el mensaje del sistema
    system_message = SystemMessage(content=summary_prompt)
    
    # Obtener los últimos mensajes de la conversación
    messages = [system_message] + state["messages"][-4:]  # Últimos 4 mensajes para contexto
    
    # Crear el modelo
    llm_chat = ChatOpenAI(
        model_name=Configuration.llm_chat_model,
        temperature=0.1,
        callbacks=[token_counter]
    )
    
    # Generar el resumen
    response = await llm_chat.ainvoke(messages)
    
    # Actualizar el estado con el nuevo resumen
    state["summary"] = response.content
    
    # Actualizar la información de tokens
    token = token_counter.get_token_summary()
    State.update_token_info(state, token)
    
    console.print("Resumen generado:", style="bold magenta")
    console.print(response.content, style="magenta")
    console.print("-"*20, style="bold magenta")
    
    return state 