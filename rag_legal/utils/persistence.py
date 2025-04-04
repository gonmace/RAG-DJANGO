from rag_legal.models import State as StateModel
from langchain_core.load import load
from rich.console import Console

console = Console()

def save_state(
    conversation_id: str,
    messages_data: list,
    summary_data: str,
    token_info_data: dict
    ) -> None:
    """
    Guarda el estado de la conversación en la base de datos.
    
    Args:
        conversation_id: ID de la conversación
        messages_data: Datos de los mensajes a guardar
        summary_data: Datos del resumen a guardar
        token_info_data: Datos de la información de los tokens a guardar
    """
    StateModel.objects.update_or_create(
        conversation_id=conversation_id,
        defaults={
            'messages': messages_data,
            'summary': summary_data,
            'token_info': token_info_data
            }
        )

def get_state(conversation_id: str) -> list[str, list, dict]:
    """
    Obtiene el estado de la conversación desde la base de datos.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        list[summary, messages, token_info]: Estado de la conversación o None si no existe
    """
    try:
        state_obj = StateModel.objects.get(conversation_id=conversation_id)
        return state_obj.summary, state_obj.messages, state_obj.token_info
    except StateModel.DoesNotExist:
        return None