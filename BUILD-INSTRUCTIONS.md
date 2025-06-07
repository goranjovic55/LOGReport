# LOGReport Build Instructions

## Requirements
- Python 3.10+
- Windows OS (for .exe build)
- Administrator privileges

## Step-by-Step Build Process
1. **Install dependencies**:
   ```cmd
   pip install -r requirements-narrow.txt
   ```

2. **Set up environment**:
   ```cmd
   mkdir assets
   ```
   Place your application icon at `assets\logo.ico`

3. **Run build script**:
   ```cmd
   build.bat
   ```

4. **Locate executable**:  
   The built executable will be at:  
   `dist\LOGReporter.exe`

## Customization Options
- **Icon**: Replace `assets\logo.ico`
- **Metadata**: Edit `version_info.txt`
- **App name**: Modify `--name` in build.bat

## Post-Build Testing
Verify functionality by:
1. Running the executable
2. Testing node connections
3. Retrieving sample logs
4. Generating PDF reports

## Troubleshooting
- Missing dependencies: Run `pip install -r requirements-narrow.txt`
- Missing icon: Place a valid .ico file in assets or remove `--icon` from build.bat
- PyInstaller errors: Try `--clean` switch with build command

## Notes
- Linux/macOS builds require slight script modifications
- Executable size can be reduced with UPX compression
