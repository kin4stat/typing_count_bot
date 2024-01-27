import sqlite3
from telethon import TelegramClient, events, types, functions
import datetime
import os
from database.connection import async_session, engine
from database.models import ChatStatsModel, GlobalChatStatsModel, CreationDate, OldChatStatsModel
from database.init_db import create_database
from sqlalchemy import select, update, insert
import asyncio
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/global_stats/{chat_id}")
async def global_stats(chat_id):
    async with async_session() as session:
        db_res = await session.execute(select(GlobalChatStatsModel).where(GlobalChatStatsModel.chat_id == chat_id))
        data = db_res.scalars().all()
        result = {}
        for user in data:
            result[user.user_id] = {}
            result[user.user_id]["username"] = user.username
            result[user.user_id]["time"] = user.time
        return result


@app.get("/weekly_stats/{chat_id}")
async def weekly_stats(chat_id):
    async with async_session() as session:
        db_res = await session.execute(select(ChatStatsModel).where(ChatStatsModel.chat_id == chat_id))
        data = db_res.scalars().all()
        result = {}
        for user in data:
            result[user.user_id] = {}
            result[user.user_id]["username"] = user.username
            result[user.user_id]["time"] = user.time
        return result
    

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

API_ID = os.environ['TG_API_ID']
API_HASH = os.environ['TG_API_HASH']

client = TelegramClient('/persistent/typing_session', API_ID, API_HASH, system_version="1.01", loop=loop)

timings = {}
chat_members = {}

def format_seconds_to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)


async def get_or_create_chat_stats(session, type, chat_id, user_id):
    result = await session.execute(select(type).where(type.chat_id == chat_id, type.user_id == user_id))
    data = result.scalar()
    if data is None:
        data = type()
        data.chat_id = chat_id
        data.user_id = user_id
        data.username = timings[chat_id][user_id]["username"]
        data.time = 0
        session.add(data)
        await session.commit()
    return data


async def get_or_create_creation_date(session, table) -> CreationDate:
    result = await session.execute(select(CreationDate).where(CreationDate.table == table))
    data = result.scalar()
    if data is None:
        data = CreationDate()
        data.table = table
        data.creation_date = datetime.datetime.now()
        session.add(data)
        await session.commit()
    return data


async def update_weekly_stats():
    async with async_session() as session:
        result = await get_or_create_creation_date(session, 1)
        date = result.creation_date
        date -= datetime.timedelta(days=date.weekday() % 7)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        now = datetime.datetime.now()
        today = now - datetime.timedelta(days=now.weekday() % 7)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if date != today:
        async with engine.begin() as conn:
            await conn.run_sync(OldChatStatsModel.__table__.drop, checkfirst=False)
            await conn.run_sync(OldChatStatsModel.__table__.create)
        
        statement = insert(OldChatStatsModel).from_select(["chat_id", "user_id", "username", "time"], select(ChatStatsModel))
        
        async with async_session() as session:
            await session.execute(statement)
            await session.commit()

        async with engine.begin() as conn:
            await conn.run_sync(ChatStatsModel.__table__.drop, checkfirst=False)
            await conn.run_sync(ChatStatsModel.__table__.create)
        
        async with async_session() as session:
            result = await get_or_create_creation_date(session, 1)
            result.creation_date = datetime.datetime.now()
            await session.commit()


async def update_timings(chat_id, user_id):
    while (datetime.datetime.now() - timings[chat_id][user_id]["time"]).total_seconds() < 6:
        print("not updating, still typing")
        await asyncio.sleep(1)
    async with async_session() as session:
        c_stats = await get_or_create_chat_stats(session, ChatStatsModel, chat_id, user_id)
        g_stats = await get_or_create_chat_stats(session, GlobalChatStatsModel, chat_id, user_id)
        diff = (datetime.datetime.now() - timings[chat_id][user_id]["start"]).total_seconds()
        c_stats.time += diff
        g_stats.time += diff
        c_stats.username = g_stats.username = timings[chat_id][user_id]["username"]
        await session.commit()
        print(f'time: {diff}')
    timings[chat_id].pop(user_id)
    

@client.on(events.UserUpdate)
async def handler(update: events.UserUpdate):
    if not isinstance(update.original_update, (types.UpdateChatUserTyping, types.UpdateChannelUserTyping)):
        return

    await update_weekly_stats()

    chat_id = update.chat_id
    from_id = update.sender_id

    if chat_members.get(chat_id, None) is None:
        chat_members.setdefault(chat_id, dict())
        async for user in update.client.iter_participants(await update.get_input_chat()):
            if user.last_name:
                name = f"{user.first_name} {user.last_name}"
            else:
                name = user.first_name
            chat_members[chat_id][user.id] = name
    timings.setdefault(chat_id, dict())
    timings[chat_id].setdefault(from_id, dict())
    now = datetime.datetime.now()
    timings[chat_id][from_id]["time"] = now
    timings[chat_id][from_id]["username"] = chat_members[chat_id][from_id]
    if timings[chat_id][from_id].get("start", None) is None:
        timings[chat_id][from_id]["start"] = now
        asyncio.get_event_loop().create_task(update_timings(chat_id, from_id))
    print(timings[chat_id][from_id]["username"])

@client.on(events.NewMessage)
async def my_event_handler(event: events.NewMessage):
    first_day = datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday() % 7)
    first_day = first_day.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if event.raw_text.lower() == "кто больше всех жмет по клаве" or event.raw_text.lower() == "кто больше всех жмет по клаве?":
        start_week = (first_day - datetime.timedelta(days=7)).strftime("%d.%m.%Y")
        end_week = (first_day - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
        result = f"Лучшие мастера клавишного джаза за неделю {start_week} - {end_week}\n"
        async with async_session() as session:
            db_res = await session.execute(select(ChatStatsModel).where(ChatStatsModel.chat_id == event.chat_id))
            data = db_res.scalars().all()
            if data and len(data) > 0:
                for i, k in enumerate(data):
                    time = format_seconds_to_hhmmss(k.time)
                    result += f"{i + 1}. {k.username} - {time}\n"
                await event.respond(result)


async def update_online():
    while True:
        await client(functions.account.UpdateStatusRequest(
            offline=False
        ))
        await asyncio.sleep(10)


async def main():
    await client.start()
    asyncio.create_task(update_online())

    config = uvicorn.Config("main:app", port=25424, log_level="info")
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
