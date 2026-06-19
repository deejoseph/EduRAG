# EduRAG 智能写作助手

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)
![Flask](https://img.shields.io/badge/Flask-latest-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**基于 RAG 的本地化 K12 语文智能写作辅助系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [项目架构](#-项目架构) • [开发文档](#-开发文档) • [常见问题](#-常见问题)

</div>

---

## 项目简介

EduRAG（Educational Retrieval-Augmented Generation）是一个专为 K12 阶段设计的智能写作辅助系统，特别针对高考语文写作训练。系统采用本地化部署方案，结合检索增强生成（RAG）技术，为学生提供从审题、构思、写作到评估的全流程智能指导。

### 核心优势

- **隐私安全**：全本地部署，数据不出校园，无需联网
- **知识库丰富**：28,000+ 文本块，涵盖范文、真题、知识点
- **智能检索**：BGE Embedding + 重排序，精准匹配教学内容
- **专业评估**：基于高考评分标准的四维评分体系
- **成长追踪**：完整的训练历史和进步趋势分析

---

## 功能特性

### 1. 写作训练模块

提供完整的高考写作训练流程：

| 步骤 | 功能 | 说明 |
|------|------|------|
| 审题训练 | 关键词提取、文体识别、题眼分析 | 帮助学生准确把握题目要求 |
| 构思提纲 | 结构建议、素材推荐、逻辑梳理 | 构建清晰的写作框架 |
| 写作辅助 | 渐进式提示、润色建议、修辞指导 | 不代写，只提供改进方向 |
| 作文评估 | 四维评分、详细反馈、提升建议 | 内容/结构/语言/发展等级 |

### 2. 强化训练模块

模拟考试环境的限时训练：

- **正向计时**：减压设计，显示"已用时间"而非倒计时
- **分阶段训练**：审题(15min) → 构思(10min) → 写作(40min) → 评估
- **AI 对比**：学生答案与 AI 参考答案对比分析
- **成长日志**：自动记录训练数据，可视化进步轨迹

### 3. 作品集模块

管理和展示优秀作文作品：

- **作品收藏**：一键收藏写作训练和强化训练的优秀作品
- **标签管理**：自定义标签分类，支持多维筛选
- **星标功能**：标记重点作品，快速定位
- **学习笔记**：记录学习心得和写作技巧
- **统计分析**：作品数量、分数分布、热门标签

### 4. 知识检索模块

强大的知识库搜索能力：

- **语义检索**：基于向量相似度的智能搜索
- **多维筛选**：年份/考区/题型/学段等 8 个维度
- **LLM 增强**：可选的 AI 总结回答
- **结果展示**：高亮相关片段，显示元数据
- **RAG 热门主题**：基于知识库历史检索数据统计，展示高考作文高频主题方向，支持一键收藏到题库（标记为 `[RAG]` 来源）

### 5. 命题热点模块

AI 驱动的高考作文命题预测：

- **智能命题预测**：基于社会热点、教育动态、时政新闻，由 LLM 生成模拟高考作文题目
- **六大分类覆盖**：科技发展、文化传承、生态文明、教育改革、社会责任、国际视野
- **自定义命题**：支持输入自定义主题名称和关键词，生成个性化命题预测
- **题目详情**：每个预测题目包含材料、写作要求、参考角度、评分标准
- **题库收藏**：一键收藏到题库，标记为 `[AI预测]` 来源，供后续训练使用
- **缓存机制**：LLM 生成结果本地缓存，支持强制刷新
- **容错解析**：内置状态机 JSON 解析器，自动修复 LLM 返回的格式异常

### 6. 题库系统

统一管理来自不同来源的收藏题目：

- **来源标识**：题目明确标注 `[RAG]`（知识库历史数据）或 `[AI预测]`（LLM 生成）
- **优先展示**：RAG 来源题目优先排在列表前面，学生练习时优先选择
- **练习统计**：显示每道题目的练习次数，避免重复训练
- **多入口收藏**：支持从"知识检索"和"命题热点"两个页面收藏题目

### 7. 成长日志模块

可视化的学习数据分析：

- **分数趋势图**：AreaChart 展示分数变化曲线
- **用时统计**：BarChart 显示各阶段用时分布
- **能力雷达**：RadarChart 呈现四维能力分布
- **历史记录**：完整的训练历史查询

### 8. 系统设置模块

系统配置和数据管理：

- **后端状态监控**：实时显示服务运行状态
- **模型信息管理**：查看当前使用的 LLM 和 Embedding 模型
- **知识库统计**：各集合文档数量展示
- **数据重置**：安全的作品集和成长日志清空功能

---

## 快速开始

### 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| 内存 | 16 GB | 32 GB |
| 显卡 | NVIDIA RTX 3060 (6GB) | NVIDIA RTX 3070 (8GB) |
| 硬盘 | 50 GB 可用空间 | 100 GB SSD |
| 系统 | Windows 10 / 11 | Windows 11 |

### 一键启动

1. **安装依赖**（首次使用）
   ```bash
   # Python 后端依赖
   pip install -r requirements.txt
   
   # 前端依赖
   cd frontend
   npm install
   ```

2. **启动 Ollama**
   ```bash
   ollama serve
   ollama pull qwen3:8b
   ```

3. **运行启动脚本**
   
   双击 `start.bat` 文件，系统将自动启动：
   - ✅ Ollama 服务检查
   - ✅ 后端 API 服务（端口 5000）
   - ✅ 前端开发服务器（端口 3000）
   - ✅ 自动打开浏览器访问 http://localhost:3000

### 手动启动

如需调试或单独启动某个服务：

```bash
# 终端 1：Ollama（如已运行可跳过）
ollama serve

# 终端 2：后端 API
cd D:\PixelSmile\EduRAG
conda activate pixel_ai
python -m api.app

# 终端 3：前端
cd D:\PixelSmile\EduRAG\frontend
npm run dev
```

### 验证安装

启动成功后，访问以下地址验证：

- **前端页面**：http://localhost:3000
- **后端健康检查**：http://localhost:5000/health

应返回：
```json
{
  "status": "ok",
  "service": "EduRAG",
  "model": "qwen3:8b",
  "collection_docs": 28583
}
```

---

## 项目架构

### 技术栈

| 层级 | 技术选型 |
|------|---------|
| **前端框架** | React 18 + TypeScript + Vite |
| **UI 组件库** | Ant Design 5.x |
| **状态管理** | Zustand |
| **数据可视化** | Recharts |
| **HTTP 客户端** | Axios |
| **后端框架** | Flask |
| **向量数据库** | ChromaDB |
| **Embedding 模型** | BAAI/bge-base-zh-v1.5 |
| **重排序模型** | BAAI/bge-reranker-base |
| **大语言模型** | Qwen3:8B (via Ollama) |
| **深度学习框架** | PyTorch 2.5.1+cu121 |

### 目录结构

```
EduRAG/
├── core/                    # 核心 RAG 引擎
│   ├── db_manager.py        # ChromaDB 封装
│   ├── embedding.py         # 向量化接口
│   ├── retriever.py         # 检索器
│   ├── reranker.py          # 重排序模型
│   ├── llm_client.py        # Ollama 调用封装
│   └── rag_pipeline.py      # RAG 完整链路
│
├── api/                     # Flask API 服务
│   ├── app.py               # 应用入口
│   └── routes/
│       ├── writing.py       # 写作训练接口
│       ├── practice.py      # 强化训练接口
│       ├── portfolio.py     # 作品集接口
│       ├── search.py        # 知识库检索接口
│       ├── hot_topics.py    # 命题热点与题库接口
│       └── upload.py        # 知识库上传接口
│
├── subjects/                # 学科模块
│   └── chinese/
│       ├── writing.py       # 写作训练器
│       ├── prompt_loader.py # Prompt 模板加载
│       └── prompts/         # Prompt 模板文件
│
├── scripts/                 # 工具脚本
│   ├── import_docs.py       # 批量导入文档
│   ├── import_exam_papers.py # 试卷批量导入
│   ├── doc_extractors.py    # PDF/DOCX 提取
│   ├── text_chunker.py      # 文本分块
│   └── exam_parser.py       # 试卷解析
│
├── frontend/                # React 前端
│   └── src/
│       ├── pages/           # 页面组件
│       │   ├── Dashboard/   # 首页仪表盘
│       │   ├── Writing/     # 写作训练
│       │   ├── Practice/    # 强化训练
│       │   ├── Portfolio/   # 作品集
│       │   ├── Search/      # 知识检索（含 RAG 热门主题）
│       │   ├── HotTopics/   # 智能命题热点
│       │   ├── GrowthLog/   # 成长日志
│       │   ├── Upload/      # 文档上传
│       │   └── Settings/    # 系统设置
│       ├── components/      # 通用组件
│       ├── api/             # API 封装
│       ├── store/           # 状态管理
│       └── types/           # TypeScript 类型
│
├── data/                    # 数据存储
│   ├── chroma_db/           # ChromaDB 持久化
│   ├── practice_records/    # 训练记录
│   ├── portfolio/           # 作品集数据
│   ├── hot_topics_cache/    # 命题热点缓存
│   └── hot_topics_favorites.json  # 题库收藏
│
├── config.yaml              # 全局配置
├── requirements.txt         # Python 依赖
├── start.bat                # 一键启动脚本
└── start_backend.py         # 后端启动脚本
```

### 数据流图

```
写作/训练请求 → API 路由 → 学科模块（如 writing.py）
                              ↓
                        调用 RAG Pipeline
                              ↓
                ┌─────────────┼─────────────┐
                ↓             ↓             ↓
            检索器         Prompt 模板    LLM 客户端
                ↓             ↓             ↓
            向量数据库    上下文构建    Ollama 模型
                ↓             ↓             ↓
                └─────────────┼─────────────┘
                              ↓
                        后处理（过滤、格式化）
                              ↓
                        返回结构化响应

命题热点请求 → hot_topics.py → LLM 生成 / 缓存读取
                              ↓
                     状态机 JSON 解析器（容错）
                              ↓
                     返回预测题目列表

知识检索热门 → search.py → ChromaDB 统计
                              ↓
                     聚合高频主题 → 标记 [RAG] 来源
                              ↓
                     返回热门主题列表（可收藏）
```

---

## 开发文档

### API 端点汇总

#### 写作训练模块

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/writing/analyze` | 审题分析 |
| POST | `/writing/outline` | 构思提纲 |
| POST | `/writing/assist` | 写作辅助 |
| POST | `/writing/evaluate` | 作文评估 |

#### 强化训练模块

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/practice/start` | 开始新训练 |
| POST | `/practice/save-phase` | 保存阶段进度 |
| GET | `/practice/history` | 获取训练历史 |
| GET | `/practice/detail/:id` | 获取训练详情 |
| DELETE | `/practice/delete/:id` | 删除训练记录 |
| POST | `/practice/toggle-log` | 切换成长日志状态 |
| GET | `/practice/growth-log` | 获取成长日志统计 |

#### 作品集模块

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/portfolio/add` | 添加作品 |
| GET | `/portfolio/list` | 获取作品列表 |
| GET | `/portfolio/detail/:id` | 获取作品详情 |
| PUT | `/portfolio/update/:id` | 更新作品 |
| DELETE | `/portfolio/delete/:id` | 删除作品 |
| POST | `/portfolio/toggle-star/:id` | 切换星标 |
| POST | `/portfolio/add-tag/:id` | 添加标签 |
| DELETE | `/portfolio/remove-tag/:id` | 删除标签 |
| GET | `/portfolio/tags` | 获取所有标签 |
| DELETE | `/portfolio/reset` | 重置作品集 |

#### 知识库模块

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/search/query` | 知识库检索 |
| GET | `/search/stats` | 知识库统计 |
| GET | `/search/collections` | 集合列表 |
| GET | `/search/hot-topics` | RAG 热门主题统计 |
| POST | `/upload/document` | 上传文档 |
| POST | `/upload/exam-paper` | 上传试卷 |

#### 命题热点与题库模块

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/hot-topics/categories` | 获取分类列表 |
| POST | `/hot-topics/search` | 搜索/生成热点话题 |
| POST | `/hot-topics/refresh` | 刷新缓存 |
| POST | `/hot-topics/prompt-generator` | 自定义命题生成 |
| POST | `/hot-topics/favorite` | 收藏话题（支持 source 标识） |
| POST | `/hot-topics/favorite-all` | 批量收藏 |
| DELETE | `/hot-topics/favorite/:title` | 取消收藏 |
| GET | `/hot-topics/favorites` | 获取题库列表 |

### 配置说明

主要配置项位于 `config.yaml`：

```yaml
# Ollama 配置
ollama:
  base_url: "http://localhost:11434"
  model: "qwen3:8b"
  temperature: 0.7
  num_predict: 2048

# RAG 检索配置
retrieval:
  default_top_k: 8
  similarity_threshold: 0.25
  rerank: true

# 向量数据库
chroma:
  persist_directory: "./data/chroma_db"

# Embedding 模型
embedding:
  model_name: "BAAI/bge-base-zh-v1.5"
  device: "cuda"  # 或 "cpu"

# 重排序模型
reranker:
  model_name: "BAAI/bge-reranker-base"
  device: "cuda"
```

---

## 常见问题

### Q1: 后端启动超时

**解决方法：**
```bash
# 检查依赖
pip install -r requirements.txt

# 检查端口占用
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

### Q2: PyTorch CUDA 错误

**错误提示：** `AssertionError: Torch not compiled with CUDA enabled`

**解决方法：**
确保使用 `pixel_ai` conda 环境，该环境包含 GPU 版本的 PyTorch。

验证 GPU 是否启用：
```bash
python -c "import torch; print(torch.cuda.is_available())"
# 应输出: True
```

### Q3: 前端页面空白

**解决方法：**
```bash
cd frontend
npm install
npm run dev
```

检查浏览器控制台是否有 API 连接错误。

### Q4: Ollama 模型下载失败

**解决方法：**
```bash
# 检查网络连接
ollama pull qwen3:8b

# 如网络问题持续，可配置代理
export OLLAMA_HOST=http://localhost:11434
```

### Q5: 检索结果为空

**可能原因：**
1. 知识库未导入
2. 相似度阈值设置过高
3. 筛选条件过于严格

**解决方法：**
```bash
# 导入知识库
python scripts/import_docs.py

# 检查知识库统计
curl http://localhost:5000/search/stats
```

---

## 性能优化

### GPU 加速

当前 `pixel_ai` 环境已配置 **GPU 版本的 PyTorch** (`2.5.1+cu121`)，可充分利用 RTX 3070 8G。

**性能对比：**

| 操作 | CPU | GPU (RTX 3070) |
|------|-----|----------------|
| Embedding 编码 | ~500ms/句 | ~50ms/句 |
| 重排序 | ~200ms/次 | ~20ms/次 |
| 首次检索 | ~2s | ~0.5s |

**验证 GPU 是否启用：**

启动后端后，在控制台应看到：
```
INFO:core.embedding:Embedding 模型加载成功: BAAI/bge-base-zh-v1.5 (device: cuda)
```

---

## 数据安全

- **本地存储**：所有数据存储在本地，不会上传到任何云端
- **隐私保护**：学生写作内容完全本地化处理
- **备份建议**：定期备份 `data/` 目录下的数据

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 联系方式

- 项目主页：[GitHub Repository](https://github.com/your-repo/EduRAG)
- 问题反馈：[Issues](https://github.com/your-repo/EduRAG/issues)
- 邮箱联系：your-email@example.com

---

## 致谢

感谢以下开源项目：

- [Ollama](https://ollama.ai/) - 本地 LLM 部署
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [LangChain](https://www.langchain.com/) - LLM 应用框架
- [Ant Design](https://ant.design/) - UI 组件库
- [Recharts](https://recharts.org/) - 数据可视化

---

*最后更新：2026-06-19*
