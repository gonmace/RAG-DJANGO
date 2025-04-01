from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
    )
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from chat_rag.utils.token_counter import TokenCounterCallback
from chat_rag.utils.utils import get_message_text
from chat_rag.rag_legal.configuration import Configuration
from chat_rag.rag_legal.state import State

from rich.console import Console
console = Console()


token_counter = TokenCounterCallback(
        model_name=Configuration.llm_chat_model
        )

async def process_input(state: State, *, config: RunnableConfig) -> State:
    """
    Procesa la consulta del usuario y genera una respuesta utilizando un modelo de lenguaje.
    
    Args:
        state: Estado actual de la conversación
        config: Configuración del proceso de ejecución
    """
    configuration = Configuration.from_runnable_config(config)
    
    console.print("---process_input---", style="bold cyan")
    
    # Get context from retriever if exists
    context = state.get("context", "")
        
    # Create prompt template
    system_message_content = (
    "You are an assistant with knowledge in law for question-answering tasks. "
    "Use the following retrieved context fragments to answer the question. "
    "If you don't know the answer, simply say that you don't know. "
    "If the question refers to a single article, mention the article number. "
    "Only respond in Spanish. \n"
    "Context: {context} \n"
    )
    
    # Format the prompt with context and question
    formatted_prompt = system_message_content.format(
        context=context
        )
    
    # Crear el mensaje del sistema
    system_message = SystemMessage(content=formatted_prompt)
    
    # Asegurarse de que el historial de mensajes se mantenga y agregar el nuevo mensaje
    messages =  [system_message] + state.get("messages", [])
    
    # console.print(messages, style="bold cyan")
    
    # Crear el modelo
    llm_chat = ChatOpenAI(
        model_name=configuration.llm_chat_model,
        temperature=0.1,
        callbacks=[token_counter]
    )
    
    response = await llm_chat.ainvoke(messages)
    
    token = token_counter.get_token_summary()
    
    State.update_token_info(state, token)
    
    
    console.print(token, style="bold cyan")
    console.print(f"Token total {state['token_info']}", style="bold cyan")
    console.print("-"*20, style="bold cyan")
    
    state["messages"] = response
    return state