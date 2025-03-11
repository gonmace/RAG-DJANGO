from decouple import config
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from uuid import uuid4
from unidecode import unidecode


c_name = "langchain"
p_directory = "./chromadb"
embedding_model = "text-embedding-3-small"


class LangChainService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config('OPENAI_API_KEY'),
            model=embedding_model
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

    def similarity_search(self, query: str, k: int = 4, filter: Optional[dict] = None):
        """Realiza una búsqueda por similitud con filtrado por metadatos y scores de relevancia.
        
        Args:
            query (str): El texto de consulta para la búsqueda
            k (int): Número de resultados a retornar
            filter (dict, optional): Diccionario con los filtros de metadatos a aplicar
            
        Returns:
            List[Tuple[Document, float]]: Lista de tuplas con (documento, score de relevancia)
        """
        if self.vectorstore is None:
            raise ValueError("Vectorstore no inicializado. Llama a initialize_vectorstore primero.")
        return self.vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter=filter
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

    def get_unique_document_values(self):
        """Obtiene los valores únicos del metadato 'Documento' directamente de Chroma."""
        if self.vectorstore is None:
            self.initialize_vectorstore()

        # Obtener la colección directamente
        collection = self.vectorstore
        result = collection.get()
        
        # Extraer valores únicos del metadato 'Documento'
        documentos_set = set()
        if result['metadatas']:
            for metadata in result['metadatas']:
                if metadata and 'Documento' in metadata:
                    documentos_set.add(metadata['Documento'])
        
        # Convertir a lista ordenada
        return sorted(list(documentos_set))

    def get_document_content(self, documento_nombre: str):
        """Obtiene todo el contenido de un documento específico."""
        if self.vectorstore is None:
            self.initialize_vectorstore()

        collection = self.vectorstore
        result = collection.get()
        document_content = []

        for i in range(len(result['documents'])):
            metadata = result['metadatas'][i] if result['metadatas'] else {}
            if metadata and metadata.get('Documento') == documento_nombre:
                document_content.append({
                    'id': result['ids'][i],
                    'text': result['documents'][i],
                    'metadata': metadata
                })

        return document_content

    def subdivide_by_keyword(self, documento_nombre: str, keyword: str):
        """Subdivide un documento existente basándose en una o más palabras clave.
        
        Args:
            documento_nombre (str): Nombre del documento a subdividir
            keyword (str): Palabras clave separadas por comas. Pueden incluir patrones como '\n\n'
                         Las palabras son insensibles a acentos.
        """
        # Obtener el contenido original del documento
        original_content = self.get_document_content(documento_nombre)
        new_chunks = []
        
        # Convertir la cadena de palabras clave en una lista y normalizar (quitar acentos)
        keywords = [unidecode(k.strip()) for k in keyword.split(',')]
        
        for content in original_content:
            text = content['text']
            normalized_text = unidecode(text)  # Texto sin acentos para búsqueda
            chunk_created = False  # Flag para rastrear si se creó algún chunk
            
            # Aplicar cada patrón de división secuencialmente
            for key in keywords:
                # Manejar el caso especial de '\n\n'
                if key == '\\n\\n':
                    key = '\n\n'
                    # Para '\n\n' usamos el texto original ya que es un patrón especial
                    current_text = text
                    current_normalized_text = normalized_text
                    # Para '\n\n' no mantenemos el separador
                    keep_separator = False
                else:
                    current_text = text
                    current_normalized_text = normalized_text
                    # Para palabras clave normales, mantenemos el separador
                    keep_separator = True
                
                # Si la palabra clave está en el texto normalizado
                if key in current_normalized_text:
                    chunk_created = True  # Marcar que se creó al menos un chunk
                    # Encontrar todas las posiciones de la palabra clave en el texto normalizado
                    start = 0
                    positions = []
                    original_keys = []  # Almacenar las palabras clave originales
                    while True:
                        pos = current_normalized_text.find(key, start)
                        if pos == -1:
                            break
                        positions.append(pos)
                        # Guardar la palabra clave original del texto
                        original_keys.append(current_text[pos:pos + len(key)])
                        start = pos + len(key)
                    
                    # Usar las posiciones para dividir el texto original
                    last_pos = 0
                    paragraphs = []
                    for i, pos in enumerate(positions):
                        if keep_separator:
                            # Para el primer fragmento, añadimos la palabra al final
                            if i == 0:
                                paragraphs.append(current_text[last_pos:pos] + original_keys[i])
                            else:
                                # Para los fragmentos intermedios, añadimos la palabra al inicio y al final
                                paragraphs.append(original_keys[i-1] + current_text[last_pos:pos] + original_keys[i])
                        else:
                            paragraphs.append(current_text[last_pos:pos])
                        last_pos = pos + len(key)
                    
                    # Añadir el último fragmento
                    if keep_separator and positions:
                        # Para el último fragmento, añadimos la palabra al inicio
                        paragraphs.append(original_keys[-1] + current_text[last_pos:])
                    else:
                        paragraphs.append(current_text[last_pos:])
                    
                    # Procesar cada párrafo
                    for i, paragraph in enumerate(paragraphs):
                        if paragraph.strip():  # Solo procesar párrafos no vacíos
                            # Crear metadata para el nuevo chunk
                            new_metadata = {
                                'Documento': f"{documento_nombre} (SUBFRAGMENTOS)",
                                'ID_Original': content['id']
                            }
                            
                            # Añadir el nuevo chunk
                            new_chunks.append({
                                'text': paragraph.strip(),
                                'metadata': new_metadata
                            })
                    
                    # Actualizar el texto para la siguiente iteración
                    text = ' '.join(paragraphs)
                    normalized_text = unidecode(text)
                elif key == '\n\n' and not chunk_created:
                    # Si el separador es \n\n y no se encontró en el texto,
                    # considerar todo el texto como un chunk
                    new_metadata = {
                        'Documento': f"{documento_nombre} (SUBFRAGMENTOS)",
                        'ID_Original': content['id']
                    }
                    
                    new_chunks.append({
                        'text': current_text.strip(),
                        'metadata': new_metadata
                    })
                    chunk_created = True

        return new_chunks
