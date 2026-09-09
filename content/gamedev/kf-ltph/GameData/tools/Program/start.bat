@echo off
chcp 65001 >nul

rem 已在运行则跳过
curl -s --noproxy "*" -m 2 http://127.0.0.1:8712/ping >nul 2>&1
if not errorlevel 1 (
    echo [INFO] server already running
    timeout /t 3 >nul
    exit /b
)

rem 启动 HTTP 服务器（同时服务导出配置+点位编辑）
start "DataPipe" /min uv run "%~dp0server.py"

rem 等待就绪
set /a N=0
:wait
ping -n 2 127.0.0.1 >nul
set /a N+=1
curl -s --noproxy "*" -m 2 http://127.0.0.1:8712/ping >nul 2>&1
if not errorlevel 1 goto :ready
if %N% lss 8 goto :wait
echo [FAIL] start timeout
pause
exit /b

:ready
echo [READY] server ready on 127.0.0.1:8712
echo Tool pages: GameData/tools/View/*.html (Obsidian HTML Reader or browser)
timeout /t 3 >nul
