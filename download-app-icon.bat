@echo off
echo Downloading app icon...

mkdir electron_app\icons 2>nul

curl -o electron_app\icons\app.ico https://raw.githubusercontent.com/electron-userland/electron-builder/master/test/fixtures/app-executable-deps/build/icon.ico

echo Icon downloaded. You can now run: npm run dist
pause
