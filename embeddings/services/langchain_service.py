from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from decouple import config
import chromadb

class LangChainService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config('OPENAI_API_KEY'),
            model="text-embedding-ada-002"
        )
        self.vectorstore = None

    def initialize_vectorstore(self):
        """Inicializa o carga una base de datos de vectores existente."""
        self.persistent_client = chromadb.PersistentClient()
        self.vectorstore = Chroma(
          client=self.persistent_client,
          collection_name="langchain",
          embedding_function=self.embeddings
        )
        return self.vectorstore

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None):
        """Añade textos al vectorstore."""
        if self.vectorstore is None:
            self.initialize_vectorstore()
        
        return self.vectorstore.add_texts(
            texts=texts,
            metadatas=metadatas
        )

    def get_all_documents(self):
        """Obtiene todos los documentos almacenados en la colección."""
        if self.vectorstore is None:
            self.initialize_vectorstore()
        
        collection = self.persistent_client.get_collection("langchain")
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