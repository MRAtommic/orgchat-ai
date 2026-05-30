@echo off
title OrgChat AI - One Click Startup
setlocal enabledelayedexpansion

echo ==================================================
echo   OrgChat AI : One-Click Installer ^& Runner
echo ==================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ไม่พบ Python ในเครื่องนี้!
    echo กรุณาติดตั้งจาก https://www.python.org/ และติ๊ก 'Add Python to PATH'
    pause
    exit /b 1
)

:: 2. Move to webai directory
cd /d "%~dp0\webai"

:: 3. Setup Virtual Environment
if not exist ".venv" (
    echo [INFO] กำลังสร้างสภาพแวดล้อมจำลอง (Virtual Environment)...
    python -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] สร้าง .venv ไม่สำเร็จ!
        pause
        exit /b 1
    )
)

:: 4. Activate and Install Requirements
echo [INFO] กำลังตรวจสอบและติดตั้ง dependencies (อาจใช้เวลาสักครู่)...
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

:: 5. Start Server
echo.
echo [SUCCESS] ทุกอย่างพร้อมแล้ว!
echo [INFO] กำลังเริ่ม Server ที่ http://localhost:5005
echo.

:: Start browser in background after 3 seconds
start /b timeout /t 3 /nobreak >nul && start http://localhost:5005

:: Run App
python app_server.py

pause
