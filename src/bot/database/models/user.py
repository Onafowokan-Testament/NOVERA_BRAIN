from bson import ObjectId
from bot.database.database import db_connection
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AsyncUserModel:
    def __init__(self):
        self.collection = db_connection.get_collection('users')
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        try:
            result = await self.collection.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.collection.find_one({'_id': ObjectId(telegram_id)})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.collection.find_one({'email': email})
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_users(self, limit: int = 100) -> list:
        try:
            cursor = self.collection.find().limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            result = await self.collection.update_one(
                {'_id': ObjectId(user_id)}, 
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        try:
            result = await self.collection.delete_one({'_id': ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
