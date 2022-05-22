@echo off

if "%~1" == "" goto :build
if "%~1" == "-wsl" set wsl=1

:build

echo Building client

if "%wsl%" == "1" (
    wsl.exe /bin/bash -ic "yarn build"
) else (
    yarn build || goto :error
)

echo Ensuring Python dependencies are installed

pip3 install -r requirements.txt || goto :error

echo Building server

python3 -m PyInstaller --noconfirm --workpath .\server_build --distpath .\package server\kaiheila_streamkit.py || goto :error

echo Packaging

robocopy .\dist .\package\kaiheila_streamkit\static /e
copy .\server\config.default.json .\package\kaiheila_streamkit\config.json

echo Built to .\package.

goto :EOF

:error
echo Failed with error #%errorlevel%.
exit /b %errorlevel%