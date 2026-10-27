@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Preparando el entorno virtual...
    py -3 -m venv .venv 2>nul || python -m venv .venv
)

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error

echo Preparando base de datos y datos demostrativos...
".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 goto error
".venv\Scripts\python.exe" manage.py crear_reservas_demo --reset-demo
if errorlevel 1 goto error

echo Abriendo la aplicacion en http://127.0.0.1:8000/
start "" "http://127.0.0.1:8000/"
".venv\Scripts\python.exe" manage.py runserver
goto end

:error
echo.
echo No fue posible preparar la aplicacion. Revisa el mensaje anterior.
pause

:end
endlocal
