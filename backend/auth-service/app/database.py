import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.models import UserInDB, UserCreate, UserRole, AuditLog
from app.auth import hash_password

settings = get_settings()
logger = logging.getLogger(__name__)


class Database:
    """MongoDB database client using Motor for async operations."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            self.db = self.client[settings.mongodb_database]

            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")

            # Create indexes
            await self._create_indexes()

            # Create default admin if not exists
            await self._ensure_default_admin()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes."""
        # Users collection
        await self.db.users.create_index([("username", 1)], unique=True)
        await self.db.users.create_index([("email", 1)], sparse=True, unique=True)

        # Sessions collection
        await self.db.sessions.create_index([("user_id", 1)])
        await self.db.sessions.create_index([("expires_at", 1)], expireAfterSeconds=0)

        # Audit logs collection
        await self.db.audit_logs.create_index([("user_id", 1)])
        await self.db.audit_logs.create_index([("timestamp", -1)])

    async def _ensure_default_admin(self):
        """Create default admin user if it doesn't exist."""
        existing = await self.get_user_by_username(settings.default_admin_username)
        if not existing:
            admin_user = UserCreate(
                username=settings.default_admin_username,
                password=settings.default_admin_password,
                full_name="System Administrator",
                role=UserRole.ADMIN
            )
            await self.create_user(admin_user)
            logger.info(f"Created default admin user: {settings.default_admin_username}")

    # User operations
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        doc = await self.db.users.find_one({"username": username})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return UserInDB(**doc)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        from bson import ObjectId
        try:
            doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                return UserInDB(**doc)
        except:
            pass
        return None

    async def create_user(self, user: UserCreate) -> Optional[UserInDB]:
        """Create a new user."""
        try:
            user_dict = {
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "hashed_password": hash_password(user.password),
                "created_at": datetime.utcnow(),
                "last_login": None
            }

            result = await self.db.users.insert_one(user_dict)
            user_dict["id"] = str(result.inserted_id)
            if "_id" in user_dict:
                del user_dict["_id"]

            return UserInDB(**user_dict)

        except DuplicateKeyError:
            logger.warning(f"User already exists: {user.username}")
            return None

    async def update_last_login(self, username: str):
        """Update user's last login timestamp."""
        await self.db.users.update_one(
            {"username": username},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    # Audit log operations
    async def log_audit(self, audit: AuditLog):
        """Log an audit event."""
        audit_dict = audit.model_dump(exclude={"id"})
        await self.db.audit_logs.insert_one(audit_dict)

    async def get_user_audit_logs(self, user_id: str, limit: int = 50):
        """Get audit logs for a user."""
        cursor = self.db.audit_logs.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            logs.append(AuditLog(**doc))
        return logs


# Singleton instance
database = Database()
