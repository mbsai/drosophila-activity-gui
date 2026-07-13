@echo off
REM Build the Windows desktop app locally. Run this from the repo root on a
REM Windows 10/11 machine that has Python 3.11 installed:
REM     windows\build_windows.bat
setlocal

echo === Creating virtual environment ===
python -m venv .venv || goto :error
call .venv\Scripts\activate.bat || goto :error

echo === Installing dependencies ===
python -m pip install --upgrade pip || goto :error
pip install -r requirements.txt pyinstaller || goto :error

echo === Building executable (this takes a few minutes) ===
pyinstaller DrosophilaActivityGUI.spec --noconfirm || goto :error

echo.
echo === Done ===
echo Portable app: dist\DrosophilaActivityGUI\DrosophilaActivityGUI.exe
echo Double-click that .exe to launch the app in your browser.
echo.
echo (Optional) To build an installer, install Inno Setup and run:
echo     iscc windows\installer.iss
goto :eof

:error
echo.
echo BUILD FAILED. See the messages above.
exit /b 1
