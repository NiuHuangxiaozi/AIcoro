"""配置文件"""
import os
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
    # MongoDB配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "aicoro"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # DeepSeek API配置
    deepseek_api_key: Optional[str] = "test-api-key"  # 默认测试密钥
    deepseek_base_url: str = "https://api.deepseek.com"
    
    # CORS配置
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    def __init__(self):
        super().__init__()
        # 从环境变量加载配置
        self.mongodb_url = os.getenv("MONGODB_URL", self.mongodb_url)
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", self.mongodb_db_name)
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", self.jwt_secret_key)
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", self.jwt_algorithm)
        self.jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", self.jwt_access_token_expire_minutes))
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", self.deepseek_base_url)


settings = Settings()
