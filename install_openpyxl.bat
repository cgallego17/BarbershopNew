@echo off
cd /d "%~dp0"
echo Instalando openpyxl para exportar a Excel...
echo.
if exist "venv\Scripts\python.exe" (
    echo Usando venv del proyecto...
    venv\Scripts\python.exe -m pip install openpyxl
) else if exist ".venv\Scripts\python.exe" (
    echo Usando .venv del proyecto...
    .venv\Scripts\python.exe -m pip install openpyxl
) else (
    echo Usando Python del sistema...
    python -m pip install openpyxl
)
echo.
echo Listo. Reinicie el servidor si esta corriendo.
echo Para iniciar: python manage.py runserver
echo (o: venv\Scripts\python.exe manage.py runserver si usa venv)
pause
