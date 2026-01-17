# 气泡笔记 (Bubble Note) API

基于 FastAPI + Supabase + 阿里云 OSS 的气泡笔记服务 + 地灵对话系统

## ✨ 核心功能

- 📝 **气泡笔记**：创建、查询附近笔记、图片上传
- 🤖 **地灵对话**：基于视觉感知和地理记忆的智能对话系统
- 🧠 **记忆检索**：基于 PostGIS 的地理位置记忆检索
- 👁️ **视觉感知**：多模态图片解析和场景理解
- 💬 **流式响应**：实时流式对话，提升用户体验

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置:

```bash
cp .env.example .env
```

配置说明：
- Supabase：数据库和存储服务
- 魔搭模型：对话大模型 API
- 视觉模型：多模态图片解析 API（可选 GPT-4o、Gemini Vision 等）
- 阿里云 OSS：图片存储服务

### 3. 初始化数据库

在 Supabase SQL Editor 中执行：

```bash
# 执行气泡笔记表结构
psql -f docs/database/bubble_note.sql

# 执行地灵对话记忆表结构
psql -f docs/database/genius_loci_record.sql
```

### 4. 启动服务

```bash
python run.py
```

服务将在 `http://localhost:8000` 启动

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
app/
├── main.py              # FastAPI 应用入口
├── api/                 # API 路由
│   └── v1/
│       ├── bubbles.py   # 气泡笔记接口
│       └── genius_loci.py # 地灵对话接口
├── core/                # 核心模块
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接
│   └── oss_storage.py   # OSS 存储
├── models/              # 数据模型
│   └── schemas.py       # Pydantic 模型
├── services/            # 业务服务
│   ├── vision_service.py     # 视觉感知服务
│   ├── chat_service.py       # 对话流式服务
│   ├── genius_loci_service.py# 地灵核心服务
│   └── bubble_service.py     # 气泡笔记服务
└── utils/               # 工具模块
    └── emotion_analyzer.py
```

详细结构说明请查看 [STRUCTURE.md](STRUCTURE.md)

## API 端点

### 气泡笔记接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/bubbles/note` | 创建/更新笔记 (JSON) |
| POST | `/api/v1/bubbles/note/with-image` | 创建/更新笔记 (含图片) |
| GET | `/api/v1/bubbles/nearby` | 获取附近气泡 |
| GET | `/api/v1/bubbles/top` | 获取 Top 气泡 |
| DELETE | `/api/v1/bubbles/note/{note_id}` | 删除笔记 |
| GET | `/api/v1/bubbles/health` | 健康检查 |

### 地灵对话接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/genius-loci/chat` | 地灵流式对话 (SSE) |
| GET | `/api/v1/genius-loci/health` | 健康检查 |

📖 **地灵对话详细文档：** [docs/GENIUS_LOCI_GUIDE.md](docs/GENIUS_LOCI_GUIDE.md)

## 调用示例

### 创建纯文本笔记

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "content": "今天天气真好!",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408
  }'
```

### 创建带图片的笔记

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note/with-image" \
  -F "user_id=1" \
  -F "content=分享美丽的风景" \
  -F "gps_longitude=120.15507" \
  -F "gps_latitude=30.27408" \
  -F "image=@image.jpg"
```

更多示例请查看 [API_EXAMPLES.md](API_EXAMPLES.md)

## 核心功能

- ✅ 前置校验 (内容完整性、坐标范围、幂等性)
- ✅ 并发上传图片到阿里云 OSS
- ✅ AI 情感识别 (难过/开心/平静/神秘/愤怒)
- ✅ Supabase 数据库持久化
- ✅ PostGIS 空间索引 (附近查询)
- ✅ 自动权重计算

## 技术栈

- **Web 框架**: FastAPI 0.109.0
- **数据库**: Supabase (PostgreSQL + PostGIS)
- **对象存储**: 阿里云 OSS
- **AI 模型**: 魔搭 ModelScope
- **数据验证**: Pydantic 2.5.3

## 开发指南

### 添加新 API 模块

1. 在 `app/api/v1/` 创建新文件
2. 定义 APIRouter 和端点
3. 在 `app/api/v1/__init__.py` 注册路由

详细步骤请查看 [STRUCTURE.md](STRUCTURE.md)

## 常见问题

查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 许可证

MIT License
