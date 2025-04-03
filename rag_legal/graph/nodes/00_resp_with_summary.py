from app.rag_memory.state import State
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from app.rag_memory.configuration import Configuration
from app.utils.token_counter import TokenCounterCallback

token_counter = TokenCounterCallback(
        model_name=Configuration.llm_chat_model
        )

model_chat = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    callbacks=[token_counter]
    )

async def call_model(state: State):

    # Get summary if it exists
    summary = state.get("summary", "")

    # If there is summary, then we add it
    if summary:
        
        # Add summary to system message
        system_message = f"Summary of conversation earlier: {summary}"

        # Append summary to any newer messages
        messages = [SystemMessage(content=system_message)] + state["messages"]
    
    else:
        messages = state["messages"]
    
    response = await model_chat.ainvoke(messages)
    
    token_info = token_counter.get_token_summary()
    
    return {"messages": response, "token_info": token_info}