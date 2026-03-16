from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings

report_search_client = SearchClient(
    endpoint=settings.SEARCH_ENDPOINT,
    index_name=settings.REPORT_SEARCH_INDEX,
    credential=AzureKeyCredential(settings.SEARCH_KEY)
)