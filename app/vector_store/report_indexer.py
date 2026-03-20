from datetime import datetime, timezone

from app.vector_store.embedder import embed_query
from app.vector_store.report_search import report_search_client


async def index_daily_report(
    report_id: int,
    elder_id: int,
    period_start: str,
    period_end: str,
    content: str,
    report_type: str = "daily"
):
    vector = await embed_query(content)

    doc = {
        "id": f"report-{report_id}",
        "elder_id": elder_id,
        "report_type": report_type,
        "period_start": period_start,
        "period_end": period_end,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "content_vector": vector
    }

    result = report_search_client.upload_documents([doc])

    return result