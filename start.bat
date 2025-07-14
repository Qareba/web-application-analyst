@echo off
echo Starting Parser and Bot...
echo.

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Запускаем главный файл
python main.py

pause 