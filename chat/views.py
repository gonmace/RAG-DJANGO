from django.shortcuts import render
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rag_legal.models import State as StateModel
from rag_legal.utils.persistence import get_state
from rich.console import Console
from langchain_core.load import load
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
console = Console()

@login_required
def chat_legal(request):
    # Obtener las últimas 6 conversaciones del usuario actual
    summary, messages, token_info = get_state(request.user)

    # Crear un diccionario para almacenar las conversaciones
    conversations = []
    
    # Recorremos de dos en dos: HumanMessage seguido de AIMessage
    for i in range(0, len(messages) - 1, 2):
        user_msg = load(messages[i])
        assistant_msg = load(messages[i + 1])
        
        if isinstance(user_msg, HumanMessage) and isinstance(assistant_msg, AIMessage):
            conversations.append({
                'user_message': user_msg.content,
                'assistant_message': assistant_msg.content,
            })

    # Invertir la lista para mostrar las conversaciones más antiguas primero
    conversations.reverse()
    
    return render(request, 'chat_legal.html', {'conversations': conversations})

API_URL = "http://localhost:8000/rag_legal/api/v1/legal/"

@csrf_exempt  # sólo para pruebas, idealmente se maneja con CSRFToken
@login_required
def chat_ajax_view(request):
    if request.method == "POST":
        user = str(request.user)
        try:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get("message", "")
            payload = {
                'message': message,
                'conversation_id': user
                }
            
            # Agregar las cabeceras necesarias para la autenticación
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': request.COOKIES.get('csrftoken'),
            }
            
            # Incluir todas las cookies de sesión para la autenticación
            session_cookies = request.COOKIES.copy()
            
            console.print(f"Enviando cookies: {session_cookies}", style="bold green")
            
            response = requests.post(
                API_URL, 
                json=payload, 
                headers=headers, 
                cookies=session_cookies
            )
            
            console.print(f"Respuesta: {response.status_code}", style="bold blue")
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result['response']
            else:
                console.print(f"Error en la respuesta: {response.text}", style="bold red")
                assistant_message = "Lo siento, hubo un error al procesar tu solicitud."

            return JsonResponse({"response": assistant_message})
        except json.JSONDecodeError as e:
            console.print(f"Error JSON: {str(e)}", style="bold red")
            return JsonResponse({"error": "JSON inválido", "details": str(e)}, status=400)
        except requests.exceptions.HTTPError as e:
            console.print(f"Error HTTP: {str(e)}", style="bold red")
            return JsonResponse({"error": "Error de autenticación", "details": str(e)}, status=401)
        except Exception as e:
            console.print(f"Error inesperado: {str(e)}", style="bold red")
            return JsonResponse({"error": "Error inesperado", "details": str(e)}, status=500)