@echo off
chcp 65001 >nul
title EndStartL - 鹰角启动器极简一键启动

:: 检查是否具备管理员权限，若无则自动请求管理员权限提权执行
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [EndStartL] 游戏启动器需要管理员权限，正在请求提升运行...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo ========================================================
echo   [EndStartL] 正在执行鹰角启动器自动化: 拉起 -^> 识别 -^> 开始游戏
echo ========================================================
echo.

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

"%PYTHON_EXE%" main.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 游戏已成功启动，自动化程序将在 2 秒后自动退出...
    timeout /t 2 >nul
    exit
) else (
    echo.
    echo [错误] 启动遇到异常，请查看上方提示。按任意键关闭窗口...
    pause >nul
)
