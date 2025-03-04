from decouple import config
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from uuid import uuid4


c_name = "langchain"
p_directory = "./chromadb"


class LangChainService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config('OPENAI_API_KEY'),
            model="text-embedding-ada-002"
        )
        self.vectorstore = None
        self.initialize_vectorstore()

    def initialize_vectorstore(self):
        """Inicializa o carga una base de datos de vectores existente."""
        try:
            self.vectorstore = Chroma(
                collection_name=c_name,
                embedding_function=self.embeddings,
                persist_directory=p_directory
            )
            return self.vectorstore
        except Exception as e:
            print(f"Error al inicializar vectorstore: {e}")
            return None

    def add_document(self,
                     text: str,
                     metadata: Optional[List[dict]] = None):
        """Añade textos al vectorstore."""
        if self.vectorstore is None:
            self.initialize_vectorstore()

        # Si no se proporcionan metadatos,
        # crear una lista de diccionarios vacíos
        if metadata is None:
            metadata = [{}]

        # Crear un documento para cada texto con su metadata correspondiente
        document = [
            Document(
              page_content=text,
              metadata=metadata)
            ]

        # Generar IDs únicos para cada documento
        ids = [str(uuid4()) for _ in text]

        return self.vectorstore.add_documents(
            documents=document,
            ids=ids
        )

    def get_all_documents(self):
        """Obtiene todos los documentos almacenados en la colección."""
        
        if self.vectorstore is None:

            self.initialize_vectorstore()

        # Obtener la colección directamente del vectorstore
        collection = self.vectorstore
        result = collection.get()
        documents = []

        for i in range(len(result['documents'])):
            documents.append({
                'id': result['ids'][i],
                'text': result['documents'][i],
                'metadata': result['metadatas'][i] if result['metadatas'] else {}
            })

        return documents

    def similarity_search(self, query: str, k: int = 4):
        """Realiza una búsqueda por similitud."""
        if self.vectorstore is None:
            raise ValueError("Vectorstore no inicializado. Llama a initialize_vectorstore primero.")
        
        return self.vectorstore.similarity_search(
            query=query,
            k=k
        )

    def query_collection(self, query_text: str, n_results: int = 2):
        """Realiza una búsqueda directa usando ChromaDB."""
        if self.vectorstore is None:
            self.initialize_vectorstore()

        # Realizar la búsqueda utilizando el vectorstore
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query=query_text,
            k=n_results
        )
        # Formatear los resultados
        documents = []
        scores = []
        ids = []
        metadatas = []

        for doc, score in results:
            documents.append(doc.page_content)
            scores.append(score)
            ids.append(doc.metadata.get('id', ''))
            metadatas.append(doc.metadata)

        return {
            'ids': [ids],
            'documents': [documents],
            'distances': [scores],
            'metadatas': [metadatas]
        }

    def delete_documents(self, ids: List[str]):
        """Elimina documentos del vectorstore por sus IDs."""
        if self.vectorstore is None:
            self.initialize_vectorstore()

        self.vectorstore.delete(ids=ids)

    def update_text(self, doc_id: str, new_text: str, new_metadata: Optional[dict] = None):
        """Actualiza un documento existente manteniendo su ID."""
        if self.vectorstore is None:
            self.initialize_vectorstore()

        # Asegurar que siempre haya al menos un campo en los metadatos
        if new_metadata is None or not new_metadata:
            new_metadata = {"source": "none"}

        try:
            updated_document = Document(
              page_content=new_text,
              metadata=new_metadata
              )

            # Actualizar el documento en Chroma
            self.vectorstore.update_document(
                document_id=doc_id,
                document=updated_document
            )

            print(f"Documento actualizado exitosamente con ID: {doc_id}")
            return True
        except Exception as e:
            print(f"Error detallado al actualizar documento: {str(e)}")
            raise Exception(f"Error al actualizar el documento: {str(e)}")
