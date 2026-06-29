@echo off
:: 设置字符集为 UTF-8，防止控制台中文乱码
chcp 65001 > nul
title 车辆管理系统 - 一键同步至 GitHub

echo ======================================================
echo          车辆管理系统 一键同步工具 (GitHub)
echo ======================================================
echo.

:: 1. 检查是否有需要提交的文件
git status -s > temp_status.txt
set /p STATUS_OUT=<temp_status.txt
del temp_status.txt

if "%STATUS_OUT%"=="" (
    echo [提示] 您的本地代码没有任何改动，无需同步！
    goto end
)

echo [1/4] 检测到代码有以下改动：
git status -s
echo.

:: 2. 引导输入提交说明
set "COMMIT_MSG=Auto sync update: %date% %time%"
set /p USER_MSG="[2/4] 请输入本次修改的简单说明 (直接回车将使用默认描述): "
if not "%USER_MSG%"=="" (
    set "COMMIT_MSG=%USER_MSG%"
)

echo.
echo [3/4] 正在保存本地更改并创建版本...
git add .
git commit -m "%COMMIT_MSG%"

echo.
echo [4/4] 正在准备推送至 GitHub...

:: 3. 检测本地代理并配置 (防止443超时错误)
netstat -ano | findstr 127.0.0.1:7890 > nul
if %errorlevel% equ 0 (
    echo [网络安全提示] 检测到本地已开启 7890 代理端口，正在临时开启 Git 代理加速通道...
    git config --global http.proxy http://127.0.0.1:7890
    git config --global https.proxy http://127.0.0.1:7890
) else (
    echo [网络提示] 未检测到本地 7890 代理，将尝试使用直连模式推送...
)

echo 正在传输代码，请稍候...
git push -u origin main

:: 4. 无论成功与否，还原代理设置防止影响其他局域网 Git 使用
if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo [成功] 代码已成功推送到您的 GitHub 个人私有仓库！
    echo ======================================================
) else (
    echo.
    echo ======================================================
    echo [失败] 推送时遇到了网络问题，请检查代理软件是否正常工作。
    echo ======================================================
)

echo 正在清理临时代理配置...
git config --global --unset http.proxy
git config --global --unset https.proxy
echo 代理配置已恢复默认。

:end
echo.
echo 按任意键退出本窗口...
pause > nul
