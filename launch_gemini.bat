@echo off
TITLE Gemini CLI - PixelForge Workspace
echo ==========================================
echo    Gemini CLI 專業啟動器 (PixelForge)
echo ==========================================
echo [STATUS] 正在定位專案目錄...

:: 切換至專案資料夾
cd /d "C:\Users\User\Desktop\gemini cli"

echo [STATUS] 啟動 Gemini CLI 代理人系統...
echo [INFO] 輸入 'exit' 退出系統。
echo ------------------------------------------

:: 執行指令
npx @google/gemini-cli

:: 若發生錯誤，暫停視窗
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 啟動失敗！請檢查 Node.js 是否已安裝。
    pause
)
