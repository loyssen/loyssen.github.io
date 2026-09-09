@echo off
chcp 65001 >nul
curl -s --noproxy "*" -X POST http://127.0.0.1:8712/shutdown >nul 2>&1
echo [已停止] 服务器关闭
timeout /t 1 /nobreak >nul
