from sentence_transformers import SentenceTransformer

# Make sure this model outputs 384 dimensions
_model = SentenceTransformer("all-MiniLM-L6-v2")


async def embed_query(text: str) -> list[float]:
    return _model.encode(text).tolist()