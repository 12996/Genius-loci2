# 前端集成指南 - 地灵对话系统

## 🎯 API 端点总览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/genius-loci/chat` | POST | 流式对话接口 |
| `/api/v1/genius-loci/end-session` | POST | 结束会话接口 ⭐ |
| `/api/v1/genius-loci/session/{session_id}` | GET | 查询会话状态 |
| `/api/v1/genius-loci/health` | GET | 健康检查 |

---

## 💬 核心功能：会话结束机制

### 为什么需要主动结束会话？

**问题：** 用户可能关闭页面或离开，对话未归档

**解决方案：**
1. **用户主动触发**：点击"结束对话"按钮
2. **页面卸载触发**：监听 `beforeunload`/`unload` 事件
3. **超时自动归档**：30分钟无操作自动归档（兜底）

---

## 📱 前端集成示例

### 1. React Hook 示例

```typescript
import { useState, useCallback, useRef, useEffect } from 'react';

interface GeniusLociMessage {
  type: 'metadata' | 'content' | 'end' | 'error';
  session_id?: string;
  content?: string;
  code?: number;
  message?: string;
}

interface UseGeniusLociChatOptions {
  userId: number;
  gpsLongitude: number;
  gpsLatitude: number;
  imageUrl?: string;
  onMessage?: (message: string) => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

export function useGeniusLociChat({
  userId,
  gpsLongitude,
  gpsLatitude,
  imageUrl,
  onMessage,
  onEnd,
  onError
}: UseGeniusLociChatOptions) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{
    role: 'user' | 'assistant';
    content: string;
  }>>([]);

  const abortControllerRef = useRef<AbortController | null>(null);

  // 发送消息
  const sendMessage = useCallback(async (message: string) => {
    if (isLoading) return;

    setIsLoading(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/api/v1/genius-loci/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message,
          gps_longitude: gpsLongitude,
          gps_latitude: gpsLatitude,
          session_id: sessionId,
          image_url: sessionId ? undefined : imageUrl // 只在首次对话时传图片
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No response body');

      let fullResponse = '';

      // 读取 SSE 流
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          const dataStr = line.substring(6);
          if (!dataStr || dataStr.trim() === '[DONE]') continue;

          try {
            const data: GeniusLociMessage = JSON.parse(dataStr);

            switch (data.type) {
              case 'metadata':
                // 保存 session_id
                if (data.session_id) {
                  setSessionId(data.session_id);
                }
                break;

              case 'content':
                // 流式文本内容
                fullResponse += data.content || '';
                onMessage?.(data.content || '');
                break;

              case 'end':
                // 对话结束
                console.log('对话结束');
                onEnd?.();
                break;

              case 'error':
                // 错误信息
                onError?.(data.message || '未知错误');
                break;
            }
          } catch (e) {
            console.error('解析 SSE 数据失败:', e);
          }
        }
      }

      // 保存到历史记录
      setConversationHistory(prev => [
        ...prev,
        { role: 'user', content: message },
        { role: 'assistant', content: fullResponse }
      ]);

    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        onError?.(error.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId, gpsLongitude, gpsLatitude, imageUrl, sessionId, isLoading, onMessage, onEnd, onError]);

  // 结束会话（用户主动触发）
  const endSession = useCallback(async () => {
    if (!sessionId) return;

    try {
      const response = await fetch('http://localhost:8000/api/v1/genius-loci/end-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId
        })
      });

      const result = await response.json();

      if (result.code === 200) {
        console.log('会话已结束:', result.data);
        setSessionId(null);
        setConversationHistory([]);
      } else {
        console.error('结束会话失败:', result.message);
      }
    } catch (error) {
      console.error('结束会话异常:', error);
    }
  }, [sessionId, userId]);

  // 页面卸载时自动结束会话
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (sessionId) {
        // 使用 sendBeacon 确保请求发送（即使页面正在卸载）
        navigator.sendBeacon(
          'http://localhost:8000/api/v1/genius-loci/end-session',
          JSON.stringify({
            session_id: sessionId,
            user_id: userId
          })
        );
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      // 组件卸载时也结束会话
      endSession();
    };
  }, [sessionId, userId, endSession]);

  // 取消当前请求
  const cancelRequest = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  }, []);

  return {
    sessionId,
    isLoading,
    conversationHistory,
    sendMessage,
    endSession,
    cancelRequest
  };
}
```

### 2. React 组件示例

```tsx
import React, { useState } from 'react';
import { useGeniusLociChat } from './useGeniusLociChat';

function GeniusLociChatComponent() {
  const [inputMessage, setInputMessage] = useState('');
  const [displayedResponse, setDisplayedResponse] = useState('');

  const {
    sessionId,
    isLoading,
    sendMessage,
    endSession
  } = useGeniusLociChat({
    userId: 1,
    gpsLongitude: 120.15507,
    gpsLatitude: 30.27408,
    imageUrl: 'https://example.com/cafe.jpg', // 只在首次对话时使用
    onMessage: (chunk) => {
      // 实时显示流式内容
      setDisplayedResponse(prev => prev + chunk);
    },
    onEnd: () => {
      console.log('对话结束');
    },
    onError: (error) => {
      console.error('对话错误:', error);
      alert(`错误: ${error}`);
    }
  });

  const handleSend = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage;
    setInputMessage('');
    setDisplayedResponse(''); // 清空之前的响应

    await sendMessage(message);
  };

  const handleEndSession = async () => {
    await endSession();
    setDisplayedResponse('');
    alert('会话已结束');
  };

  return (
    <div className="chat-container">
      <h1>地灵对话系统</h1>

      {/* 会话信息 */}
      {sessionId && (
        <div className="session-info">
          <p>会话 ID: {sessionId}</p>
          <button onClick={handleEndSession} className="end-button">
            结束对话
          </button>
        </div>
      )}

      {/* 对话内容 */}
      <div className="chat-messages">
        {displayedResponse && (
          <div className="message assistant">
            <strong>地灵:</strong> {displayedResponse}
          </div>
        )}
      </div>

      {/* 输入框 */}
      <div className="chat-input">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="输入消息..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !inputMessage.trim()}>
          {isLoading ? '发送中...' : '发送'}
        </button>
      </div>
    </div>
  );
}

export default GeniusLociChatComponent;
```

### 3. Vue 3 示例

```vue
<template>
  <div class="genius-loci-chat">
    <h1>地灵对话系统</h1>

    <!-- 会话信息 -->
    <div v-if="sessionId" class="session-info">
      <p>会话 ID: {{ sessionId }}</p>
      <button @click="endSession" class="end-button">结束对话</button>
    </div>

    <!-- 对话内容 -->
    <div class="chat-messages">
      <div v-for="(msg, index) in conversationHistory" :key="index"
           :class="['message', msg.role]">
        <strong>{{ msg.role === 'user' ? '用户' : '地灵' }}:</strong>
        {{ msg.content }}
      </div>
    </div>

    <!-- 输入框 -->
    <div class="chat-input">
      <input
        v-model="inputMessage"
        @keyup.enter="sendMessage"
        :disabled="isLoading"
        placeholder="输入消息..."
      />
      <button @click="sendMessage" :disabled="isLoading || !inputMessage">
        {{ isLoading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue';

const sessionId = ref<string | null>(null);
const inputMessage = ref('');
const isLoading = ref(false);
const conversationHistory = ref<Array<{role: string, content: string}>>([]);

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const message = inputMessage.value;
  inputMessage.value = '';
  isLoading.value = true;

  try {
    const response = await fetch('http://localhost:8000/api/v1/genius-loci/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 1,
        message,
        gps_longitude: 120.15507,
        gps_latitude: 30.27408,
        session_id: sessionId.value,
        image_url: sessionId.value ? undefined : 'https://example.com/cafe.jpg'
      })
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split('\n');

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const dataStr = line.substring(6);
        if (!dataStr || dataStr.trim() === '[DONE]') continue;

        const data = JSON.parse(dataStr);

        if (data.type === 'metadata' && data.session_id) {
          sessionId.value = data.session_id;
        } else if (data.type === 'content') {
          fullResponse += data.content || '';
        }
      }
    }

    conversationHistory.value.push(
      { role: 'user', content: message },
      { role: 'assistant', content: fullResponse }
    );

  } catch (error) {
    console.error('发送消息失败:', error);
  } finally {
    isLoading.value = false;
  }
};

// 结束会话
const endSession = async () => {
  if (!sessionId.value) return;

  try {
    const response = await fetch('http://localhost:8000/api/v1/genius-loci/end-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        user_id: 1
      })
    });

    const result = await response.json();
    if (result.code === 200) {
      sessionId.value = null;
      conversationHistory.value = [];
      alert('会话已结束');
    }
  } catch (error) {
    console.error('结束会话失败:', error);
  }
};

// 组件卸载时自动结束会话
onUnmounted(() => {
  if (sessionId.value) {
    navigator.sendBeacon(
      'http://localhost:8000/api/v1/genius-loci/end-session',
      JSON.stringify({
        session_id: sessionId.value,
        user_id: 1
      })
    );
  }
});
</script>

<style scoped>
.genius-loci-chat {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f0f0f0;
  border-radius: 4px;
  margin-bottom: 20px;
}

.chat-messages {
  min-height: 400px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
}

.message.user {
  background: #e3f2fd;
  text-align: right;
}

.message.assistant {
  background: #f5f5f5;
}

.chat-input {
  display: flex;
  gap: 10px;
}

.chat-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.chat-input button {
  padding: 10px 20px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.end-button {
  padding: 5px 15px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

---

## 🔑 关键要点

### 1. 会话生命周期

```
创建会话 → 进行对话 → ... → 结束会话（用户主动/页面卸载/超时）
                    ↓
              更新活跃时间
```

### 2. 三种归档方式

| 方式 | 触发时机 | 优先级 |
|------|----------|--------|
| 用户主动触发 | 点击"结束对话"按钮 | ⭐ 最高 |
| 页面卸载触发 | `beforeunload` 事件 | ⭐⭐ 中等 |
| 超时自动归档 | 30分钟无操作 | ⭐⭐⭐ 兜底 |

### 3. sendBeacon vs fetch

```javascript
// ✅ 推荐：页面卸载时使用 sendBeacon
navigator.sendBeacon(url, data); // 可靠，即使页面正在卸载

// ❌ 不推荐：页面卸载时使用 fetch
fetch(url, { method: 'POST', body: data }); // 可能被取消
```

---

## 🧪 测试

### 测试会话结束

```bash
# 1. 发起对话，获取 session_id
curl -X POST "http://localhost:8000/api/v1/genius-loci/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "message": "你好", "gps_longitude": 120.15507, "gps_latitude": 30.27408}'

# 2. 结束会话
curl -X POST "http://localhost:8000/api/v1/genius-loci/end-session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid-from-step1", "user_id": 1}'

# 3. 查询会话状态（应该返回404）
curl "http://localhost:8000/api/v1/genius-loci/session/uuid-from-step1"
```

---

## 📚 相关文档

- [API 端点文档](../GENIUS_LOCI_GUIDE.md)
- [V2 更新总结](../V2_UPDATE_SUMMARY.md)
- [数据库表结构](../database/genius_loci_record_v2.sql)

---

**最后更新：** 2025-01-17
