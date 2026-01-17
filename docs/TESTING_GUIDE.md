# 归档功能测试指南

## 🚀 快速开始

### 步骤 1: 启动服务

```bash
python run.py
```

### 步骤 2: 运行测试脚本

```bash
python tests/test_archive.py
```

---

## 📋 测试清单

### ✅ 测试 1: 用户主动结束会话

**目的：** 验证用户可以手动结束对话并归档

**步骤：**
1. 发起对话（带图片）
2. 进行3-5轮对话
3. 调用结束会话接口
4. 验证会话已清除
5. 查询数据库验证归档记录

**预期结果：**
- ✅ 会话成功创建
- ✅ 对话正常进行
- ✅ 归档成功写入数据库
- ✅ 会话从内存清除

**验证命令：**
```sql
SELECT * FROM genius_loci_record WHERE user_id = 999 ORDER BY process_time DESC LIMIT 1;
```

---

### ✅ 测试 2: 查询会话状态

**目的：** 验证可以实时查询会话信息

**API：** `GET /api/v1/genius-loci/session/{session_id}`

**验证点：**
- ✅ 返回当前对话轮数
- ✅ 返回 bubble_id
- ✅ 返回自动归档阈值（100）
- ✅ 会话不存在时返回404

**示例：**
```bash
curl "http://localhost:8000/api/v1/genius-loci/session/{session_id}"
```

---

### ✅ 测试 3: 渐进式归档（快速验证）

**目的：** 验证每N轮对话后自动归档

**快速验证方法：**

1. **修改配置**（临时，用于测试）
   ```python
   # 编辑 app/services/genius_loci_service.py
   AUTO_ARCHIVE_TURNS = 3  # 改为3轮（测试用）
   ```

2. **重启服务**
   ```bash
   python run.py
   ```

3. **进行对话测试**
   ```bash
   python tests/test_archive.py
   ```

4. **观察日志**
   ```
   INFO: 对话完成: session_id=abc..., turns=1/3, response_length=45
   INFO: 对话完成: session_id=abc..., turns=2/3, response_length=52
   INFO: 对话完成: session_id=abc..., turns=3/3, response_length=41
   INFO: 🔄 触发渐进式归档: session_id=abc..., turns=3
   INFO: 开始归档对话...
   INFO: ✓ 对话归档成功: record_id=1, bubble_id=123
   INFO: ✓ 渐进式归档完成，已切换到新会话
   INFO: 对话完成: session_id=def..., turns=4/3, response_length=38
   ```

5. **恢复配置**
   ```python
   AUTO_ARCHIVE_TURNS = 100  # 改回100轮
   ```

---

### ✅ 测试 4: 超时归档（快速验证）

**目的：** 验证30分钟无操作自动归档

**快速验证方法：**

1. **修改配置**（临时，用于测试）
   ```python
   # 编辑 app/services/genius_loci_service.py
   SESSION_TIMEOUT = 30  # 改为30秒（测试用）
   ```

2. **发起对话但不结束**
   ```python
   # 发起对话后，不要调用 end_session
   session_id = create_session(...)
   # 等待超时...
   ```

3. **等待30秒**
   ```bash
   sleep 30
   ```

4. **查询会话状态（应该返回404）**
   ```bash
   curl "http://localhost:8000/api/v1/genius-loci/session/{session_id}"
   # 应该返回: {"code": 404, "message": "会话不存在"}
   ```

5. **查看日志**
   ```
   INFO: 会话超时，准备归档: session_id=abc...
   INFO: 开始归档对话...
   INFO: ✓ 对话归档成功
   INFO: 清除会话: session_id=abc...
   ```

6. **恢复配置**
   ```python
   SESSION_TIMEOUT = 30 * 60  # 改回30分钟
   ```

---

## 🗄️ 数据库验证

### 查询归档记录

```sql
-- 查询所有归档记录
SELECT
    id,
    bubble_id,
    user_id,
    ai_process_type,
    ai_result,
    process_time,
    is_effective
FROM genius_loci_record
WHERE user_id = 999  -- 使用测试用户ID
ORDER BY process_time DESC;
```

### 验证 JSON 格式

```sql
-- 解析 JSON 字段
SELECT
    id,
    bubble_id,
    JSON_EXTRACT(ai_result, '$.summary') as summary,
    JSON_EXTRACT(ai_result, '$.turns') as turns,
    JSON_EXTRACT(ai_result, '$.session_id') as session_id,
    process_time
FROM genius_loci_record
WHERE user_id = 999
AND ai_process_type = 5
ORDER BY process_time DESC;
```

### 验证 bubble_id 关联

```sql
-- 关联查询
SELECT
    r.id as record_id,
    r.bubble_id,
    r.user_id,
    JSON_EXTRACT(r.ai_result, '$.summary') as summary,
    b.content as bubble_content,
    b.note_type,
    b.gps_longitude,
    b.gps_latitude
FROM genius_loci_record r
LEFT JOIN bubble_note b ON r.bubble_id = b.id
WHERE r.user_id = 999
AND r.ai_process_type = 5
ORDER BY r.process_time DESC;
```

---

## 📊 完整测试流程

### 方式 1: 自动化测试

```bash
# 运行完整测试脚本
python tests/test_archive.py
```

### 方式 2: 手动测试（使用 curl）

#### 2.1 发起对话

```bash
curl -X POST "http://localhost:8000/api/v1/genius-loci/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 999,
    "message": "你好",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085"
  }'
```

**从响应中获取 `session_id`**

#### 2.2 继续对话

```bash
curl -X POST "http://localhost:8000/api/v1/genius-loci/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 999,
    "message": "这里是什么地方？",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "session_id": "从第一步获取的session_id"
  }'
```

#### 2.3 查询会话状态

```bash
curl "http://localhost:8000/api/v1/genius-loci/session/{session_id}"
```

**预期输出：**
```json
{
  "code": 200,
  "message": "会话存在",
  "data": {
    "session_id": "abc-123-def",
    "user_id": 999,
    "bubble_id": 123,
    "conversation_turns": 2,
    "is_first": false,
    "location": {"longitude": 120.15507, "latitude": 30.27408},
    "auto_archive_threshold": 100
  }
}
```

#### 2.4 结束会话

```bash
curl -X POST "http://localhost:8000/api/v1/genius-loci/end-session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "你的session_id",
    "user_id": 999
  }'
```

**预期输出：**
```json
{
  "code": 200,
  "message": "会话已成功结束",
  "data": {
    "session_id": "abc-123-def",
    "conversation_turns": 2,
    "archived": true
  }
}
```

#### 2.5 再次查询会话（应该返回404）

```bash
curl "http://localhost:8000/api/v1/genius-loci/session/{session_id}"
```

**预期输出：**
```json
{
  "code": 404,
  "message": "会话不存在",
  "data": null
}
```

#### 2.6 查询数据库验证

```sql
SELECT * FROM genius_loci_record WHERE user_id = 999 ORDER BY process_time DESC LIMIT 1;
```

---

## ✅ 验证清单

### 功能验证

- [ ] 用户主动结束会话成功
- [ ] 会话状态查询正常
- [ ] 对话轮数计数正确
- [ ] bubble_id 关联正确
- [ ] 归档记录写入数据库
- [ ] ai_result JSON 格式正确
- [ ] 会话清除后查询返回404
- [ ] 渐进式归档逻辑正常
- [ ] 超时归档逻辑正常

### 数据验证

- [ ] `genius_loci_record` 表有新记录
- [ ] `bubble_id` 字段不为 NULL
- [ ] `ai_process_type` = 5（对话总结）
- [ ] `ai_result` 是有效的 JSON
- [ ] `ai_result.summary` 字段存在
- [ ] `ai_result.turns` 字段正确
- [ ] `ai_result.session_id` 字段正确
- [ ] `process_time` 时间戳正确
- [ ] `is_effective` = 1

### 日志验证

- [ ] 创建会话日志
- [ ] 视觉分析日志
- [ ] 记忆检索日志
- [ ] 归档开始日志
- [ ] 归档成功日志
- [ ] 会话清除日志
- [ ] 渐进式归档日志（如果触发）
- [ ] 超时归档日志（如果触发）

---

## 🔧 快速测试技巧

### 技巧 1: 使用专用测试用户

```python
user_id = 999  # 专用测试ID，便于清理
```

### 技巧 2: 临时降低阈值

```python
# 测试时临时修改
AUTO_ARCHIVE_TURNS = 3  # 快速触发归档
SESSION_TIMEOUT = 30     # 快速触发超时

# 测试完成后恢复
AUTO_ARCHIVE_TURNS = 100
SESSION_TIMEOUT = 30 * 60
```

### 技巧 3: 查看实时日志

```bash
# 启动服务并查看详细日志
python run.py 2>&1 | grep -E "归档|会话|archive|session"
```

### 技巧 4: 清理测试数据

```sql
-- 清理测试用户的所有记录
DELETE FROM genius_loci_record WHERE user_id = 999;

-- 清理测试用户的所有气泡
DELETE FROM bubble_note WHERE user_id = 999;
```

---

## 📈 性能测试

### 测试并发会话

```python
import asyncio

async def test_concurrent_sessions():
    """测试多个并发会话"""
    tasks = []
    for i in range(10):
        task = asyncio.create_task(test_single_session(user_id=1000+i))
        tasks.append(task)

    await asyncio.gather(*tasks)
    print("✓ 并发测试完成")
```

### 测试长对话

```python
async def test_long_conversation():
    """测试长对话（100+轮）"""
    session_id = create_session(...)

    for i in range(150):
        await send_message(
            session_id=session_id,
            message=f"这是第{i+1}轮对话"
        )

        if (i+1) % 50 == 0:
            print(f"已完成 {i+1} 轮对话")

    print("✓ 长对话测试完成，验证渐进式归档")
```

---

## ❓ 常见问题

### Q1: 数据库没有记录？

**A:** 检查以下几点：
1. 是否有 `bubble_id`？（没有 bubble_id 无法归档）
2. 是否有对话记录？（空对话不归档）
3. 是否主动结束会话？（不结束只触发超时或渐进式归档）

### Q2: 归档的 JSON 是空的？

**A:** 检查对话总结服务：
1. `MODEL_API_KEY` 是否配置正确
2. 模型 API 是否可访问
3. 查看日志中的错误信息

### Q3: 会话没有被清除？

**A:** 检查：
1. 是否成功调用结束接口
2. 是否有异常抛出
3. 查看 server 日志

---

## 📝 测试报告模板

```markdown
# 归档功能测试报告

## 测试时间
2025-01-17

## 测试环境
- Python 版本: 3.x
- 服务端口: 8000
- 数据库: Supabase

## 测试结果

### 功能测试
- [x] 用户主动结束: 通过
- [ ] 渐进式归档: 待测试
- [ ] 超时归档: 待测试

### 数据验证
- [x] 归档记录写入: 通过
- [x] bubble_id 关联: 通过
- [x] JSON 格式: 通过

### 问题记录
1. 无

## 建议
1. 建议降低 AUTO_ARCHIVE_TURNS 到 50 轮
2. 建议添加归档失败重试机制
```

---

**最后更新：** 2025-01-17
