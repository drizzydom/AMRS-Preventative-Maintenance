@echo off
REM Batch file to run offline token authentication tests

echo ==================================================
echo Offline Token Authentication Testing Script
echo ==================================================
echo.

echo Available test options:
echo 1. Run offline app with token authentication
echo 2. Run full end-to-end token authentication test
echo 3. Run manual token testing tool
echo 4. Run token API endpoint tests
echo 5. Run token security tests
echo 6. Exit
echo.

:menu
set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto run_e2e
if "%choice%"=="3" goto run_manual
if "%choice%"=="4" goto run_api
if "%choice%"=="5" goto run_security
if "%choice%"=="6" goto exit

echo Invalid choice. Please try again.
goto menu

:run_app
echo.
echo Running offline app with token authentication...
echo.
python run_offline_token_test.py --debug
goto end

:run_e2e
echo.
echo Running end-to-end token authentication test...
echo.
python test_offline_auth.py e2e --username admin --password admin
goto end

:run_manual
echo.
echo Running manual token testing tool...
echo.
python test_token_manual.py
goto end

:run_api
echo.
echo Running token API endpoint tests...
echo.
python test_offline_auth.py api --app-url http://localhost:5000
goto end

:run_security
echo.
echo Running token security tests...
echo.
python test_offline_auth.py security --username admin
goto end

:exit
echo.
echo Exiting...
goto :eof

:end
echo.
echo Press any key to return to menu...
pause > nul
cls
echo ==================================================
echo Offline Token Authentication Testing Script
echo ==================================================
echo.
echo Available test options:
echo 1. Run offline app with token authentication
echo 2. Run full end-to-end token authentication test
echo 3. Run manual token testing tool
echo 4. Run token API endpoint tests
echo 5. Run token security tests
echo 6. Exit
echo.
goto menu
