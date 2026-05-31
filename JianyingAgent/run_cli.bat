@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -B -m apps %*
    goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -B -m apps %*
    goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -B -m apps %*
    goto :end
)

echo [ERROR] No Python runtime was found.
echo Portable package should include .venv\Scripts\python.exe.
pause

:end
endlocal
