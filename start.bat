@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo  AICTE Integrated Institution Complaint Monitoring System
echo  SIH Problem Statement ID: 26264
echo ============================================================
echo.

:: 1. Check Docker
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in your PATH.
    echo Please install Docker Desktop and restart.
    pause
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running.
    echo Please start Docker Desktop and run start.bat again.
    pause
    exit /b 1
)

:: 2. Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in your PATH.
    echo Please install Node.js 18+ and restart.
    pause
    exit /b 1
)

:: 3. Prepare Environment
if not exist ".env" (
    echo [*] Creating .env from .env.example...
    copy ".env.example" ".env" >nul
)

:: 4. Start Docker Containers
echo [*] Starting backend containers (PostgreSQL 17, Django API, Q2 Worker)...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose failed to start containers.
    pause
    exit /b 1
)

:: 5. Wait for Database & API
echo [*] Waiting for database and API service to initialize...
timeout /t 5 /nobreak >nul

:: 6. Apply Migrations
echo [*] Applying database migrations...
docker compose exec -T api python manage.py migrate --noinput >nul 2>&1

:: 7. Check Frontend Dependencies
if not exist "frontend\node_modules" (
    echo [*] Installing frontend dependencies (first time setup)...
    cd frontend
    call npm install
    cd ..
)

:: 8. Start Frontend
echo [*] Starting frontend Vite dev server...
start "AICTE Coordination Portal (Vite Frontend)" cmd /c "cd /d %~dp0frontend && npm run dev"

:: 9. Display Ready Banner & Credentials
echo.
echo ============================================================
echo  AICTE Coordination System is RUNNING!
echo ============================================================
echo  Web Application:   http://localhost:5173
echo  Backend REST API:  http://localhost:8000/api/
echo  Admin Portal:      http://localhost:8000/admin/
echo ------------------------------------------------------------
echo  Default Demonstration Accounts:
echo    Role                  Username        Password
echo    Portal Coordinator:   coordinator     Demo-only-26264!
echo    Vigilance Auditor:    auditor         Demo-only-26264!
echo    Approval Bureau (RB): officer_rb      Demo-only-26264!
echo    PGRC Bureau:          officer_pgrc    Demo-only-26264!
echo ============================================================
echo  To stop all services cleanly, run stop.bat
echo ============================================================
echo.
pause
