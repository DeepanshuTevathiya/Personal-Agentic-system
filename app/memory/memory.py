from sentence_transformers import SentenceTransformer
from app.database.db import db_store_memory
from app.database.config import supabase

# LOADING EMBEDDING MODEL -----------------------------------------------------------------------
_embedding_model = None

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L12-v2"
        )

    return _embedding_model


def create_embeddings(text: str):
    model = get_embedding_model()

    embeddings = model.encode(text)

    return embeddings.tolist()

# STORE EMDDINGS OF CONTENT ----------------------------------------------------------
def store_memory(
    user_id: int,
    source_type: str,
    source_id: int,
    content: str
):
    embedding = create_embeddings(content)

    result = db_store_memory(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        content=content,
        embedding=embedding
    )

    return result

# RETRIEVE CONTENT FROM DATABASE
def retrieve_memories(
        user_id: int,
        query: str,
        top_k: int = 5
):
    query_embedding = create_embeddings(query)

    result = supabase.rpc(
        "match_memories",
        {
            "query_embedding": query_embedding  ,
            "match_user_id": user_id,
            "match_count": top_k
        }
    ).execute()

    return result.data