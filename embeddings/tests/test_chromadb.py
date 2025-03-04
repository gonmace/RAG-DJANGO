from embeddings.services.langchain_service import LangChainService
from django.test import TestCase

class ChromaDBTest(TestCase):
    def test_chromadb(self):
        # Crear una instancia del servicio
        print("Inicializando servicio...")
        service = LangChainService()

        # Agregar algunos documentos de ejemplo
        print("\nAgregando documentos de ejemplo...")
        textos_ejemplo = [
            "Hawaii es un hermoso estado con playas paradisíacas",
            "La capital de Francia es París",
            "Los volcanes de Hawaii son muy famosos",
            "El monte Kilauea es un volcán activo en Hawaii",
            "La Torre Eiffel es el símbolo de París"
        ]

        # Agregar los textos a la base de datos
        service.add_Documents(texts=textos_ejemplo)
        print("Documentos agregados exitosamente!")

        # Realizar una consulta
        print("\nRealizando consulta sobre Hawaii...")
        resultados = service.query_collection("Tell me about Hawaii")

        # Imprimir los resultados de forma legible
        print("\nResultados de la búsqueda:")
        print("------------------------")
        for i in range(len(resultados['documents'][0])):
            print(f"\nDocumento {i+1}:")
            print(f"ID: {resultados['ids'][0][i]}")
            print(f"Texto: {resultados['documents'][0][i]}")
            print(f"Distancia: {resultados['distances'][0][i]}")
            if resultados['metadatas'][0]:
                print(f"Metadata: {resultados['metadatas'][0][i]}")

        # Verificar que obtuvimos resultados
        self.assertTrue(len(resultados['documents'][0]) > 0)

    # # Mostrar todos los documentos almacenados
    # print("\nTodos los documentos en la base de datos:")
    # print("----------------------------------------")
    # todos_docs = service.get_all_documents()
    # for doc in todos_docs:
    #     print(f"\nID: {doc['id']}")
    #     print(f"Texto: {doc['text']}")
    #     print(f"Metadata: {doc['metadata']}")

if __name__ == "__main__":
    test_chromadb() 