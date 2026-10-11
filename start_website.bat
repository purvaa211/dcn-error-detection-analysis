@echo off
title DCN Error Detection System - Web Application
cd /d "%~dp0"
echo ====================================================================
echo Starting DCN Error Detection and Analysis Web Application...
echo The web page will automatically open in your browser shortly.
echo Keep this terminal window open while using the website.
echo ====================================================================
python run_web.py
pause
