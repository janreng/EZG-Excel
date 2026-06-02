@echo off
REM Tao bo cai dat Ezcel-Setup.exe tu thu muc dist\Ezcel.
REM Yeu cau: da chay build.bat truoc do, va da cai Inno Setup.
cd /d "%~dp0"

if not exist "dist\Ezcel\Ezcel.exe" (
  echo [LOI] Chua co dist\Ezcel\Ezcel.exe. Hay chay build.bat truoc.
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
