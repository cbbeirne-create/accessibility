"""MongoDB database connection and index setup."""
from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]


async def ensure_indexes() -> None:
    """Create idempotent indexes required for security, tenancy and worker queues."""
    await db.users.create_index("id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("stripe_customer_id", sparse=True)

    await db.scan_requests.create_index("id", unique=True)
    await db.scan_requests.create_index([("user_id", 1), ("createdAt", -1)])
    await db.scan_requests.create_index([("organization_id", 1), ("createdAt", -1)])
    await db.scan_requests.create_index([("status", 1), ("createdAt", -1)])

    await db.scan_jobs.create_index("id", unique=True)
    await db.scan_jobs.create_index("scan_id")
    await db.scan_jobs.create_index([("status", 1), ("available_at", 1)])
    await db.scan_jobs.create_index("lock_until")

    await db.refresh_tokens.create_index("token_hash", unique=True)
    await db.refresh_tokens.create_index([("user_id", 1), ("revoked_at", 1)])
    await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)

    await db.scheduled_scans.create_index("id", unique=True)
    await db.scheduled_scans.create_index([("user_id", 1), ("created_at", -1)])
    await db.scheduled_scans.create_index([("enabled", 1), ("next_run", 1), ("lock_until", 1)])

    await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
    await db.notifications.create_index("event_key", unique=True, sparse=True)
    await db.organizations.create_index("id", unique=True)
    await db.organization_members.create_index([("organization_id", 1), ("user_id", 1)], unique=True)
    await db.organization_invites.create_index("token", unique=True)
    await db.stripe_events.create_index("event_id", unique=True)


async def close_db_connection():
    client.close()
