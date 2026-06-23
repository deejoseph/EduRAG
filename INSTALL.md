# EduRAG 智能写作助手 - 安装部署指南

> 基于 RAG（检索增强生成）的本地化 K12 教育辅助系统，专注高考语文写作训练。

---

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细安装步骤](#详细安装步骤)
- [数据恢复](#数据恢复)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| 内存 | 8 GB RAM | 16 GB RAM |
| 显卡 | NVIDIA GPU (4GB VRAM) | NVIDIA RTX 3070 (8GB VRAM) |
| 硬盘 | 50 GB 可用空间 | 100 GB SSD |

### 软件要求

- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.10+
- **Node.js**: 18+ 
- **Ollama**: 最新版本
- **Git**: 最新版本

---

## 快速开始

### 方式一：使用一键启动脚本（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd EduRAG

# 2. 双击启动脚本
start.bat  # Windows
# 或
./start.sh  # Linux/Mac
```

首次运行时，脚本会自动：
- 检查并安装依赖
- 下载 Ollama 模型
- 启动后端和前端服务
- 打开浏览器访问 http://localhost:3000

### 方式二：手动安装

详见[详细安装步骤](#详细安装步骤)

---

## 详细安装步骤

### 步骤 1：克隆项目

```bash
git clone <your-repo-url>
cd EduRAG
```

### 步骤 2：安装 Python 环境

#### 使用 Conda（推荐）

```bash
# 创建虚拟环境
conda create -n edurag python=3.10 -y

# 激活环境
conda activate edurag

# 安装依赖
pip install -r requirements.txt
```

#### 使用 venv

```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：安装 Node.js 依赖

```bash
cd frontend
npm install
cd ..
```

### 步骤 4：安装 Ollama

1. **下载 Ollama**
   - 访问 https://ollama.ai
   - 下载并安装对应系统的版本

2. **启动 Ollama**
   ```bash
   ollama serve
   ```

3. **拉取模型**
   
   查看 `config.yaml` 中配置的模型名称，例如：
   ```yaml
   llm:
     model: gemma3:4b
   ```
   
   然后执行：
   ```bash
   ollama pull gemma3:4b
   ```

### 步骤 5：配置环境变量（可选）

复制配置文件模板：
```bash
cp config.yaml config.local.yaml
```

根据需要修改 `config.local.yaml` 中的配置：
- LLM 模型
- Embedding 模型
- 数据库路径
- API 端口等

### 步骤 6：启动服务

#### 方式 A：使用启动脚本

```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

#### 方式 B：手动启动

需要打开 **3 个终端窗口**：

**终端 1：Ollama**（如已运行可跳过）
```bash
ollama serve
```

**终端 2：后端 API**
```bash
cd D:\PixelSmile\EduRAG
python start_backend.py
# 或
python -m api.app
```

后端将在 http://localhost:5000 启动

**终端 3：前端**
```bash
cd D:\PixelSmile\EduRAG\frontend
npm run dev
```

前端将在 http://localhost:3000 启动

### 步骤 7：验证安装

打开浏览器访问 http://localhost:3000，检查：

- ✅ 首页正常显示
- ✅ 知识库统计有数据（文档数量 > 0）
- ✅ 写作训练功能可用
- ✅ 知识检索功能可用
- ✅ 模型加载成功（系统设置中查看）

---

## 数据恢复

如果您之前有备份数据，可以按照以下步骤恢复：

### 方法一：使用前端恢复功能（推荐）

1. **放置备份文件**
   
   将备份文件夹复制到项目的 `backup/` 目录下：
   ```
   EduRAG/
   └── backup/
       └── chroma_db_YYYYMMDD_HHMMSS/  # 您的备份文件夹
   ```

2. **通过前端恢复**
   
   - 访问 http://localhost:3000
   - 进入"系统设置"页面
   - 在"数据备份与导出"部分找到"历史备份"
   - 点击对应备份的"恢复"按钮
   - 确认恢复操作
   - **重启后端服务**以使更改生效

### 方法二：手动恢复

1. **停止后端服务**（Ctrl+C）

2. **备份当前数据**（可选但推荐）
   ```bash
   mv data/chroma_db data/chroma_db_old
   ```

3. **复制备份数据**
   ```bash
   # 假设备份文件夹是 chroma_db_20260624_025757
   cp -r backup/chroma_db_20260624_025757/* data/chroma_db/
   ```

4. **重启后端服务**
   ```bash
   python start_backend.py
   ```

### ⚠️ 重要提示

- **不要**直接把 `backup/` 文件夹放到 `data/` 目录下
- **必须**将备份内容恢复到 `data/chroma_db/` 目录
- 恢复后**必须重启后端服务**才能生效
- 恢复前系统会自动备份当前数据到 `backup/auto_backup_before_restore_XXX`

---

## 常见问题

### Q1: 启动时提示 "ModuleNotFoundError: No module named 'xxx'"

**解决方案**：
```bash
# 确保在正确的虚拟环境中
conda activate edurag  # 或 source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: 前端页面刷新出现 404 错误

**原因**：Vite 开发服务器的 SPA 路由问题

**解决方案**：
- 确保使用最新版本的代码
- 清除浏览器缓存（Ctrl+F5 强制刷新）
- 检查后端是否正常运行

### Q3: Ollama 模型下载失败或超时

**解决方案**：

1. **使用镜像源**（中国用户）
   ```bash
   # 设置环境变量
   export OLLAMA_HOST=https://ollama.ai
   
   # 或使用国内镜像
   export OLLAMA_HOST=https://ollama.cnb.cool
   ```

2. **手动下载模型**
   ```bash
   # 先下载小模型测试
   ollama pull llama2:7b
   
   # 再下载需要的模型
   ollama pull gemma3:4b
   ```

### Q4: ChromaDB 报错 "embedding dimension mismatch"

**原因**：备份数据的 embedding 维度与当前配置不匹配

**解决方案**：
```bash
# 重新生成 embedding（耗时较长）
python scripts/regen_embedding.py
```

### Q5: GPU 加速未生效

**检查步骤**：

1. **验证 CUDA 可用性**
   ```python
   import torch
   print(torch.cuda.is_available())  # 应该输出 True
   print(torch.cuda.get_device_name(0))  # 显示 GPU 名称
   ```

2. **检查 config.yaml**
   ```yaml
   device: cuda  # 确保设置为 cuda
   ```

3. **验证 PyTorch CUDA 版本**
   ```bash
   pip list | grep torch
   # 应该看到类似：torch 2.5.1+cu121
   ```

### Q6: 备份/恢复功能找不到数据

**检查清单**：

- ✅ 备份文件夹在 `backup/` 目录下
- ✅ 备份文件夹包含 `chroma.sqlite3` 文件
- ✅ 恢复后重启了后端服务
- ✅ 前端页面已刷新

---

## 故障排除

### 后端启动失败

1. **检查端口占用**
   ```bash
   # Windows
   netstat -ano | findstr ":5000"
   
   # Linux/Mac
   lsof -i :5000
   ```

2. **杀死占用进程**
   ```bash
   # Windows
   taskkill /F /PID <PID>
   
   # Linux/Mac
   kill -9 <PID>
   ```

3. **查看详细错误日志**
   ```bash
   python start_backend.py
   # 观察控制台输出的错误信息
   ```

### 前端启动失败

1. **清理缓存**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **检查 Node.js 版本**
   ```bash
   node --version  # 应该 >= 18
   ```

3. **查看错误日志**
   ```bash
   npm run dev
   # 观察控制台输出
   ```

### 知识库为空

1. **检查 ChromaDB 路径**
   ```bash
   ls data/chroma_db/
   # 应该有多个文件夹和一个 chroma.sqlite3 文件
   ```

2. **重新导入数据**
   ```bash
   python scripts/import_docs.py
   ```

3. **验证集合存在**
   ```python
   from core.db_manager import EduRAGDatabase
   db = EduRAGDatabase('./data/chroma_db')
   print(db.list_collections())
   ```

---

## 性能优化建议

### 1. 启用 GPU 加速

如果您的电脑有 NVIDIA GPU：

```yaml
# config.yaml
device: cuda
embedding_device: cuda
reranker_device: cuda
```

### 2. 调整批处理大小

根据显存大小调整：

```yaml
# config.yaml
batch_size: 32  # 显存小则减小此值
```

### 3. 使用更快的 Embedding 模型

如果速度较慢，可以考虑：

```yaml
embedding_model: BAAI/bge-small-zh-v1.5  # 更小的模型，速度更快
```

---

## 联系与支持

如遇问题，请：

1. 查看本文档的[常见问题](#常见问题)部分
2. 检查后端和前端控制台的错误日志
3. 提交 Issue 时附上：
   - 操作系统版本
   - Python/Node.js 版本
   - 错误日志截图
   - 复现步骤

---

**祝您使用愉快！** 🎉
