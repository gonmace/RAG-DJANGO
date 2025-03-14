from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from .services.langgraph_service import LangGraphService
from asgiref.sync import sync_to_async
from functools import partial

json_loads = sync_to_async(json.loads)
JsonResponse = sync_to_async(JsonResponse)

# Vista para renderizar la página del chat
def chat_view(request):
    return render(request, 'langGraph/chat.html')

# Vista para procesar mensajes
@csrf_exempt
@require_http_methods(["POST"])
async def process_message(request):
    try:
        # Convertir el body a string de manera asíncrona
        body_unicode = await sync_to_async(lambda: request.body.decode('utf-8'))()
        data = await json_loads(body_unicode)
        user_message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return await JsonResponse({
                'error': 'El mensaje no puede estar vacío'
            }, status=400)
            
        if not conversation_id:
            conversation_id = "+59167728817"
            # conversation_id = str(uuid.uuid4())
        
        # Verificar si el usuario está autenticado de manera asíncrona
        is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
        if not is_authenticated:
            return await JsonResponse({
                'error': 'El usuario debe estar autenticado'
            }, status=401)
        
        # Procesar el mensaje usando el servicio
        service = LangGraphService()
        result = await service.process_user_message(user_message, conversation_id, request.user)
        
        return await JsonResponse({
            'response': result['response'],
            'conversation_id': conversation_id,
            'prompt_tokens': result['token_info']['prompt_tokens'],
            'completion_tokens': result['token_info']['completion_tokens'],
            'total_tokens': result['token_info']['total_tokens'],
            'cost': result['token_info']['cost']
        })
    except json.JSONDecodeError:
        return await JsonResponse({
            'error': 'Formato JSON inválido'
        }, status=400)
    except Exception as e:
        return await JsonResponse({
            'error': f'Error del servidor: {str(e)}'
        }, status=500)
