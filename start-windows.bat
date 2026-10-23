@echo off
rem Double-click this file to start creamy keyboard sounds.
rem Close the window (or press Ctrl+C in it) to stop.
cd /d "%~dp0"

if not exist .venv\installed (
    echo First run: setting things up, this takes a minute...
    py -3 -m venv .venv 2>nul || python -m venv .venv || goto :nopython
    .venv\Scripts\python -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto :failed
    echo ok> .venv\installed
)

.venv\Scripts\python -m creamy_keys %*
pause
exit /b

:nopython
echo.
echo Python is not installed. Get it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH" in the installer), then run this again.
pause
exit /b 1

:failed
echo.
echo Installing failed. Check your internet connection and run this again.
rmdir /s /q .venv
pause
exit /b 1
