@echo off
setlocal
cd /d "%~dp0"

set "CF_TOKEN=eyJhIjoiYTY1YmRjOTgwYjEzMmM2MTI5NTAyMDk5OTU0ZGFjMTMiLCJ0IjoiMzI2MDlhM2UtYzJiYi00Nzk4LWEyOTEtMTUzNmQ3ODNlNGM4IiwicyI6IlpqaG1NRGRpWmpFdE1qTTVaUzAwTVRKbExXSmtNbVl0TVdVMFpEUm1aVGxoTmpZMCJ9"
set "CLOUDFLARED_BIN=cloudflared.exe"

where cloudflared.exe >nul 2>&1
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe" (
        set "CLOUDFLARED_BIN=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
    )
)

echo ========================================================
echo    Iniciando Plataforma SalesIA Enterprise
echo ========================================================
echo.
echo 0. Sincronizando migraciones de base de datos...
call cmd /c "cd /d ""%~dp0backend"" && (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && alembic upgrade head"
echo.
echo 1. Levantando servidor Backend (FastAPI / Uvicorn en http://127.0.0.1:8000)...
start "SalesIA Backend (FastAPI)" cmd /k "cd /d ""%~dp0"" && (if exist backend\.venv\Scripts\activate.bat call backend\.venv\Scripts\activate.bat) && (if exist backend\venv\Scripts\activate.bat call backend\venv\Scripts\activate.bat) && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && python scripts\dev_backend.py"

timeout /t 2 /nobreak >nul

echo 2. Levantando servidor Frontend (React / Vite en http://127.0.0.1:5234)...
start "SalesIA Frontend (Vite)" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --port 5234"

timeout /t 2 /nobreak >nul

echo 3. Levantando procesador de trabajos y correos...
start "SalesIA Worker" cmd /k "cd /d ""%~dp0backend"" && (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && (if exist ..\venv\Scripts\activate.bat call ..\venv\Scripts\activate.bat) && set ""PYTHONPATH=src"" && python -m salesia.manage worker"

timeout /t 2 /nobreak >nul

echo 4. Levantando Tunel Cloudflare (Puerto 5234)...
start "SalesIA Cloudflare Tunnel" cmd /k "echo ======================================================== && echo    SalesIA - Tunel Cloudflare (Frontend en puerto 5234) && echo ======================================================== && "%CLOUDFLARED_BIN%" tunnel run --token %CF_TOKEN%"

echo.
echo ========================================================
echo    Servidores iniciados en terminales independientes:
echo    - Backend API: http://127.0.0.1:8000
echo    - Documentacion Swagger: http://127.0.0.1:8000/docs
echo    - Frontend Web Local: http://127.0.0.1:5234
echo    - Procesador de trabajos y correos: Activo
echo    - Tunel Cloudflare: Activo hacia http://localhost:5234
echo ========================================================
echo.
pause