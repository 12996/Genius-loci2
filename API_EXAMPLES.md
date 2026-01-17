# 气泡笔记 API 调用示例

本文档提供了气泡笔记 API 的完整调用示例,包括 Python、JavaScript 和 curl 三种方式。

---

## 目录

1. [环境准备](#环境准备)
2. [API 端点总览](#api-端点总览)
3. [调用示例](#调用示例)
   - [创建气泡笔记 (纯文本)](#创建气泡笔记-纯文本)
   - [创建气泡笔记 (带图片)](#创建气泡笔记-带图片)
   - [更新气泡笔记](#更新气泡笔记)
   - [获取笔记详情](#获取笔记详情)
   - [获取附近气泡](#获取附近气泡)
   - [获取 Top 气泡](#获取-top-气泡)
   - [删除气泡笔记](#删除气泡笔记)
4. [错误处理](#错误处理)

---

## 环境准备

### 1. 启动服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

服务将在 `http://localhost:8000` 启动

### 2. 访问 API 文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API 端点总览

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/bubbles/note` | 创建/更新笔记 (multipart/form-data) |
| POST | `/api/v1/bubbles/note/json` | 创建/更新笔记 (JSON) |
| GET | `/api/v1/bubbles/note/{note_id}` | 获取笔记详情 |
| GET | `/api/v1/bubbles/nearby` | 获取附近气泡 |
| GET | `/api/v1/bubbles/top` | 获取 Top 气泡 |
| DELETE | `/api/v1/bubbles/note/{note_id}` | 删除笔记 |
| GET | `/api/v1/bubbles/health` | 健康检查 |

---

## 调用示例

### 创建气泡笔记 (纯文本)

#### cURL

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

**响应:**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "note_id": 1,
    "emotion": "开心",
    "note_type": 2
  }
}
```

#### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/note/json"
payload = {
    "user_id": 1,
    "content": "今天天气真好,心情很愉快!",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "status": 1
}

response = requests.post(url, json=payload)
print(response.json())
```

#### JavaScript (fetch)

```javascript
fetch('http://localhost:8000/api/v1/bubbles/note/json', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 1,
    content: '今天天气真好,心情很愉快!',
    gps_longitude: 120.15507,
    gps_latitude: 30.27408,
    status: 1
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 创建气泡笔记 (带图片)

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note" \
  -F "user_id=1" \
  -F "content=分享一张美丽的风景照" \
  -F "gps_longitude=120.15507" \
  -F "gps_latitude=30.27408" \
  -F "status=1" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg"
```

**响应:**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "note_id": 2,
    "emotion": "开心",
    "note_type": 1
  }
}
```

#### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/note"
files = {
    "images": open("image1.jpg", "rb"),
    "images": open("image2.jpg", "rb")
}
data = {
    "user_id": 1,
    "content": "分享一张美丽的风景照",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "status": 1
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

#### JavaScript (FormData)

```javascript
const formData = new FormData();
formData.append('user_id', 1);
formData.append('content', '分享一张美丽的风景照');
formData.append('gps_longitude', 120.15507);
formData.append('gps_latitude', 30.27408);
formData.append('status', 1);
formData.append('images', fileInput.files[0]); // <input type="file" id="fileInput">

fetch('http://localhost:8000/api/v1/bubbles/note', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 更新气泡笔记

#### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note/json" \
  -H "Content-Type: application/json" \
  -d '{
    "note_id": 1,
    "user_id": 1,
    "content": "更新后的内容:今天依然是美好的一天!",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408
  }'
```

**响应:**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "note_id": 1,
    "emotion": "开心",
    "note_type": 2
  }
}
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/note/json"
payload = {
    "note_id": 1,
    "user_id": 1,
    "content": "更新后的内容:今天依然是美好的一天!",
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408
}

response = requests.post(url, json=payload)
print(response.json())
```

---

### 获取笔记详情

#### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/bubbles/note/1"
```

**响应:**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "note_type": 2,
    "content": "今天天气真好,心情很愉快!",
    "image_urls": null,
    "gps_longitude": 120.15507,
    "gps_latitude": 30.27408,
    "status": 1,
    "emotion": "开心",
    "create_time": "2025-01-17T12:00:00",
    "update_time": "2025-01-17T12:00:00",
    "weight_score": 95.50,
    "is_valid": 1
  }
}
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/note/1"
response = requests.get(url)
print(response.json())
```

---

### 获取附近气泡

#### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/bubbles/nearby?longitude=120.15507&latitude=30.27408&radius_km=1.0&limit=20&status=1"
```

**响应:**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "note_type": 2,
      "content": "今天天气真好!",
      "gps_longitude": 120.15507,
      "gps_latitude": 30.27408,
      "status": 1,
      "emotion": "开心",
      "distance_meters": 15.5
    }
  ],
  "total": 1
}
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/nearby"
params = {
    "longitude": 120.15507,
    "latitude": 30.27408,
    "radius_km": 1.0,
    "limit": 20,
    "status": 1
}

response = requests.get(url, params=params)
print(response.json())
```

---

### 获取 Top 气泡

#### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/bubbles/top?limit=20"
```

**响应:**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "note_type": 1,
      "content": "分享美丽的风景",
      "image_urls": "https://example.com/image1.jpg",
      "gps_longitude": 120.15507,
      "gps_latitude": 30.27408,
      "status": 1,
      "emotion": "开心",
      "weight_score": 98.50,
      "create_time": "2025-01-17T12:00:00"
    }
  ],
  "total": 1
}
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/top"
params = {
    "limit": 20
}

response = requests.get(url, params=params)
print(response.json())
```

---

### 删除气泡笔记

#### cURL

```bash
curl -X DELETE "http://localhost:8000/api/v1/bubbles/note/1?user_id=1"
```

**响应:**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": {
    "note_id": 1
  }
}
```

#### Python

```python
import requests

url = "http://localhost:8000/api/v1/bubbles/note/1"
params = {
    "user_id": 1
}

response = requests.delete(url, params=params)
print(response.json())
```

---

## 错误处理

### 400 Bad Request (参数错误)

```json
{
  "code": 400,
  "message": "经度必须在 [-180, 180] 范围内",
  "detail": null
}
```

### 404 Not Found (笔记不存在)

```json
{
  "code": 404,
  "message": "笔记不存在",
  "detail": "note_id=999"
}
```

### 500 Internal Server Error (服务器错误)

```json
{
  "code": 500,
  "message": "服务器内部错误",
  "detail": "详细错误信息"
}
```

---

## 完整 Python 客户端示例

```python
import requests
from typing import List, Optional

class BubbleNoteClient:
    """气泡笔记 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_note(
        self,
        user_id: int,
        content: str,
        longitude: float,
        latitude: float,
        images: Optional[List[str]] = None,
        status: int = 1
    ) -> dict:
        """创建笔记"""
        if images:
            # 带图片的笔记
            files = [("images", open(img, "rb")) for img in images]
            data = {
                "user_id": user_id,
                "content": content,
                "gps_longitude": longitude,
                "gps_latitude": latitude,
                "status": status
            }
            response = requests.post(
                f"{self.base_url}/api/v1/bubbles/note",
                files=files,
                data=data
            )
        else:
            # 纯文本笔记
            payload = {
                "user_id": user_id,
                "content": content,
                "gps_longitude": longitude,
                "gps_latitude": latitude,
                "status": status
            }
            response = requests.post(
                f"{self.base_url}/api/v1/bubbles/note/json",
                json=payload
            )

        return response.json()

    def get_note(self, note_id: int) -> dict:
        """获取笔记详情"""
        response = requests.get(f"{self.base_url}/api/v1/bubbles/note/{note_id}")
        return response.json()

    def get_nearby(
        self,
        longitude: float,
        latitude: float,
        radius_km: float = 1.0,
        limit: int = 20
    ) -> dict:
        """获取附近气泡"""
        params = {
            "longitude": longitude,
            "latitude": latitude,
            "radius_km": radius_km,
            "limit": limit
        }
        response = requests.get(
            f"{self.base_url}/api/v1/bubbles/nearby",
            params=params
        )
        return response.json()

    def get_top(self, limit: int = 20) -> dict:
        """获取 Top 气泡"""
        params = {"limit": limit}
        response = requests.get(
            f"{self.base_url}/api/v1/bubbles/top",
            params=params
        )
        return response.json()

    def delete_note(self, note_id: int, user_id: int) -> dict:
        """删除笔记"""
        params = {"user_id": user_id}
        response = requests.delete(
            f"{self.base_url}/api/v1/bubbles/note/{note_id}",
            params=params
        )
        return response.json()


# 使用示例
if __name__ == "__main__":
    client = BubbleNoteClient()

    # 创建笔记
    result = client.create_note(
        user_id=1,
        content="今天天气真好!",
        longitude=120.15507,
        latitude=30.27408
    )
    print(f"创建结果: {result}")

    # 获取笔记详情
    note_id = result["data"]["note_id"]
    note = client.get_note(note_id)
    print(f"笔记详情: {note}")

    # 获取附近气泡
    nearby = client.get_nearby(120.15507, 30.27408)
    print(f"附近气泡: {nearby}")

    # 获取 Top 气泡
    top = client.get_top(limit=10)
    print(f"Top 气泡: {top}")

    # 删除笔记
    delete_result = client.delete_note(note_id, user_id=1)
    print(f"删除结果: {delete_result}")
```

---

## 注意事项

1. **图片上传**: 使用 `multipart/form-data` 格式上传图片
2. **坐标范围**: 经度 [-180, 180], 纬度 [-90, 90]
3. **情感识别**: 系统会自动分析文本情感 (难过/开心/平静/神秘/愤怒)
4. **权限控制**: 更新和删除操作需要验证用户 ID
5. **软删除**: 删除操作实际上是软删除 (is_valid = 0)

---

## 常见问题

### Q: 如何上传多张图片?

A: 使用 `multipart/form-data` 格式,多次指定 `images` 字段:

```bash
curl -X POST "http://localhost:8000/api/v1/bubbles/note" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg" \
  ...
```

### Q: 如何实现分页?

A: 使用 `limit` 参数控制返回数量:

```bash
curl "http://localhost:8000/api/v1/bubbles/nearby?limit=50"
```

### Q: 如何筛选公开/私有笔记?

A: 使用 `status` 参数 (1-公开/2-私有):

```bash
curl "http://localhost:8000/api/v1/bubbles/nearby?status=1"
```
