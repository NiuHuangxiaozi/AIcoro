"""配置文件"""
import os
from typing import Optional,List
from pydantic import BaseModel


class Settings(BaseModel):
    # MongoDB配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "aicoro"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    
    
    # LLM 的api配置
    # 支持的模型
    supported_LLM :List[str] = [
        "deepseek-chat",
        "deepseek-reasoner"
    ]
    # DeepSeek API配置
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: Optional[str] = "sk-b879ea4cf9fa413e86e2f93167c817b2"
    
    deepseek_chat_model: str = "deepseek-chat"
    deepseek_reasoner_model: str = "deepseek-reasoner"
    
    
    
    # CORS配置
    cors_origins: list = ["*"]
    
    def __init__(self):
        super().__init__()
        # 从环境变量加载配置
        self.mongodb_url = os.getenv("MONGODB_URL", self.mongodb_url)
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", self.mongodb_db_name)
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", self.jwt_secret_key)
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", self.jwt_algorithm)
        self.jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", self.jwt_access_token_expire_minutes))

    
    # code agent configs
    base_code_dir :str = "/home/niu/code/AIcoro/backend/src/ai_code_agent"

settings = Settings()
