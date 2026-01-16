from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from config import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    role: str
    email: Optional[str] = None
    
class UserInDB(User):
    hashed_password: str

# Mock user database
fake_users_db = {
    "security_admin": {
        "username": "security_admin",
        "email": "admin@company.com",
        "hashed_password": pwd_context.hash("security123"),
        "role": "security"
    },
    "engineer": {
        "username": "engineer",
        "email": "engineer@company.com",
        "hashed_password": pwd_context.hash("engineer123"),
        "role": "engineering"
    },
    "sales_user": {
        "username": "sales_user",
        "email": "sales@company.com",
        "hashed_password": pwd_context.hash("sales123"),
        "role": "sales"
    }
}

class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self):
        self.role_permissions = config.ROLE_PERMISSIONS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user_dict = fake_users_db.get(username)
        if not user_dict:
            return None
        if not self.verify_password(password, user_dict["hashed_password"]):
            return None
        return UserInDB(**user_dict)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def has_permission(self, role: str, required_permission: str) -> bool:
        """Check if a role has a specific permission"""
        permissions = self.role_permissions.get(role, [])
        return required_permission in permissions
    
    def get_user_permissions(self, role: str) -> List[str]:
        """Get all permissions for a role"""
        return self.role_permissions.get(role, [])

rbac_manager = RBACManager()
