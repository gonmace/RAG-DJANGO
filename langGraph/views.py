from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from .services.langgraph_service import LangGraphService

# Vista para renderizar la página del chat
def chat_view(request):
    return render(request, 'langGraph/chat.html')

# Vista para procesar mensajes
@csrf_exempt
@require_http_methods(["POST"])
def process_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return JsonResponse({
                'error': 'El mensaje no puede estar vacío'
            }, status=400)
            
        if not conversation_id:
            conversation_id = "+59167728817"
            # conversation_id = str(uuid.uuid4())
        
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'El usuario debe estar autenticado'
            }, status=401)
        
        # Procesar el mensaje usando el servicio
        service = LangGraphService()
        result = service.process_user_message(user_message, conversation_id, request.user)
        
        return JsonResponse({
            'response': result['response'],
            'conversation_id': conversation_id,
            'prompt_tokens': result['token_info']['prompt_tokens'],
            'completion_tokens': result['token_info']['completion_tokens'],
            'total_tokens': result['token_info']['total_tokens'],
            'cost': result['token_info']['cost']
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error del servidor: {str(e)}'
        }, status=500)
