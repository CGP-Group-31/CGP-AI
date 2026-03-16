from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    SEARCH_ENDPOINT: str
    SEARCH_KEY: str
    SEARCH_INDEX: str
    REPORT_SEARCH_INDEX: str
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str

    CRUD_API: str

    APP_TIMEZONE: str = "Asia/Colombo"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()