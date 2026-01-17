# 渐进式归档配置说明

## 📊 配置参数

### 位置
文件：`app/services/genius_loci_service.py`

### 参数说明

```python
# ========================================
# 配置常量
# ========================================

SESSION_TIMEOUT = 30 * 60  # 会话超时时间（秒），默认30分钟
AUTO_ARCHIVE_TURNS = 100  # ⭐ 每100轮对话后自动归档并开启新会话
AI_PROCESS_TYPE_CHAT_SUMMARY = 5  # AI处理类型：5-对话总结
```

---

## 🎯 如何调整归档轮数

### 方式 1：直接修改代码（推荐）

编辑 `app/services/genius_loci_service.py`：

```python
# 根据你的需求调整
AUTO_ARCHIVE_TURNS = 50   # 每50轮对话归档（较频繁）
AUTO_ARCHIVE_TURNS = 100  # 每100轮对话归档（推荐）⭐
AUTO_ARCHIVE_TURNS = 200  # 每200轮对话归档（较少）
```

### 方式 2：通过环境变量配置

**步骤 1：** 修改 `app/core/config.py`

```python
# 在 Settings 类中添加
AUTO_ARCHIVE_TURNS: int = int(os.getenv("AUTO_ARCHIVE_TURNS", "100"))
```

**步骤 2：** 修改 `.env` 文件

```bash
AUTO_ARCHIVE_TURNS=100
```

**步骤 3：** 修改 `genius_loci_service.py`

```python
from app.core.config import settings

AUTO_ARCHIVE_TURNS = settings.AUTO_ARCHIVE_TURNS
```

---

## 📈 不同值的对比

| 轮数 | 内存占用 | AI调用成本 | 数据完整性 | 推荐场景 |
|------|----------|------------|------------|----------|
| 50轮 | 低 | 较高 | 很高 | 高频对话应用 |
| 100轮 | 中等 | 中等 | 高 | **通用场景** ⭐ |
| 200轮 | 较高 | 较低 | 中等 | 低频对话应用 |
| ∞（不归档） | 高 | 最低 | 低（崩溃丢失） | 不推荐 |

---

## 🔄 归档流程示意

### 100轮归档流程

```
第1轮对话 → 第2轮 → ... → 第99轮 → 第100轮
                                        ↓
                                   [检查: 100 % 100 == 0]
                                        ↓
                                   🔄 触发自动归档
                                        ↓
                              ┌─────────────────┐
                              │ 1. 归档当前会话  │
                              │ 2. 总结对话内容  │
                              │ 3. 保存到数据库  │
                              └─────────────────┘
                                        ↓
                              ┌─────────────────┐
                              │ 4. 创建新会话   │
                              │ 5. 继承最近10轮  │
                              │ 6. 继续对话     │
                              └─────────────────┘
                                        ↓
第101轮对话 → 第102轮 → ... → 第200轮
                                        ↓
                                   [再次归档]
                                        ↓
                                      ...循环
```

---

## 💾 数据存储示例

### genius_loci_record 表

```sql
-- 第1个会话（1-100轮）
SELECT * FROM genius_loci_record WHERE bubble_id = 123;
-- 结果: 1条记录，ai_result = {"summary": "...", "turns": 100}

-- 第2个会话（101-200轮）
SELECT * FROM genius_loci_record WHERE bubble_id = 123;
-- 结果: 2条记录，第2条的 ai_result = {"summary": "...", "turns": 100}

-- 查询某个气泡的所有对话历史
SELECT
    id,
    ai_result,
    process_time
FROM genius_loci_record
WHERE bubble_id = 123
ORDER BY process_time ASC;
```

---

## 🧪 测试验证

### 方法 1：查看日志

启动服务后观察日志：

```bash
python run.py
```

日志输出示例：

```
INFO: 对话完成: session_id=abc123..., turns=1/100, response_length=45
INFO: 对话完成: session_id=abc123..., turns=2/100, response_length=52
...
INFO: 对话完成: session_id=abc123..., turns=99/100, response_length=38
INFO: 对话完成: session_id=abc123..., turns=100/100, response_length=41
INFO: 🔄 触发渐进式归档: session_id=abc123..., turns=100
INFO: 开始归档对话，session_id=abc123..., bubble_id=123, 对话轮数=50
INFO: ✓ 对话归档成功: record_id=456, bubble_id=123
INFO: ✓ 渐进式归档完成，已切换到新会话: old=abc123..., new=def456...
INFO: 对话完成: session_id=def456..., turns=101/100, response_length=39
```

### 方法 2：查询会话状态

```bash
curl "http://localhost:8000/api/v1/genius-loci/session/{session_id}"
```

响应示例：

```json
{
  "code": 200,
  "message": "会话存在",
  "data": {
    "session_id": "abc-123-def",
    "user_id": 1,
    "bubble_id": 123,
    "conversation_turns": 50,
    "is_first": false,
    "location": {"longitude": 120.15507, "latitude": 30.27408},
    "auto_archive_threshold": 100
  }
}
```

---

## ⚙️ 性能调优建议

### 根据实际使用情况调整

#### 高频对话场景（如客服机器人）
```python
AUTO_ARCHIVE_TURNS = 50  # 减少内存占用
```

#### 低频对话场景（如个人助理）
```python
AUTO_ARCHIVE_TURNS = 200  # 减少 AI 调用成本
```

#### 测试环境
```python
AUTO_ARCHIVE_TURNS = 5  # 快速验证归档逻辑
```

### 监控指标

1. **活跃会话数**：`len(session_manager.sessions)`
2. **平均对话轮数**：观察用户平均对话多少轮
3. **AI 总结调用次数**：监控 API 成本
4. **内存占用**：观察服务内存使用情况

---

## ❓ 常见问题

### Q1: 为什么不是每轮对话都归档？

**A:** 频繁调用 AI 总结会：
- 增加 API 成本（每次总结都需要调用 LLM）
- 增加数据库写入压力
- 影响用户体验（每次都要等待总结）

### Q2: 归档时用户会感知到吗？

**A:** 不会。归档是异步执行的：
- 用户立即收到响应
- 归档在后台进行
- 新会话继承最近10轮对话，保持上下文连续

### Q3: 如果服务重启会怎样？

**A:** 未归档的对话会丢失。这是内存存储的固有风险。
- **解决方法1**：用户主动结束会话（已实现）
- **解决方法2**：定期持久化会话状态到 Redis（可选）
- **解决方法3**：降低归档轮数阈值

### Q4: 可以禁用渐进式归档吗？

**A:** 可以，设置一个很大的值：

```python
AUTO_ARCHIVE_TURNS = 999999  # 实际上不会触发
```

但这样会：
- 内存占用持续增长
- 依赖超时机制（30分钟）
- 服务重启丢失更多数据

---

## ✅ 总结

### 推荐配置

```python
AUTO_ARCHIVE_TURNS = 100  # 平衡内存、成本和用户体验
```

### 三层保障

1. **用户主动结束**（最优先）
2. **渐进式归档**（每100轮，自动）
3. **超时归档**（30分钟，兜底）

---

**最后更新：** 2025-01-17
**默认值：** 100轮对话
