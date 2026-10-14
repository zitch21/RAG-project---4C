@echo off
title RAG Simulator - CLI Mode
python main.py --cli
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo If 'python' was not recognized, retrying with py...
    py main.py --cli
)
if %ERRORLEVEL% NEQ 0 (
    pause
)
