@echo off
REM GT23 Film Workflow - GUI Launcher
REM EN: Quick launcher for GUI application
REM CN: GUI 应用快速启动脚本

echo ========================================
echo    GT23 Film Workflow - GUI Launcher
echo    GT23 胶片工作流 - GUI 启动器
echo ========================================
echo.

REM Check if gt23gui environment exists
call conda info --envs | findstr /C:"gt23gui" >nul 2>&1
if errorlevel 1 (
    echo [!] Environment 'gt23gui' not found / 未找到环境 'gt23gui'
    echo [*] Creating environment... / 正在创建环境...
    call conda create -n gt23gui python=3.11 -y
    if errorlevel 1 (
        echo [ERROR] Failed to create environment / 创建环境失败
        pause
        exit /b 1
    )
    
    echo [*] Installing dependencies... / 正在安装依赖...
    call conda activate gt23gui
    pip install -r requirements-gui.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies / 安装依赖失败
        pause
        exit /b 1
    )
)

REM Activate environment and run
echo [*] Starting GUI... / 正在启动 GUI...
call conda activate gt23gui
pythonw main.py

if errorlevel 1 (
    echo.
    echo [ERROR] GUI failed to start / GUI 启动失败
    echo [*] Check the error messages above / 请查看上方错误信息
    pause
)
