@echo off
echo Initializing Database...
set FLASK_APP=d:/Project/FY/tga/run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
echo Starting Application...
python run.py
