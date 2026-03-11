from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings

search_client = SearchClient(
    endpoint=settings.SEARCH_ENDPOINT,
    index_name=settings.SEARCH_INDEX,
    credential=AzureKeyCredential(settings.SEARCH_KEY)
)