"""
名人名言API路由
提供随机金句获取、学习日志记录等功能
"""

from flask import Blueprint, request, jsonify, current_app
import json
import os
from pathlib import Path
from datetime import datetime
import random

quotes_bp = Blueprint('quotes', __name__)

# 数据文件路径
QUOTES_LOG_FILE = Path('data/quotes_learning_log.json')


def load_learning_log():
    """加载学习日志"""
    if QUOTES_LOG_FILE.exists():
        try:
            with open(QUOTES_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_learning_log(log):
    """保存学习日志"""
    QUOTES_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUOTES_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


@quotes_bp.route('/random', methods=['GET'])
def get_random_quote():
    """
    获取随机一条名人名言
    
    Returns:
        {
            "id": "quote_0123",
            "text": "名言内容",
            "author": "作者",
            "category": "分类"
        }
    """
    try:
        # 从应用上下文中获取数据库实例
        edurag = current_app.config.get('edurag', {})
        db = edurag.get('db')
        if db is None:
            return jsonify({'error': '数据库未初始化'}), 500
        
        # 获取名言集合
        collection = db.get_collection('quotes_collection')
        
        if collection is None:
            return jsonify({'error': '知识库中没有名言'}), 404
        
        # 获取所有名言的ID
        all_data = collection.get(include=['metadatas'])
        quote_ids = all_data['ids']
        metadatas = all_data['metadatas']
        
        if not quote_ids:
            return jsonify({'error': '知识库中没有名言'}), 404
        
        # 随机选择一条
        random_index = random.randint(0, len(quote_ids) - 1)
        quote_id = quote_ids[random_index]
        metadata = metadatas[random_index]
        
        # 获取完整信息
        result = collection.get(ids=[quote_id], include=['documents'])
        quote_text = result['documents'][0] if result['documents'] else ''
        
        return jsonify({
            'success': True,
            'quote': {
                'id': quote_id,
                'text': quote_text,
                'author': metadata.get('author', '未知'),
                'category': metadata.get('category', '其他'),
                'source_file': metadata.get('source_file', '')
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quotes_bp.route('/daily', methods=['GET'])
def get_daily_quote():
    """
    获取每日金句（基于日期种子，保证同一天相同）
    
    Returns:
        每日金句信息
    """
    try:
        # 从应用上下文中获取数据库实例
        edurag = current_app.config.get('edurag', {})
        db = edurag.get('db')
        if db is None:
            return jsonify({'error': '数据库未初始化'}), 500
        
        # 获取名言集合
        collection = db.get_collection('quotes_collection')
        
        if collection is None:
            return jsonify({'error': '知识库中没有名言'}), 404
        
        # 获取所有名言
        all_data = collection.get(include=['documents', 'metadatas'])
        quote_ids = all_data['ids']
        documents = all_data['documents']
        metadatas = all_data['metadatas']
        
        if not quote_ids:
            return jsonify({'error': '知识库中没有名言'}), 404
        
        # 使用当前日期作为随机种子（保证同一天相同）
        today = datetime.now().strftime('%Y-%m-%d')
        seed_value = hash(today) % len(quote_ids)
        
        selected_index = seed_value
        quote_id = quote_ids[selected_index]
        quote_text = documents[selected_index]
        metadata = metadatas[selected_index]
        
        return jsonify({
            'success': True,
            'date': today,
            'quote': {
                'id': quote_id,
                'text': quote_text,
                'author': metadata.get('author', '未知'),
                'category': metadata.get('category', '其他')
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quotes_bp.route('/log', methods=['POST'])
def log_quote_learning():
    """
    记录名人名言学习日志
    
    Request Body:
        quote_id: 名言ID
        action: 学习动作 (view/copy/favorite)
    
    Returns:
        学习统计信息
    """
    data = request.get_json() or {}
    quote_id = data.get('quote_id')
    action = data.get('action', 'view')
    
    if not quote_id:
        return jsonify({'error': '请提供名言ID'}), 400
    
    try:
        # 加载学习日志
        log = load_learning_log()
        
        # 初始化该名言的记录
        if quote_id not in log:
            log[quote_id] = {
                'quote_id': quote_id,
                'total_views': 0,
                'total_copies': 0,
                'total_favorites': 0,
                'last_viewed_at': None,
                'learning_sessions': []
            }
        
        # 更新统计数据
        if action == 'view':
            log[quote_id]['total_views'] += 1
            log[quote_id]['last_viewed_at'] = datetime.now().isoformat()
        elif action == 'copy':
            log[quote_id]['total_copies'] += 1
        elif action == 'favorite':
            log[quote_id]['total_favorites'] += 1
        
        # 记录学习会话
        session = {
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        log[quote_id]['learning_sessions'].append(session)
        
        # 限制会话记录数量（保留最近100条）
        if len(log[quote_id]['learning_sessions']) > 100:
            log[quote_id]['learning_sessions'] = log[quote_id]['learning_sessions'][-100:]
        
        # 保存日志
        save_learning_log(log)
        
        return jsonify({
            'success': True,
            'stats': {
                'quote_id': quote_id,
                'total_views': log[quote_id]['total_views'],
                'total_copies': log[quote_id]['total_copies'],
                'total_favorites': log[quote_id]['total_favorites'],
                'last_viewed_at': log[quote_id]['last_viewed_at']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quotes_bp.route('/stats/<quote_id>', methods=['GET'])
def get_quote_stats(quote_id):
    """
    获取指定名言的学习统计
    
    Returns:
        学习统计信息
    """
    try:
        log = load_learning_log()
        
        if quote_id not in log:
            return jsonify({
                'success': True,
                'stats': {
                    'quote_id': quote_id,
                    'total_views': 0,
                    'total_copies': 0,
                    'total_favorites': 0,
                    'last_viewed_at': None
                }
            })
        
        stats = log[quote_id]
        return jsonify({
            'success': True,
            'stats': {
                'quote_id': stats['quote_id'],
                'total_views': stats['total_views'],
                'total_copies': stats['total_copies'],
                'total_favorites': stats['total_favorites'],
                'last_viewed_at': stats['last_viewed_at']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quotes_bp.route('/list', methods=['GET'])
def list_quotes():
    """
    获取名言列表（支持分页和过滤）
    
    Query Params:
        page: 页码（默认1）
        limit: 每页数量（默认20）
        category: 分类过滤
        author: 作者过滤
    
    Returns:
        名言列表和分页信息
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category')
        author = request.args.get('author')
        
        # 从应用上下文中获取数据库实例
        edurag = current_app.config.get('edurag', {})
        db = edurag.get('db')
        if db is None:
            return jsonify({'error': '数据库未初始化', 'quotes': [], 'pagination': {'total': 0, 'page': page, 'limit': limit}}), 500
        
        # 获取名言集合
        collection = db.get_collection('quotes_collection')
        
        if collection is None:
            return jsonify({'error': '知识库中没有名言', 'quotes': [], 'pagination': {'total': 0, 'page': page, 'limit': limit}}), 404
        
        # 获取所有名言
        all_data = collection.get(include=['documents', 'metadatas'])
        quote_ids = all_data['ids']
        documents = all_data['documents']
        metadatas = all_data['metadatas']
        
        # 过滤
        filtered_indices = []
        for i, metadata in enumerate(metadatas):
            if category and metadata.get('category') != category:
                continue
            if author and metadata.get('author') != author:
                continue
            filtered_indices.append(i)
        
        # 分页
        total = len(filtered_indices)
        start = (page - 1) * limit
        end = start + limit
        page_indices = filtered_indices[start:end]
        
        # 构建结果
        quotes = []
        for idx in page_indices:
            quotes.append({
                'id': quote_ids[idx],
                'text': documents[idx],
                'author': metadatas[idx].get('author', '未知'),
                'category': metadatas[idx].get('category', '其他')
            })
        
        return jsonify({
            'success': True,
            'quotes': quotes,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
