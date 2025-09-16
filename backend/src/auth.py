"""认证相关功能"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings
from .database import get_database
from .models import User, UserResponse

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    # expire就是过期时间
    
    # 下面update之后，to_encoder里面就有userid和exp：过期时间
    to_encode.update({"exp": expire})
    
    
    # 这个encoded_jwt指的是加密过后的密钥
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_user_by_username(username: str) -> Optional[User]:
    """根据用户名获取用户"""
    db = get_database()
    user_data = await db.users.find_one({"username": username})
    if user_data:
        return User(**user_data)
    return None


async def get_user_by_id(user_id: str) -> Optional[User]:
    """根据用户ID获取用户"""
    db = get_database()
    user_data = await db.users.find_one({"id": user_id})
    if user_data:
        return User(**user_data)
    return None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户"""
    
    # 首先查看有没有这样的用户名
    user = await get_user_by_username(username)
    if not user:
        return None
    # 再查看对应的密码对不对
    if not verify_password(password, user.password_hash):
        return None
    
    # 如果都对，就返回这个用户结构体
    return user

'''
当把 security 作为接口的依赖项（Depends(security)）时，它会自动完成：
检查请求头中是否包含 Authorization 字段；
检查 Authorization 字段的格式是否符合 Bearer <令牌>（即开头是否为 Bearer ，后面是否跟随令牌字符串）；
若格式正确，提取出 <令牌内容> 并返回；若格式错误（如缺少 Authorization 头、格式不是 Bearer 令牌），则直接返回 401 未授权错误（状态码 401 Unauthorized）
'''
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    
    # credentials 就是前端发来的jwt
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    
    user = await get_user_by_id(user_id)
    # 找不到用户就报错
    if user is None:
        raise credentials_exception
    return user
