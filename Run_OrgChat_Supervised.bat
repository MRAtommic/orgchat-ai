@echo off
rem ============================================================
rem  OrgChat AI - supervised runner
rem  Starts app_server.py and restarts it automatically if it stops or crashes.
rem  Close this window (or press Ctrl+C twice) to stop the server for good.
rem  Do NOT run it while another copy of the server is already running (port 5005 would be busy).
rem ============================================================
title OrgChat AI - Supervised Server
cd /d "%~dp0webai"
if not exist logs mkdir logs

:loop
rem refuse to start a second copy: wait while something already listens on the app port
set "PORT_TO_CHECK=5005"
for /f "tokens=2 delims==" %%p in ('findstr /b /c:"PORT=" .env 2^>nul') do set "PORT_TO_CHECK=%%p"
netstat -ano | findstr /r /c:":%PORT_TO_CHECK% .*LISTENING" >nul
if %errorlevel%==0 (
  echo [%date% %time%] port %PORT_TO_CHECK% is already in use - waiting 20s... >> logs\supervisor.log
  echo Port %PORT_TO_CHECK% already in use - another server is running. Waiting...
  timeout /t 20 /nobreak >nul
  goto loop
)

echo [%date% %time%] starting app_server.py >> logs\supervisor.log
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" app_server.py
) else (
  python app_server.py
)
echo [%date% %time%] app_server.py exited with code %errorlevel% - restarting in 5s >> logs\supervisor.log
echo Server stopped (code %errorlevel%). Restarting in 5 seconds... (Ctrl+C to quit)
timeout /t 5 /nobreak >nul
goto loop
