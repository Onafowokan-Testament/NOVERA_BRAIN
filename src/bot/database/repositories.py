from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, BulkWriteError
from pymongo import ReturnDocument, ASCENDING, DESCENDING
import logging
from loguru import logger
from bot.database.database import get_database
from bot.database.models.user import User, UserCreate, UserUpdate, PaginationParams, PaginatedResponse

logger = logging.getLogger(__name__)

class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get collection instance"""
        if self._collection is None:
            db = get_database()
            self._collection = db[self.collection_name]
        return self._collection
    
    async def find_by_id(self, id: Union[str, ObjectId]) -> Optional[dict]:
        """Find document by ID"""
        try:
            if isinstance(id, str):
                id = ObjectId(id)
            
            document = await self.collection.find_one({"_id": id})
            return document
        except Exception as e:
            logger.error(f"Error finding document by ID {id}: {e}")
            raise
    
    async def find_one(self, filter: dict) -> Optional[dict]:
        """Find one document by filter"""
        try:
            document = await self.collection.find_one(filter)
            return document
        except Exception as e:
            logger.error(f"Error finding document with filter {filter}: {e}")
            raise
    
    async def find_many(
        self,
        filter: dict = None,
        pagination: PaginationParams = None,
        projection: dict = None
    ) -> PaginatedResponse:
        """Find multiple documents with pagination"""
        try:
            filter = filter or {}
            pagination = pagination or PaginationParams()
            
            # Create cursor
            cursor = self.collection.find(filter, projection)
            
            # Apply sorting
            sort_direction = DESCENDING if pagination.sort_order == -1 else ASCENDING
            cursor = cursor.sort(pagination.sort_by, sort_direction)
            
            # Count total documents
            total = await self.collection.count_documents(filter)
            
            # Apply pagination
            cursor = cursor.skip(pagination.skip).limit(pagination.limit)
            
            # Fetch documents
            documents = await cursor.to_list(pagination.limit)
            
            return PaginatedResponse(
                items=documents,
                total=total,
                skip=pagination.skip,
                limit=pagination.limit,
                has_next=pagination.skip + pagination.limit < total,
                has_prev=pagination.skip > 0
            )
        except Exception as e:
            logger.error(f"Error finding documents: {e}")
            raise
    
    async def create(self, document: dict) -> dict:
        """Create a new document"""
        try:
            # Add timestamps
            now = datetime.now(timezone.utc)
            document['created_at'] = now
            document['updated_at'] = now
            
            result = await self.collection.insert_one(document)
            document['_id'] = result.inserted_id
            return document
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error creating document: {e}")
            raise ValueError("Document with this unique field already exists")
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def update_by_id(
        self, 
        id: Union[str, ObjectId], 
        update_data: dict,
        upsert: bool = False
    ) -> Optional[dict]:
        """Update document by ID"""
        try:
            if isinstance(id, str):
                id = ObjectId(id)
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            result = await self.collection.find_one_and_update(
                {"_id": id},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
                upsert=upsert
            )
            return result
        except Exception as e:
            logger.error(f"Error updating document {id}: {e}")
            raise
    
    async def delete_by_id(self, id: Union[str, ObjectId]) -> bool:
        """Delete document by ID"""
        try:
            if isinstance(id, str):
                id = ObjectId(id)
            
            result = await self.collection.delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document {id}: {e}")
            raise
    
    async def count(self, filter: dict = None) -> int:
        """Count documents matching filter"""
        try:
            filter = filter or {}
            return await self.collection.count_documents(filter)
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            raise
    
    async def exists(self, filter: dict) -> bool:
        """Check if document exists"""
        try:
            count = await self.collection.count_documents(filter, limit=1)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            raise

class UserRepository(BaseRepository):
    """User-specific repository operations"""
    
    def __init__(self):
        super().__init__("users")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await self.find_one({
                "$or": [
                    {"email": user_data.email},
                    {"username": user_data.username}
                ]
            })
            
            if existing_user:
                if existing_user["email"] == user_data.email:
                    raise ValueError("User with this email already exists")
                else:
                    raise ValueError("User with this username already exists")
            
            # Create user document
            user = User(**user_data.dict())
            user_dict = user.dict(by_alias=True)
            
            # Hash password
            user.set_password(user_data.password)
            user_dict['hashed_password'] = user.hashed_password
            
            # Remove plain password
            user_dict.pop('password', None)
            
            created_user = await self.create(user_dict)
            return User(**created_user)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_doc = await self.find_one({"email": email.lower()})
        return User(**user_doc) if user_doc else None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_doc = await self.find_one({"username": username.lower()})
        return User(**user_doc) if user_doc else None
    
    async def get_user_by_id(self, user_id: Union[str, ObjectId]) -> Optional[User]:
        """Get user by ID"""
        user_doc = await self.find_by_id(user_id)
        return User(**user_doc) if user_doc else None
    
    async def update_user(
        self, 
        user_id: Union[str, ObjectId], 
        update_data: UserUpdate
    ) -> Optional[User]:
        """Update user"""
        try:
            # Filter out None values
            update_dict = {
                k: v for k, v in update_data.dict().items() 
                if v is not None
            }
            
            if not update_dict:
                return await self.get_user_by_id(user_id)
            
            # Check for unique field conflicts
            if 'email' in update_dict or 'username' in update_dict:
                conflict_filter = {"_id": {"$ne": ObjectId(user_id) if isinstance(user_id, str) else user_id}}
                
                if 'email' in update_dict:
                    conflict_filter["email"] = update_dict["email"]
                    existing = await self.find_one(conflict_filter)
                    if existing:
                        raise ValueError("User with this email already exists")
                
                if 'username' in update_dict:
                    conflict_filter["username"] = update_dict["username"]
                    existing = await self.find_one(conflict_filter)
                    if existing:
                        raise ValueError("User with this username already exists")
            
            updated_user = await self.update_by_id(user_id, update_dict)
            return User(**updated_user) if updated_user else None
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def increment_login_attempts(self, user_id: Union[str, ObjectId]) -> None:
        """Increment login attempts counter"""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(user_id) if isinstance(user_id, str) else user_id},
                {
                    "$inc": {"login_attempts": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
        except Exception as e:
            logger.error(f"Error incrementing login attempts for user {user_id}: {e}")
            raise
    
    async def lock_user(self, user_id: Union[str, ObjectId], lock_duration_minutes: int = 30) -> None:
        """Lock user account"""
        try:
            lock_until = datetime.now(timezone.utc).timestamp() + (lock_duration_minutes * 60)
            lock_until_dt = datetime.fromtimestamp(lock_until, timezone.utc)
            
            await self.collection.update_one(
                {"_id": ObjectId(user_id) if isinstance(user_id, str) else user_id},
                {
                    "$set": {
                        "locked_until": lock_until_dt,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error locking user {user_id}: {e}")
            raise
    
    async def reset_login_attempts(self, user_id: Union[str, ObjectId]) -> None:
        """Reset login attempts and unlock account"""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(user_id) if isinstance(user_id, str) else user_id},
                {
                    "$set": {
                        "login_attempts": 0,
                        "locked_until": None,
                        "last_login": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error resetting login attempts for user {user_id}: {e}")
            raise
    
    async def get_active_users(self, pagination: PaginationParams = None) -> PaginatedResponse:
        """Get all active users"""
        return await self.find_many(
            filter={"is_active": True},
            pagination=pagination,
            projection={"hashed_password": 0}  # Exclude password hash
        )
    
    async def get_users_by_role(self, role: str, pagination: PaginationParams = None) -> PaginatedResponse:
        """Get users by role"""
        return await self.find_many(
            filter={"roles": role, "is_active": True},
            pagination=pagination,
            projection={"hashed_password": 0}
        )

# Initialize repositories
user_repository = UserRepository()