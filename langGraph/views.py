from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
import requests

# Vista para renderizar la página del chat
@login_required
def chat_view(request):
    return render(request, 'langGraph/chat.html')

# Vista para procesar mensajes
@login_required
@require_http_methods(["POST"])
def process_message(request):
    try:
        # Convertir el body a string
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return JsonResponse({
                'error': 'El mensaje no puede estar vacío'
            }, status=400)
            
        if not conversation_id:
            conversation_id = "+59167728817"
        
        # Procesar el mensaje usando el servicio
        api_url = 'http://localhost:8000/rag_legal/api/v1/legal/'
        payload = {
            'message': user_message,
            'conversation_id': conversation_id
        }
        
        # Agregar las cabeceras necesarias para la autenticación
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CSRFToken': request.COOKIES.get('csrftoken'),
        }
        
        response = requests.post(api_url, json=payload, headers=headers, cookies=request.COOKIES)
        response.raise_for_status()  # Lanza una excepción si hay error HTTP
        result = response.json()
        
        return JsonResponse({
            'response': result['response'],
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
