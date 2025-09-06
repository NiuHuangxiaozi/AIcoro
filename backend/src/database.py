"""数据库连接和操作"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Union
from .config import settings
from .memory_db import memory_db, MemoryDatabase


class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[Union[AsyncIOMotorDatabase, MemoryDatabase]] = None
    use_memory: bool = False


db = Database()


async def connect_to_mongo():
    """连接到MongoDB或使用内存数据库"""
    try:
        # 尝试连接MongoDB
        db.client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        # 测试连接
        await db.client.admin.command('ping')
        db.database = db.client[settings.mongodb_db_name]
        db.use_memory = False
        print(f"Connected to MongoDB at {settings.mongodb_url}")
    except Exception as e:
        # 如果连接失败，使用内存数据库
        print(f"MongoDB connection failed: {e}")
        print("Using in-memory database for development")
        db.database = memory_db
        db.use_memory = True


async def close_mongo_connection():
    """关闭MongoDB连接"""
    if db.client and not db.use_memory:
        db.client.close()
        print("Disconnected from MongoDB")
    elif db.use_memory:
        print("Memory database closed")


def get_database() -> Union[AsyncIOMotorDatabase, MemoryDatabase]:
    """获取数据库实例"""
    return db.database
