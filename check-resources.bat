@echo off
echo ===================================================
echo Checking packaging of resources
echo ===================================================

set APP_DIR=dist\win-unpacked\resources\app

echo Checking Python files...
if exist "%APP_DIR%\app.py" (
  echo app.py: Found
) else (
  echo app.py: MISSING
)

echo Checking venv...
if exist "dist\win-unpacked\resources\venv\Scripts\python.exe" (
  echo Python executable: Found
) else (
  echo Python executable: MISSING
)

echo Checking required directories...
if exist "%APP_DIR%\static" (
  echo static directory: Found
) else (
  echo static directory: MISSING
)

if exist "%APP_DIR%\templates" (
  echo templates directory: Found
) else (
  echo templates directory: MISSING
)

echo ===================================================
echo Python Environment Diagnosis
echo ===================================================

set PYTHON=dist\win-unpacked\resources\venv\Scripts\python.exe

if exist "%PYTHON%" (
  echo Testing Python...
  "%PYTHON%" -V
  echo.
  echo Testing Flask import...
  "%PYTHON%" -c "import flask; print('Flask version:', flask.__version__)"
) else (
  echo Cannot test Python because executable is missing
)

echo ===================================================
echo App.py content (first 20 lines)
echo ===================================================
if exist "%APP_DIR%\app.py" (
  type "%APP_DIR%\app.py" | find /v /n "" | find " [1]" > nul
  if not errorlevel 1 (
    for /f "skip=1 tokens=1* delims=]" %%a in ('type "%APP_DIR%\app.py" ^| find /v /n ""') do (
      if %%a leq 20 echo %%b
    )
  )
) else (
  echo Cannot show app.py because file is missing
)

echo ===================================================
echo Directory structure
echo ===================================================
if exist "dist\win-unpacked\resources" (
  dir /s /b "dist\win-unpacked\resources" > resources-dir.txt
  echo Directory listing saved to resources-dir.txt
) else (
  echo Resources directory not found
)

echo ===================================================
echo DONE - Check output for issues
echo ===================================================
pause
