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
    summary: str

class LangGraphService:
    def __init__(self):
        self.llm = ChatOpenAI(model=llm, temperature=temperature)
        
    def create_chat_graph(self) -> StateGraph:
        """
        Crea y configura el grafo de conversación.
        """

        def node_inicial(state: State) -> State:
            
            initial_message = """Eres una enfermera, responde maximo en 10 palabras."""
            
            # obtener el resumen de la conversación si existe
            summary = state.get("summary", "")
            
            if summary:
                # Agregar resumen al mensaje del sistema
                system_message_summary = (
                    f"Summary of conversation earlier: {summary}"
                    "Puedes recordar esta información durante la conversación actual."
                    )
                messages = [SystemMessage(content=f"{initial_message} {system_message_summary}")] + state["messages"]
            else:
                # Agregar mensajes del sistema al estado
                messages = [SystemMessage(content=initial_message)] + state["messages"]


            response = self.llm.invoke(messages)
            return {"messages": response}
        
        def node_resumir_conversacion(state: State):
            # First, we get any existing summary
            summary = state.get("summary", "")

            # Create our summarization prompt 
            if summary:
                # A summary already exists
                summary_message = (
                    f"This is summary of the conversation to date: {summary}\n\n"
                    "Extend the summary by taking into account the new messages above:"
                )
            else:
                summary_message = """Extract only the relevant data from the conversation above in a paragraph: names, addresses, whether prices were discussed (yes/no), and any links mentioned. If there is no data, do not extract anything."""

            # Add prompt to our history
            messages = state["messages"] + [HumanMessage(content=summary_message)]
            # from pprint import pprint
            # print("================")
            # pprint(messages)
            # print("================")
            response = self.llm.invoke(messages)
            
            # Delete all but the 2 most recent messages
            delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
            return {"summary": response.content, "messages": delete_messages}
        
        # Determine whether to end or summarize the conversation
        def should_continue(state: State):            
            """Return the next node to execute."""
            messages = state["messages"]
            
            # If there are more than six messages, then we summarize the conversation
            if len(messages) > 6:
                return "resumir"
            
            # Otherwise we can just end
            return END
        
        # Crear el grafo de estado
        workflow = StateGraph(State)
        workflow.add_node("inicial", node_inicial)
        workflow.add_node("resumir", node_resumir_conversacion)
        
        # Agregar las aristas del grafo
        workflow.add_edge(START, "inicial")
        workflow.add_conditional_edges("inicial", should_continue)
        workflow.add_edge("resumir", END)
        
        return workflow.compile()
    
    def process_user_message(self, user_message: str, thread_id: str, user) -> dict:
        """
        Procesa un mensaje del usuario y retorna la respuesta del asistente junto con la información de tokens.
        """
        # Obtener el estado guardado o inicializarlo
        stored_state = StateManager.get_or_create_graph_state(thread_id, user)
        
        graph = self.create_chat_graph()
        result = graph.invoke({
            "messages": stored_state["messages"] + [HumanMessage(content=user_message)],
            "thread_id": thread_id,
            "summary": stored_state["summary"]
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

        # Guardar el nuevo estado del grafo en la BD
        new_state = {
            "messages": result["messages"],
            "summary": result.get("summary", stored_state.get("summary", ""))
        }
        StateManager.update_graph_state(thread_id, user, new_state)

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