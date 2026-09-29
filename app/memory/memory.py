from sentence_transformers import SentenceTransformer
from app.database.db import db_store_memory

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