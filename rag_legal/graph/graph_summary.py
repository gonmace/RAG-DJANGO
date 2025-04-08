from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from langchain_core.runnables import RunnableConfig
from rag_legal.graph.configuration import Configuration
from rag_legal.graph.state import State
from langgraph.checkpoint.memory import MemorySaver

from rich.console import Console
console = Console()

async def evaluate_summarizing(state: State) -> State:
    messages = state["messages"]
    console.print(f"len(messages): {len(messages)}", style="bold white")
    if len(messages) > 4:
        console.print("Se generara resumen", style="bold red")
        state["create_summary"] = True
    else:
        console.print("No se generara resumen", style="bold green")
        state["create_summary"] = False
    return state

async def should_summarize(state: State) -> bool:
    return state.get("create_summary", False)

async def summarize_conversation(state: State):
    console.print("Creando resumen", style="bold white")
    
    model_chat = ChatOpenAI(
        model=Configuration.llm_chat_model,
        temperature=0
        )

    summary = state.get("summary", "")

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
    
    messages = state["messages"] + [HumanMessage(content=summary_prompt)]

    callback_handler = OpenAICallbackHandler()

    response = model_chat.invoke(
        messages,
        config={"callbacks":[callback_handler]}
        )
    
    print(f"Prompt Tokens: {callback_handler.prompt_tokens}")
    print(f"Completion Tokens: {callback_handler.completion_tokens}")
    print(f"Successful Requests: {callback_handler.successful_requests}")
    print(f"Total Cost (USD): ${callback_handler.total_cost}")
    state["token_cost"] += callback_handler.total_cost
    
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]

    return {
        "summary": response.content,
        "messages": delete_messages,
        "token_cost": state["token_cost"]
        }


async def create_workflow_summary(memory_saver: MemorySaver) -> tuple[StateGraph, MemorySaver]:
    workflowSummary = StateGraph(State)
    
    workflowSummary.add_node("evaluate_summarizing", evaluate_summarizing)
    workflowSummary.add_node("summarize_conversation", summarize_conversation)
    

    workflowSummary.set_entry_point("evaluate_summarizing")
    workflowSummary.add_conditional_edges("evaluate_summarizing", should_summarize,
                                           {True: "summarize_conversation",
                                            False: END}
                                           )
    workflowSummary.add_edge("summarize_conversation", END)
    
    return workflowSummary.compile(checkpointer=memory_saver)
