@echo off
REM Dong goi EZG - Excel thanh dang THU MUC (onedir) + icon.
REM Ket qua: dist\EZG-Excel\EZG-Excel.exe (mo nhanh, dung de tao installer).
cd /d "%~dp0"

echo === Tao icon ===
".venv\Scripts\python.exe" tools\make_icon.py

echo === Cai PyInstaller (neu chua co) ===
".venv\Scripts\python.exe" -m pip install pyinstaller

echo === Dong goi (onedir) ===
".venv\Scripts\python.exe" -m PyInstaller ^
  --name "EZG-Excel" ^
  --windowed ^
  --noconfirm ^
  --clean ^
  --icon assets\icon.ico ^
  --add-data "assets\icon.ico;assets" ^
  --paths src ^
  run.py

echo.
echo Hoan tat. Ung dung nam o: dist\EZG-Excel\EZG-Excel.exe
