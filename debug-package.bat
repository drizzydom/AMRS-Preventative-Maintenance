@echo off
echo ===================================================
echo In-depth package debugging
echo ===================================================

if not exist dist\win-unpacked (
  echo Build output directory not found.
  echo Please run 'npm run dist' first.
  exit /b 1
)

echo Checking resources directory structure:
echo -------------------------------------
dir /b dist\win-unpacked\resources > resources.txt
type resources.txt
echo.

echo Checking for app.py:
echo -------------------------------------
if exist dist\win-unpacked\resources\app.py (
  echo app.py: FOUND
  echo Content:
  type dist\win-unpacked\resources\app.py | find /v /n "" | findstr /r "^\[[0-9]*\]" | findstr /r "\[[1-5]\]"
) else (
  echo app.py: MISSING
  echo This file should be in resources directory.
  
  echo Searching for app.py in package:
  findstr /s /i /m "app.py" dist\win-unpacked\resources\*
)
echo.

echo Checking for static and templates directories:
echo -------------------------------------
if exist dist\win-unpacked\resources\static (
  echo static directory: FOUND
  dir /b dist\win-unpacked\resources\static
) else (
  echo static directory: MISSING
)

if exist dist\win-unpacked\resources\templates (
  echo templates directory: FOUND
  dir /b dist\win-unpacked\resources\templates
) else (
  echo templates directory: MISSING
)
echo.

echo Checking Python environment:
echo -------------------------------------
if exist dist\win-unpacked\resources\venv\Scripts\python.exe (
  echo Python executable: FOUND
  dist\win-unpacked\resources\venv\Scripts\python.exe -V
  
  echo Test Flask import:
  dist\win-unpacked\resources\venv\Scripts\python.exe -c "import flask; print('Flask version:', flask.__version__)"
  
  echo Testing full application launch:
  echo -------------------------------------
  echo Running app.py directly to check for errors:
  cd dist\win-unpacked\resources
  ..\resources\venv\Scripts\python.exe app.py --test > python_test.log 2>&1
  echo Results saved to: dist\win-unpacked\resources\python_test.log
  cd ..\..\..
) else (
  echo Python executable: MISSING
)

echo ===================================================
echo Debug completed. Check output for issues.
echo ===================================================
pause
