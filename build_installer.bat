@echo off
REM Tao bo cai dat EZG-Excel-Setup.exe tu thu muc dist\EZG-Excel.
REM Yeu cau: da chay build.bat truoc do, va da cai Inno Setup.
cd /d "%~dp0"

if not exist "dist\EZG-Excel\EZG-Excel.exe" (
  echo [LOI] Chua co dist\EZG-Excel\EZG-Excel.exe. Hay chay build.bat truoc.
  exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo [LOI] Khong tim thay Inno Setup. Cai bang: winget install JRSoftware.InnoSetup
  exit /b 1
)

"%ISCC%" installer.iss
echo.
echo Hoan tat. Bo cai dat nam o thu muc: installer\
