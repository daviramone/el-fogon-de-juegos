@echo off
title El Fogón del Juego - Servidor

echo Navegando a la carpeta del proyecto...

REM ¡¡¡IMPORTANTE!!! Asegurate de que esta ruta sea la correcta para tu proyecto.
cd /d "C:\Users\Davi\Desktop\python\clue\Juegos terminados\PlataformaDeJuegos"

echo.
echo ======================================================
echo     Iniciando El Fogon del Juego...
echo ======================================================
echo.
echo Si todo va bien, abri tu navegador en: http://127.0.0.1:5000
echo.
echo Para cerrar el servidor, cerra esta ventana o presiona CTRL+C.
echo.

python servidor.py

pause