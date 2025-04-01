"""
Módulo para la creación y configuración del workflow de resumen de conversación.
Este módulo define la estructura del grafo de procesamiento que maneja el resumen
de la conversación de forma asíncrona.
"""
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, RemoveMessage

from chat_rag.rag_legal.configuration import Configuration
from chat_rag.rag_legal.state import State
from chat_rag.utils.token_counter import TokenCounterCallback
from langgraph.checkpoint.memory import MemorySaver

from rich.console import Console
console = Console()

token_counter = TokenCounterCallback(
        model_name=Configuration.llm_chat_model
        )

model_chat = ChatOpenAI(
    model=Configuration.llm_chat_model,
    temperature=0,
    callbacks=[token_counter]
    )


def summarize_conversation(state: State):

    summary = state.get("summary", "")

    if summary:
        summary_prompt = (
            f"""This is the user's information so far:  
            {summary}  
            Please update the information **only if new details are present**, following these fields:  
            - User's name  
            - Address  
            - Age  
            - Phone number  
            - Shared links  
            Do **not** add any additional context or explanations—only update the relevant fields."""
        )
    else:
        summary_prompt = """Extract the following information from the conversation **only if present**:
            - User's name  
            - Address  
            - Age  
            - Phone number  
            - Shared links  
            Do **not** include any additional context or explanations—only update the relevant fields."""
    
    messages = state["messages"] + [HumanMessage(content=summary_prompt)]

    response = model_chat.invoke(messages)
    
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]

    return {"summary": response.content, "messages": delete_messages}

async def create_summary_workflow(memory_saver: MemorySaver):

    # Crear el grafo de estado
    workflowSummary = StateGraph(State)
    
    # Agregar el nodo de generación de resumen
    workflowSummary.add_node("summarize_conversation", summarize_conversation)
    
    # Configurar el flujo de trabajo
    workflowSummary.set_entry_point("summarize_conversation")
    
    # Compilar el workflow
    return workflowSummary.compile(checkpointer=memory_saver) 