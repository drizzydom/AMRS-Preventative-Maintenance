@echo off
REM Enhanced copy static files script for AMRS Maintenance Tracker
REM This script copies required static files and GTK dependencies to the portable application

echo ======================================
echo AMRS Maintenance Tracker File Repair Tool
echo ======================================
echo.
echo This script will repair missing files in your portable application.
echo Specifically targeting the GTK/GObject issue: "cannot load library 'libgobject-2.0-0'"
echo.

set SOURCE_DIR=%~dp0
set TARGET_DIR=%SOURCE_DIR%dist\win-unpacked\resources
echo Source directory: %SOURCE_DIR%
echo Target directory: %TARGET_DIR%
echo.

REM First check if target directory exists
if not exist "%TARGET_DIR%" (
    echo ERROR: Target directory does not exist: %TARGET_DIR%
    echo Please run this script from the root of the AMRS-Preventative-Maintenance repository.
    echo.
    pause
    exit /b 1
)

REM === Copy static files ===
echo [1/5] Copying static files (CSS, JavaScript, images)...
if exist "%SOURCE_DIR%static" (
    xcopy /E /I /Y /Q "%SOURCE_DIR%static\*" "%TARGET_DIR%\static\"
    if %ERRORLEVEL% EQU 0 (
        echo     √ Static files copied successfully.
    ) else (
        echo     X Failed to copy static files. Error code: %ERRORLEVEL%
    )
) else (
    echo     ! Static directory not found at: %SOURCE_DIR%static
)

REM === Copy templates ===
echo [2/5] Copying template files...
if exist "%SOURCE_DIR%templates" (
    xcopy /E /I /Y /Q "%SOURCE_DIR%templates\*" "%TARGET_DIR%\templates\"
    if %ERRORLEVEL% EQU 0 (
        echo     √ Template files copied successfully.
    ) else (
        echo     X Failed to copy template files. Error code: %ERRORLEVEL%
    )
) else (
    echo     ! Templates directory not found at: %SOURCE_DIR%templates
)

REM === Copy Python modules ===
echo [3/5] Copying Python modules...
if exist "%SOURCE_DIR%modules" (
    xcopy /E /I /Y /Q "%SOURCE_DIR%modules\*" "%TARGET_DIR%\modules\"
    if %ERRORLEVEL% EQU 0 (
        echo     √ Module files copied successfully.
    ) else (
        echo     X Failed to copy module files. Error code: %ERRORLEVEL%
    )
) else (
    echo     ! Modules directory not found at: %SOURCE_DIR%modules
)

REM === Copy required core files ===
echo [4/5] Copying core Python files...
set CORE_FILES=app.py models.py config.py auto_migrate.py db_config.py cache_config.py flask-launcher.py wsgi.py api_endpoints.py

for %%f in (%CORE_FILES%) do (
    if exist "%SOURCE_DIR%%%f" (
        copy /Y "%SOURCE_DIR%%%f" "%TARGET_DIR%\%%f" > nul
        if %ERRORLEVEL% EQU 0 (
            echo     √ Copied %%f successfully.
        ) else (
            echo     X Failed to copy %%f. Error code: %ERRORLEVEL%
        )
    ) else (
        echo     ! Core file not found: %%f
    )
)

REM === Copy GTK dependencies ===
echo [5/5] Setting up GTK dependencies...

REM First check if we have GTK files locally
set GTK_SOURCE=%SOURCE_DIR%dependencies\gtk
set VENV_SITE_PACKAGES=%TARGET_DIR%\venv\Lib\site-packages
set VENV_DLL_DIR=%TARGET_DIR%\venv\DLLs

REM Create directories if they don't exist
if not exist "%VENV_DLL_DIR%" mkdir "%VENV_DLL_DIR%"
if not exist "%VENV_SITE_PACKAGES%" mkdir "%VENV_SITE_PACKAGES%"

REM Try to find weasyprint in the venv site-packages
set WEASYPRINT_DIR=%VENV_SITE_PACKAGES%\weasyprint
if not exist "%WEASYPRINT_DIR%" (
    echo     ! Weasyprint directory not found in venv, attempting to create it...
    mkdir "%WEASYPRINT_DIR%"
)

REM Try to find a local copy of GTK
if exist "%GTK_SOURCE%" (
    echo     √ Found local GTK files, copying them...
    xcopy /E /I /Y /Q "%GTK_SOURCE%\bin\*.dll" "%TARGET_DIR%\"
    xcopy /E /I /Y /Q "%GTK_SOURCE%\bin\*.dll" "%VENV_DLL_DIR%\"
    
    if exist "%GTK_SOURCE%\lib" (
        xcopy /E /I /Y /Q "%GTK_SOURCE%\lib\*" "%TARGET_DIR%\venv\Lib\"
    )
) else (
    echo     ! Local GTK files not found at %GTK_SOURCE%
    echo     ! Attempting to download missing DLLs...
    
    REM Create a powershell script to download the files
    echo $webrootUrl = "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2021-04-29/gtk3-runtime-3.24.29-2021-04-29-ts-win64.exe" > "%TEMP%\download_gtk.ps1"
    echo $destination = "$env:TEMP\gtk3-runtime.exe" >> "%TEMP%\download_gtk.ps1"
    echo Write-Host "Downloading GTK3 Runtime..." >> "%TEMP%\download_gtk.ps1"
    echo Invoke-WebRequest -Uri $webrootUrl -OutFile $destination >> "%TEMP%\download_gtk.ps1"
    echo Write-Host "Extracting files..." >> "%TEMP%\download_gtk.ps1"
    echo Start-Process -FilePath $destination -ArgumentList "/S", "/D=$env:TEMP\gtk3-runtime" -Wait >> "%TEMP%\download_gtk.ps1"
    echo Write-Host "Copying files..." >> "%TEMP%\download_gtk.ps1"
    echo Copy-Item -Path "$env:TEMP\gtk3-runtime\bin\*.dll" -Destination "%TARGET_DIR%" -Force >> "%TEMP%\download_gtk.ps1"
    echo Copy-Item -Path "$env:TEMP\gtk3-runtime\bin\libgobject-2.0-0.dll" -Destination "%TARGET_DIR%" -Force >> "%TEMP%\download_gtk.ps1"
    echo Copy-Item -Path "$env:TEMP\gtk3-runtime\bin\libglib-2.0-0.dll" -Destination "%TARGET_DIR%" -Force >> "%TEMP%\download_gtk.ps1"
    echo Write-Host "Done!" >> "%TEMP%\download_gtk.ps1"
    
    powershell -ExecutionPolicy Bypass -File "%TEMP%\download_gtk.ps1"
)

REM Create a symlink to the dll for easier access
echo Creating symbolic links for GTK libraries...
if exist "%TARGET_DIR%\libgobject-2.0-0.dll" (
    echo     √ Found libgobject-2.0-0.dll
) else (
    echo     ! libgobject-2.0-0.dll not found. Trying to locate it elsewhere...
    
    REM Try common locations for GTK
    set GTK_LOCATIONS=^
    C:\GTK\bin\libgobject-2.0-0.dll^
    C:\Program Files\GTK3-Runtime\bin\libgobject-2.0-0.dll^
    C:\Program Files (x86)\GTK3-Runtime\bin\libgobject-2.0-0.dll
    
    for %%g in (%GTK_LOCATIONS%) do (
        if exist "%%g" (
            echo     √ Found GTK at %%g, copying...
            copy /Y "%%g" "%TARGET_DIR%\" > nul
            echo     √ Copied libgobject-2.0-0.dll from %%g
            goto :found_gobject
        )
    )
    
    echo     ! GTK libraries not found in common locations.
    echo     ! You might need to install GTK3 Runtime manually.
    echo     ! Visit: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
)

:found_gobject

echo.
echo ======================================
echo Verification of copied files:
echo ======================================

REM Verify key files now exist
set CRITICAL_FILES=^
%TARGET_DIR%\static\css^
%TARGET_DIR%\static\js^
%TARGET_DIR%\templates^
%TARGET_DIR%\app.py^
%TARGET_DIR%\flask-launcher.py

set MISSING_FILES=0
for %%c in (%CRITICAL_FILES%) do (
    if not exist "%%c" (
        echo     X MISSING: %%c
        set /a MISSING_FILES+=1
    )
)

if %MISSING_FILES% EQU 0 (
    echo     √ All critical files are present!
) else (
    echo     ! %MISSING_FILES% critical files or directories are missing.
)

REM Verify GTK libraries
if exist "%TARGET_DIR%\libgobject-2.0-0.dll" (
    echo     √ libgobject-2.0-0.dll is present
) else (
    echo     X MISSING: libgobject-2.0-0.dll - This will cause the "cannot load library" error
)

echo.
echo ======================================
echo Repair process completed!
echo ======================================
echo.
echo If you still experience issues, please create a new build with the updated post_build_copy.py script.
echo.

pause