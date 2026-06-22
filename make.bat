@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "EXE=dist\WOS-Calculator.exe"

echo [1/4] 실행 중인 프로그램 종료...
taskkill /IM "WOS-Calculator.exe" /F >nul 2>&1
if errorlevel 1 (
    echo      - 실행 중인 프로세스 없음
) else (
    echo      - 종료 완료
)

echo [2/4] git pull...
git pull
if errorlevel 1 (
    echo [오류] git pull 실패. 중단합니다.
    pause
    exit /b 1
)

echo [3/4] 빌드...
py -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo      - PyInstaller 미설치, 설치 중...
    py -m pip install pyinstaller
    if errorlevel 1 (
        echo [오류] PyInstaller 설치 실패. 중단합니다.
        pause
        exit /b 1
    )
)
py -m PyInstaller --onefile --windowed --name "WOS-Calculator" --icon "assets/icon.ico" --add-data "assets;assets" main.py --noconfirm
if errorlevel 1 (
    echo [오류] 빌드 실패. 중단합니다.
    pause
    exit /b 1
)

echo [4/4] 실행...
if not exist "%EXE%" (
    echo [오류] %EXE% 를 찾을 수 없습니다.
    pause
    exit /b 1
)
start "" "%EXE%"

echo 완료.
endlocal
