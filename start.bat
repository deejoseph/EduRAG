@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title EduRAG 智能写作助手 - 启动器

echo ============================================
echo   EduRAG 智能写作助手 - 一键启动
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
set "PYTHON_PATH=C:\Users\deejo\anaconda3\envs\pixel_ai\python.exe"

:: ── 1. 检查 Ollama ──────────────────────────
echo [1/4] 检查 Ollama 服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama 未运行，正在启动 Ollama...
    start "" /B ollama serve
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if !errorlevel! neq 0 (
        echo       [!] Ollama 启动失败，请手动启动后重试
        echo       [!] 运行命令: ollama serve
        pause
        exit /b 1
    )
    echo       Ollama 已启动
) else (
    echo       Ollama 正在运行
)

:: ── 2. 预加载模型 ──────────────────────────
echo [2/4] 读取配置文件...
:: 使用Python从 config.yaml读取模型名称
for /f "usebackq tokens=*" %%a in (`%PYTHON_PATH% -c "import yaml; c=yaml.safe_load(open('config.yaml', encoding='utf-8')); print(c.get('ollama',{}).get('model','gemma3:4b'))"`) do set "MODEL_NAME=%%a"
if "%MODEL_NAME%"=="" set "MODEL_NAME=gemma3:4b"

echo       预加载 LLM 模型 (%MODEL_NAME%)...
curl -s http://localhost:11434/api/generate -d "{\"model\":\"%MODEL_NAME%\",\"prompt\":\"hi\",\"stream\":false}" >nul 2>&1
echo       模型已就绪

:: ── 3. 启动后端 Flask API ──────────────────
echo [3/4] 启动后端 API 服务 (port 5000, pixel_ai GPU)...
cd /d "%PROJECT_DIR%"

:: 检查并清理占用 5000 端口的旧进程
netstat -ano | findstr :5000 | findstr LISTENING >nul 2>&1
if !errorlevel! equ 0 (
    echo       检测到旧的后端进程，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo       旧进程已清理
)

:: 使用 start_backend.py 启动（自动设置HF_ENDPOINT环境变量）
start "EduRAG Backend" cmd /c "cd /d "%PROJECT_DIR%" && title EduRAG Backend && "%PYTHON_PATH%" start_backend.py && pause"

:: 等待后端启动
echo       等待后端就绪...
set /a retry=0
:wait_backend
timeout /t 3 /nobreak >nul
curl -s http://localhost:5000/health >nul 2>&1
if !errorlevel! neq 0 (
    set /a retry+=1
    if !retry! lss 50 goto wait_backend
    echo.
    echo       [!] 后端启动超时
    echo       [!] 请检查 EduRAG Backend 窗口的错误信息
    echo       [!] 常见原因:
    echo            - 依赖缺失: C:\Users\deejo\anaconda3\envs\pixel_ai\python.exe -m pip install -r requirements.txt
    echo            - 端口被占用: 检查 5000 端口
    echo            - 模型加载失败: 检查网络连接
    echo            - pixel_ai 环境不存在: conda env list
    echo.
    pause
    exit /b 1
) else (
    echo       后端 API 已就绪
)

:: ── 4. 启动前端 Vite ──────────────────────
echo [4/4] 启动前端开发服务器 (port 3000)...
cd /d "%PROJECT_DIR%frontend"
start "EduRAG Frontend" cmd /c "cd /d "%PROJECT_DIR%frontend" && title EduRAG Frontend && npm run dev && pause"

:: 等待前端启动
timeout /t 5 /nobreak >nul

:: ── 5. 打开浏览器 ──────────────────────────
echo.
echo ============================================
echo   正在打开浏览器...
echo   前端: http://localhost:3000
echo   后端: http://localhost:5000
echo ============================================
echo.
start "" http://localhost:3000

echo.
echo 启动完成！关闭此窗口不影响服务运行。
echo 要停止服务，请分别关闭 EduRAG Backend 和 EduRAG Frontend 窗口。
echo.
timeout /t 3 /nobreak >nul
