@echo off
title RAG Visual Simulator
python main.py
if %ERRORLEVEL% NEQ 0 (
    py main.py
)
if %ERRORLEVEL% NEQ 0 (
    pause
)
