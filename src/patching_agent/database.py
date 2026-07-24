"""
Module: Central Database & Long-Term Memory Manager
Description: Implements async persistence models to record repair attempts,
             patch historical runs, and maintain operational logs in MongoDB Atlas.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from patching_agent.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages the lifecycle of the asynchronous MongoDB Atlas connection pool and long-term memory logs."""
    
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

    async def save_repair_history(self, session_id: str, state_dump: Dict[str, Any]) -> bool:
        """
        Saves or updates a complete snapshot of a repair operation in long-term memory.
        """
        if self.db is None:
            logger.error("Database uninitialized. Cannot write repair logs.")
            return False

        collection = self.db["repair_history"]
        
        # Build a persistent historical context package
        historical_document = {
            "session_id": session_id,
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
            # Upsert the record based on the session ID
            await collection.update_one(
                {"session_id": session_id},
                {"$set": historical_document},
                upsert=True
            )
            logger.info(f"Successfully committed repair snapshot to database for session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to write repair metrics snapshot to MongoDB Atlas: {e}")
            return False

    async def get_repair_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a historical repair snapshot from the database."""
        if self.db is None:
            return None
            
        try:
            record = await self.db["repair_history"].find_one({"session_id": session_id})
            return record
        except Exception as e:
            logger.error(f"Error fetching historical database session {session_id}: {e}")
            return None

    async def fetch_successful_patches(self, error_type: str) -> List[Dict[str, Any]]:
        """
        Queries long-term memory to find historical repair patterns that successfully
        fixed a specific type of exception class.
        """
        if self.db is None:
            return []

        collection = self.db["repair_history"]
        query = {
            "failure_analysis.error_type": error_type,
            "execution_status": "patch_validated_successfully"
        }

        try:
            cursor = collection.find(query).sort("timestamp", -1).limit(3)
            return await cursor.to_list(length=3)
        except Exception as e:
            logger.error(f"Failed to extract historical pattern matches for {error_type}: {e}")
            return []

# Global database manager instance
db_manager = DatabaseManager()