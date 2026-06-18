"""
EduRAG Backend 启动脚本
设置必要的环境变量并启动服务
自动检测并切换到 pixel_ai 虚拟环境
"""
import os
import sys
import subprocess
from pathlib import Path

def find_pixel_ai_python():
    """查找 pixel_ai 虚拟环境的 Python 解释器路径"""
    # 常见的 conda 环境路径
    possible_paths = [
        Path.home() / "anaconda3" / "envs" / "pixel_ai" / "python.exe",
        Path.home() / "miniconda3" / "envs" / "pixel_ai" / "python.exe",
        Path("C:/Users/deejo/anaconda3/envs/pixel_ai/python.exe"),  # start.bat 中的路径
        Path("C:/ProgramData/miniconda3/envs/pixel_ai/python.exe"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # 尝试通过 conda 命令查找
    try:
        result = subprocess.run(
            ["conda", "run", "-n", "pixel_ai", "where", "python"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    
    return None

def restart_in_virtual_env():
    """如果不在 pixel_ai 环境中，重启到此环境"""
    if 'pixel_ai' in sys.executable:
        return False  # 已经在正确的环境中
    
    pixel_ai_python = find_pixel_ai_python()
    if not pixel_ai_python:
        print("[WARN] 警告: 未找到 pixel_ai 虚拟环境！")
        print("       将使用当前 Python 环境继续...")
        print("       建议: 使用 start.bat 启动以确保环境正确")
        return False
    
    print(f"[INFO] 检测到 pixel_ai 环境: {pixel_ai_python}")
    print("[INFO] 正在重启到虚拟环境...")
    
    # 重新执行此脚本，但使用 pixel_ai 的 Python
    env = os.environ.copy()
    env['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    try:
        subprocess.run(
            [pixel_ai_python] + sys.argv,
            env=env,
            cwd=os.getcwd()
        )
        return True  # 子进程已启动
    except Exception as e:
        print(f"[ERROR] 重启失败: {e}")
        print("       将使用当前环境继续...")
        return False

if __name__ == '__main__':
    # 设置控制台编码为UTF-8
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # 检查并自动切换到 pixel_ai 环境
    restarted = restart_in_virtual_env()
    if restarted:
        sys.exit(0)  # 已在子进程中运行
    
    # 设置 HuggingFace 镜像（中国用户）
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

    # 确保项目根目录在 Python 路径中
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print("=" * 60)
    print("  EduRAG Backend 启动中...")
    print("=" * 60)
    print(f"项目目录: {project_root}")
    print(f"Python 路径: {sys.executable}")
    print(f"Python 版本: {sys.version}")
    print(f"HF_ENDPOINT: {os.environ.get('HF_ENDPOINT', 'default')}")
    
    # 检查是否在正确的虚拟环境中
    if 'pixel_ai' in sys.executable:
        print("[OK] 虚拟环境: pixel_ai (正确)")
    else:
        print("[WARN] 警告: 未使用 pixel_ai 虚拟环境！")
        print(f"       当前环境: {sys.executable}")
    
    # 检查 CUDA 可用性
    try:
        import torch
        print(f"\nPyTorch 版本: {torch.__version__}")
        print(f"CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA 版本: {torch.version.cuda}")
            print(f"GPU 设备: {torch.cuda.get_device_name(0)}")
        print(f"Torch device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    except ImportError:
        print("[WARN] PyTorch 未安装")
    
    print("=" * 60)
    print()
    
    # 导入并启动应用
    from api.app import main as app_main
    app_main()
