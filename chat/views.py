from django.conf import settings
from django.shortcuts import render
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rag_legal.utils.persistence import get_state
from decouple import config
from langchain_core.load import load
from langchain_core.messages import HumanMessage, AIMessage
from rag_legal.models import TokenCost

from rich.console import Console
console = Console()

if settings.DEBUG:
    DOMAIN = 'http://localhost:8000'
else:
    DOMAIN = config('DOMAIN', default='http://localhost:8000', cast=str)

API_URL = f"{DOMAIN}/rag_legal/api/v1/legal/"

@login_required
def chat_legal(request):
    # Obtener las conversaciones en el state del usuario actual
    try:
        state_result = get_state(request.user)
        if state_result is not None:
            _, messages, _ = state_result
        else:
            messages = []
    except Exception as e:
        messages = []
        print(f"Error al obtener el estado: {str(e)}")
    
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
    
    # Obtener los valores de credits y total_cost del usuario actual
    try:
        token_cost = TokenCost.objects.get(user=request.user)
        credits = token_cost.credits
        total_cost = token_cost.total_cost
        console.print(f"Credits: {credits}", style="bold green")
        console.print(f"Total cost: {total_cost}", style="bold green")
    except TokenCost.DoesNotExist:
        credits = 0.5  # Valor por defecto
        total_cost = 0
    
    return render(request, 'chat_legal.html', {
        'conversations': conversations,
        'credits': credits*1000000,
        'total_cost': total_cost*1000000,
        'ratio': total_cost/credits*100
    })

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
            
            # console.print(f"Enviando cookies: {session_cookies}", style="bold green")
            
            response = requests.post(
                API_URL, 
                json=payload, 
                headers=headers, 
                cookies=session_cookies
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result['response']
                
                # Obtener los valores actualizados de credits y total_cost
                try:
                    token_cost = TokenCost.objects.get(user=request.user)
                    credits = token_cost.credits
                    total_cost = token_cost.total_cost
                except TokenCost.DoesNotExist:
                    credits = 0.5  # Valor por defecto
                    total_cost = 0
                
                return JsonResponse({
                    "response": assistant_message,
                    "credits": credits,
                    "total_cost": total_cost
                })
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