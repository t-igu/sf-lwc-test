@echo off
setlocal


call .venv\Scripts\activate

taskkill /F /IM python.exe

echo ============================================
echo   Starting storage_server (port 8080)
echo ============================================
start "storage_server" cmd /k uvicorn storage_server.app.server:app --port 8080

REM 少し待つ
ping -n 2 127.0.0.1 >nul

echo ============================================
echo   Starting salesforce_server (port 8000)
echo ============================================
start "salesforce_server" cmd /k uvicorn salesforce_server.app.server:app --port 8000

REM 少し待つ
ping -n 2 127.0.0.1 >nul

echo ============================================
echo   Starting storage_worker
echo ============================================
start "storage_worker" cmd /k python -m storage_server.app.worker.worker_loop

echo ============================================
echo   All servers + worker started
echo ============================================

endlocal
