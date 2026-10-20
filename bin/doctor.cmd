@echo off
rem Windows wrapper for bin/doctor.py
set DIR=%~dp0
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 "%DIR%doctor.py" %*
    exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%DIR%doctor.py" %*
    exit /b %ERRORLEVEL%
)
echo bin\doctor.cmd: no Python interpreter on PATH (py or python). >&2
exit /b 1
