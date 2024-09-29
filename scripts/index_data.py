import json
import glob
import os
import uuid
from dataclasses import dataclass, asdict
from typing import List

from azure.search.documents import SearchClient
from azure.search.documents.models import IndexingResult
from azure.search.documents.indexes.models import (
    SearchIndex, 
    SearchField,
    SimpleField, 
    SearchableField,
    SearchFieldDataType,
    CorsOptions,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration
)
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI
from dotenv import load_dotenv



@dataclass
class DocumentChunk:
    id: str
    document_id: str
    document_title: str
    chunk_id: str
    content: str
    content_vector: List[float]

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict())
    

def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_embedding_vector(client: OpenAI, text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def process_markdown_file(client: OpenAI, file_path: str) -> List[DocumentChunk]:
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    document_id = generate_uuid()
    document_title = ""
    chunks = []
    chunk_id = 0
    chunk_content = ""

    for line in lines:
        line = line.strip()

        if line.startswith("# ") and not document_title:
            document_title = line[2:].strip()

        elif line.startswith("## "):
            if chunk_content:
                chunks.append(DocumentChunk(
                    id=generate_uuid(),
                    document_id=document_id,
                    document_title=document_title,
                    chunk_id=str(chunk_id),
                    content=chunk_content.strip(),
                    content_vector=get_embedding_vector(client, chunk_content.strip())
                ))
                chunk_id += 1

            chunk_content = f"{document_title}\n{line}\n"

        else:
            chunk_content += f"{line}\n"

    if chunk_content:
        chunks.append(DocumentChunk(
            id=generate_uuid(),
            document_id=document_id,
            document_title=document_title,
            chunk_id=str(chunk_id),
            content=chunk_content.strip(),
            content_vector=get_embedding_vector(client, chunk_content.strip())
        ))

    return chunks


def process_directory(client: OpenAI, directory_path: str) -> List[DocumentChunk]:
    all_chunks = []
    
    md_files = glob.glob(os.path.join(directory_path, "*.md"))
    
    for md_file in md_files:
        document_chunks = process_markdown_file(client, md_file)
        all_chunks.extend(document_chunks)
    
    return all_chunks


def create_index_if_not_exists(client: SearchIndexClient, name: str):
    index = SearchIndex(
        name=name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String),
            SimpleField(name="document_title", type=SearchFieldDataType.String),
            SimpleField(name="chunk_id", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector", 
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                vector_search_dimensions=1536, 
                vector_search_profile_name='vector-search-config-v1'
            ),
        ],
        scoring_profiles=[],
        cors_options=CorsOptions(allowed_origins=["*"]),
        vector_search=VectorSearch(
            profiles=[VectorSearchProfile(
                name="vector-search-config-v1", 
                algorithm_configuration_name="algorithm-config-v1"
            )],
            algorithms=[HnswAlgorithmConfiguration(name="algorithm-config-v1")],
        )
    )

    client.create_or_update_index(index)
    print(f"Index {name} created or updated successfully")


def upsert_documents(client: SearchClient, documents: list[DocumentChunk]) -> List[IndexingResult]:
    documents_dicts = [doc.to_dict() for doc in documents]
    return client.merge_or_upload_documents(documents=documents_dicts)


def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=openai_api_key)

    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    azure_ai_search_key = os.getenv('AZURE_SEARCH_KEY')
    azure_ai_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    credentials = AzureKeyCredential(azure_ai_search_key)
    search_index_client = SearchIndexClient(azure_ai_search_endpoint, credentials)
    create_index_if_not_exists(search_index_client, index_name)
    search_client = SearchClient(endpoint=azure_ai_search_endpoint, index_name=index_name, credential=credentials)

    data_directory = os.path.join(os.getcwd(), "data", "processed")
    document_chunks = process_directory(openai_client, data_directory)
    json.dump([doc.to_dict() for doc in document_chunks], open("data/temp/document_chunks.json", "w"), indent=2)
    if not document_chunks:
        print("No document chunks to upsert")
        return
    results = upsert_documents(search_client, document_chunks)
    print(f"Upserted {len(results)} documents")


if __name__ == "__main__":
    main()
