import logging
from typing import List

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import OpenAI
from semantic_kernel.functions import kernel_function


class TaxDataPlugin:
    def __init__(
        self, 
        search_client: SearchClient,
        openai_client: OpenAI
    ):
        self.search_client = search_client
        self.openai_client = openai_client
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    

    @kernel_function(
        name="search_tax_data",
        description="Search for data about taxes based on a natural language query",
    )
    def search_tax_data(
        self,
        query: str
    ) -> str:
        self.logger.info(f"Searching for tax data based on query: {query}")
        query_vector = self.get_embedding_vector(query)
        results = self.search_index(
            query=query,
            vector=query_vector
        )
        text_results = "\n\n".join([result["content"] for result in results])
        print(text_results)
        return text_results


    def search_index(
        self,
        query: str | None = None,
        vector: List[float] | None = None, 
        top_k: int = 5
    ) -> List[dict]:
        if vector is not None:
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=5,
                fields="content_vector"
            )

            results = self.search_client.search(
                search_text=query, 
                vector_queries=[vector_query],
                top=top_k
            )

            return results
        elif query is not None:
            results = self.search_client.search(search_text=query, top=top_k)
            return results
        else:
            raise ValueError("Either query or vector must be provided")
        

    def get_embedding_vector(
        self, 
        text: str
    ) -> List[float]:
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
