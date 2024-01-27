from os import getenv

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = getenv('DATABASE_URL', "sqlite+aiosqlite:////persistent/message_stat.db?check_same_thread")

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)