@echo off
setlocal enabledelayedexpansion

REM Set your Python environment paths
SET CONDA_ENV=myenv
SET METAVISION_SDK_PATH=D:\Prophesee\Prophesee

REM Verify Metavision paths exist
if not exist "%METAVISION_SDK_PATH%" (
    echo Error: Metavision SDK path not found: %METAVISION_SDK_PATH%
    pause
    exit /b 1
)

REM Activate conda environment
call conda activate %CONDA_ENV%

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del /f /q main.spec

REM List all DLL files to copy
echo Checking Metavision DLL locations...
set "DLL_PATHS="
for %%d in (lib lib64 bin x64) do (
    if exist "%METAVISION_SDK_PATH%\%%d" (
        if exist "%METAVISION_SDK_PATH%\%%d\*.dll" (
            set "DLL_PATHS=!DLL_PATHS! --add-data "%METAVISION_SDK_PATH%\%%d\*.dll;.""
        )
    )
)

REM Build the executable
echo Building executable...
pyinstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --paths "%METAVISION_SDK_PATH%\lib\python3\site-packages" ^
    %DLL_PATHS% ^
    --hidden-import metavision_core ^
    --hidden-import metavision_base ^
    --hidden-import metavision_sdk_ui ^
    --hidden-import metavision_core ^
    --hidden-import metavision_sdk_core ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import pandas ^
    main.py

REM Check if build was successful
if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

REM Copy DLL files to dist directory
echo Copying DLLs to dist directory...
if not exist "dist" mkdir dist
for %%d in (lib lib64 bin x64) do (
    if exist "%METAVISION_SDK_PATH%\%%d" (
        if exist "%METAVISION_SDK_PATH%\%%d\*.dll" (
            echo Copying DLLs from %%d...
            xcopy /y "%METAVISION_SDK_PATH%\%%d\*.dll" "dist\"
        )
    )
)

REM Create run script in dist folder
echo Creating run script...
(
echo @echo off
echo setlocal enabledelayedexpansion
echo.
echo SET METAVISION_SDK_PATH=%METAVISION_SDK_PATH%
echo SET PATH=%%CD%%;%%PATH%%
echo.
echo main.exe
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo Error running main.exe
echo     type error.log 2^>^&1
echo     pause
echo ^)
) > dist\run_app.bat

echo Build completed successfully!
echo Executable is located in the dist folder
pause