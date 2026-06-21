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
from flask import Flask, jsonify, request
from flask_cors import CORS

from core.embedding import EmbeddingModel
from core.db_manager import EduRAGDatabase
from core.llm_client import OllamaClient
from core.retriever import Retriever
from core.rag_pipeline import RAGPipeline
from core.reranker import CrossEncoderReranker
from subjects.chinese.writing import ChineseWritingTrainer

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
        device='cpu',  # 强制使用CPU，避免CUDA错误
    )

    db = EduRAGDatabase(
        db_path=chroma_cfg.get('persist_directory', './data/chroma_db'),
        embedding_model=embed_cfg.get('model_name', 'BAAI/bge-base-zh-v1.5'),
        device='cpu',  # 强制使用CPU
        embedder=embedder,
    )

    llm = OllamaClient(
        base_url=ollama_cfg.get('base_url', 'http://localhost:11434'),
        model=ollama_cfg.get('model', 'qwen2.5:7b'),
        temperature=ollama_cfg.get('temperature', 0.7),
        num_predict=ollama_cfg.get('num_predict', 1024),
    )
    
    logger.info(f"LLM模型配置: {llm.model} (从配置文件读取: {ollama_cfg.get('model')})")

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

    # 初始化语文写作训练器（用于多AI并行生成和播客素材导出）
    chinese_trainer = ChineseWritingTrainer(db=db, llm=llm, collection_name='chinese_essays')

    # 将共享实例存储到 app 上下文
    app.config['edurag'] = {
        'embedder': embedder,
        'db': db,
        'llm': llm,
        'retriever': retriever,
        'rag': rag,
        'chinese_trainer': chinese_trainer,  # 新增：写作训练器实例
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

    # 播客音频文件服务（静态文件）
    from flask import send_from_directory
    @app.route('/podcast-audio/<filename>', methods=['GET'])
    def serve_podcast_audio(filename):
        """提供播客音频文件访问"""
        audio_dir = Path('./data/podcast_audio/')
        return send_from_directory(str(audio_dir), filename)

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

    # 获取当前LLM模型配置和可用模型列表
    @app.route('/system/model', methods=['GET'])
    def get_model():
        """获取当前LLM模型配置和Ollama可用模型"""
        try:
            # 从Ollama获取实际安装的模型列表
            installed_models = llm._get_installed_models()
            
            # 为已知模型添加友好标签
            model_labels = {
                'gemma3:4b': 'Gemma 3 4B (快速)',
                'gemma3:12b': 'Gemma 3 12B (平衡)',
                'qwen2.5:7b': 'Qwen 2.5 7B (中文强)',
                'qwen3:8b': 'Qwen 3 8B (质量高)',
                'qwen2.5:14b': 'Qwen 2.5 14B (更强)',
                'llama3.2:3b': 'Llama 3.2 3B (轻量)',
                'llama3.1:8b': 'Llama 3.1 8B (通用)',
            }
            
            # 构建可用模型列表
            available_models = []
            for model_name in installed_models:
                label = model_labels.get(model_name, model_name)
                available_models.append({
                    'value': model_name,
                    'label': label
                })
            
            # 如果没有检测到模型，提供默认推荐
            if not available_models:
                available_models = [
                    {'value': 'gemma3:4b', 'label': 'Gemma 3 4B (快速)'},
                    {'value': 'qwen2.5:7b', 'label': 'Qwen 2.5 7B (中文强)'},
                    {'value': 'qwen3:8b', 'label': 'Qwen 3 8B (质量高)'},
                ]
            
            return jsonify({
                'success': True,
                'model': llm.model,
                'available_models': available_models
            })
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            # 降级到默认列表
            return jsonify({
                'success': True,
                'model': llm.model,
                'available_models': [
                    {'value': 'gemma3:4b', 'label': 'Gemma 3 4B (快速)'},
                    {'value': 'qwen2.5:7b', 'label': 'Qwen 2.5 7B (中文强)'},
                    {'value': 'qwen3:8b', 'label': 'Qwen 3 8B (质量高)'},
                ]
            })

    # 切换LLM模型
    @app.route('/system/model', methods=['POST'])
    def set_model():
        """切换LLM模型"""
        try:
            data = request.get_json() or {}
            new_model = data.get('model')

            if not new_model:
                return jsonify({'success': False, 'error': '请指定模型名称'}), 400

            # 验证模型是否存在于Ollama中
            installed_models = llm._get_installed_models()
            if new_model not in installed_models:
                logger.warning(f"模型 {new_model} 未安装，将尝试自动拉取")

            # 更新全局llm对象的model
            llm.model = new_model

            # 同时更新config
            config['ollama']['model'] = new_model

            logger.info(f"模型已切换为: {new_model}")
            return jsonify({
                'success': True,
                'model': new_model,
                'message': f'模型已切换为 {new_model}'
            })
        except Exception as e:
            logger.error(f"切换模型失败: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'切换模型失败: {str(e)}'
            }), 500

    logger.info("EduRAG API 服务初始化完成")
    return app


def main():
    """启动 API 服务"""
    # 配置日志 - 禁用缓冲，确保实时输出
    import sys
    
    # 设置环境变量禁用Python缓冲
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # 创建自定义Handler，确保每次写入后立即刷新
    class FlushHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有handler
    root_logger.handlers.clear()
    
    # 添加自定义handler（使用stderr，因为Werkzeug不会重定向stderr）
    handler = FlushHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # 特别配置werkzeug日志器
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = True  # 传播到根日志器
    
    # 确保api.routes.hot_topics的logger也传播到根日志器
    hot_topics_logger = logging.getLogger('api.routes.hot_topics')
    hot_topics_logger.setLevel(logging.INFO)
    hot_topics_logger.propagate = True
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("EduRAG Backend 启动")
    logger.info(f"Python: {sys.executable}")
    logger.info(f"版本: {sys.version}")
    logger.info("=" * 60)

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
    
    # 确保日志立即刷新
    sys.stdout.flush()
    sys.stderr.flush()

    # 配置Werkzeug日志，确保实时输出
    import werkzeug.serving
    werkzeug.serving.WSGIRequestHandler.log = lambda self, type, message, *args: (
        logging.getLogger('werkzeug').info(message % args)
    )
    
    # 禁用Werkzeug的reloader以避免双重进程
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    main()
