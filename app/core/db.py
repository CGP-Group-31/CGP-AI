# from sqlalchemy import create_engine
# from sqlalchemy.engine import Engine
# from sqlalchemy.pool import QueuePool
# from .config import settings


# def get_engine() -> Engine:

#     engine = create_engine(
#         settings.DATABASE_URL,
#         poolclass=QueuePool,
#         pool_size=10,
#         max_overflow=20,
#         pool_pre_ping=True,
#         future=True
#     )

#     return engine


# engine = get_engine()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)