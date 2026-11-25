@echo off
call venv\Scripts\activate.bat
start "" http://127.0.0.1:8000/docs
uvicorn backend.main:app --reload
pause