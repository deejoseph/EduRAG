@echo off
chcp 65001 >nul
echo ============================================
echo   EduRAG 清理缓存并重启
echo ============================================
echo.

echo [1/3] 停止后端服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo   正在终止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   后端服务已停止
echo.

echo [2/3] 清理Python缓存...
del /s /q __pycache__ >nul 2>&1
del /s /q *.pyc >nul 2>&1
echo   Python缓存已清理
echo.

echo [3/3] 重新启动服务...
start "" cmd /c "cd /d "%~dp0" && title EduRAG Backend && C:\Users\deejo\anaconda3\envs\pixel_ai\python.exe start_backend.py"
echo   后端正在启动...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   清理完成！请在浏览器中按 Ctrl+Shift+R 强制刷新
echo ============================================
pause
