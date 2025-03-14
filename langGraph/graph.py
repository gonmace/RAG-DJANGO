from decouple import config
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_graph_retriever import GraphRetriever
from graph_retriever.strategies import Eager

def main():
    # Configurar el modelo de embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=config('OPENAI_API_KEY'),
        model="text-embedding-3-small"
    )

    # Inicializar Chroma
    vectorstore = Chroma(
        collection_name="langchain",
        embedding_function=embeddings,
        persist_directory="./chromadb"
    )

    # Configurar el retriever de grafo
    graph_retriever = GraphRetriever(
        store=vectorstore,
        edges=[
            # ("ID_Original", "id"),  # Conecta documentos del mismo título
            ("id", "ID_Original"),  # Conecta documentos del mismo título
            # ("Documento", "Documento"),
            # ("Libro", "Libro"),
            # ("Título", "Título"),
            # ("Capítulo", "Capítulo")
        ],
        strategy=Eager(k=18, start_k=14, max_depth=1)
    )

    # Ejemplo de consulta con filtro de metadata
    query = "En caso que tengo hijkastros y han sido reconocidos por su padre que acaba de fallecer, ellos pueden reclamar en la pmisma proporcion su herenciaq que los hijos naturales?"
    # results = graph_retriever.invoke(query)
    # Definimos el filtro de metadata
    
    metadata_filter = {"Documento": "CODIGO CIVIL"}
    
    # Realizamos la consulta con el filtro
    results = graph_retriever.invoke(
        query,
        # filter=metadata_filter  # Aplicamos el filtro aquí
    )

    # Mostrar resultados
    print("\nResultados de la búsqueda:")
    print("-" * 50)
    for i, doc in enumerate(results, 1):
        print(f"\nDocumento {i}:")
        print(f"Contenido: {doc.page_content}")
        print(f"Metadatos: {doc.metadata}")
        print("-" * 50)

if __name__ == "__main__":
    main() 