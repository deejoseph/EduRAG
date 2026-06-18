"""
EduRAG RAG 流水线模块
将检索（Retrieval）与生成（Generation）串联，实现增强式问答
"""

import logging
from typing import List, Dict, Any, Optional

from core.db_manager import EduRAGDatabase
from core.llm_client import OllamaClient
from core.embedding import EmbeddingModel
from core.retriever import Retriever, RetrievalResult

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG 流水线：检索 + 增强 + 生成"""
    
    def __init__(
        self,
        db: EduRAGDatabase,
        llm: OllamaClient,
        retriever: Optional[Retriever] = None,
        default_collection: str = "chinese_essays",
        default_top_k: int = 5,
        default_score_threshold: float = 0.0,
        enable_rerank: bool = False
    ):
        """
        初始化 RAG 流水线
        
        Args:
            db: 数据库实例
            llm: LLM 客户端实例
            retriever: 检索器实例（不传则自动创建）
            default_collection: 默认集合名称
            default_top_k: 默认检索数量
            default_score_threshold: 相似度阈值（0-1），低于此值的结果将被过滤
            enable_rerank: 是否启用重排序（暂未实现，预留）
        """
        self.db = db
        self.llm = llm
        self.default_collection = default_collection
        self.default_top_k = default_top_k
        self.default_score_threshold = default_score_threshold
        self.enable_rerank = enable_rerank
        
        # 使用外部注入的 retriever 或自动创建
        if retriever is not None:
            self.retriever = retriever
        else:
            embedder = getattr(db, 'embedder', None) or EmbeddingModel()
            self.retriever = Retriever(db=db, embedder=embedder)
        
        # 默认的 System Prompt 模板
        self.default_system_template = (
            "你是一位专业的{role}，擅长{expertise}。"
            "请基于以下参考资料回答用户的问题。"
            "如果参考资料不足以回答，请诚实说明，不要编造信息。"
            "回答要具体、有针对性，避免空泛。"
        )
    
    def _build_context(self, retrieved_docs: List[str], metadatas: Optional[List[Dict]] = None) -> str:
        """将检索到的文档拼接成上下文"""
        if not retrieved_docs:
            return "（没有找到相关参考资料）"
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            # 如果有元数据，添加引用信息
            if metadatas and i-1 < len(metadatas):
                meta = metadatas[i-1]
                source = meta.get("source", "未知来源")
                grade = meta.get("grade", "")
                topic = meta.get("topic", "")
                header = f"[参考{i} 来源:{source}"
                if grade:
                    header += f" 年级:{grade}"
                if topic:
                    header += f" 主题:{topic}"
                header += "]"
                context_parts.append(f"{header}\n{doc}")
            else:
                context_parts.append(f"[参考{i}]\n{doc}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def query(
        self,
        question: str,
        collection: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        where: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        role: str = "语文写作教师",
        expertise: str = "作文审题、构思、写作技巧和评估",
        temperature: float = 0.7,
        rerank: Optional[bool] = None,
        **llm_kwargs
    ) -> Dict[str, Any]:
        """
        执行 RAG 查询
        
        Args:
            question: 用户问题
            collection: 集合名称（不指定则使用默认）
            top_k: 检索数量
            score_threshold: 相似度阈值
            where: 元数据过滤条件
            system_prompt: 完整的系统提示（优先级高于 role+expertise）
            role: 系统角色（用于默认模板）
            expertise: 专长领域（用于默认模板）
            temperature: LLM 温度参数
            rerank: 是否启用重排序（None=使用全局设置）
            **llm_kwargs: 传递给 LLM 的其他参数
            
        Returns:
            包含 answer, retrieved_docs, metadata 的字典
        """
        # 参数默认值
        collection = collection or self.default_collection
        top_k = top_k or self.default_top_k
        # 关键修正：使用 default_score_threshold 作为 fallback
        if score_threshold is None:
            score_threshold = self.default_score_threshold
        
        # 1. 检索
        logger.info(f"RAG 检索: collection={collection}, query={question[:50]}...")
        try:
            retrieval_result = self.retriever.search(
                collection_name=collection,
                query=question,
                top_k=top_k,
                where=where,
                score_threshold=score_threshold,
                rerank=rerank,
            )
            retrieved_docs = retrieval_result.documents
            metadatas = retrieval_result.metadatas
            distances = [1.0 - s for s in retrieval_result.scores] if retrieval_result.scores else []
        except Exception as e:
            logger.error(f"检索失败: {e}")
            retrieved_docs = []
            metadatas = []
            distances = []
        
        # 2. 构建上下文
        context = self._build_context(retrieved_docs, metadatas)
        
        # 3. 构建提示词
        if system_prompt is None:
            system_prompt = self.default_system_template.format(role=role, expertise=expertise)
        
        user_prompt = f"""【参考资料】
{context}

【用户问题】
{question}

请基于参考资料回答问题。如果参考资料不足以支持回答，请明确说明需要更多信息。"""
        
        # 4. 调用 LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"调用 LLM: model={self.llm.model}, temperature={temperature}")
        try:
            llm_response = self.llm.chat(
                messages=messages,
                temperature=temperature,
                **llm_kwargs
            )
            answer = llm_response.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            answer = f"生成回答时出错: {e}"
        
        # 5. 返回结果
        return {
            "answer": answer,
            "retrieved_docs": retrieved_docs,
            "metadatas": metadatas,
            "distances": distances,
            "context": context,
            "llm_response": llm_response if 'llm_response' in locals() else None
        }
    
    def query_with_history(
        self,
        question: str,
        history: List[Dict[str, str]],
        collection: Optional[str] = None,
        top_k: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        支持对话历史的查询
        
        Args:
            question: 当前问题
            history: 历史消息列表 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            collection: 集合名称
            top_k: 检索数量
            **kwargs: 传递给 query 的其他参数
            
        Returns:
            同 query 返回
        """
        # 将历史与当前问题合并成一个完整的问题用于检索（简单拼接）
        context_for_retrieval = question
        if history:
            # 取最近三轮对话作为检索上下文
            recent = history[-6:]  # 最多 3 轮
            context_for_retrieval = "\n".join([f"{m['role']}: {m['content']}" for m in recent]) + f"\nuser: {question}"
        
        # 执行检索
        base_result = self.query(
            question=context_for_retrieval,  # 用增强后的问题检索
            collection=collection,
            top_k=top_k,
            **kwargs
        )
        
        # 重新构建用于生成的消息（包含完整历史）
        collection_name = collection or self.default_collection
        top_k_val = top_k or self.default_top_k
        # 重新检索一次（或者使用之前的检索结果？为了简单，复用之前的 retrieved_docs）
        retrieved_docs = base_result.get("retrieved_docs", [])
        metadatas = base_result.get("metadatas", [])
        context = self._build_context(retrieved_docs, metadatas)
        
        # 构建包含历史的对话
        messages = []
        # 添加 system prompt
        role = kwargs.get("role", "语文写作教师")
        expertise = kwargs.get("expertise", "作文审题、构思、写作技巧和评估")
        system_prompt = kwargs.get("system_prompt") or self.default_system_template.format(role=role, expertise=expertise)
        messages.append({"role": "system", "content": system_prompt})
        # 添加历史
        messages.extend(history)
        # 添加当前问题（带参考资料）
        current_prompt = f"""【参考资料】
{context}

【当前问题】
{question}

请基于参考资料和历史对话回答。"""
        messages.append({"role": "user", "content": current_prompt})
        
        # 调用 LLM
        try:
            llm_response = self.llm.chat(
                messages=messages,
                temperature=kwargs.get("temperature", 0.7)
            )
            answer = llm_response.get("message", {}).get("content", "")
        except Exception as e:
            answer = f"生成回答时出错: {e}"
        
        base_result["answer"] = answer
        base_result["llm_response"] = llm_response if 'llm_response' in locals() else None
        return base_result


# 简单测试
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from core.db_manager import EduRAGDatabase
    from core.llm_client import OllamaClient
    
    db = EduRAGDatabase(db_path="./data/chroma_db")
    llm = OllamaClient(model="qwen2.5:7b")
    
    # 确保测试集合存在并有数据
    db.create_collection("test_essays")
    db.add_documents(
        "test_essays",
        [
            "母爱是清晨的一杯热牛奶，是深夜的一盏守候的灯。记得那次发烧，妈妈整夜未眠...",
            "成长是一场蜕变，从幼稚到成熟，从依赖到独立。那年夏天，我第一次独自远行...",
            "友谊是人生路上的明灯。当我考试失利时，是朋友的那句'没关系'给了我力量..."
        ],
        [
            {"grade": "7", "genre": "记叙文", "topic": "母爱"},
            {"grade": "8", "genre": "记叙文", "topic": "成长"},
            {"grade": "9", "genre": "记叙文", "topic": "友谊"}
        ]
    )
    
    rag = RAGPipeline(db, llm, default_collection="test_essays")
    result = rag.query("怎么写关于母爱的作文？")
    print("=== 回答 ===")
    print(result["answer"])
    
    db.delete_collection("test_essays")