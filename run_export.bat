@echo off
chcp 65001 >nul
echo ========================================
echo   EduRAG 对话记录导出工具
echo ========================================
echo.

REM 检查是否安装了 bun
where bun >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到 Bun，正在运行...
    bun run export_conversation_bun.ts
) else (
    echo ⚠️  未检测到 Bun
    echo.
    echo 请选择:
    echo   1. 安装 Bun (推荐)
    echo   2. 使用 Node.js 版本 (即将创建)
    echo.
    
    set /p choice="请选择 (1/2, 默认2): "
    
    if "%choice%"=="1" (
        echo.
        echo 正在安装 Bun...
        echo 请访问 https://bun.sh/docs/installation 获取安装说明
        echo.
        echo Windows 用户可以使用 PowerShell:
        echo   irm bun.sh/install.ps1 | iex
        echo.
        pause
    ) else (
        echo.
        echo 将为您创建 Node.js 版本的脚本...
        echo 请稍候...
        call create_node_version.bat
    )
)

pause
