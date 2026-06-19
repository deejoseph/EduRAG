# EduRAG 智能写作助手 — 系统架构文档

> 基于 RAG（检索增强生成）的本地化 K12 教育辅助系统，专注高考语文写作训练。

---

## 1. 项目概述

**EduRAG** 是一个基于检索增强生成（RAG）的本地化智能教育辅助系统，专注于 K12 阶段（小学到高中）的语文写作训练，并计划扩展至数学、英语等学科。系统通过 Ollama 部署本地大模型，结合自定义的知识库（范文库、真题库、知识点库），为学生提供审题、构思、写作、评估的全流程指导。

### 核心特性
- **全本地部署**：数据不出校园，无需联网，隐私安全
- **多知识库支持**：分学科、分学段的向量数据库
- **写作专项训练**：从审题到评估的闭环教学
- **智能检索增强**：RAG 确保回答基于真实教学资料
- **模块化设计**：核心 RAG 引擎与学科应用解耦

---

## 2. 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 向量数据库 | ChromaDB | 轻量级嵌入式向量数据库，支持持久化 |
| Embedding 模型 | BAAI/bge-base-zh-v1.5 | 中文语义向量模型，免费本地运行 |
| 重排序模型 | BAAI/bge-reranker-base | 交叉编码器，提升检索精度 |
| 大语言模型 | Qwen3:8B (Q4_K_M) | 通过 Ollama 调用，支持多模型切换 |
| API 服务 | Flask | 提供 RESTful 接口 |
| 前端框架 | React + TypeScript + Vite | SPA 单页应用 |
| UI 组件库 | Ant Design | 企业级 React UI 组件 |
| 图表库 | Recharts | 数据可视化（成长日志图表） |
| 状态管理 | Zustand | 轻量级状态管理 |
| GPU 加速 | CUDA | config.yaml 配置 device: cuda |

---

## 3. 目录结构

```
EduRAG/
├── ARCHITECTURE.md            # 本文件（系统架构文档）
├── 项目开发进度.md              # 开发进度记录
├── config.yaml                # 全局配置（模型、检索参数等）
├── requirements.txt           # Python 依赖
├── start.bat                  # 一键启动脚本（Ollama→后端→前端→浏览器）
├── start_backend.py           # 后端启动脚本（自动设置 HF_ENDPOINT 镜像源）
│
├── core/                      # 核心 RAG 引擎（可跨学科复用）
│   ├── db_manager.py          # ChromaDB 封装（集合 CRUD、元数据过滤）
│   ├── embedding.py           # BGE 中文向量嵌入（CPU/GPU 自适应）
│   ├── llm_client.py          # Ollama LLM 客户端（支持流式输出、多模型切换）
│   ├── rag_pipeline.py        # RAG 查询流水线（检索→重排序→LLM 生成）
│   ├── reranker.py            # BGE 重排序模型（交叉编码器）
│   └── retriever.py           # 向量检索（多路召回 + 元数据过滤 + 相似度阈值）
│
├── api/                       # Flask API 服务
│   ├── app.py                 # 应用入口（Blueprint 注册、CORS、日志配置）
│   └── routes/
│       ├── __init__.py        # 通用过滤条件构建（8 维元数据）
│       ├── search.py          # 知识库检索（3 接口）
│       ├── writing.py         # 写作训练（4 接口）
│       ├── practice.py        # 强化训练（7 接口）
│       ├── portfolio.py       # 作品集管理（10 接口）
│       ├── hot_topics.py      # 命题热点（9 接口）
│       └── upload.py          # 知识库上传（2 接口）
│
├── subjects/                  # 学科 Prompt 模板
│   └── chinese/
│       ├── prompt_loader.py   # Jinja2 模板渲染引擎
│       ├── writing.py         # 写作训练器封装（4 步流程）
│       └── prompts/           # 4 套 Prompt 模板
│           ├── topic_analysis.txt
│           ├── outline_gen.txt
│           ├── writing_assist.txt
│           └── evaluation.txt
│
├── scripts/                   # 数据导入工具
│   ├── doc_extractors.py      # PDF/DOCX 文本提取
│   ├── text_chunker.py        # 智能文本分块（500 字/50 字重叠）
│   ├── metadata_parser.py     # 文件名元数据解析
│   ├── import_docs.py         # 知识库批量导入（断点续传）
│   ├── exam_parser.py         # 试卷结构化解析（7 种题型）
│   └── import_exam_papers.py  # 真题导入脚本
│
├── frontend/                  # React 前端应用
│   └── src/
│       ├── api/               # API 请求封装（7 个模块）
│       ├── components/        # 通用组件（6 个）
│       ├── constants/         # 高考枚举常量
│       ├── pages/             # 10 个页面
│       ├── store/             # zustand 状态管理
│       ├── styles/            # 全局样式
│       └── types/             # TypeScript 类型定义
│
├── data/                      # 数据存储
│   ├── chroma_db/             # ChromaDB 持久化目录
│   ├── hot_topics_cache/      # 命题热点缓存（JSON 文件）
│   ├── practice_records/      # 强化训练记录（JSON 文件）
│   ├── portfolio/             # 作品集数据（JSON 文件）
│   └── import_progress.json   # 批量导入断点续传记录
│
└── tests/                     # 测试脚本
```

---

## 4. 核心模块设计

### 4.1 核心 RAG 引擎 (`core/`)

#### `db_manager.py` — 数据库抽象层
- 封装 ChromaDB 客户端
- 提供 `create_collection`, `add_documents`, `search`, `delete_collection` 等方法
- 自动处理 embedding 生成（调用 embedding 模块）
- 支持元数据过滤（8 维度）

#### `embedding.py` — 向量嵌入
- 使用 BAAI/bge-base-zh-v1.5 模型
- 自动检测 GPU 可用性，支持 CPU/CUDA 切换
- 统一的 `embed()` 接口供 db_manager 和 retriever 调用

#### `llm_client.py` — LLM 客户端
- 封装 Ollama API 调用
- 支持流式和非流式输出
- 支持多模型动态切换（qwen3:8b, gemma3:4b 等）
- 可配置 `think` 参数（关闭思考模式以加速推理）

#### `retriever.py` — 检索引擎
- 支持单集合检索、跨集合检索
- 8 维元数据过滤：year / exam_region / doc_category / file_type / question_type / grade_level / subject / source_type
- 相似度阈值过滤（默认 threshold=0.25）
- 结果合并与去重

#### `reranker.py` — 重排序模型
- 使用 BAAI/bge-reranker-base 交叉编码器
- 对初始检索结果进行精排
- 可配置启用/禁用（config.yaml 的 rerank 参数）

#### `rag_pipeline.py` — RAG 完整链路
- 输入：用户问题 + 学科 + 学段 + 检索参数
- 流程：检索 → 重排序 → 构建上下文 → 调用 LLM → 后处理
- 支持模板化 Prompt（从 prompts 文件加载）
- 内置参考答案来源标注

### 4.2 写作训练模块 (`subjects/chinese/writing.py`)

实现四个核心方法，每个方法都内置 RAG 检索：

| 方法 | 功能 | 说明 |
|------|------|------|
| `analyze_topic()` | 审题训练 | 提取关键词、文体、题眼，RAG 检索相关范文 |
| `generate_outline()` | 构思提纲 | 生成提纲、推荐素材，结合知识库 |
| `assist_writing()` | 写作辅助 | 渐进式提示（润色/续写/修辞/过渡），不代写 |
| `evaluate_essay()` | 作文评估 | 高考 4 维度评分（内容/结构/语言/发展）+ 反馈 |

#### `prompt_loader.py` — Prompt 模板渲染引擎
- 使用 Jinja2 模板引擎
- 支持变量注入（题目、年级、学生文本等）
- 从 `.txt` 文件加载模板

### 4.3 API 层 (`api/routes/`)

#### 知识库检索 (`search.py`) — 3 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/search/query` | 知识库语义检索（支持 LLM 增强回答） |
| GET | `/search/stats` | 知识库统计信息（文档数、chunk 数、集合数） |
| GET | `/search/collections` | 集合列表 |
| GET | `/search/hot-topics` | 知识库热门主题统计（基于检索历史） |

#### 写作训练 (`writing.py`) — 4 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/writing/analyze` | 审题分析（关键词、文体、题眼） |
| POST | `/writing/outline` | 构思提纲（结构化提纲 + 素材推荐） |
| POST | `/writing/assist` | 写作辅助（润色/续写/修辞/过渡） |
| POST | `/writing/evaluate` | 作文评估（高考 4 维度评分） |

#### 强化训练 (`practice.py`) — 7 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/practice/start` | 开始训练会话（4 阶段：审题→构思→写作→评估） |
| POST | `/practice/save-phase` | 保存阶段结果（正向计时 + 内容） |
| GET | `/practice/history` | 训练历史列表（分页） |
| GET | `/practice/detail/<id>` | 训练详情 |
| DELETE | `/practice/delete/<id>` | 删除训练记录 |
| POST | `/practice/toggle-log` | 切换成长日志计入状态 |
| GET | `/practice/growth-log` | 成长日志数据（分数趋势 + 维度均分） |

**核心设计**：
- 正向计时（已用 MM:SS）代替倒计时，减压设计
- 成长日志开关：用户可选择是否计入成长统计
- AI 反馈复用写作训练模块的 Prompt 模板
- JSON 文件持久化：`data/practice_records/{session_id}.json`

#### 作品集管理 (`portfolio.py`) — 10 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/portfolio/add` | 添加作品到作品集 |
| GET | `/portfolio/list` | 作品列表（分页 + 筛选） |
| GET | `/portfolio/detail/<id>` | 作品详情 |
| PUT | `/portfolio/update/<id>` | 更新作品信息 |
| DELETE | `/portfolio/delete/<id>` | 删除单个作品 |
| POST | `/portfolio/toggle-star/<id>` | 星标/取消星标 |
| POST | `/portfolio/add-tag/<id>` | 添加标签 |
| DELETE | `/portfolio/remove-tag/<id>` | 移除标签 |
| GET | `/portfolio/tags` | 所有标签列表 |
| DELETE | `/portfolio/batch-delete` | 批量删除作品 |
| GET | `/portfolio/stats` | 作品集统计（总数/平均分/热门标签） |

**核心功能**：
- 从写作训练或强化训练评估页一键收藏作文
- 标签管理（添加/删除/按标签筛选）
- 星标功能（标记重点作品）
- 学习笔记（记录写作技巧总结）
- 智能搜索（按标题、内容、关键词搜索）
- 多维筛选（标签/来源/星标/排序方式）

#### 命题热点 (`hot_topics.py`) — 9 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/hot-topics/categories` | 获取话题分类列表（6 大分类） |
| POST | `/hot-topics/search` | 搜索热点话题（支持分类搜索和关键词搜索） |
| POST | `/hot-topics/refresh` | 强制刷新缓存 |
| POST | `/hot-topics/prompt-generator` | 自定义命题生成 |
| POST | `/hot-topics/favorite` | 收藏单个话题 |
| POST | `/hot-topics/favorite-all` | 一键收藏所有话题（批量收藏，自动去重） |
| DELETE | `/hot-topics/favorite/<title>` | 取消收藏 |
| GET | `/hot-topics/favorites` | 获取收藏列表（支持排序：时间/标题/相关度/练习次数） |

**6 大话题分类**：科技发展、文化传承、生态文明、教育改革、社会责任、国际视野

**核心功能**：
- **智能命题预测**：LLM 分析社会热点，生成模拟高考作文题目
- **关键词定向搜索**：输入关键词（如"责任担当"），生成紧扣主题的命题
- **一键收藏**：批量收藏当前所有话题到题库，自动跳过已收藏项
- **单个收藏/取消**：在话题卡片上单独操作
- **自定义命题**：基于关键词生成个性化作文题目
- **缓存机制**：搜索结果按分类缓存（24 小时 TTL）
- **降级策略**：LLM 不可用时返回预设示例话题
- **智能 JSON 解析**：状态机解析器处理 LLM 返回的格式不规范 JSON（中文引号、截断等）
- **练习次数统计**：收藏列表显示每个题目在作品集中的练习次数

**相关度评分说明**：
- **向量相似度评分**（知识库检索模块）：基于 BGE Embedding 的余弦相似度，范围 0-1，由 ChromaDB 返回
- **LLM 主观评分**（命题热点模块）：`relevance_score` 字段，范围 1-10，由 LLM 根据话题与高考命题的关联程度打分

#### 知识库上传 (`upload.py`) — 2 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/upload/file` | 上传单个文件（PDF/DOCX/TXT） |
| POST | `/upload/batch` | 批量上传文件 |

---

## 5. 前端页面

### 5.1 页面结构

| 页面 | 路径 | 组件数 | 说明 |
|------|------|--------|------|
| 首页仪表盘 | `Dashboard/index.tsx` | 1 | 系统状态卡片、知识库统计、LLM 模型信息、快捷入口 |
| 写作训练 | `Writing/` | 5 | 4 步向导：审题(TopicAnalysis)→构思(OutlineGen)→辅助(WritingAssist)→评估(EssayEval) |
| 强化训练 | `Practice/` | 5 | 主容器 + 4 阶段(TopicPhase/OutlinePhase/EssayPhase/EvalPhase) + 历史(History) |
| 成长日志 | `GrowthLog/index.tsx` | 1 | 统计卡片 + 分数曲线(AreaChart) + 用时柱状图(BarChart) + 维度雷达图(RadarChart) |
| 作品集 | `Portfolio/` | 2 | 主页面(列表/筛选/搜索) + 详情页(Tab 切换：作文/评估/笔记) |
| 命题热点 | `HotTopics/index.tsx` | 1 | 分类搜索 + 关键词搜索 + 话题卡片 + 一键收藏 + 自定义命题弹窗 |
| 知识检索 | `Search/index.tsx` | 1 | 搜索栏 + 8 项筛选 + LLM 增强回答 + 参考列表 |
| 知识库上传 | `Upload/index.tsx` | 1 | 文件拖拽上传 + 进度显示 + 格式验证 |
| 系统设置 | `Settings/index.tsx` | 1 | 后端状态 + 模型切换 + 作品集/成长日志重置 |

### 5.2 布局与导航

| 组件 | 文件 | 说明 |
|------|------|------|
| 全局布局 | `layout/AppLayout.tsx` | Sider + Content 响应式布局 |
| 侧边导航 | `layout/SideMenu.tsx` | 9 项导航（首页/写作/训练/成长/作品集/命题热点/检索/上传/设置） |

### 5.3 通用组件

| 组件 | 文件 | 说明 |
|------|------|------|
| Markdown 渲染 | `common/MarkdownRenderer.tsx` | react-markdown + GFM 支持 |
| 加载遮罩 | `common/LoadingOverlay.tsx` | LLM 推理等待全屏遮罩 |
| 回答展示 | `writing/AnswerDisplay.tsx` | AI 回答卡片展示 |
| 参考资料 | `writing/ReferencePanel.tsx` | 可折叠参考列表 + 元数据标签 |

### 5.4 API 封装层 (`frontend/src/api/`)

| 文件 | 方法数 | 说明 |
|------|--------|------|
| `client.ts` | 1 | axios 基础实例（120s 超时 + 错误拦截器） |
| `writing.ts` | 4 | 审题/构思/辅助/评估 |
| `search.ts` | 3 | 查询/统计/集合 |
| `practice.ts` | 7 | 训练会话管理 + 成长日志 |
| `portfolio.ts` | 10 | 作品集 CRUD + 标签 + 星标 + 统计 |
| `hotTopics.ts` | 9 | 分类/搜索/刷新/命题/收藏/取消收藏/收藏列表/一键收藏/热门统计 |
| `upload.ts` | 2 | 单文件/批量上传 |

### 5.5 前端功能特性

**命题热点页面完整功能**：
- 分类下拉选择（6 大分类 + 全部）
- 关键词搜索（输入自定义关键词，如"责任担当"）
- 搜索热点（force_refresh 模式，每次重新生成）
- 刷新缓存（清空缓存并重新调用 LLM）
- 话题卡片展示（标题/摘要/作文题/写作角度/参考素材/难度/相关度）
- 话题详情弹窗（完整内容展示）
- 单个收藏/取消收藏按钮
- **一键收藏所有话题**按钮（批量操作，自动去重）
- 自定义命题生成弹窗（输入关键词 → LLM 生成作文题）
- 收藏列表查看（仅显示已收藏）
- 历史热门主题统计（从知识库检索历史中提取）

**写作训练页面完整功能**：
- 4 步向导流程（审题→构思→辅助→评估）
- 每步调用 RAG 检索 + LLM 生成
- 评估页支持一键收藏到作品集
- 高考默认配置：高中 / 材料作文 / 议论文 / 800 字

**强化训练页面完整功能**：
- 4 阶段限时训练（审题→构思→正文→评估）
- 正向计时显示（已用时间 + 建议用时）
- 正文写作自动保存（localStorage）
- 成长日志开关（可选是否计入统计）
- 训练历史查看（分页 + 删除）

**成长日志页面完整功能**：
- 统计概览卡片（总训练次数/平均分/最高分/平均用时）
- 分数趋势曲线图（AreaChart）
- 用时柱状图（BarChart）
- 维度雷达图（RadarChart，内容/结构/语言/发展 4 维）

---

## 6. 数据流图

```
用户请求 → API 路由 → 学科模块（如 writing.py）
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
```

---

## 7. 数据存储方案

| 数据类型 | 存储方式 | 路径 |
|----------|----------|------|
| 知识库文档 | ChromaDB 向量数据库 | `data/chroma_db/` |
| 命题热点缓存 | JSON 文件（按分类） | `data/hot_topics_cache/{category}.json` |
| 热点收藏列表 | JSON 文件 | `data/hot_topics_favorites.json` |
| 强化训练记录 | JSON 文件（按会话） | `data/practice_records/{session_id}.json` |
| 作品集数据 | JSON 文件（按作品） | `data/portfolio/{item_id}.json` |
| 导入断点续传 | JSON 文件 | `data/import_progress.json` |
| 前端自定义学科 | localStorage | 浏览器本地 |

---

## 8. 配置说明 (`config.yaml`)

```yaml
# Ollama 配置
ollama:
  base_url: "http://localhost:11434"
  model: "qwen3:8b"              # 可选 gemma3:4b, qwen2.5:7b 等
  temperature: 0.7
  num_predict: 1024

# RAG 检索配置
retrieval:
  default_top_k: 8
  similarity_threshold: 0.25
  rerank: false                   # 是否使用重排序

# 向量数据库
chroma:
  persist_directory: "./data/chroma_db"

# Embedding 模型
embedding:
  model_name: "BAAI/bge-base-zh-v1.5"
  device: "cuda"                  # 可选 cpu

# API 服务
api:
  host: "0.0.0.0"
  port: 5000
  debug: false
```

---

## 9. 运行指南

### 一键启动
双击 `start.bat`，自动启动 Ollama → 后端 → 前端 → 打开浏览器

### 手动启动
```bash
# 终端 1：Ollama（如已运行可跳过）
ollama serve

# 终端 2：后端 API（port 5000）
cd D:\PixelSmile\EduRAG
python -m api.app

# 终端 3：前端（port 3000）
cd D:\PixelSmile\EduRAG\frontend
npm run dev
```

访问 http://localhost:3000

---

## 10. API 端点汇总

共计 **38 个端点**：

| # | 方法 | 路径 | 功能 | 模块 |
|---|------|------|------|------|
| 1 | GET | `/health` | 健康检查 + 模型信息 | 系统 |
| 2 | POST | `/search/query` | 知识库语义检索 | 检索 |
| 3 | GET | `/search/stats` | 知识库统计 | 检索 |
| 4 | GET | `/search/collections` | 集合列表 | 检索 |
| 5 | GET | `/search/hot-topics` | 热门主题统计 | 检索 |
| 6 | POST | `/writing/analyze` | 审题分析 | 写作 |
| 7 | POST | `/writing/outline` | 构思提纲 | 写作 |
| 8 | POST | `/writing/assist` | 写作辅助 | 写作 |
| 9 | POST | `/writing/evaluate` | 作文评估 | 写作 |
| 10 | POST | `/practice/start` | 开始训练 | 训练 |
| 11 | POST | `/practice/save-phase` | 保存阶段 | 训练 |
| 12 | GET | `/practice/history` | 训练历史 | 训练 |
| 13 | GET | `/practice/detail/<id>` | 训练详情 | 训练 |
| 14 | DELETE | `/practice/delete/<id>` | 删除训练 | 训练 |
| 15 | POST | `/practice/toggle-log` | 切换日志计入 | 训练 |
| 16 | GET | `/practice/growth-log` | 成长日志数据 | 训练 |
| 17 | POST | `/portfolio/add` | 添加作品 | 作品集 |
| 18 | GET | `/portfolio/list` | 作品列表 | 作品集 |
| 19 | GET | `/portfolio/detail/<id>` | 作品详情 | 作品集 |
| 20 | PUT | `/portfolio/update/<id>` | 更新作品 | 作品集 |
| 21 | DELETE | `/portfolio/delete/<id>` | 删除作品 | 作品集 |
| 22 | POST | `/portfolio/toggle-star/<id>` | 星标切换 | 作品集 |
| 23 | POST | `/portfolio/add-tag/<id>` | 添加标签 | 作品集 |
| 24 | DELETE | `/portfolio/remove-tag/<id>` | 移除标签 | 作品集 |
| 25 | GET | `/portfolio/tags` | 标签列表 | 作品集 |
| 26 | DELETE | `/portfolio/batch-delete` | 批量删除 | 作品集 |
| 27 | GET | `/portfolio/stats` | 作品集统计 | 作品集 |
| 28 | GET | `/hot-topics/categories` | 话题分类 | 命题热点 |
| 29 | POST | `/hot-topics/search` | 搜索热点 | 命题热点 |
| 30 | POST | `/hot-topics/refresh` | 刷新缓存 | 命题热点 |
| 31 | POST | `/hot-topics/prompt-generator` | 自定义命题 | 命题热点 |
| 32 | POST | `/hot-topics/favorite` | 收藏话题 | 命题热点 |
| 33 | POST | `/hot-topics/favorite-all` | 一键收藏全部 | 命题热点 |
| 34 | DELETE | `/hot-topics/favorite/<title>` | 取消收藏 | 命题热点 |
| 35 | GET | `/hot-topics/favorites` | 收藏列表 | 命题热点 |
| 36 | POST | `/upload/file` | 上传文件 | 上传 |
| 37 | POST | `/upload/batch` | 批量上传 | 上传 |
| 38 | GET | `/system/model` | 系统模型信息 | 系统 |

---

## 11. 注意事项

- **数据安全**：所有数据存储在本地，不上传到任何云端
- **模型选择**：低配置设备可使用 qwen2.5:3b 或 gemma2:2b
- **评分标准**：参考高考评分细则（内容/结构/语言/发展 4 维度）
- **GPU 加速**：config.yaml 设置 `device: cuda` 启用 GPU 加速
- **并发支持**：当前为单线程，如需多用户请使用 gunicorn 部署
- **LLM 超时**：命题热点模块有独立的超时控制（每分类 40 秒，总计 180 秒）
- **JSON 解析**：内置状态机解析器处理 LLM 返回的格式不规范 JSON

---

*文档版本：v2.0 | 最后更新：2026-06-19*
