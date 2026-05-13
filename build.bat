@echo off
:: build.bat — Compila Typoo a un ejecutable .exe con PyInstaller
:: Resultado: dist\Typoo.exe

setlocal
set PROJ=%~dp0
set ICO=%PROJ%assets\iconos\typoo-icon.ico

echo [1/3] Verificando PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller no encontrado. Instalando...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyInstaller.
        pause
        exit /b 1
    )
)

echo [2/3] Compilando Typoo...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name Typoo ^
    --icon "%ICO%" ^
    --add-data "%PROJ%assets;assets" ^
    --distpath "%PROJ%dist" ^
    --workpath "%PROJ%build_tmp" ^
    --specpath "%PROJ%build_tmp" ^
    --noconfirm ^
    "%PROJ%main.py"

if errorlevel 1 (
    echo ERROR: La compilacion fallo. Revisa los mensajes anteriores.
    pause
    exit /b 1
)

echo [3/3] Limpiando archivos temporales...
if exist "%PROJ%build_tmp" rmdir /s /q "%PROJ%build_tmp"

echo.
echo Compilacion completada: dist\Typoo.exe
pause
