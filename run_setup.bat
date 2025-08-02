@echo off
echo Setting up UAT Tracker...
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Running setup script...
python setup.py

echo.
echo Setup complete! You can now run:
echo python manage.py runserver
echo.
pause