@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -B -m webui --open %*
    goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -B -m webui --open %*
    goto :end
)

echo [ERROR] No Python launcher was found.
echo Please install Python or add it to PATH.
pause

:end
endlocal
