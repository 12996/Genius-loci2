# 项目结构说明

```
heikeshong/
├── app/                        # 应用主目录
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口 ⭐
│   │
│   ├── api/                    # API 路由层
│   │   ├── __init__.py         # 路由聚合
│   │   └── v1/                 # API v1 版本
│   │       ├── __init__.py     # v1 路由聚合
│   │       └── bubbles.py      # 气泡笔记路由
│   │
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理 ⭐
│   │   ├── database.py         # 数据库连接
│   │   └── oss_storage.py      # OSS 文件存储
│   │
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic 模型
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   └── bubble_service.py   # 气泡笔记服务
│   │
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       └── emotion_analyzer.py # 情感分析工具
│
├── .env                        # 环境配置
├── .env.example                # 配置模板
├── requirements.txt            # 依赖列表
├── run.py                      # 启动入口 ⭐
├── README.md                   # 项目说明
├── API_EXAMPLES.md             # API 调用示例
├── TROUBLESHOOTING.md          # 故障排查
└── STRUCTURE.md                # 本文档
```

## 模块说明

### app/main.py
FastAPI 应用主入口,负责:
- 创建 FastAPI 应用实例
- 配置 CORS 中间件
- 注册路由
- 生命周期管理
- 全局异常处理

### app/api/
API 路由层,负责:
- 定义 HTTP 端点
- 请求参数验证
- 调用业务服务层
- 返回 HTTP 响应

**添加新 API 模块步骤:**
1. 在 `app/api/v1/` 下创建新文件,如 `users.py`
2. 创建 APIRouter 并定义端点
3. 在 `app/api/v1/__init__.py` 中注册路由
4. 自动生效,路径为 `/api/v1/{module_name}`

### app/core/
核心基础设施模块:
- **config.py**: 统一配置管理,从 .env 读取配置
- **database.py**: 数据库连接和操作
- **oss_storage.py**: 文件存储服务

### app/models/
数据模型定义,使用 Pydantic 进行数据验证

### app/services/
业务逻辑层,负责:
- 核心业务流程
- 数据处理和转换
- 调用核心模块
- 事务管理

### app/utils/
通用工具模块,如情感分析、日志、缓存等

## 添加新功能指南

### 1. 添加新的 API 模块 (例如: 用户管理)

```python
# app/api/v1/users.py
from fastapi import APIRouter
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.post("/")
async def create_user():
    return await user_service.create_user()
```

```python
# app/api/v1/__init__.py
from app.api.v1 import users

router.include_router(users.router)
```

### 2. 添加新的业务服务

```python
# app/services/user_service.py
class UserService:
    async def create_user(self):
        # 业务逻辑
        pass

user_service = UserService()
```

### 3. 添加新的数据模型

```python
# app/models/schemas.py
class UserCreate(BaseModel):
    username: str
    email: str
```

## 启动方式

### 方式 1: 使用启动脚本
```bash
python run.py
```

### 方式 2: 使用 uvicorn
```bash
uvicorn app.main:app --reload
```

### 方式 3: 指定端口
```bash
uvicorn app.main:app --port 8080
```

## 环境变量

所有配置集中在 `.env` 文件中,通过 `app/core/config.py` 统一管理。

## 设计原则

1. **分层架构**: API → Service → Core
2. **依赖注入**: 使用单例模式管理资源
3. **配置分离**: 配置集中在 config.py
4. **路由聚合**: 按版本和模块组织路由
5. **易于扩展**: 添加新功能无需修改现有代码
