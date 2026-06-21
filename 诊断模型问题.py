"""
模型配置诊断脚本
帮助排查为什么模型配置没有生效
"""
import yaml
import requests
import subprocess
import sys
import os

# 设置UTF-8输出
os.system('chcp 65001 >nul')

print("=" * 60)
print("  EduRAG 模型配置诊断工具")
print("=" * 60)
print()

# 1. 检查config.yaml
print("[1] 检查 config.yaml...")
try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    model_in_config = config.get('ollama', {}).get('model', '未找到')
    print(f"    [OK] config.yaml中的模型: {model_in_config}")
except Exception as e:
    print(f"    [ERROR] 读取config.yaml失败: {e}")
    sys.exit(1)

print()

# 2. 检查Ollama服务
print("[2] 检查 Ollama 服务...")
try:
    resp = requests.get('http://localhost:11434/api/tags', timeout=5)
    if resp.status_code == 200:
        models = resp.json().get('models', [])
        print(f"    [OK] Ollama正在运行，已安装{len(models)}个模型:")
        for m in models:
            print(f"      - {m['name']}")
        
        # 检查gemma3:4b是否存在
        gemma_exists = any(m['name'] == 'gemma3:4b' for m in models)
        if gemma_exists:
            print(f"    [OK] gemma3:4b 已安装")
        else:
            print(f"    [WARN] gemma3:4b 未安装！")
    else:
        print(f"    [ERROR] Ollama返回错误: {resp.status_code}")
except Exception as e:
    print(f"    [ERROR] Ollama未运行: {e}")
    print(f"    请先运行: ollama serve")
    sys.exit(1)

print()

# 3. 检查后端服务
print("[3] 检查后端服务...")
try:
    resp = requests.get('http://localhost:5000/health', timeout=5)
    if resp.status_code == 200:
        health = resp.json()
        current_model = health.get('model', '未知')
        print(f"    [OK] 后端正在运行")
        print(f"    当前使用的模型: {current_model}")
        
        if current_model == model_in_config:
            print(f"    [OK] 模型配置正确！后端使用的是config.yaml中的{model_in_config}")
        else:
            print(f"    [ERROR] 模型不匹配！")
            print(f"       config.yaml配置: {model_in_config}")
            print(f"       后端实际使用: {current_model}")
            print(f"       原因: 后端是旧进程，需要重启")
    else:
        print(f"    [ERROR] 后端返回错误: {resp.status_code}")
except Exception as e:
    print(f"    [ERROR] 后端未运行或无法连接: {e}")
    print(f"    请运行: python start_backend.py")

print()

# 4. 检查是否有多个Python进程
print("[4] 检查Python进程...")
try:
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                          capture_output=True, text=True, encoding='gbk')
    lines = [l for l in result.stdout.split('\n') if 'python.exe' in l.lower()]
    if len(lines) > 0:
        print(f"    发现 {len(lines)} 个Python进程:")
        for line in lines[:5]:  # 最多显示5个
            print(f"      {line.strip()}")
        if len(lines) > 1:
            print(f"    [WARN] 可能有多个后端实例在运行！")
    else:
        print(f"    未发现Python进程")
except Exception as e:
    print(f"    无法检查进程: {e}")

print()
print("=" * 60)
print("  建议操作:")
print("=" * 60)
print()
print("如果后端显示的模型与config.yaml不一致:")
print("  1. 关闭所有EduRAG Backend窗口")
print("  2. 双击 start.bat 重新启动")
print("  3. 观察后端窗口是否显示: LLM模型配置: gemma3:4b")
print()
