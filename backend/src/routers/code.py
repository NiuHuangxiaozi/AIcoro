"""代码管理路由"""
import os
import tarfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends,Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ..auth import get_current_user
from ..models import User

router = APIRouter(prefix="/code", tags=["代码管理"])

# 代码生成根目录
CODE_GENERATION_ROOT = Path(__file__).parent.parent.parent.parent / "tmp_code_generation"

class FileNode(BaseModel):
    """文件节点模型"""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None
    children: Optional[List['FileNode']] = None

class FileContent(BaseModel):
    """文件内容模型"""
    path: str
    content: str
    size: int

def get_file_tree(directory: Path, base_path: str = "") -> List[FileNode]:
    """获取目录的文件树结构"""
    items = []
    
    if not directory.exists() or not directory.is_dir():
        return items
    
    try:
        for item in sorted(directory.iterdir()):
            # 跳过隐藏文件和特殊目录
            if item.name.startswith('.') or item.name == '__pycache__':
                continue
                
            relative_path = os.path.join(base_path, item.name) if base_path else item.name
            
            if item.is_dir():
                # 递归获取子目录
                children = get_file_tree(item, relative_path)
                node = FileNode(
                    name=item.name,
                    path=relative_path,
                    is_directory=True,
                    children=children
                )
            else:
                # 文件节点
                try:
                    size = item.stat().st_size
                except OSError:
                    size = 0
                    
                node = FileNode(
                    name=item.name,
                    path=relative_path,
                    is_directory=False,
                    size=size
                )
            
            items.append(node)
    except PermissionError:
        # 如果没有权限访问目录，返回空列表
        pass
        
    return items

@router.get("/projects", response_model=List[str])
async def get_projects():
    """获取所有项目列表"""
    try:
        projects = []
        if CODE_GENERATION_ROOT.exists():
            for item in CODE_GENERATION_ROOT.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    projects.append(item.name)
        return sorted(projects)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}"
        )

@router.get("/projects/tree", response_model=List[FileNode])
async def get_project_tree(
     # 声明 project_name 为查询参数，required=True 确保必传（避免空值导致的 404/业务错误）
    project_name: str = Query(..., 
                             description="需要查询文件树的项目路径",
                             min_length=1,  # 可选：限制项目名最小长度，避免无效值
                             example="/home/code/my-first-project")  # 可选：提供示例值，方便接口文档测试
    ):
    """获取项目的文件树结构"""
    project_path = Path(project_name)
    
    if not project_path.exists():
        print(f"node tree wrong")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    if not project_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定路径不是目录"
        )
    
    try:
        tree = get_file_tree(project_path)
        return tree
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件树失败: {str(e)}"
        )

@router.get("/projects/files", response_model=FileContent)
async def get_file_content(
                project_name: str = Query(..., 
                             description="需要查询文件树的项目路径",
                             min_length=1,  # 可选：限制项目名最小长度，避免无效值
                             example="/home/code/my-first-project"),  # 可选：提供示例值，方便接口文档测试,
                file_path: str = Query(...,
                            description="文件名字",
                             min_length=1,  # 可选：限制项目名最小长度，避免无效值
                             example="main.cpp"),
                ):
    """获取文件内容"""
    # 安全检查：防止路径遍历攻击
    if ".." in file_path or file_path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非法的文件路径"
        )
    
    full_path = Path(project_name) / file_path
    
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    if not full_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定路径不是文件"
        )
    
    try:
        # 尝试以文本方式读取文件
        content = full_path.read_text(encoding='utf-8')
        size = full_path.stat().st_size
        
        return FileContent(
            path=file_path,
            content=content,
            size=size
        )
    except UnicodeDecodeError:
        # 如果不是文本文件，返回错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件不是文本格式，无法显示内容"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取文件失败: {str(e)}"
        )

@router.get("/projects/download")
async def download_project(
    background_tasks: BackgroundTasks,
    project_name: str =  Query(...,description="下载文件",example="main.cpp")
    ):
    """下载项目的tar.gz文件"""
    project_path = Path(project_name)
    
    if not project_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    if not project_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定路径不是目录"
        )
    
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f"niu.tar.gz",
            delete=False
        )
        temp_file.close()
        
        # 创建tar.gz文件
        with tarfile.open(temp_file.name, "w:gz") as tar:
            tar.add(project_path, arcname="niu")
        
        background_tasks.add_task(os.unlink, temp_file.name)
        # 返回文件下载响应
        return FileResponse(
            path=temp_file.name,
            filename=f"niu.tar.gz",
            media_type="application/gzip",
        )
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建下载文件失败: {str(e)}"
        )
