from typing import Dict, TypedDict, Annotated, Sequence, List
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END, START

llm = "gpt-4o-mini"
temperature = 0

class State(MessagesState):
    customer_id: str

class LangGraphService:
    def __init__(self):
        self.llm = ChatOpenAI(model=llm, temperature=temperature)
        
    def create_chat_graph(self) -> StateGraph:
        """
        Crea y configura el grafo de conversación.
        """
        system_messages = [
                SystemMessage(content="Eres un asistente amigable y servicial."),
            ]
        
        
        def node_inicial(state: State) -> State:
            print("==============")
            print(state["messages"])
            print("==============")
            if not state["messages"]:
                add_messages(state, system_messages)
            
            print(state["messages"])
            return {"messages": [self.llm.invoke(state["messages"])]}
        
        workflow = StateGraph(State)
        workflow.add_node("inicial", node_inicial)
        workflow.add_edge(START, "inicial")
        workflow.add_edge("inicial", END)
        # workflow.set_entry_point("process")
        
        return workflow.compile()
    
    
    def process_user_message(self, user_message: str, conversation_id: str) -> str:
        """
        Procesa un mensaje del usuario y retorna la respuesta del asistente.
        """
        
        
        mensaje = "hola"
        graph = self.create_chat_graph()
        result = graph.invoke({
            "messages": [HumanMessage(content=user_message)],
            "customer_id": conversation_id
        })
        
        assistant_message = result["messages"][-1].content
        return assistant_message

if __name__ == "__main__":
    # Crear una instancia del servicio
    # initial_state = State(messages=[], customer_id="test_conversation")
    service = LangGraphService()
    
    # Ejemplo de uso
    conversation_id = "test_conversation"
    user_message = "Hola, ¿cómo estás?"
    
    # Procesar un mensaje de prueba
    response = service.process_user_message(user_message, conversation_id)
    print(f"Usuario: {user_message}")
    print(f"Asistente: {response}") 