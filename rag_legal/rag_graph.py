# rag_graph.py
from asgiref.sync import async_to_sync
from langgraph.checkpoint.memory import MemorySaver
from rag_legal.graph.graph import create_workflow
from rag_legal.graph.graph_summary import create_workflow_summary
from langgraph.graph import StateGraph

from rich.console import Console
console = Console()

console.print("[rag_graph.py] Compilando grafos...", style="bold blue")

# Este archivo se ejecutará una sola vez cuando se importe
memory_saver = MemorySaver()

workflow = async_to_sync(create_workflow)(memory_saver=memory_saver)
workflow_summary = async_to_sync(create_workflow_summary)(memory_saver=memory_saver)

workflow: StateGraph
workflow_summary: StateGraph

console.print("[rag_graph.py] Grafos cargados ✅", style="bold green")