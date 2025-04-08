from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from rag_legal.models import ChatMessage

class MessageService:
    @staticmethod
    async def save_message(user: User, role: str, content: str, cost: float = None) -> None:
        """
        Guarda un mensaje en la base de datos.
        
        Args:
            user: Usuario autenticado
            role: Rol del mensaje ('user' o 'assistant')
            content: Contenido del mensaje
        """
        try:
            # Verificar que el usuario esté autenticado
            if not user or not user.is_authenticated:
                print("Usuario no autenticado, no se guarda el mensaje")
                return
                
            # Crear y guardar el mensaje
            await sync_to_async(ChatMessage.objects.create)(
                user=user,
                role=role,
                content=content,
                cost=cost
            )
            
        except Exception as e:
            print(f"Error al guardar el mensaje: {str(e)}")
    
    @staticmethod
    async def save_conversation(user: User, user_message: str, assistant_response: str, token_cost: float) -> None:
        """
        Guarda una conversación completa (mensaje del usuario y respuesta del asistente).
        
        Args:
            user: Usuario autenticado
            user_message: Mensaje del usuario
            assistant_response: Respuesta del asistente
        """
        # Verificar que el usuario esté autenticado
        if not user or not user.is_authenticated:
            print("Usuario no autenticado, no se guarda la conversación")
            return
            
        # Guardar el mensaje del usuario
        await MessageService.save_message(
            user=user,
            role='user',
            content=user_message,
        )
        
        # Guardar la respuesta del asistente
        await MessageService.save_message(
            user=user,
            role='assistant',
            content=assistant_response,
            cost=token_cost
        ) 