@echo off
title OrgChat - AI Chatbot
echo.
echo ============================================
echo   OrgChat - AI Chatbot for Organizations
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ไม่พบ Python กรุณาติดตั้ง Python 3.11+
    pause
    exit /b 1
)

:: Set API key from environment if not already set
if not defined GEMINI_API_KEY (
    echo [INFO] ไม่พบ GEMINI_API_KEY ในระบบ
    echo        สามารถใส่ได้ในหน้าเว็บหลังจากเปิด
    echo.
)

echo [OK] กำลังเริ่มต้น server...
echo [OK] เปิดเบราว์เซอร์ที่ http://localhost:5000
echo.
echo กด Ctrl+C เพื่อหยุด server
echo.

:: Open browser after short delay
start /b timeout /t 2 /nobreak >nul && start http://localhost:5000

:: Start Flask
python app.py

pause
