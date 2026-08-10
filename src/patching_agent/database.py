

# import logging
# from datetime import datetime, timezone
# from typing import Dict, Any, List, Optional
# from motor.motor_asyncio import AsyncIOMotorClient
# from patching_agent.config import settings

# logger = logging.getLogger(__name__)

# class DatabaseManager:
#     """Manages asynchronous MongoDB connection pool, repair history, and user authentication."""
    
#     def __init__(self):
#         self.client: Optional[AsyncIOMotorClient] = None
#         self.db = None

#     def connect(self) -> None:
#         """Initialize connection pool to the Atlas cluster."""
#         if not self.client:
#             try:
#                 self.client = AsyncIOMotorClient(settings.MONGODB_URI)
#                 self.db = self.client[settings.DB_NAME]
#                 logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
#             except Exception as e:
#                 logger.critical(f"Failed to instantiate connection pool to MongoDB: {e}")
#                 raise e

#     def disconnect(self) -> None:
#         """Close connection pool gracefully."""
#         if self.client:
#             self.client.close()
#             logger.info("MongoDB connection pool closed safely.")
#             self.client = None
#             self.db = None

#     # --- USER AUTHENTICATION DATABASE METHODS ---
#     async def create_user(self, username: str, email: str, hashed_password: str) -> Optional[Dict[str, Any]]:
#         """Registers a new user in MongoDB."""
#         if self.db is None:
#             return None

#         users_col = self.db["users"]
        
#         # Check existing user
#         existing_user = await users_col.find_one({"$or": [{"username": username}, {"email": email}]})
#         if existing_user:
#             return None

#         user_doc = {
#             "username": username,
#             "email": email.lower(),
#             "password": hashed_password,
#             "created_at": datetime.now(timezone.utc)
#         }

#         result = await users_col.insert_one(user_doc)
#         user_doc["_id"] = str(result.inserted_id)
#         return user_doc

#     async def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
#         """Retrieves user by username or email."""
#         if self.db is None:
#             return None

#         users_col = self.db["users"]
#         return await users_col.find_one({
#             "$or": [{"username": identifier}, {"email": identifier.lower()}]
#         })

#     # --- REPAIR HISTORY METHODS ---
#     async def save_repair_history(self, session_id: str, state_dump: Dict[str, Any]) -> bool:
#         if self.db is None:
#             return False

#         collection = self.db["repair_history"]
#         historical_document = {
#             "session_id": session_id,
#             "timestamp": datetime.now(timezone.utc),
#             "raw_logs": state_dump.get("raw_logs", ""),
#             "target_file_path": state_dump.get("target_file_path", ""),
#             "execution_status": state_dump.get("execution_status", "unknown"),
#             "retry_count": state_dump.get("retry_count", 0),
#             "generated_patch": state_dump.get("generated_patch", ""),
#             "validation_report": state_dump.get("validation_report", {}),
#             "failure_analysis": state_dump.get("failure_analysis", {})
#         }

#         try:
#             await collection.update_one(
#                 {"session_id": session_id},
#                 {"$set": historical_document},
#                 upsert=True
#             )
#             return True
#         except Exception as e:
#             logger.error(f"Failed to write repair metrics: {e}")
#             return False

#     async def get_repair_record(self, session_id: str) -> Optional[Dict[str, Any]]:
#         if self.db is None:
#             return None
#         return await self.db["repair_history"].find_one({"session_id": session_id})

#     async def fetch_successful_patches(self, error_type: str) -> List[Dict[str, Any]]:
#         if self.db is None:
#             return []

#         collection = self.db["repair_history"]
#         query = {
#             "failure_analysis.error_type": error_type,
#             "execution_status": "patch_validated_successfully"
#         }
#         cursor = collection.find(query).sort("timestamp", -1).limit(3)
#         return await cursor.to_list(length=3)

# # Global database manager instance
# db_manager = DatabaseManager()


import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from patching_agent.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages asynchronous MongoDB connection pool, repair history, and user authentication."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    def connect(self) -> None:
        """Initialize connection pool to the Atlas cluster."""
        if not self.client:
            try:
                self.client = AsyncIOMotorClient(settings.MONGODB_URI)
                self.db = self.client[settings.DB_NAME]
                logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
            except Exception as e:
                logger.critical(f"Failed to instantiate connection pool to MongoDB: {e}")
                raise e

    def disconnect(self) -> None:
        """Close connection pool gracefully."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection pool closed safely.")
            self.client = None
            self.db = None

    # --- USER AUTHENTICATION DATABASE METHODS ---
    async def create_user(self, username: str, email: str, hashed_password: str) -> Optional[Dict[str, Any]]:
        """Registers a new user in MongoDB."""
        if self.db is None:
            return None

        users_col = self.db["users"]
        existing_user = await users_col.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            return None

        user_doc = {
            "username": username,
            "email": email.lower(),
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc)
        }

        result = await users_col.insert_one(user_doc)
        user_doc["_id"] = str(result.inserted_id)
        return user_doc

    async def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by username or email."""
        if self.db is None:
            return None

        users_col = self.db["users"]
        return await users_col.find_one({
            "$or": [{"username": identifier}, {"email": identifier.lower()}]
        })

    # --- REPAIR HISTORY METHODS ---
    async def save_repair_history(self, session_id: str, state_dump: Dict[str, Any], username: str = "anonymous") -> bool:
        """Saves a complete snapshot of a repair operation linked to a specific username."""
        if self.db is None:
            logger.error("Database uninitialized. Cannot write repair logs.")
            return False

        collection = self.db["repair_history"]
        historical_document = {
            "session_id": session_id,
            "username": username,
            "timestamp": datetime.now(timezone.utc),
            "raw_logs": state_dump.get("raw_logs", ""),
            "target_file_path": state_dump.get("target_file_path", ""),
            "execution_status": state_dump.get("execution_status", "unknown"),
            "retry_count": state_dump.get("retry_count", 0),
            "generated_patch": state_dump.get("generated_patch", ""),
            "validation_report": state_dump.get("validation_report", {}),
            "failure_analysis": state_dump.get("failure_analysis", {})
        }

        try:
            await collection.update_one(
                {"session_id": session_id},
                {"$set": historical_document},
                upsert=True
            )
            logger.info(f"Successfully committed repair snapshot for user {username}, session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to write repair metrics snapshot: {e}")
            return False

    async def get_user_repair_history(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves all historical repair records created by a specific user."""
        if self.db is None:
            return []

        try:
            collection = self.db["repair_history"]
            cursor = collection.find({"username": username}).sort("timestamp", -1).limit(limit)
            records = await cursor.to_list(length=limit)
            # Format MongoDB ObjectIDs to strings for Jinja rendering
            for r in records:
                r["_id"] = str(r["_id"])
            return records
        except Exception as e:
            logger.error(f"Error fetching history for user {username}: {e}")
            return []

    async def get_repair_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.db is None:
            return None
        return await self.db["repair_history"].find_one({"session_id": session_id})

    async def fetch_successful_patches(self, error_type: str) -> List[Dict[str, Any]]:
        if self.db is None:
            return []

        collection = self.db["repair_history"]
        query = {
            "failure_analysis.error_type": error_type,
            "execution_status": "patch_validated_successfully"
        }
        cursor = collection.find(query).sort("timestamp", -1).limit(3)
        return await cursor.to_list(length=3)

db_manager = DatabaseManager()