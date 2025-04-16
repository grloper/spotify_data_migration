# Release Guide for Spotify Data Migration

This guide explains how to publish new releases of the Spotify Data Migration tool on GitHub.

## Creating a Release

1. **Build the executable and installer**
   - Run the PyInstaller build script
   - Create the installer with Inno Setup
   - Test the installer on a clean system if possible

2. **Create a GitHub Release**
   - Go to your repository on GitHub
   - Click on "Releases" in the right sidebar
   - Click "Create a new release" or "Draft a new release"
   - Set the tag version (e.g., `v1.0.0`)
   - Add a release title (e.g., "Spotify Data Migration v1.0.0")
   - Write release notes describing features and changes
   - Upload the installer executable from `installer_output` folder
   - Mark as "pre-release" if still testing
   - Click "Publish release"

## Release Notes Template

