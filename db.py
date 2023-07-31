import os

import dotenv
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

dotenv.load_dotenv()

engine = create_async_engine(
    os.getenv("DATABASE_URL")
    .replace("postgres://", "postgresql+asyncpg://")
    .replace("?sslmode=disable", ""),
    echo=True,
)
SessionLocal = async_sessionmaker(engine, autocommit=False, autoflush=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass
