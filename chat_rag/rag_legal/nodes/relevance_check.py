from langchain_core.vectorstores import VectorStore

from chat_rag.rag_legal.state import State

from rich.console import Console

console = Console()

class RelevanceCheckNode:
    """
    Nodo que verifica la relevancia de una consulta contra un vectorstore.
    
    Esta clase se encarga de determinar si una consulta dada es lo suficientemente
    relevante para continuar con el procesamiento, utilizando un modelo de embeddings
    y un vectorstore para la comparación.
    
    Attributes:
        threshold (float): Umbral de similitud para considerar una consulta relevante.
        vectorstore (VectorStore): Almacén de vectores para búsqueda de similitud.
    """
    
    def __init__(self, vectorstore: VectorStore, threshold: float = 0.5):
        """
        Inicializa el nodo de verificación de relevancia.
        
        Args:
            vectorstore (VectorStore): Vectorstore para búsqueda de similitud.
            threshold (float, optional): Umbral de similitud. Por defecto 0.5.
        """
        self.threshold = threshold
        self.vectorstore = vectorstore

    async def __call__(self, state: State) -> bool:
        """
        Ejecuta la verificación de relevancia sobre el estado actual.
        
        Args:
            state (State): Estado actual del sistema que contiene la consulta.
            
        Returns:
            bool: True si la consulta es relevante, False en caso contrario.
        """
        console.print("---relevance_check---", style="bold green")
        # Obtener la última consulta del estado
        query = state["query"][0]
        if not query:
            console.print("No se proporcionó una consulta.", style="bold red")
            return state

        console.print(f"query: {query}", style="green")
        # Realizar búsqueda de similitud en el vectorstore
        results = await self.vectorstore.asimilarity_search_with_relevance_scores(query, k=1)

        # Obtener el score de similitud del primer resultado
        score = results[0][1]
        console.print(f"result score: {score}", style="bold green")

        # Verificar si hay resultados y si superan el umbral
        if not results or score < self.threshold:
            console.print(f"No hay resultados relevantes para la consulta: {query}", style="bold red")
            console.print("-" * 20, style="bold yellow")
            return False

        console.print(f"Hay resultados relevantes para la consulta: {query}", style="green")
        console.print("-" * 20, style="bold green")
        return True
