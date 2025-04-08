import {marked} from "marked";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("message-input");
    const chatBox = document.querySelector("#chat-container .overflow-y-auto");

    // Cargar las conversaciones guardadas
    loadSavedConversations();

    // Referencias a los elementos de la barra de progreso
    const creditsProgress = document.getElementById("credits-progress");
    const creditsValue = document.getElementById("credits-value");

    let ratio = window.initialTotalCost/window.initialCredits*100;

    updateProgressBar(ratio);

    function updateProgressBar(ratio) {
        if (ratio > 70) {
            creditsProgress.classList.add("progress-warning");
            creditsProgress.classList.remove("progress-success");
        }
        if (ratio > 90) {
            creditsProgress.classList.remove("progress-success");
            creditsProgress.classList.add("progress-error");        
        }
    }


    form.addEventListener("submit", async (e) => {
        e.preventDefault();
    
        const message = input.value.trim();
        if (!message) return;
    
        // Mostrar mensaje del usuario
        appendMessage(message, "end");
        input.value = "";
    
        // Mostrar burbuja de "escribiendo..." personalizada
        const typingBubble = document.createElement("div");
        typingBubble.className = "chat chat-start";
        typingBubble.innerHTML = `
            <div class="chat-bubble bg-base-200 text-base-content rounded-2xl backdrop-blur-sm">
                <span class="loading loading-dots loading-sm"></span>
            </div>
        `;
        chatBox.appendChild(typingBubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    
        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({ message })
            });
    
            const data = await response.json();
    
            typingBubble.remove();

            if (data.response) {
                appendMessage(data.response, "start");
                } else {
                appendMessage("Error: respuesta vacía del servidor.", "start");
                }
            
            // Actualizar la barra de progreso cuando se recibe una respuesta del servidor
            if (data.total_cost !== undefined) {
                // Calcular el avance de la barra de progreso
                let ratio = data.total_cost/data.credits*100;
                creditsProgress.value = ratio;
                creditsValue.textContent = ratio.toFixed(0) + "%";
                updateProgressBar(ratio);
            }
            
        } catch (err) {
            typingBubble.remove();
            appendMessage("❌ Error de red. Intenta de nuevo.", "start");
        }
    });
    function scrollToBottomSmooth() {
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: "smooth"
        });
    }
    

    function appendMessage(text, side = "start", timestamp = null) {
        const wrapper = document.createElement("div");
        wrapper.className = `chat chat-${side}`;
        wrapper.innerHTML = `
            <div class="flex flex-col">
                <div class="chat-bubble ${side === "end" ? "chat-bubble-primary" : "chat-bubble-neutral"} rounded-xl backdrop-blur-sm break-words max-w-lg">
                    ${marked.parse(text)}
                </div>
                <div class="text-xs opacity-70 mt-1 text-${side === "end" ? "right" : "left"}">
                    <!-- 
                    La variable 'usuario' viene del template Django (chat_legal.html) donde se define como:
                    const usuario = "{% if request.user.first_name %}{{ request.user.first_name|first|upper }}{{ request.user.last_name|first|upper }}{% else %}{{ request.user.username|first|upper }}{% endif %}";
                    Esta variable contiene las iniciales del nombre del usuario actual.
                    -->
                    <span class="badge badge-ghost badge-sm">${side === "end" ? usuario : "Asistente"}</span>
                    <span class="badge badge-ghost badge-sm ml-1">${timestamp || new Date().toLocaleTimeString(undefined, { hour12: false })}</span>
                </div>
            </div>
        `;
        chatBox.appendChild(wrapper);
        scrollToBottomSmooth();
    }
    

    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Función para cargar las conversaciones guardadas
    function loadSavedConversations() {
        // 
        // La variable 'window.conversations' viene del template Django (chat_legal.html) donde se define como:
        // window.conversations = {{ conversations|safe }};
        // Esta variable contiene un array con el historial de conversaciones que se pasa desde la vista de Django
        // a través del contexto del template.
        //
        const conversations = window.conversations || [];
        
        // Mostrar cada conversación
        conversations.forEach(conversation => {
            // Mostrar mensaje del usuario
            appendMessage(conversation.user_message, "end", "-");
            // Mostrar mensaje del asistente
            appendMessage(conversation.assistant_message, "start", "-");
        });
    }
});





