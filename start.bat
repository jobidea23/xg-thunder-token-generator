@echo off
echo Starting XG THUNDER Token Generator server...
echo Open http://localhost:8000/ in your browser
cd /d "%~dp0"
python dev_server.py
pause
