@echo off
echo Creating installer for Spotify Data Migration Tool...

:: Create output directory
mkdir installer_output

:: Compile the installer using Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\installer_script.iss

echo Installer created in installer_output folder!
echo Complete!
pause
