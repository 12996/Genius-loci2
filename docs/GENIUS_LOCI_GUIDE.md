# 地灵对话接口使用指南

## 📖 概述

地灵（Genius Loci）对话系统是一个基于多模态感知和地理位置记忆的智能对话服务，具备以下核心能力：

- **视觉感知**：解析图片生成场景描述
- **记忆检索**：基于地理位置检索历史对话记忆
- **流式对话**：实时流式响应，提升用户体验
- **异步归档**：对话结束后自动总结并存储

---

## 🗄️ 数据库配置

### 1. 创建数据表

在 Supabase SQL Editor 中执行以下 SQL：

```bash
# 执行数据库初始化脚本
psql -f docs/database/genius_loci_record.sql
```

或在 Supabase Dashboard 的 SQL Editor 中执行 [genius_loci_record.sql](../database/genius_loci_record.sql) 文件的内容。

### 2. 验证表结构

执行以下查询验证表创建成功：

```sql
SELECT * FROM genius_loci_record LIMIT 1;
```

---

## ⚙️ 环境配置

在 `.env` 文件中添加以下配置：

```bash
# ========================================
# 魔搭模型配置（对话模型）
# ========================================
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
MODEL_API_KEY=your_model_api_key
MODEL_API_URL=https://api-inference.modelscope.cn/v1/chat/completions

# 模型参数
TEMPERATURE=0.7
MAX_TOKENS=2000
TOP_P=0.9

# ========================================
# 视觉模型配置（多模态模型）
# ========================================
VISION_MODEL_NAME=gpt-4o
VISION_API_KEY=your_vision_model_api_key
VISION_API_URL=https://api.openai.com/v1/chat/completions
```

**配置说明：**

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `MODEL_NAME` | 对话模型名称 | `Qwen/Qwen2.5-7B-Instruct` |
| `MODEL_API_KEY` | 对话模型 API Key | 从魔搭平台获取 |
| `VISION_MODEL_NAME` | 视觉模型名称 | `gpt-4o` |
| `VISION_API_KEY` | 视觉模型 API Key | 从 OpenAI 获取 |

---

## 🚀 启动服务

```bash
# 启动 FastAPI 服务
python run.py
```

服务将在 `http://localhost:8000` 启动

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📡 API 接口说明

### 1. 流式对话接口

**端点：** `POST /api/v1/genius-loci/chat`

**请求格式：**

```json
{
  "user_id": 1,
  "message": "你好，今天天气真好！",
  "gps_longitude": 120.15507,
  "gps_latitude": 30.27408,
  "session_id": null,
  "image_url": "https://example.com/image.jpg"
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | int | ✅ | 用户 ID |
| `message` | string | ✅ | 用户消息内容 |
| `gps_longitude` | float | ✅ | 经度 [-180, 180] |
| `gps_latitude` | float | ✅ | 纬度 [-90, 90] |
| `session_id` | string | ❌ | 会话 ID（首次对话时为空） |
| `image_url` | string | ❌ | 图片 URL（首次对话时传入） |

**响应格式（SSE 流）：**

```
data: {"type": "metadata", "session_id": "uuid-string", "code": 200}

data: {"type": "content", "content": "你"}

data: {"type": "content", "content": "好"}

data: {"type": "content", "content": "！"}

data: {"type": "end", "code": 200}
```

**SSE 事件类型：**

| 类型 | 说明 |
|------|------|
| `metadata` | 元数据（包含 session_id） |
| `content` | 文本内容片段 |
| `end` | 流结束标志 |
| `error` | 错误信息 |

---

## 🔄 业务逻辑说明

### 首次对话流程（冷启动）

1. **视觉感知**
   - 调用视觉模型解析图片
   - 生成场景描述（如："一个充满现代感的咖啡厅，午后阳光充足"）

2. **记忆检索**
   - 搜索1km内的历史记忆
   - 获取最近的一条 `ai_result`
   - 如果无记忆则跳过此步骤

3. **上下文注入**
   - 将场景描述 + 历史记忆注入 System Prompt
   - 生成符合现场环境和记忆传承感的开场白

4. **场景气泡创建**
   - 在 `bubble_note` 表创建记录（`note_type=3`）

### 多轮对话流程

1. **会话状态维护**
   - 内存中维护会话窗口记忆（最近10轮对话）
   - 不再重复视觉解析和记忆检索

2. **流式响应**
   - 实时推送文本流至前端
   - 提升用户体验

3. **异步归档**
   - 对话结束后总结对话内容
   - 保存到 `genius_loci_record` 表
   - 只存储当前用户的 Query 和 Answer

---

## 🧪 测试示例

### 使用 cURL 测试

```bash
curl -X POST "http://localhost:8000/api/v1/genius-loci/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "message": "你好，今天天气真好！",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "session_id": null,
    "image_url": "https://example.com/cafe.jpg"
  }'
```

### 使用 Python 测试

```python
import requests
import json

url = "http://localhost:8000/api/v1/genius-loci/chat"
data = {
    "user_id": 1,
    "message": "你好，今天天气真好！",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "session_id": None,
    "image_url": "https://example.com/cafe.jpg"
}

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(data)
```

### 使用 JavaScript 测试

```javascript
const response = await fetch('http://localhost:8000/api/v1/genius-loci/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 1,
    message: '你好，今天天气真好！',
    gps_longitude: 120.15507,
    gps_latitude: 30.27408,
    session_id: null,
    image_url: 'https://example.com/cafe.jpg'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));
      console.log(data);
    }
  }
}
```

---

## 📊 数据库查询示例

### 查询用户的地灵记忆

```sql
SELECT
    id,
    user_id,
    session_id,
    ai_result,
    gps_longitude,
    gps_latitude,
    create_time
FROM genius_loci_record
WHERE user_id = 1
ORDER BY create_time DESC
LIMIT 10;
```

### 查询某个位置附近的记忆

```sql
SELECT
    id,
    user_id,
    ai_result,
    create_time,
    ST_Distance(
        location,
        ST_SetSRID(ST_MakePoint(120.15507, 30.27408), 4326)::GEOGRAPHY
    ) as distance_meters
FROM genius_loci_record
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(120.15507, 30.27408), 4326)::GEOGRAPHY,
    1000  -- 1km
)
ORDER BY distance_meters ASC;
```

---

## 🛠️ 项目结构

```
app/
├── api/v1/
│   └── genius_loci.py          # 地灵对话路由
├── core/
│   ├── config.py               # 配置管理
│   └── database.py             # 数据库操作
├── models/
│   └── schemas.py              # 数据模型
└── services/
    ├── vision_service.py       # 视觉感知服务
    ├── chat_service.py         # 对话流式服务
    └── genius_loci_service.py  # 地灵核心服务
```

---

## ⚠️ 注意事项

### 1. 数据纯净度原则

- **严禁**将检索到的"他人历史记忆"写入当前用户的 `genius_loci_record`
- **只存储**当前用户的 Query 和 Answer
- 避免记忆污染（Feedback Loop）

### 2. API Key 安全

- 不要将 `.env` 文件提交到 Git
- 定期更换 API Key
- 使用环境变量管理密钥

### 3. 性能优化

- 会话历史限制在最近10轮对话
- 异步归档不阻塞流式响应
- 视觉分析仅在首次对话时执行

### 4. 错误处理

- 视觉分析失败时跳过视觉信息
- 记忆检索失败时使用空上下文
- 对话异常时返回错误信息但不中断服务

---

## 📚 相关文档

- [数据库表结构](../database/genius_loci_record.sql)
- [API 文档](http://localhost:8000/docs)
- [气泡笔记接口](./BUBBLE_API.md)

---

## 💡 常见问题

### Q: 如何更换视觉模型？

A: 修改 `.env` 文件中的 `VISION_MODEL_NAME` 和 `VISION_API_KEY`，支持 GPT-4o、Gemini Vision 等多模态模型。

### Q: 会话状态会持久化吗？

A: 不会。会话状态仅存储在内存中，服务重启后会丢失。但对话内容已异步归档到数据库。

### Q: 如何禁用视觉分析？

A: 不传 `image_url` 参数即可跳过视觉分析。

### Q: 记忆检索半径可以调整吗？

A: 可以，修改 `genius_loci_service.py` 中的 `radius_km` 参数，默认为 1km。

---

**作者：** Claude Sonnet 4.5
**创建时间：** 2025-01-17
**版本：** 1.0.0
