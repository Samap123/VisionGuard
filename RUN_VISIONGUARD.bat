@echo off
title VisionGuard - AI Security Surveillance
color 0A

echo.
echo ============================================================
echo                  VISIONGUARD
echo             AI SECURITY SURVEILLANCE
echo ============================================================
echo.
echo Starting VisionGuard...
echo.

REM ============================================================
REM PROJECT ROOT
REM ============================================================

cd /d "%~dp0"

REM ============================================================
REM START BACKEND
REM ============================================================

echo [1/3] Starting VisionGuard AI Backend...
echo.

start "VisionGuard Backend" cmd /k "cd /d "%~dp0" && "%~dp0venv\Scripts\python.exe" -m uvicorn backend.main:app --reload"

REM ============================================================
REM WAIT FOR BACKEND
REM ============================================================

timeout /t 5 /nobreak >nul

REM ============================================================
REM START REACT DASHBOARD
REM ============================================================

echo [2/3] Starting React Dashboard...
echo.

start "VisionGuard Dashboard" cmd /k "cd /d "%~dp0react-dashboard" && npm run dev"

REM ============================================================
REM WAIT FOR REACT
REM ============================================================

timeout /t 5 /nobreak >nul

REM ============================================================
REM OPEN DASHBOARD
REM ============================================================

echo [3/3] Opening VisionGuard Dashboard...
echo.

start "" "http://localhost:5173"

echo.
echo ============================================================
echo          VISIONGUARD STARTED SUCCESSFULLY
echo ============================================================
echo.
echo Dashboard : http://localhost:5173
echo Backend   : http://127.0.0.1:8000
echo Swagger   : http://127.0.0.1:8000/docs
echo.
echo Keep the Backend and Dashboard windows running.
echo ============================================================
echo.

pause