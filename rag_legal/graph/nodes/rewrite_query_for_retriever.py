from langchain_core.prompts import PromptTemplate

from langchain_core.language_models.base import BaseLanguageModel

from rag_legal.graph.configuration import Configuration
from langchain_core.runnables import RunnableLambda
from rag_legal.graph.state import State

from rich.console import Console

from rag_legal.utils.token_counter import TokenCounterCallback

console = Console()

# Prompt para dividir y ajustar consulta para retrieval
split_and_prepare_prompt = PromptTemplate.from_template("""
You are an assistant helping to process user queries for a legal document retriever.

Given a user's question, follow these steps:
1. If the question includes multiple parts or topics, split it into separate standalone questions.
2. If the question is already simple and focused, return it as-is.
3. For each resulting question, rewrite it to be as clear and precise as possible, using legal terms if relevant.

Query: "{query}"

Return the final list of queries (1 per line, no numbering):
""")

class QueryRewriter:
    def __init__(
        self, model: BaseLanguageModel,
        token_counter: TokenCounterCallback | None = None
        ):
        self.model = model
        self.token_counter = token_counter
        """
        Inicializa el QueryRewriter con el prompt y el contador de tokens.

        Args:
            model (BaseLanguageModel): Modelo de lenguaje a utilizar.
            token_counter (TokenCounterCallback | None): Callback opcional para contar tokens.
        """


    async def __call__(self, state: State) -> State:
        """
        Reformula la consulta proporcionada usando el contexto anterior.

        Args:
            state (State): Estado actual con las consultas y mensajes.
            config (RunnableConfig): Configuración para el modelo de lenguaje.

        Returns:
            State: Estado actualizado con la consulta reformulada.
        """
        # Determinar la consulta más reciente
        console.print("---rewrite_query_for_retriever---", style="bold magenta")
        console.print("Reformula la consulta para el retriever", style="magenta")

        query = state["query"][0]
        console.print(f"Query original: {query}", style="magenta")

        # Crear el reescritor de consultas
        chain = split_and_prepare_prompt | self.model | RunnableLambda(
            lambda msg: msg.content.strip().split("\n")
            )

        # Ejecutar la reformulación de la consulta
        subqueries  = await chain.ainvoke(
            {"query": query}
        )
        
        console.print(f"Query reescrita: {subqueries}", style="bold magenta")
        
        # Obtener y actualizar la información de tokens solo si token_counter está presente
        if self.token_counter is not None:
            console.print("Token info inicial:", style="magenta")
            console.print(state["token_info"], style="magenta")
            State.update_token_info(state, self.token_counter.get_token_summary())
            console.print("Token info final:", style="magenta")
            console.print(state["token_info"], style="magenta")
        
        state["query"] = subqueries
                
        console.print("-" * 20, style="bold magenta")

        return state
