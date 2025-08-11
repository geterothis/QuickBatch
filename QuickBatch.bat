@echo off
title QuickBatch - Drag and Drop
echo.
echo ===========================================
echo   QUICKBATCH - DRAG AND DROP MODE
echo ===========================================
echo.

if not "%~1"=="" (
    if exist "%~1\*" (
        REM Directory Opus - normal launch
        cd /d "%~1"
        python "%~dp0QuickBatch.py"
    ) else (
        REM Drag and Drop mode
        for %%i in (%1) do cd /d "%%~dpi"
        python "%~dp0QuickBatch.py" %*
    )
) else (
    REM Normal launch without arguments
    python "%~dp0QuickBatch.py"
)

echo.
echo ===========================================
echo   OPERATION COMPLETED
echo ===========================================
pause