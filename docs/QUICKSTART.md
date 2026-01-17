# 地灵对话系统 - 快速启动指南

## 🚀 5分钟快速启动

### 步骤 1: 配置环境变量 (2分钟)

编辑 `.env` 文件，添加以下配置：

```bash
# ========================================
# 视觉模型配置（必填）
# ========================================
VISION_MODEL_NAME=gpt-4o
VISION_API_KEY=sk-your-openai-api-key
VISION_API_URL=https://api.openai.com/v1/chat/completions

# ========================================
# 对话模型配置（已有，无需修改）
# ========================================
MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
MODEL_API_KEY=ms-37087bb1-5efd-482e-87f1-3ab6a6b0db37
MODEL_API_URL=https://api-inference.modelscope.cn/v1/chat/completions
```

**获取 API Key：**
- OpenAI: https://platform.openai.com/api-keys
- 或使用其他兼容 GPT-4o 的服务

### 步骤 2: 初始化数据库 (1分钟)

在 Supabase Dashboard 执行：

1. 登录 Supabase Dashboard
2. 点击左侧 "SQL Editor"
3. 点击 "New Query"
4. 复制并执行 [docs/database/genius_loci_record.sql](database/genius_loci_record.sql) 的内容

验证表创建成功：
```sql
SELECT COUNT(*) FROM genius_loci_record;
-- 应返回: 0
```

### 步骤 3: 启动服务 (1分钟)

```bash
# 启动 FastAPI 服务
python run.py
```

看到以下输出说明启动成功：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 4: 测试接口 (1分钟)

**方式1: 使用测试脚本**

```bash
python tests/test_genius_loci.py
```

**方式2: 使用 curl**

```bash
curl -X POST "http://localhost:8000/api/v1/genius-loci/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "message": "你好，这里是什么地方？",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "session_id": null,
    "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085"
  }'
```

**方式3: 访问 Swagger UI**

浏览器打开：http://localhost:8000/docs

找到 `/api/v1/genius-loci/chat` 接口，点击 "Try it out"

---

## ✅ 验证清单

- [ ] `.env` 文件包含 `VISION_API_KEY`
- [ ] Supabase 中创建了 `genius_loci_record` 表
- [ ] 服务启动成功（无错误日志）
- [ ] 健康检查通过：http://localhost:8000/api/v1/genius-loci/health
- [ ] 能够成功发起对话并收到流式响应

---

## 📖 下一步

- 阅读完整文档：[GENIUS_LOCI_GUIDE.md](GENIUS_LOCI_GUIDE.md)
- 查看实现总结：[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- 查看项目主文档：[README.md](../README.md)

---

## ❓ 常见问题

### Q1: 视觉分析失败怎么办？

**A:** 检查以下几点：
1. `VISION_API_KEY` 是否正确
2. `VISION_API_URL` 是否可访问
3. 图片 URL 是否有效（必须是公网可访问的 URL）

如果视觉分析失败，系统会自动跳过视觉信息，不影响对话功能。

### Q2: 如何获取图片 URL？

**A:** 有以下几种方式：
1. 使用阿里云 OSS 上传图片，获取 OSS URL
2. 使用 Unsplash 等免费图床测试
3. 使用在线图片托管服务

**注意：** 图片 URL 必须是公网可访问的，不能使用本地文件路径。

### Q3: 对话没有记忆怎么办？

**A:** 确保：
1. 首次对话时传入了 `gps_longitude` 和 `gps_latitude`
2. Supabase 中的 `genius_loci_record` 表有数据
3. 对话结束后等待几秒，异步归档需要时间

查看记忆：
```sql
SELECT * FROM genius_loci_record ORDER BY create_time DESC;
```

### Q4: 如何调整记忆检索半径？

**A:** 修改 [app/services/genius_loci_service.py](../../app/services/genius_loci_service.py) 第 95 行：

```python
memory_result = await get_nearby_genius_loci_memory(
    gps_longitude=gps_longitude,
    gps_latitude=gps_latitude,
    radius_km=1.0,  # 修改这里，默认 1km
    exclude_user_id=user_id
)
```

### Q5: 服务重启后会话会丢失吗？

**A:** 会话存储在内存中，服务重启后会丢失。但：
1. 对话内容已异步归档到数据库
2. 用户可以基于历史记忆继续对话
3. 不会影响数据完整性

---

## 🎯 测试场景

### 场景 1: 首次对话（带图片）

```json
{
  "user_id": 1,
  "message": "你好，这里是什么地方？",
  "gps_longitude": 120.15507,
  "gps_latitude": 30.27408,
  "session_id": null,
  "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085"
}
```

**预期结果：**
- 视觉分析：解析咖啡厅场景
- 记忆检索：查找附近历史记忆
- 生成开场白：结合场景和记忆

### 场景 2: 多轮对话

```json
{
  "user_id": 1,
  "message": "今天天气真好，有什么推荐的地方吗？",
  "gps_longitude": 120.15507,
  "gps_latitude": 30.27408,
  "session_id": "第一次对话返回的session_id",
  "image_url": null
}
```

**预期结果：**
- 不再进行视觉分析
- 不再检索历史记忆
- 基于会话历史继续对话

### 场景 3: 无图片对话

```json
{
  "user_id": 2,
  "message": "你好",
  "gps_longitude": 120.15507,
  "gps_latitude": 30.27408,
  "session_id": null,
  "image_url": null
}
```

**预期结果：**
- 跳过视觉分析
- 只进行记忆检索
- 生成标准开场白

---

## 📞 技术支持

遇到问题？
1. 查看日志：控制台输出的详细日志
2. 查看文档：[GENIUS_LOCI_GUIDE.md](GENIUS_LOCI_GUIDE.md)
3. 检查配置：确认 `.env` 文件配置正确
4. 检查数据库：确认表结构正确创建

---

**最后更新：** 2025-01-17
