from pprint import pprint
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END, START

import os
import sys
from pathlib import Path

# Este es un simple grafo de conversación, tiene memoria y guarda estados, tiene un simple contexto.
# python langGraph/services/langgraph_service.py

# Agregar el directorio raíz al PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Configurar Django antes de cualquier importación de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')

import django
django.setup()

# Importar modelos y servicios de Django después de la configuración
from .state_manager import StateManager

llm = "gpt-4o-mini"
temperature = 0

token_input_price = 0.15/1000000
token_output_price = 0.6/1000000

class State(MessagesState):
    thread_id: str

class LangGraphService:
    def __init__(self):
        self.llm = ChatOpenAI(model=llm, temperature=temperature)
        
    def create_chat_graph(self) -> StateGraph:
        """
        Crea y configura el grafo de conversación.
        """

        def node_inicial(state: State) -> State:
            
            initial_message = """Eres una enfermera, responde maximo en 10 palabras."""
            
            # Agregar mensajes del sistema al estado
            messages = [SystemMessage(content=initial_message)] + state["messages"]

            response = self.llm.invoke(messages)
            return {"messages": response}
                
        # Crear el grafo de estado
        workflow = StateGraph(State)
        workflow.add_node("inicial", node_inicial)
        
        # Agregar las aristas del grafo
        workflow.add_edge(START, "inicial")
        workflow.add_edge("inicial", END)
        
        return workflow.compile()
    
    def process_user_message(self, user_message: str, thread_id: str, user) -> dict:
        """
        Procesa un mensaje del usuario y retorna la respuesta del asistente junto con la información de tokens.
        """
        
        graph = self.create_chat_graph()
        result = graph.invoke({
            "messages": [HumanMessage(content=user_message)],
            "thread_id": thread_id
        })

        # Obtener y guardar la respuesta del asistente
        assistant_message = result["messages"][-1]
    
        token_input = assistant_message.response_metadata["token_usage"].get("prompt_tokens", 0)
        token_output = assistant_message.response_metadata["token_usage"].get("completion_tokens", 0)
        total_tokens = assistant_message.response_metadata["token_usage"].get("total_tokens", 0)

        # Obtener información de tokens de la respuesta
        token_info = {
            "prompt_tokens": token_input,
            "completion_tokens": token_output,
            "total_tokens": total_tokens,
            "cost": f"${(token_input * token_input_price) + (token_output * token_output_price):.6f}"
        }

        return {
            "response": assistant_message.content,
            "token_info": token_info
        }

if __name__ == "__main__":
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    service = LangGraphService()
    
    # Ejemplo de uso
    thread_id = "test_conversation"
    user_message = "Como me llamo?"
    
    # Crear un usuario de prueba
    test_user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Procesar un mensaje de prueba
    response = service.process_user_message(user_message, thread_id, test_user)
    print(f"Usuario: {user_message}")
    print(f"Asistente: {response}") 