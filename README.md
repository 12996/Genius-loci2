# 气泡笔记 (Bubble Note) API

基于 FastAPI + Supabase + 阿里云 OSS 的气泡笔记服务

## 项目结构

```
heikeshong/
├── .env                      # 环境配置文件 (需要您填写)
├── .env.example              # 环境配置模板
├── requirements.txt          # Python 依赖
├── main.py                   # FastAPI 主应用入口 ⭐
├── routers.py                # API 路由接口
├── schemas.py                # Pydantic 数据模型
├── service.py                # 核心业务逻辑层
├── database.py               # Supabase 数据库连接
├── oss_storage.py            # 阿里云 OSS 文件上传
├── emotion_analyzer.py       # 情感分析模块
├── test_imports.py           # 导入测试脚本
├── API_EXAMPLES.md           # API 调用示例文档 ⭐
└── README.md                 # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置:

```bash
# Supabase 配置
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name
OSS_BUCKET_DOMAIN=https://your_bucket_name.oss-cn-hangzhou.aliyuncs.com
```

### 3. 测试模块导入

```bash
python test_imports.py
```

如果所有模块都显示 ✓, 则说明配置正确。

### 4. 启动服务

```bash
python main.py
```

或使用 uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/bubbles/note` | 创建/更新笔记 (multipart/form-data) |
| POST | `/api/v1/bubbles/note/json` | 创建/更新笔记 (JSON) |
| GET | `/api/v1/bubbles/note/{note_id}` | 获取笔记详情 |
| GET | `/api/v1/bubbles/nearby` | 获取附近气泡 |
| GET | `/api/v1/bubbles/top` | 获取 Top 气泡 |
| DELETE | `/api/v1/bubbles/note/{note_id}` | 删除笔记 |
| GET | `/api/v1/bubbles/health` | 健康检查 |

## 快速测试

### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/bubbles/health
```

### 2. 创建纯文本笔记

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note/json" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "content": "今天天气真好,心情很愉快!",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "status": 1
  }'
```

### 3. 获取笔记详情

```bash
curl http://localhost:8000/api/v1/bubbles/note/1
```

### 4. 获取附近气泡

```bash
curl "http://localhost:8000/api/v1/bubbles/nearby?longitude=120.15507&latitude=30.27408&radius_km=1.0"
```

更多示例请查看 [API_EXAMPLES.md](API_EXAMPLES.md)

## 核心功能

### 1. 前置校验
- ✓ 内容完整性校验 (文本与图片不可同时为空)
- ✓ 地理坐标合法性校验 (经度 [-180,180], 纬度 [-90,90])
- ✓ 操作幂等性判别 (通过 note_id 区分创建/更新)

### 2. 多媒体处理
- ✓ 并发上传图片到阿里云 OSS
- ✓ 异常熔断机制 (任一图片上传失败则终止流程)
- ✓ OSS 路径规范: `bubbles/{YYYY}/{MM}/{DD}/{user_id}_{uuid}.jpg`

### 3. 情感识别
- ✓ 自动分析文本情感 (难过/开心/平静/神秘/愤怒)
- ✓ AI 模型调用 + 结果归一化
- ✓ 空文本默认为"平静"或"未知"

### 4. 数据库持久化
- ✓ 原子性 Upsert 操作
- ✓ PostGIS 空间索引支持附近查询
- ✓ 自动计算权重得分 (图文/纯文 + 时间衰减)

### 5. 空间查询
- ✓ 获取指定半径内的气泡笔记
- ✓ 毫秒级距离计算 (使用 PostGIS)
- ✓ 支持按状态筛选 (公开/私有)

## 数据库表结构

表 `bubble_note` 包含以下字段:

```sql
CREATE TABLE bubble_note (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    note_type TINYINT NOT NULL,  -- 1-图文/2-纯文
    content TEXT NOT NULL,
    image_urls VARCHAR(1024),
    gps_longitude DECIMAL(10,6) NOT NULL,
    gps_latitude DECIMAL(10,6) NOT NULL,
    location GEOGRAPHY(POINT, 4326),  -- PostGIS 空间字段
    status TINYINT NOT NULL DEFAULT 1,  -- 1-公开/2-私有
    emotion VARCHAR(20) DEFAULT '未知',
    create_time DATETIME NOT NULL,
    update_time DATETIME NOT NULL,
    weight_score DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    is_valid TINYINT NOT NULL DEFAULT 1
);
```

## 常见问题

### Q: 如何上传多张图片?

使用 `multipart/form-data` 格式,多次指定 `images` 字段:

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note" \
  -F "user_id=1" \
  -F "content=分享美丽的风景" \
  -F "gps_longitude=120.15507" \
  -F "gps_latitude=30.27408" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg"
```

### Q: 如何实现分页?

使用 `limit` 参数控制返回数量:

```bash
curl "http://localhost:8000/api/v1/bubbles/nearby?limit=50"
```

### Q: 如何筛选公开/私有笔记?

使用 `status` 参数:

```bash
curl "http://localhost:8000/api/v1/bubbles/nearby?status=1"  # 仅公开
curl "http://localhost:8000/api/v1/bubbles/nearby?status=2"  # 仅私有
```

### Q: Python 模块导入失败?

确保已安装所有依赖:

```bash
pip install -r requirements.txt
```

然后运行测试脚本:

```bash
python test_imports.py
```

## 技术栈

- **Web 框架**: FastAPI 0.109.0
- **数据库**: Supabase (PostgreSQL + PostGIS)
- **对象存储**: 阿里云 OSS
- **AI 模型**: 魔搭 ModelScope
- **数据验证**: Pydantic 2.5.3
- **ASGI 服务器**: Uvicorn 0.27.0

## 开发说明

### 项目特点

1. **异步处理**: 使用 `asyncio` 实现高性能并发
2. **空间索引**: PostGIS 支持毫秒级地理查询
3. **情感分析**: AI 模型自动识别文本情感
4. **权重算法**: 智能计算笔记权重 (图文/纯文 + 时间衰减)
5. **异常熔断**: 图片上传失败自动回滚

### 代码规范

- 使用类型注解 (Type Hints)
- 使用 Pydantic 进行数据验证
- 使用单例模式管理资源
- 完整的错误处理和日志记录

## 许可证

MIT License

## 联系方式

如有问题,请提交 Issue 或 Pull Request。
