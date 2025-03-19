# Este archivo está intencionalmente vacío
# Se usa para marcar el directorio como un paquete de Python 

from .langgraph_service import LangGraphService

# Crear una instancia del servicio
service = LangGraphService()

# Exportar el grafo directamente
workflow = service.create_chat_graph()

__all__ = ['LangGraphService', 'workflow'] 