"""
EduRAG API 服务入口
提供 RESTful 接口供外部系统调用写作训练和知识库检索功能
"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import yaml
from flask import Flask, jsonify
from flask_cors import CORS

from core.embedding import EmbeddingModel
from core.db_manager import EduRAGDatabase
from core.llm_client import OllamaClient
from core.retriever import Retriever
from core.rag_pipeline import RAGPipeline
from core.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    config_path = os.path.abspath(config_path)

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        return {}


def create_app(config: dict = None) -> Flask:
    """
    创建 Flask 应用并初始化共享的服务实例

    Args:
        config: 配置字典，不传则从 config.yaml 加载

    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    if config is None:
        config = load_config()

    # 解析配置
    ollama_cfg = config.get('ollama', {})
    chroma_cfg = config.get('chroma', {})
    embed_cfg = config.get('embedding', {})
    retrieval_cfg = config.get('retrieval', {})

    # 初始化共享服务实例（所有路由共享，避免重复加载模型）
    logger.info("正在初始化服务组件...")

    embedder = EmbeddingModel(
        model_name=embed_cfg.get('model_name', 'BAAI/bge-base-zh-v1.5'),
        device=embed_cfg.get('device', None),
    )

    db = EduRAGDatabase(
        db_path=chroma_cfg.get('persist_directory', './data/chroma_db'),
        embedding_model=embed_cfg.get('model_name', 'BAAI/bge-base-zh-v1.5'),
        device=embed_cfg.get('device', None),
        embedder=embedder,
    )

    llm = OllamaClient(
        base_url=ollama_cfg.get('base_url', 'http://localhost:11434'),
        model=ollama_cfg.get('model', 'qwen2.5:7b'),
        temperature=ollama_cfg.get('temperature', 0.7),
        num_predict=ollama_cfg.get('num_predict', 1024),
    )

    # 初始化重排序器（可选）
    reranker_cfg = config.get('reranker', {})
    enable_rerank = retrieval_cfg.get('rerank', False)
    reranker = None
    if enable_rerank or reranker_cfg.get('model_name'):
        reranker = CrossEncoderReranker(
            model_name=reranker_cfg.get('model_name', 'BAAI/bge-reranker-base'),
            device=reranker_cfg.get('device', None),
        )
        logger.info(f"重排序器已初始化: {reranker.model_name} (启用: {enable_rerank})")

    retriever = Retriever(
        db=db,
        embedder=embedder,
        reranker=reranker,
        enable_rerank=enable_rerank,
    )

    rag = RAGPipeline(
        db=db,
        llm=llm,
        retriever=retriever,
        default_collection='chinese_essays',
        default_top_k=retrieval_cfg.get('default_top_k', 8),
        default_score_threshold=retrieval_cfg.get('similarity_threshold', 0.25),
    )

    # 将共享实例存储到 app 上下文
    app.config['edurag'] = {
        'embedder': embedder,
        'db': db,
        'llm': llm,
        'retriever': retriever,
        'rag': rag,
        'config': config,
    }

    # 注册路由蓝图
    from api.routes.writing import writing_bp
    from api.routes.search import search_bp
    from api.routes.practice import practice_bp
    from api.routes.upload import upload_bp
    from api.routes.portfolio import portfolio_bp
    from api.routes.hot_topics import hot_topics_bp

    app.register_blueprint(writing_bp, url_prefix='/writing')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(practice_bp, url_prefix='/practice')
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
    app.register_blueprint(hot_topics_bp, url_prefix='/hot-topics')

    # 健康检查
    @app.route('/health', methods=['GET'])
    def health():
        db_count = db.get_collection_count('chinese_essays')
        return jsonify({
            'status': 'ok',
            'service': 'EduRAG',
            'model': llm.model,
            'collection_docs': db_count,
        })

    logger.info("EduRAG API 服务初始化完成")
    return app


def main():
    """启动 API 服务"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    config = load_config()
    api_cfg = config.get('api', {})

    app = create_app(config)

    host = api_cfg.get('host', '0.0.0.0')
    port = api_cfg.get('port', 5000)
    debug = api_cfg.get('debug', False)

    print(f"\n{'='*50}")
    print(f"  EduRAG API 服务")
    print(f"  地址: http://{host}:{port}")
    print(f"  调试: {'开启' if debug else '关闭'}")
    print(f"{'='*50}\n")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
