# from typing import Dict, TypedDict, Annotated, Sequence, List
# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph, END
# from ..models import ChatMessage

# class AgentState(TypedDict):
#     messages: Sequence[HumanMessage | AIMessage]
#     next: str

# class LangGraphService:
#     def __init__(self):
#         # gpt-4o
#         self.llm = ChatOpenAI(model="gpt-4o-mini")
    
#     def create_chat_graph(self) -> StateGraph:
#         """
#         Crea y configura el grafo de conversación.
#         """
#         workflow = StateGraph(AgentState)
        
#         def process_message(state: AgentState) -> AgentState:
#             messages = state["messages"]
#             response = self.llm.invoke(messages)
#             return {"messages": [*messages, response], "next": END}
        
#         workflow.add_node("process", process_message)
#         workflow.set_entry_point("process")
        
#         return workflow.compile()
    
#     def get_conversation_messages(self, conversation_id: str) -> List[BaseMessage]:
#         """
#         Obtiene el historial de mensajes de una conversación.
#         """
#         messages = [
#             SystemMessage(content="Eres un asistente amigable y servicial."),
#         ]
        
#         chat_history = ChatMessage.objects.filter(
#             conversation_id=conversation_id
#         ).order_by('timestamp')
        
#         for msg in chat_history:
#             if msg.role == 'user':
#                 messages.append(HumanMessage(content=msg.content))
#             elif msg.role == 'assistant':
#                 messages.append(AIMessage(content=msg.content))
        
#         return messages
    
#     def process_user_message(self, user_message: str, conversation_id: str) -> str:
#         """
#         Procesa un mensaje del usuario y retorna la respuesta del asistente.
#         """
#         # Guardar mensaje del usuario
#         ChatMessage.objects.create(
#             role='user',
#             content=user_message,
#             conversation_id=conversation_id
#         )
        
#         # Obtener historial y procesar con LangGraph
#         messages = self.get_conversation_messages(conversation_id)
#         graph = self.create_chat_graph()
#         result = graph.invoke({
#             "messages": messages,
#             "next": "process"
#         })
        
#         # Obtener y guardar la respuesta del asistente
#         assistant_message = result["messages"][-1].content
#         ChatMessage.objects.create(
#             role='assistant',
#             content=assistant_message,
#             conversation_id=conversation_id
#         )
        
#         return assistant_message 