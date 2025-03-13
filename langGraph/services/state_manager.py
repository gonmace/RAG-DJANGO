from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langGraph.models import GraphState

class StateManager:
    @staticmethod
    def _message_to_dict(message):
        """
        Convierte un mensaje de LangChain a un diccionario serializable.
        """
        return {
            'type': message.__class__.__name__,
            'content': message.content,
            'additional_kwargs': message.additional_kwargs
        }
    
    @staticmethod
    def _dict_to_message(message_dict):
        """
        Convierte un diccionario a un mensaje de LangChain.
        """
        message_type = message_dict['type']
        if message_type == 'HumanMessage':
            return HumanMessage(content=message_dict['content'], **message_dict['additional_kwargs'])
        elif message_type == 'AIMessage':
            return AIMessage(content=message_dict['content'], **message_dict['additional_kwargs'])
        elif message_type == 'SystemMessage':
            return SystemMessage(content=message_dict['content'], **message_dict['additional_kwargs'])
        return None
        
    @classmethod
    def get_or_create_graph_state(cls, thread_id, user):
        """
        Recupera el estado del grafo desde la base de datos o lo inicializa si no existe.
        """
        state, created = GraphState.objects.get_or_create(
            thread_id=thread_id,
            user=user,
            defaults={"state": {"messages": [], "summary": ""}}
        )
        # Convertir los mensajes guardados a objetos LangChain
        if state.state.get("messages"):
            state.state["messages"] = [cls._dict_to_message(m) for m in state.state["messages"]]
        return state.state  # Devuelve el estado guardado

    @classmethod
    def update_graph_state(cls, thread_id, user, new_state):
        """
        Guarda el estado actualizado del grafo en la base de datos.
        """
        # Convertir los mensajes a formato serializable antes de guardar
        if "messages" in new_state:
            new_state["messages"] = [cls._message_to_dict(m) for m in new_state["messages"]]
        GraphState.objects.filter(thread_id=thread_id, user=user).update(state=new_state) 