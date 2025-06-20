@echo off
echo ========================================
echo   CROSSWMS - Instalador de Dependencias
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Baixe e instale Python em: https://www.python.org/downloads/
    echo Lembre-se de marcar "Add Python to PATH" durante a instalacao
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Instalando dependencias...
echo.

echo [1/3] Instalando Selenium...
pip install selenium
if %errorlevel% neq 0 (
    echo ERRO ao instalar Selenium
    pause
    exit /b 1
)

echo [2/3] Instalando Watchdog...
pip install watchdog
if %errorlevel% neq 0 (
    echo ERRO ao instalar Watchdog
    pause
    exit /b 1
)

echo [3/3] Instalando Requests...
pip install requests
if %errorlevel% neq 0 (
    echo ERRO ao instalar Requests
    pause
    exit /b 1
)

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Proximos passos:
echo 1. Baixe o ChromeDriver em: https://chromedriver.chromium.org/
echo 2. Coloque chromedriver.exe na mesma pasta deste script
echo 3. Execute: python automacao_crosswms.py
echo.
pause