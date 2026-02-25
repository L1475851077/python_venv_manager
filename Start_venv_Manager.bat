@echo off
chcp 65001 >nul
title Python 虚拟环境管家启动器

:: ==========================================
:: 1. 自动获取管理员权限 (UAC 提权)
:: ==========================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 正在请求管理员权限以检索系统目录...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    :: 将工作目录切换到 bat 所在的当前路径
    pushd "%CD%"
    CD /D "%~dp0"

:: ==========================================
:: 2. 启动环境管家
:: ==========================================
echo =========================================
echo       Python 虚拟环境管家启动中...
echo =========================================
echo.
echo 注意：请不要关闭此黑色窗口！
echo 正在自动为您打开浏览器...
echo.

:: 调用 Python 运行脚本 (请确保你的脚本文件名一致)
python venv_web_manager.py

:: 如果程序异常退出，暂停窗口以便查看报错信息
pause