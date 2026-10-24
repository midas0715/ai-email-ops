from functools import lru_cache

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

from ai_email_ops.app.config import settings
from ai_email_ops.app.db import engine

TABLE_NAME = "knowledge"  # LlamaIndex stores it as "data_knowledge"
EMBED_DIM = 768  # nomic-embed-text produces 768 numbers per chunk


def get_embed_model() -> OllamaEmbedding:
    return OllamaEmbedding(
        model_name=settings.embed_model,
        base_url=settings.ollama_base_url,
    )


@lru_cache
def get_vector_store() -> PGVectorStore:
    # Reuse the same DB settings as the rest of the app
    url = make_url(settings.database_url)
    return PGVectorStore.from_params(
        host=url.host,
        port=url.port,
        database=url.database,
        user=url.username,
        password=url.password,
        table_name=TABLE_NAME,
        embed_dim=EMBED_DIM,
    )


def ingest_text(organization_id: int, document_id: int, filename: str, content: str) -> int:
    """Cut one document into chunks, embed them and store them. Returns the chunk count."""
    document = Document(
        text=content,
        metadata={
            "organization_id": str(organization_id),  # the tenant tag
            "document_id": str(document_id),
            "file_name": filename,
        },
    )
    # The tags are for us, not for the model: keep them out of the text that gets embedded
    document.excluded_embed_metadata_keys = ["organization_id", "document_id"]
    document.excluded_llm_metadata_keys = ["organization_id", "document_id"]

    nodes = SentenceSplitter(chunk_size=512, chunk_overlap=50).get_nodes_from_documents([document])
    index = VectorStoreIndex.from_vector_store(get_vector_store(), embed_model=get_embed_model())
    index.insert_nodes(nodes)
    return len(nodes)


def delete_document_chunks(document_id: int, organization_id: int) -> None:
    """Remove every chunk of one document. The organization check is a second safety net."""
    table = f"data_{TABLE_NAME}"
    if not inspect(engine).has_table(table):
        return  # nothing has ever been stored
    with engine.begin() as conn:
        conn.execute(
            text(
                f"DELETE FROM {table} "
                "WHERE metadata_->>'document_id' = :doc AND metadata_->>'organization_id' = :org"
            ),
            {"doc": str(document_id), "org": str(organization_id)},
        )


def retrieve_chunks(organization_id: int, query: str, top_k: int = 3):
    """Find the closest chunks, ONLY from this organization."""
    index = VectorStoreIndex.from_vector_store(get_vector_store(), embed_model=get_embed_model())
    org_filter = MetadataFilters(
        filters=[MetadataFilter(key="organization_id", value=str(organization_id))]
    )
    retriever = index.as_retriever(similarity_top_k=top_k, filters=org_filter)
    return retriever.retrieve(query)