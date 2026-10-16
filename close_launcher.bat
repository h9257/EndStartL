@echo off
chcp 65001 >nul
title EndStartL - 关闭鹰角启动器

:: 1. 检查是否具备管理员权限，若无则自动请求 UAC 提权并运行
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ========================================================
    echo   [EndStartL] 关闭鹰角启动器需要管理员权限，正在请求提权...
    echo ========================================================
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: 2. 切换到脚本所在目录
cd /d "%~dp0"

echo ========================================================
echo   [EndStartL] 正在查找并关闭鹰角启动器 (Games.exe / Launcher.exe)...
echo ========================================================
echo.

:: 3. 检查是否有相关进程正在运行
set HAS_PROCESS=0
tasklist /FI "IMAGENAME eq Games.exe" 2>nul | find /I /N "Games.exe" >nul
if %ERRORLEVEL% EQU 0 set HAS_PROCESS=1

tasklist /FI "IMAGENAME eq Launcher.exe" 2>nul | find /I /N "Launcher.exe" >nul
if %ERRORLEVEL% EQU 0 set HAS_PROCESS=1

if %HAS_PROCESS% EQU 0 (
    echo [提示] 鹰角启动器当前未在运行。
    timeout /t 2 >nul
    exit /b 0
)

:: 4. 强制终止相关进程
taskkill /F /T /IM Games.exe >nul 2>&1
taskkill /F /T /IM Launcher.exe >nul 2>&1
powershell -NoProfile -Command "Stop-Process -Name Games,Launcher -Force -ErrorAction SilentlyContinue" >nul 2>&1

:: 5. 严格验证是否成功关闭
timeout /t 1 >nul
tasklist /FI "IMAGENAME eq Games.exe" 2>nul | find /I /N "Games.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [警告] 首次终止未彻底，正在按 PID 强制清理...
    for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq Games.exe" /NH 2^^^>nul') do (
        taskkill /F /PID %%i >nul 2>&1
        powershell -NoProfile -Command "Stop-Process -Id %%i -Force -ErrorAction SilentlyContinue" >nul 2>&1
    )
)

:: 再次验证
tasklist /FI "IMAGENAME eq Games.exe" 2>nul | find /I /N "Games.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ❌ 未能彻底关闭 Games.exe 进程！
    echo 可能原因: 进程被安全软件或反作弊驱动深度保护。
    echo 请尝试在任务管理器中右键结束任务。
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ 鹰角启动器 (Games.exe / Launcher.exe) 已彻底成功关闭！
    timeout /t 2 >nul
    exit /b 0
)
