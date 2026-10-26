@echo off
REM Builds a single-folder Windows app in dist\ReliefDBExplorer (needs: pip install pyinstaller)
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --windowed --name ReliefDBExplorer main.py
echo.
echo Done. Run dist\ReliefDBExplorer\ReliefDBExplorer.exe
echo (The Firebird client, fbclient.dll, still has to be installed on the machine, or copied next to the .exe.)
