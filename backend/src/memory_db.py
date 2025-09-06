"""内存数据库（用于开发测试）"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class MemoryDatabase:
    """内存数据库类"""
    
    def __init__(self):
        self.collections: Dict[str, List[Dict[str, Any]]] = {
            "users": [],
            "sessions": []
        }
    
    def __getattr__(self, name: str):
        """动态获取集合"""
        if name not in self.collections:
            self.collections[name] = []
        return MemoryCollection(self.collections[name])
    
    def get_collection(self, name: str):
        """获取集合"""
        if name not in self.collections:
            self.collections[name] = []
        return MemoryCollection(self.collections[name])


class MemoryCollection:
    """内存集合类"""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        for doc in self.data:
            if self._match_filter(doc, filter_dict):
                return doc
        return None
    
    async def insert_one(self, document: Dict[str, Any]) -> None:
        """插入单个文档"""
        # 确保有时间戳
        if 'created_at' not in document:
            document['created_at'] = datetime.utcnow().isoformat()
        if 'updated_at' not in document:
            document['updated_at'] = datetime.utcnow().isoformat()
        
        self.data.append(document.copy())
    
    async def replace_one(self, filter_dict: Dict[str, Any], document: Dict[str, Any]) -> None:
        """替换单个文档"""
        for i, doc in enumerate(self.data):
            if self._match_filter(doc, filter_dict):
                document['updated_at'] = datetime.utcnow().isoformat()
                self.data[i] = document.copy()
                return
        # 如果没找到，插入新文档
        await self.insert_one(document)
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> Dict[str, int]:
        """删除单个文档"""
        for i, doc in enumerate(self.data):
            if self._match_filter(doc, filter_dict):
                self.data.pop(i)
                return {"deleted_count": 1}
        return {"deleted_count": 0}
    
    def find(self, filter_dict: Dict[str, Any]):
        """查找多个文档"""
        return MemoryCursor([doc for doc in self.data if self._match_filter(doc, filter_dict)])
    
    def _match_filter(self, doc: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """检查文档是否匹配过滤条件"""
        for key, value in filter_dict.items():
            if key not in doc or doc[key] != value:
                return False
        return True


class MemoryCursor:
    """内存游标类"""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
    
    def sort(self, key: str, direction: int = 1):
        """排序"""
        reverse = direction == -1
        self.data.sort(key=lambda x: x.get(key, ''), reverse=reverse)
        return self
    
    def limit(self, count: int):
        """限制数量"""
        self.data = self.data[:count]
        return self
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if not self.data:
            raise StopAsyncIteration
        return self.data.pop(0)


# 全局内存数据库实例
memory_db = MemoryDatabase()
