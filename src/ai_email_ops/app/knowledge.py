from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

from ai_email_ops.app.config import settings
from ai_email_ops.app.db import engine

from functools import lru_cache

from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

TABLE_NAME = "knowledge"  # LlamaIndex stores it as "data_knowledge"
EMBED_DIM = 768  # nomic-embed-text produces 768 numbers per chunk


def get_embed_model() -> OllamaEmbedding:
    return OllamaEmbedding(
        model_name=settings.embed_model,
        base_url=settings.ollama_base_url,
    )


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


def delete_org_knowledge(organization_id: int) -> None:
    """Remove old chunks of this organization so re-running ingestion doesn't duplicate them."""
    table = f"data_{TABLE_NAME}"
    if not inspect(engine).has_table(table):
        return  # first run: nothing to delete yet
    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {table} WHERE metadata_->>'organization_id' = :org"),
            {"org": str(organization_id)},
        )


def ingest_folder(organization_id: int, folder: str) -> int:
    """Read every file in the folder, chunk it, embed it, store it. Returns the file count."""
    documents = SimpleDirectoryReader(folder).load_data()
    for doc in documents:
        doc.metadata["organization_id"] = str(organization_id)  # the tenant tag

    delete_org_knowledge(organization_id)

    storage_context = StorageContext.from_defaults(vector_store=get_vector_store())
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=get_embed_model(),
        transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=50)],
    )
    return len(documents)

def retrieve_chunks(organization_id: int, query: str, top_k: int = 3):
    """Find the closest chunks, ONLY from this organization."""
    index = VectorStoreIndex.from_vector_store(get_vector_store(), embed_model=get_embed_model())
    org_filter = MetadataFilters(
        filters=[MetadataFilter(key="organization_id", value=str(organization_id))]
    )
    retriever = index.as_retriever(similarity_top_k=top_k, filters=org_filter)
    return retriever.retrieve(query)