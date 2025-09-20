from bson import ObjectId
from bot.database.database import db_connection
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AsyncUserModel:
    def __init__(self):
        pass
        
    async def _get_collection(self):
        """Helper to get collection"""
        return db_connection.database['users'] 
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        try:
            collection = await self._get_collection()
            result = await collection.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        try:
            collection = await self._get_collection()
            # Use telegram_id field, not ObjectId
            return await collection.find_one({'telegram_id': telegram_id})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
        
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            collection = await self._get_collection()
            return await collection.find_one({'email': email})
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_users(self, limit: int = 100) -> list:
        try:
            collection = await self._get_collection()
            cursor =await collection.find().limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {'_id': ObjectId(user_id)}, 
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({'_id': ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
