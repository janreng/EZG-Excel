@echo off
REM Chay ung dung Ezcel bang Python trong moi truong ao.
cd /d "%~dp0"
".venv\Scripts\pythonw.exe" run.py %*
