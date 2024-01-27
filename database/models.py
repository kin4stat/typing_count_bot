from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ChatStatsModel(Base):
    __tablename__ = "chat_statistics"

    chat_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    time = Column(Integer)
    creation_date  = Column

    def __repr__(self) -> str:
        return f"ChatStats(chat_id={self.chat_id!r}, user_id={self.user_id!r}, username={self.username!r}, time={self.time!r})"


class GlobalChatStatsModel(Base):
    __tablename__ = "global_chat_statistics"

    chat_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    time = Column(Integer)

    def __repr__(self) -> str:
        return f"GlobalChatStatsModel(chat_id={self.chat_id!r}, user_id={self.user_id!r}, username={self.username!r}, time={self.time!r})"


class OldChatStatsModel(Base):
    __tablename__ = "old_chat_statistics"

    chat_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    time = Column(Integer)

    def __repr__(self) -> str:
        return f"OldChatStatsModel(chat_id={self.chat_id!r}, user_id={self.user_id!r}, username={self.username!r}, time={self.time!r})"


class CreationDate(Base):
    __tablename__ = "creation_date"

    table = Column(Integer, primary_key=True)
    creation_date = Column(DateTime)

    def __repr__(self) -> str:
        return f"CreationDate(table={self.table!r}, creation_date={self.creation_date!r})"