## 1. 项目概述

**EduRAG** 是一个基于检索增强生成（RAG）的本地化智能教育辅助系统，专注于 K12 阶段（小学到高中）的语文写作训练，并计划扩展至数学、英语等学科。系统通过 Ollama 部署本地大模型，结合自定义的知识库（范文库、真题库、知识点库），为学生提供审题、构思、写作、评估的全流程指导。

### 核心特性
- 🏫 **全本地部署**：数据不出校园，无需联网，隐私安全
- 📚 **多知识库支持**：分学科、分学段的向量数据库
- ✍️ **写作专项训练**：从审题到评估的闭环教学
- 🔍 **智能检索增强**：RAG 确保回答基于真实教学资料
- 🧩 **模块化设计**：核心 RAG 引擎与学科应用解耦

---

## 2. 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 向量数据库 | ChromaDB | 轻量级嵌入式向量数据库，支持持久化 |
| Embedding 模型 | BAAI/bge-base-zh-v1.5 | 中文语义向量模型，免费本地运行 |
| 大语言模型 | Qwen2.5:7B / DeepSeek-R1:8B | 通过 Ollama 调用，支持多模型切换 |
| 编排层 | LangChain | 简化 RAG 链构建 |
| API 服务 | Flask | 提供 RESTful 接口供主系统调用 |
| 运行环境 | Python 3.10+ | 依赖管理：pip + virtualenv |

---

## 3. 目录结构
EduRAG/
├── README.md # 项目说明、快速启动
├── ARCHITECTURE.md # 本文件
├── requirements.txt # Python 依赖
├── config.yaml # 配置文件（模型、检索参数等）
│
├── core/ # 核心 RAG 引擎（可跨学科复用）
│ ├── init.py
│ ├── db_manager.py # ChromaDB 封装（增删改查）
│ ├── retriever.py # 检索器（支持多路召回、重排序）
│ ├── embedding.py # 向量化统一接口
│ ├── llm_client.py # Ollama 调用封装
│ └── rag_pipeline.py # RAG 完整链路（检索 + 增强 + 生成）
│
├── subjects/ # 学科应用模块
│ ├── init.py
│ ├── chinese/ # 语文学科
│ │ ├── init.py
│ │ ├── writing.py # 写作训练四步流程
│ │ ├── prompt_loader.py # Prompt 模板加载器
│ │ ├── knowledge.py # 语文知识点检索
│ │ └── prompts/ # 各阶段 Prompt 模板
│ │ ├── topic_analysis.txt
│ │ ├── outline_gen.txt
│ │ ├── writing_assist.txt
│ │ └── evaluation.txt
│ ├── math/ # 数学学科（待实现）
│ │ ├── init.py
│ │ └── problem_solving.py
│ └── english/ # 英语学科（待实现）
│ ├── init.py
│ └── grammar_check.py
│
├── data/ # 数据存储
│ ├── raw/ # 原始文档（PDF, Word, txt）
│ │ ├── chinese/
│ │ ├── math/
│ │ └── english/
│ ├── processed/ # 清洗/分块后的中间数据
│ └── chroma_db/ # ChromaDB 持久化目录（自动生成）
│
├── scripts/ # 工具脚本
│ ├── import_docs.py # 批量导入文档到向量库
│ ├── test_retrieval.py # 测试检索效果
│ └── benchmark.py # 性能测试
│
├── api/ # API 服务（供主系统调用）
│ ├── init.py
│ ├── app.py # Flask 应用入口
│ └── routes/ # 路由定义
│ ├── writing.py # 写作相关接口
│ └── search.py # 通用检索接口
│
├── tests/ # 单元测试
│ ├── test_db_manager.py
│ ├── test_retriever.py
│ └── test_writing.py
│
└── logs/ # 运行日志

text

---

## 4. 核心模块设计

### 4.1 核心 RAG 引擎 (`core/`)

#### `db_manager.py` - 数据库抽象层
- 封装 ChromaDB 客户端
- 提供 `create_collection`, `add_documents`, `search`, `delete_collection` 等方法
- 自动处理 embedding 生成（调用 embedding 模块）

#### `retriever.py` - 检索器
- 支持单集合检索、跨集合检索
- 可选的重排序（reranking）提升精度（使用 `cross-encoder`）
- 结果合并与去重

#### `rag_pipeline.py` - RAG 完整链路
- 输入：用户问题 + 学科 + 学段 + 检索参数
- 流程：检索 → 构建上下文 → 调用 LLM → 输出
- 支持模板化 Prompt（从 prompts 文件加载）

### 4.2 写作训练模块 (`subjects/chinese/writing.py`)

实现四个核心方法，每个方法都内置 RAG 检索：

```python
def analyze_topic(topic: str, grade: str) -> dict:
    """审题训练：提取关键词、文体、题眼"""
    
def generate_outline(topic: str, student_idea: str, grade: str) -> dict:
    """构思训练：生成提纲、推荐素材"""
    
def assist_writing(topic: str, student_text: str, question: str) -> str:
    """写作辅助：渐进式提示，不代写"""
    
def evaluate_essay(topic: str, essay: str, grade: str) -> dict:
    """多维度评估：评分 + 反馈 + 进步建议"""
4.3 API 层 (api/)
供外部系统调用的 REST 接口：

端点	方法	功能
/writing/analyze	POST	审题
/writing/outline	POST	构思提纲
/writing/assist	POST	写作辅助
/writing/evaluate	POST	作文评估
/search	POST	通用知识库检索
5. 数据流图
text
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
6. 开发路线图
Phase 1：核心引擎（本周）
项目目录初始化

实现 db_manager.py 基础功能

实现 embedding.py 向量化封装

测试导入/检索功能

Phase 2：写作模块 MVP（下周）
接入 Ollama（llm_client.py）

实现 rag_pipeline.py

完成 writing.py 四个核心方法（使用固定 Prompt）

编写 API 路由

Phase 3：知识库增强（第3周）
批量导入范文（支持 PDF/Word）

加入评分细则库

加入真题库

优化检索精度（重排序、元数据过滤）

Phase 4：扩展与集成（第4周）
数学模块：解题答疑

英语模块：语法批改

集成到主 AI 伴学系统

性能优化与安全审核

7. 配置说明 (config.yaml)
yaml
# Ollama 配置
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5:7b"       # 可选 deepseek-r1:8b
  temperature: 0.7
  num_predict: 1024

# RAG 检索配置
retrieval:
  default_top_k: 5
  similarity_threshold: 0.6   # 低于此分数不采用
  rerank: false                # 是否使用重排序（更准但更慢）

# 向量数据库
chroma:
  persist_directory: "./data/chroma_db"

# Embedding 模型
embedding:
  model_name: "BAAI/bge-base-zh-v1.5"
  device: "cpu"               # 可选 cuda

# API 服务
api:
  host: "0.0.0.0"
  port: 5000
  debug: false
8. 运行指南
安装依赖
bash
pip install -r requirements.txt
启动 Ollama 服务
bash
ollama serve
ollama pull qwen2.5:7b
导入范文
bash
python scripts/import_docs.py
启动 API 服务
bash
python api/app.py
测试写作功能
bash
curl -X POST http://localhost:5000/writing/analyze \
  -H "Content-Type: application/json" \
  -d '{"topic": "成长的滋味", "grade": "8"}'
9. 注意事项
数据安全：所有数据存储在本地，不会上传到任何云端

模型选择：低配置设备可使用 qwen2.5:3b 或 gemma2:2b

评分标准：初期参考中高考标准，后期可引入本校评分细则

并发支持：当前为单线程，如需多用户请使用 gunicorn 部署

*文档版本：v1.0 | 最后更新：2026-01-19*