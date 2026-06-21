@echo off
chcp 65001 >nul
title EduRAG - 清理并重启

echo ============================================
echo   EduRAG - 清理旧进程并重启
echo ============================================
echo.

:: 1. 关闭所有Python进程
echo [1/3] 关闭所有Python进程...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo       已关闭Python进程
) else (
    echo       未发现Python进程
)
timeout /t 2 /nobreak >nul

:: 2. 关闭Ollama（可选，通常不需要）
echo [2/3] Ollama服务保持运行（无需重启）

:: 3. 启动start.bat
echo [3/3] 启动EduRAG...
timeout /t 1 /nobreak >nul
start "" "start.bat"

echo.
echo ============================================
echo   清理完成！新服务正在启动...
echo ============================================
echo.
exit
