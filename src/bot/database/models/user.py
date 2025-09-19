from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator, root_validator


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid Object Id")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "bio": "Software developer",
                "phone": "+1234567890",
            }
        }


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class BaseDBModel(BaseModel):
    """Base model with common database fields"""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }


class User(BaseDBModel):
    telegram_id: str = Field(..., unique=True)
    username: str = Field(..., min_length=3, max_length=50)
    roles: List[UserRole] = Field(default=[UserRole.USER])
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    last_login: Optional[datetime] = None
    login_attempts: int = Field(default=0, ge=0)
    locked_until: Optional[datetime] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.lower()

    @root_validator("lock_status")
    @classmethod
    def validate_lock_status(cls, values):
        locked_until = values.get("locked_until")
        if locked_until and locked_until < datetime.now(timezone.utc):
            values["locked_until"] = None
            values["login_attempts"] = 0
        return values

    def is_locked(self) -> bool:
        """Check if account is locked"""
        return self.locked_until is not None and self.locked_until > datetime.now(
            timezone.utc
        )

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "roles": ["user"],
                "is_active": True,
                "is_verified": False,
            }
        }


# Request/Response Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    profile: Optional[UserProfile] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.lower()


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    profile: Optional[UserProfile] = None
    is_active: Optional[bool] = None
    roles: Optional[List[UserRole]] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v is not None and not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower() if v else v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.lower() if v else v


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: str
    username: str
    profile: Optional[UserProfile] = None
    roles: List[UserRole]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.lower()


class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, description="Number of documents to skip")
    limit: int = Field(10, ge=1, le=100, description="Number of documents to return")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: int = Field(
        -1, ge=-1, le=1, description="Sort order: 1 for ascending, -1 for descending"
    )


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool


# Database indexes configuration
INDEXES = {
    "users": [
        ("email", 1),  # Unique index on email
        ("username", 1),  # Unique index on username
        ("created_at", -1),  # Index for sorting
        ("roles", 1),  # Index for role-based queries
        ("is_active", 1),  # Index for active user queries
        (["email", "is_active"], 1),  # Compound index
        (["roles", "is_active"], 1),  # Compound index for admin queries
    ]
}
