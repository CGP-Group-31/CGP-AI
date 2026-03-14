from azure.search.documents.models import VectorizedQuery
from app.vector_store.azure_search import search_client
from app.vector_store.embedder import embed_query


async def search_memory(elder_id: int, question: str, top_k: int = 5):
    vector = await embed_query(question)

    vector_query = VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=top_k,
        fields="content_vector"
    )

    results = search_client.search(
        search_text="",
        vector_queries=[vector_query],
        filter=f"elder_id eq {elder_id}"
    )

    memory = []
    for r in results:
        memory.append({
            "content": r.get("content"),
            "role": r.get("role"),
            "mood": r.get("mood"),
            "created_at": r.get("created_at")
        })

    return memory