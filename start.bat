@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Mebel360 Hisobchi Server

echo Mebel360 - 2D-PLACE bog'langan dastur ishga tushmoqda...

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo.
  echo XATO: Python topilmadi.
  echo Python o'rnatib, "Add python.exe to PATH" belgisini qo'ying.
  pause
  exit /b 1
)

%PY% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Flask o'rnatilmoqda...
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Flask o'rnatilmadi. Internetni tekshiring.
    pause
    exit /b 1
  )
)

%PY% server_app.py
pause
