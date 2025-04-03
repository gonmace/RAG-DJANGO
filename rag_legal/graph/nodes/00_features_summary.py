from app.rag_memory.state import State
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from app.rag_memory.configuration import Configuration
from app.utils.token_counter import TokenCounterCallback

token_counter = TokenCounterCallback(
        model_name=Configuration.llm_chat_model
        )

model_chat = ChatOpenAI(
    model=Configuration.llm_chat_model,
    temperature=0,
    callbacks=[token_counter]
    )

def summarize_conversation(state: State):
    
    # First, we get any existing summary
    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        summary_prompt = (
            f"""This is the user's information so far:  
            {summary}  
            Please update the information **only if new details are present**, following these fields:  
            - User's name  
            - Address  
            - Age  
            - Phone number  
            - Shared links  
            Do **not** add any additional context or explanations—only update the relevant fields."""
        )
    else:
        summary_prompt = """Extract the following information from the conversation **only if present**:
        - User's name  
        - Address  
        - Age  
        - Phone number  
        - Shared links  
        Do **not** include any additional context or explanations—only update the relevant fields."""

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_prompt)]
    response = model_chat.invoke(messages)
    
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}