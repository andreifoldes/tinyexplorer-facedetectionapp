@echo off
REM Setup script for dual Python environments in development mode (Windows)

echo Setting up dual Python environments for development...

REM Check if conda is available
conda --version >nul 2>&1
if errorlevel 1 (
    echo Error: conda is not installed or not in PATH
    echo Please install Anaconda or Miniconda first
    exit /b 1
)

REM Create YOLO environment
echo Creating YOLO environment...
conda env list | findstr "electron-python-yolo" >nul
if %errorlevel% == 0 (
    echo YOLO environment already exists, updating...
    conda env update -f environment-yolo.yml
) else (
    echo Creating new YOLO environment...
    conda env create -f environment-yolo.yml
)

REM Create RetinaFace environment
echo Creating RetinaFace environment...
conda env list | findstr "electron-python-retinaface" >nul
if %errorlevel% == 0 (
    echo RetinaFace environment already exists, updating...
    conda env update -f environment-retinaface.yml
) else (
    echo Creating new RetinaFace environment...
    conda env create -f environment-retinaface.yml
)

echo ✅ Dual environment setup complete!
echo.
echo Available environments:
echo - electron-python-yolo (for YOLO models)
echo - electron-python-retinaface (for RetinaFace models)
echo.
echo The app will automatically switch between environments based on model selection.