# EduRAG 安装指南

> 基于 RAG（检索增强生成）的本地化 K12 教育辅助系统，专注高考语文写作训练。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细安装步骤](#详细安装步骤)
- [知识库配置](#知识库配置)
- [常见问题](#常见问题)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| 内存 | 8 GB | 16 GB |
| 硬盘空间 | 20 GB | 50 GB SSD |
| GPU | 可选（CPU模式较慢） | NVIDIA RTX 3060 (8GB+) |

### 软件要求

- **操作系统**: Windows 10/11, macOS 10.15+, Linux
- **Python**: 3.10 - 3.13
- **Node.js**: 18.x 或更高版本
- **Ollama**: 最新版本（用于 LLM 推理）

---

## 快速开始

### 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/EduRAG.git
cd EduRAG

# 2. 双击运行
start.bat
```

`start.bat` 会自动完成以下操作：
1. 检查并激活 Python 虚拟环境
2. 安装后端依赖
3. 安装前端依赖
4. 启动 Ollama 服务
5. 启动 Flask 后端（端口 5000）
6. 启动 React 前端（端口 3000）
7. 自动打开浏览器访问 http://localhost:3000

---

## 详细安装步骤

### 步骤 1：克隆项目

```bash
git clone https://github.com/your-username/EduRAG.git
cd EduRAG
```

### 步骤 2：安装 Python 环境

#### 方式 A：使用 conda（推荐）

```bash
# 创建 conda 环境
conda create -n pixel_ai python=3.10 -y
conda activate pixel_ai

# 安装后端依赖
pip install -r requirements.txt
```

#### 方式 B：使用 venv

```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 步骤 4：安装 Ollama

1. 访问 [https://ollama.ai](https://ollama.ai) 下载并安装 Ollama
2. 启动 Ollama 服务
3. 拉取默认模型（根据 `config.yaml` 中的配置）：

```bash
# 示例：拉取 Qwen3:8b 模型
ollama pull qwen3:8b

# 或者使用更小的模型（适合低配机器）
ollama pull qwen2.5:3b
```

### 步骤 5：配置环境变量（可选）

如果从 HuggingFace 下载模型速度慢，可以设置镜像源：

**Windows (PowerShell):**
```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

**Windows (CMD):**
```cmd
set HF_ENDPOINT=https://hf-mirror.com
```

**macOS/Linux:**
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

或者在 `config.yaml` 中配置 embedding 和 reranker 模型路径。

### 步骤 6：启动服务

#### 方式 A：使用一键启动脚本

```bash
# Windows
start.bat

# macOS/Linux
chmod +x start.sh
./start.sh
```

#### 方式 B：手动启动

需要打开三个终端窗口：

**终端 1 - Ollama:**
```bash
ollama serve
```

**终端 2 - 后端 API:**
```bash
# Windows
python start_backend.py

# 或者
python -m api.app
```

**终端 3 - 前端:**
```bash
cd frontend
npm run dev
```

### 步骤 7：访问应用

浏览器打开: http://localhost:3000

---

## 知识库配置

EduRAG 支持多种知识库配置方式：

### 方式 A：联系作者获取预构建知识库

如果您想直接使用已构建好的知识库（包含 28000+ 文档片段），请联系作者获取 `data/chromadb` 目录。

**联系方式：**
- GitHub Issues: [提交 Issue](https://github.com/your-username/EduRAG/issues)
- Email: your-email@example.com

获取后，将 `chromadb` 文件夹解压到项目根目录的 `data/` 目录下：

```
EduRAG/
└── data/
    └── chromadb/      # 预构建的知识库
        └── chinese_essays/
```

### 方式 B：自行生成知识库

如果您有自己的文档数据，可以按照以下步骤生成知识库：

#### 1. 准备文档

将 PDF、DOCX、TXT、MD 等格式的文档放入以下目录：

```
data/docs/
├── pdfs/          # PDF 文档
├── docs/          # DOCX 文档
├── texts/         # TXT 文档
└── markdowns/     # MD 文档
```

或者使用扁平化目录结构（推荐）：

```
data/docs/
└── all/           # 所有文档放在一个目录
    ├── file1.pdf
    ├── file2.docx
    └── ...
```

#### 2. 运行导入脚本

```bash
# 导入普通文档
python scripts/import_docs.py

# 导入高考试卷（结构化解析）
python scripts/import_exam_papers.py
```

导入脚本会自动：
- 提取文档内容
- 智能分块（每块约 500 字）
- 解析元数据（年份、考区、题型等）
- 生成向量嵌入
- 存储到 ChromaDB

#### 3. 验证导入结果

启动后端服务后，访问:

- http://localhost:5000/search/stats - 查看知识库统计
- http://localhost:5000/search/collections - 查看集合列表

---

## 常见问题

### 1. Ollama 模型下载超时

**问题**: 从 HuggingFace 下载 embedding/reranker 模型时超时

**解决方案**:
```bash
# 设置镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 或者使用 start_backend.py 启动（自动设置镜像）
python start_backend.py
```

### 2. 端口被占用

**问题**: 端口 5000 或 3000 已被其他程序占用

**解决方案**:
```bash
# 修改后端端口（config.yaml）
server:
  port: 5001

# 修改前端端口（frontend/vite.config.ts）
server: {
  port: 3001
}
```

### 3. CUDA 相关错误

**问题**: NVIDIA GPU 但无法使用 CUDA

**解决方案**:
```bash
# 确认安装了 CUDA 版本的 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 在 config.yaml 中启用 CUDA
embedding:
  device: cuda

reranker:
  device: cuda
```

### 4. 中文文件名显示乱码

**问题**: Windows 控制台显示中文文件名为乱码

**解决方案**:
这是正常的编码问题，不影响实际功能。前端界面会正确显示中文。

### 5. 搜索结果为空

**问题**: 知识检索返回 0 条结果

**可能原因**:
1. 知识库为空 - 检查是否导入了文档
2. 相似度阈值过高 - 在 `/search/stats` 查看配置
3. 集合名称错误 - 默认为 `chinese_essays`

**解决方案**:
```bash
# 检查知识库统计
curl http://localhost:5000/search/stats

# 重新导入文档
python scripts/import_docs.py
```

### 6. 内存不足

**问题**: 导入大量文档时内存溢出

**解决方案**:
1. 减小批量大小（修改 `scripts/import_docs.py` 中的 `batch_size`）
2. 使用更小的 embedding 模型
3. 分批导入文档

### 7. 前端白屏

**问题**: 访问 http://localhost:3000 显示空白页面

**解决方案**:
```bash
# 检查后端是否启动
curl http://localhost:5000/health

# 重新启动前端
cd frontend
npm run dev
```

### 8. 文档无法打开

**问题**: 点击"打开原文"按钮返回 404

**解决方案**:
1. 确认文档文件存在于 `data/docs/all/` 或其他子目录
2. 检查文件名是否正确（注意中文编码）
3. 重启后端服务使文件索引更新

---

## 开发模式

### 后端开发

```bash
# 启用调试模式
export FLASK_DEBUG=1
python -m api.app

# 查看日志
# 日志输出在控制台实时显示
```

### 前端开发

```bash
cd frontend

# 开发服务器（热重载）
npm run dev

# 代码检查
npm run lint

# 构建生产版本
npm run build
```

---

## 生产部署

### 前端构建

```bash
cd frontend
npm run build
# 构建产物在 frontend/dist/ 目录
```

### 后端配置

修改 `config.yaml`:
```yaml
server:
  debug: false
  cors_enabled: false  # 如果前端由 Flask 托管
```

### 使用 Gunicorn（Linux/macOS）

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 api.app:app
```

---

## 技术支持

如遇到其他问题，请：

1. 查看控制台日志中的错误信息
2. 检查 [GitHub Issues](https://github.com/your-username/EduRAG/issues) 是否有类似问题
3. 提交新的 Issue 并附上：
   - 操作系统版本
   - Python 版本
   - 错误日志
   - 复现步骤

---

## 更新日志

- **v1.8** (2026-06-20): 文档扁平化，支持 794 个文档智能查找
- **v1.7** (2026-06-19): JSON 解析容错系统，一键收藏功能
- **v1.6** (2026-06-18): 作品集模块，命题热点模块
- **v1.5** (2026-06-17): 强化训练模块，成长日志

---

**最后更新**: 2026-06-20
