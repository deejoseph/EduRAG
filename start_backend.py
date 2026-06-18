"""
EduRAG Backend 启动脚本
设置必要的环境变量并启动服务
"""
import os
import sys

# 设置 HuggingFace 镜像（中国用户）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入并启动应用
from api.app import main as app_main

if __name__ == '__main__':
    print("=" * 50)
    print("  EduRAG Backend 启动中...")
    print("=" * 50)
    print(f"项目目录: {project_root}")
    print(f"HF_ENDPOINT: {os.environ.get('HF_ENDPOINT', 'default')}")
    print()
    
    app_main()
