# 常见问题排查

## 问题 1: Python 无法运行

### 症状
- 运行 `python` 命令无响应
- 显示 "Exit code 49" 或其他错误

### 解决方案

#### 方法 1: 使用完整的 Python 路径

```bash
# 查找 Python 安装路径
where python

# 使用完整路径运行
C:\Python311\python.exe main.py
```

#### 方法 2: 使用 py 启动器 (Windows)

```bash
py -3 main.py
```

#### 方法 3: 重新安装 Python

1. 从 https://www.python.org/downloads/ 下载 Python 3.8+
2. 安装时勾选 "Add Python to PATH"
3. 重启命令行窗口

---

## 问题 2: 模块导入失败

### 症状
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'supabase'
```

### 解决方案

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或单独安装
pip install fastapi uvicorn supabase oss2 python-dotenv
```

---

## 问题 3: .env 文件配置错误

### 症状
```
ValueError: SUPABASE_URL 和 SUPABASE_KEY 必须在 .env 文件中配置
```

### 解决方案

1. 复制模板:
```bash
copy .env.example .env
```

2. 编辑 `.env` 文件, 填写真实配置:
```bash
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID=your-access-key
OSS_ACCESS_KEY_SECRET=your-secret-key
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your-bucket
OSS_BUCKET_DOMAIN=https://your-bucket.oss-cn-hangzhou.aliyuncs.com
```

---

## 问题 4: Supabase 连接失败

### 症状
```
supabase.lib.client.ClientError: Invalid API key
```

### 解决方案

1. 检查 Supabase URL 是否正确 (应该包含 `https://`)
2. 检查 API Key 是否正确
3. 确认 Supabase 项目已启动
4. 检查网络连接

---

## 问题 5: OSS 上传失败

### 症状
```
oss2.exceptions.OssError: Access denied
```

### 解决方案

1. 检查 OSS Access Key 是否正确
2. 检查 Bucket 名称是否存在
3. 确认 Endpoint 区域是否正确
4. 检查 RAM 权限是否足够

---

## 问题 6: 情感分析失败

### 症状
```
API调用出错: ConnectionError
```

### 解决方案

1. 检查魔搭 API Key 是否正确
2. 检查网络连接 (可能需要代理)
3. 检查 API URL 是否正确

临时解决方案 (使用默认情感):

```python
# 在 service.py 中, 情感分析失败会自动使用 "未知" 或 "平静"
# 不会影响笔记创建
```

---

## 问题 7: 端口被占用

### 症状
```
OSError: [Errno 48] Address already in use
```

### 解决方案

#### 方法 1: 使用其他端口
```bash
uvicorn main:app --port 8001
```

#### 方法 2: 关闭占用端口的进程
```bash
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000

# 结束进程 (PID 替换为实际的进程 ID)
taskkill /PID 12345 /F
```

---

## 问题 8: 语法错误

### 症状
```
SyntaxError: invalid character '（' (U+FF08)
```

### 解决方案

这通常是由于中文全角标点符号导致的。已修复。

如果仍然出现, 请检查:

1. 确保使用英文半角括号 `()` 而不是中文全角括号 `（）`
2. 确保使用英文冒号 `:` 而不是中文冒号 `:`
3. 确保使用英文逗号 `,` 而不是中文逗号 `,`

---

## 手动测试步骤

### 1. 测试 Python 环境

```bash
python --version
# 应显示: Python 3.8.x 或更高版本
```

### 2. 测试依赖安装

```bash
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import supabase; print('Supabase: OK')"
python -c "import oss2; print('OSS2: OK')"
```

### 3. 测试模块导入

```bash
python test_imports.py
```

### 4. 测试情感分析

```bash
python -c "from emotion_analyzer import analyze_emotion; print(analyze_emotion('测试'))"
```

### 5. 启动服务

```bash
# 方法 1: 直接运行
python main.py

# 方法 2: 使用 uvicorn
uvicorn main:app --reload

# 方法 3: 使用启动脚本 (Windows)
start.bat
```

---

## 开发环境建议

### 推荐的 Python 环境

1. **官方 Python**: https://www.python.org/downloads/
   - 版本: 3.8 或更高
   - 安装时勾选 "Add Python to PATH"

2. **虚拟环境** (推荐):
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

3. **PyCharm / VS Code**:
   - 安装 Python 插件
   - 选择正确的 Python 解释器
   - 使用内置终端运行命令

---

## 获取帮助

如果以上方法都无法解决问题:

1. 查看完整的错误日志
2. 检查 Python 和依赖版本
3. 确认所有配置文件正确
4. 尝试在虚拟环境中运行

```bash
# 创建干净的虚拟环境
python -m venv test_env
test_env\Scripts\activate
pip install -r requirements.txt
python test_imports.py
```
