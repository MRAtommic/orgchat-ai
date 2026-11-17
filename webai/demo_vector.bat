@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== สาธิตเวกเตอร์ (ใช้ข้อมูลชั่วคราว ไม่แตะข้อมูลจริง) =====
if "%~1"=="" (
  python tools\demo_embeddings.py
) else (
  python tools\demo_embeddings.py %*
)
echo.
pause
