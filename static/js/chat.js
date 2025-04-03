// Configuración inicial
document.addEventListener('DOMContentLoaded', function() {
    let messages = [];
    let isLoading = false;
    
    // Referencias a elementos del DOM
    const chatContainer = document.querySelector('#chat-container');
    const messageInput = document.querySelector('#message-input');
    const sendButton = document.querySelector('#send-button');
    const messagesDiv = document.querySelector('#messages');
    
    // Funciones auxiliares
    const formatTime = (date) => {
        return new Intl.DateTimeFormat('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    };
    
    const formatDate = (date) => {
        return new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        }).format(date);
    };
    
    const scrollToBottom = () => {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    };
    
    const createMessageElement = (message) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat ${message.role === 'user' ? 'chat-end' : 'chat-start'}`;
        
        messageDiv.innerHTML = `
            <div class="flex flex-col">
                <div class="chat-bubble ${
                    message.role === 'user' 
                        ? 'chat-bubble-primary' 
                        : 'chat-bubble-secondary'
                } rounded-xl backdrop-blur-sm">
                    ${message.content}
                </div>
                <div class="text-xs opacity-70 mt-1 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                }">
                    <span class="badge badge-ghost badge-sm">
                        ${formatTime(message.timestamp)}
                    </span>
                    <span class="badge badge-ghost badge-sm ml-1">
                        ${formatDate(message.timestamp)}
                    </span>
                </div>
            </div>
        `;
        
        return messageDiv;
    };
    
    const showLoadingIndicator = () => {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat chat-start';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="chat-bubble bg-base-200 text-base-content shadow-[0_2px_8px_rgba(0,0,0,0.08)] rounded-2xl backdrop-blur-sm">
                <span class="loading loading-dots loading-sm"></span>
            </div>
        `;
        messagesDiv.appendChild(loadingDiv);
        scrollToBottom();
    };
    
    const removeLoadingIndicator = () => {
        const loadingIndicator = document.querySelector('#loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    };
    
    // Manejador del envío de mensajes
    const handleSubmit = async (e) => {
        e.preventDefault();
        const messageContent = messageInput.value.trim();
        
        if (!messageContent || isLoading) return;
        
        const userMessage = {
            role: 'user',
            content: messageContent,
            timestamp: new Date()
        };
        
        // Agregar mensaje del usuario
        messages.push(userMessage);
        messagesDiv.appendChild(createMessageElement(userMessage));
        messageInput.value = '';
        scrollToBottom();
        
        isLoading = true;
        showLoadingIndicator();
        sendButton.disabled = true;
        messageInput.disabled = true;
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Función para obtener el token CSRF de Django
                },
                body: JSON.stringify({ message: messageContent })
            });
            
            const data = await response.json();
            
            const assistantMessage = {
                role: 'assistant',
                content: data.response,
                timestamp: new Date()
            };
            
            messages.push(assistantMessage);
            removeLoadingIndicator();
            messagesDiv.appendChild(createMessageElement(assistantMessage));
            
        } catch (error) {
            console.error('Error:', error);
            const errorMessage = {
                role: 'assistant',
                content: 'Lo siento, ha ocurrido un error. Por favor, intenta de nuevo.',
                timestamp: new Date()
            };
            messages.push(errorMessage);
            removeLoadingIndicator();
            messagesDiv.appendChild(createMessageElement(errorMessage));
        } finally {
            isLoading = false;
            sendButton.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
            scrollToBottom();
        }
    };
    
    // Función para obtener el token CSRF de Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Event listeners
    document.querySelector('#chat-form').addEventListener('submit', handleSubmit);
    messageInput.addEventListener('input', () => {
        sendButton.disabled = !messageInput.value.trim() || isLoading;
    });
}); 