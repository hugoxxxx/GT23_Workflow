@echo off
setlocal EnableExtensions
chcp 65001 >nul
REM GT23 Film Workflow - GUI Launcher
REM EN: Quick launcher for GUI application
REM CN: GUI 应用快速启动脚本

echo ========================================
echo    GT23 Film Workflow - GUI Launcher
echo    GT23 胶片工作流 - GUI 启动器
echo ========================================
echo.

REM --- [NEW] EN: Check for local venv first / CN: 优先检查本地 venv ---
if exist "venv\Scripts\python.exe" (
    echo [*] Found local venv, checking dependencies... / 发现本地 venv，检查并补全依赖库...
    ".\venv\Scripts\pip.exe" install -r requirements-gui.txt --quiet
    echo [*] Starting GUI... / 正在启动 GUI...
    ".\venv\Scripts\pythonw.exe" main.py
    if errorlevel 1 (
        echo [ERROR] GUI failed to start using venv.
        echo [*] Trying with console for debugging...
        ".\venv\Scripts\python.exe" main.py
        pause
    )
    exit /b 0
)

REM --- [EXISTING] EN: Fallback to Conda / CN: 回退到 Conda ---
REM Check if gt23 environment exists
call conda info --envs | findstr /C:"gt23" >nul 2>&1
if errorlevel 1 (
    echo [!] Environment 'gt23' not found / 未找到环境 'gt23'
    echo [*] Creating environment... / 正在创建环境...
    call conda create -n gt23 python=3.11 -y
    if errorlevel 1 (
        echo [ERROR] Failed to create environment / 创建环境失败
        echo [*] Please try running manually: .\venv\Scripts\pythonw.exe main.py
        pause
        exit /b 1
    )
    
    echo [*] Installing dependencies... / 正在安装依赖...
    call conda activate gt23
    pip install -r requirements-gui.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies / 安装依赖失败
        pause
        exit /b 1
    )
)

REM Activate environment and run
echo [*] Starting GUI... / 正在启动 GUI...
call conda activate gt23
pythonw main.py

if errorlevel 1 (
    echo.
    echo [ERROR] GUI failed to start / GUI 启动失败
    echo [*] Check the error messages above / 请查看上方错误信息
    pause
)
