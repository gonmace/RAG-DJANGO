from django.test import TestCase
from unittest.mock import patch, MagicMock
from embeddings.services import LangChainService

class TestLangChainService(TestCase):
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.test_texts = [
            "Este es un texto de prueba",
            "Este es otro texto de prueba",
            "Un tercer texto para probar"
        ]
        
        # Creamos un mock para OpenAIEmbeddings
        self.embeddings_patcher = patch('embeddings.services.langchain_service.OpenAIEmbeddings')
        self.mock_embeddings = self.embeddings_patcher.start()
        
        # Creamos un mock para Chroma
        self.chroma_patcher = patch('embeddings.services.langchain_service.Chroma')
        self.mock_chroma = self.chroma_patcher.start()
        
        # Inicializamos el servicio
        self.service = LangChainService()

    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.embeddings_patcher.stop()
        self.chroma_patcher.stop()

    def test_initialize_vectorstore(self):
        """Prueba la inicialización del vectorstore"""
        # Configuramos el mock de Chroma
        mock_vectorstore = MagicMock()
        self.mock_chroma.return_value = mock_vectorstore

        # Llamamos al método
        result = self.service.initialize_vectorstore()

        # Verificamos que Chroma fue llamado correctamente
        self.mock_chroma.assert_called_once()
        self.assertEqual(result, mock_vectorstore)
        self.assertEqual(self.service.vectorstore, mock_vectorstore)

    def test_add_texts(self):
        """Prueba la adición de textos al vectorstore"""
        # Configuramos los mocks
        mock_vectorstore = MagicMock()
        self.mock_chroma.return_value = mock_vectorstore
        mock_vectorstore.add_texts.return_value = ["id1", "id2", "id3"]

        # Llamamos al método
        result = self.service.add_texts(self.test_texts)

        # Verificamos que se llamó add_texts con los textos correctos
        mock_vectorstore.add_texts.assert_called_once_with(
            texts=self.test_texts,
            metadatas=None
        )
        self.assertEqual(result, ["id1", "id2", "id3"])

    def test_similarity_search(self):
        """Prueba la búsqueda por similitud"""
        # Configuramos los mocks
        mock_vectorstore = MagicMock()
        self.mock_chroma.return_value = mock_vectorstore
        mock_results = [MagicMock() for _ in range(4)]
        mock_vectorstore.similarity_search.return_value = mock_results

        # Inicializamos el vectorstore
        self.service.initialize_vectorstore()

        # Realizamos la búsqueda
        query = "texto de búsqueda"
        result = self.service.similarity_search(query)

        # Verificamos que se llamó similarity_search correctamente
        mock_vectorstore.similarity_search.assert_called_once_with(
            query=query,
            k=4
        )
        self.assertEqual(result, mock_results)

    def test_similarity_search_without_initialization(self):
        """Prueba que se lanza un error si no se inicializa el vectorstore"""
        with self.assertRaises(ValueError):
            self.service.similarity_search("query") 