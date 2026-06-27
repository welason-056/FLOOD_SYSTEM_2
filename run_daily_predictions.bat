@echo off
echo ========================================
echo FloodGuard Daily Predictions
echo Date: %date%
echo Time: %time%
echo ========================================

cd /d C:\Users\DJ WEHALU\OneDrive\Desktop\PROJECT\flood_system

echo Running AI predictions for all 30 regions...
echo.

C:\Users\DJ WEHALU\OneDrive\Desktop\PROJECT\.venv\Scripts\python.exe manage.py daily_predictions

echo.
echo ========================================
echo Daily predictions completed at %time%
echo ========================================
pause