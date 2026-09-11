"""MongoDB connection, indexes, and shutdown helpers."""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING

from .config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]


async def ensure_indexes():
    await db.users.create_index([('email', ASCENDING)], unique=True)
    await db.refresh_sessions.create_index([('jti_hash', ASCENDING)], unique=True)
    await db.refresh_sessions.create_index('expires_at', expireAfterSeconds=0)
    await db.scan_jobs.create_index([('scan_id', ASCENDING)])
    await db.scan_jobs.create_index([('status', ASCENDING), ('created_at', ASCENDING)])
    await db.scheduled_scans.create_index([('enabled', ASCENDING), ('next_run', ASCENDING)])
    await db.rate_limits.create_index('expires_at', expireAfterSeconds=0)
    await db.stripe_events.create_index([('event_id', ASCENDING)], unique=True)


async def close_db_connection():
    client.close()
