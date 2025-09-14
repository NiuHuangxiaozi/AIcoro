"""认证路由"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from ..database import get_database
from ..models import UserLogin, UserRegister, UserResponse, TokenResponse, User
from ..auth import (
    authenticate_user, 
    get_password_hash, 
    create_access_token, 
    get_user_by_username,
    get_current_user
)
from ..config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password)
    )
    
    # 保存到数据库
    db = get_database()
    await db.users.insert_one(user.dict())
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            created_at=user.created_at
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """用户登录"""
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 时间差对象
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # 将access_token返回给前端，以后前端只要拿到了这个access_token就可以访问后端的任何接口数据
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at
    )
