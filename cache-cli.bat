@echo off
rem Windows equivalent of the ./cache-cli wrapper.
rem Prefers the project's virtualenv Python when it exists.
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0cli.py" %*
) else (
    python "%~dp0cli.py" %*
)
