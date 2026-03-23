"""
MongoDB database connection and client setup.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

# MongoDB connection
client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

async def close_db_connection():
    """Close database connection on shutdown."""
    client.close()
