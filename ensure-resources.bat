@echo off
echo ===================================================
echo Ensuring resources are available after packaging
echo ===================================================

set DIST_DIR=dist\win-unpacked\resources
if not exist %DIST_DIR% (
  echo Build not found. Run 'npm run dist' first.
  exit /b 1
)

echo Checking for required files...

if not exist %DIST_DIR%\app.py (
  echo app.py not found in resources - copying manually
  copy app.py %DIST_DIR%\app.py
) else (
  echo app.py found
)

if not exist %DIST_DIR%\static (
  echo static directory not found - copying manually
  if exist static mkdir %DIST_DIR%\static
  xcopy /E /I /Y static %DIST_DIR%\static
) else (
  echo static directory found
)

if not exist %DIST_DIR%\templates (
  echo templates directory not found - copying manually
  if exist templates mkdir %DIST_DIR%\templates
  xcopy /E /I /Y templates %DIST_DIR%\templates
) else (
  echo templates directory found
)

if not exist %DIST_DIR%\modules (
  echo modules directory not found - copying manually
  if exist modules mkdir %DIST_DIR%\modules
  xcopy /E /I /Y modules %DIST_DIR%\modules
) else (
  echo modules directory found
)

echo ===================================================
echo Resources verified. You can now run your application.
echo ===================================================
pause
