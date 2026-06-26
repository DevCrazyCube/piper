@echo off
setlocal enabledelayedexpansion

REM Change to the directory where this script is located
cd /d "%~dp0"

echo ========================================
echo Starting Pipeline...
echo ========================================

REM Step 1: Build and start containers
echo.
echo [1/7] Running: docker compose up -d --build
docker compose up -d --build
if !errorlevel! neq 0 (
    echo ERROR: docker compose up -d --build failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 1 completed successfully

REM Step 2: Upgrade database
echo.
echo [2/7] Running: docker compose exec app alembic upgrade head
docker compose exec app alembic upgrade head
if !errorlevel! neq 0 (
    echo ERROR: alembic upgrade head failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 2 completed successfully

REM Step 3: Bootstrap pipeline
echo.
echo [3/7] Running: docker compose exec app python -m pipeline bootstrap
docker compose exec app python -m pipeline bootstrap
if !errorlevel! neq 0 (
    echo ERROR: pipeline bootstrap failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 3 completed successfully

REM Step 4: Ingest data
echo.
echo [4/7] Running: docker compose exec app python -m pipeline ingest all
docker compose exec app python -m pipeline ingest all
if !errorlevel! neq 0 (
    echo ERROR: pipeline ingest all failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 4 completed successfully

REM Step 5: Curate data
echo.
echo [5/7] Running: docker compose exec app python -m pipeline curate all
docker compose exec app python -m pipeline curate all
if !errorlevel! neq 0 (
    echo ERROR: pipeline curate all failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 5 completed successfully

REM Step 6: Analyse data
echo.
echo [6/7] Running: docker compose exec app python -m pipeline analyse all
docker compose exec app python -m pipeline analyse all
if !errorlevel! neq 0 (
    echo ERROR: pipeline analyse all failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 6 completed successfully

REM Step 7: Start application
echo.
echo [7/7] Running: docker compose up
docker compose up
if !errorlevel! neq 0 (
    echo ERROR: docker compose up failed with exit code !errorlevel!
    pause
    exit /b !errorlevel!
)
echo [✓] Step 7 completed successfully

echo.
echo ========================================
echo Pipeline is running!
echo Open http://localhost:5173 in your browser
echo ========================================

endlocal
