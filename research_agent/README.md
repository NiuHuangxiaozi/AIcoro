# 智能研究Agent

一个基于DeepSeek和LangChain的智能研究助手，能够智能判断是否需要网络搜索，并具备长期偏好记忆功能。

## 功能特性

1. **智能决策路由**: 自动判断用户问题是否需要网络搜索
2. **网络搜索能力**: 集成Tavily搜索API获取最新信息
3. **长期偏好保存**: 使用CompositeBackend实现跨会话的记忆保存
4. **DeepSeek推理**: 使用DeepSeek模型进行高质量推理

## 安装依赖

```bash
uv sync
```

## 环境配置

1. 创建 `.env` 文件：
```bash
TAVILY_API=your_tavily_api_key_here
DEEPSEEK_API=your_deepseek_api_key_here
```

2. 获取API密钥：
   - **Tavily API**: 访问 [Tavily](https://tavily.com/) 获取搜索API密钥
   - **DeepSeek API**: 访问 [DeepSeek](https://platform.deepseek.com/) 获取API密钥

## 使用方法

### 直接运行测试

```bash
python main.py
```

程序会自动运行四个测试场景：
1. 简单问题（不需要网络搜索）
2. 需要网络搜索的技术问题
3. 保存用户偏好
4. 读取用户偏好（跨会话）

### 作为模块使用

```python
from main import handle_query
import uuid

# 简单查询
result = handle_query("什么是Python？")

# 复杂查询（可能需要搜索）
result = handle_query("LangChain最新版本是什么？")

# 带记忆的对话
thread_id = str(uuid.uuid4())
result = handle_query("我喜欢用比喻解释技术", thread_id=thread_id)
result = handle_query("你还记得我的偏好吗？", thread_id=thread_id)
```

### 运行示例

```bash
python example.py
```

查看 `example.py` 文件了解更多使用场景。

## 架构说明

### 决策Agent
- 任务：判断用户问题是否需要网络搜索
- 模型：DeepSeek Reasoner
- 决策依据：
  - 需要搜索：最新信息、外部验证、技术细节
  - 不需要搜索：基础概念、常识、个人偏好

### 研究Agent
- 任务：进行网络搜索并生成研究报告
- 工具：Tavily网络搜索
- 记忆：长期偏好保存到 `/memories/` 路径

### 记忆系统
- **短期记忆**: StateBackend - 会话内状态
- **长期记忆**: StoreBackend - 跨会话偏好保存
- 使用 InMemoryStore 存储（开发环境）

## 项目结构

```
research_agent/
├── main.py              # 主程序文件
├── research_agent.py    # 备用agent文件
├── pyproject.toml       # 项目配置和依赖
├── uv.lock             # 依赖锁定文件
├── README.md           # 项目说明
└── .env                # 环境变量（需要创建）
```

## 依赖包

- `deepagents`: DeepAgent框架
- `langchain-openai`: LangChain OpenAI集成
- `tavily-python`: Tavily搜索API
- `langgraph`: 图状态管理
- `python-dotenv`: 环境变量管理

## 注意事项

1. 确保API密钥有效且有足够额度
2. DeepSeek API需要网络连接
3. 长期记忆在重启程序后会丢失（使用InMemoryStore）
4. 生产环境建议使用持久化存储替代InMemoryStore
