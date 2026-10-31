@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo  Stopping AICTE Coordination System...
echo ============================================================
echo.

:: 1. Stop Frontend Server if running on port 5173
echo [*] Checking for running Vite frontend server (port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo [*] Terminating Vite dev server process (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Stop Docker Containers
echo [*] Stopping Docker containers (API, Worker, PostgreSQL)...
docker compose down
if %errorlevel% neq 0 (
    echo [WARNING] Docker Compose encountered an issue while stopping.
)

echo.
echo ============================================================
echo  AICTE Coordination System has been stopped successfully.
echo ============================================================
echo.
pause
