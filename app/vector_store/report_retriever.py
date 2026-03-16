from azure.search.documents.models import VectorizedQuery
from app.vector_store.report_search import report_search_client
from app.vector_store.embedder import embed_query


async def search_report_memory(elder_id: int, question: str, top_k: int = 3):
    vector = await embed_query(question)

    vector_query = VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=top_k,
        fields="content_vector"
    )

    results = report_search_client.search(
        search_text="",
        vector_queries=[vector_query],
        filter=f"elder_id eq {elder_id}"
    )

    reports = []
    for r in results:
        reports.append({
            "content": r.get("content"),
            "report_type": r.get("report_type"),
            "period_start": r.get("period_start"),
            "period_end": r.get("period_end"),
            "created_at": r.get("created_at")
        })

    return reports