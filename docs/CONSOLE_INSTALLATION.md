# Console Installation Guide for Windows

The TinyExplorer FaceDetectionApp Windows installer supports console output for tracking installation progress, which is useful for automated deployments, CI/CD pipelines, or troubleshooting.

## Installation Methods

### 1. GUI Installation (Default)
Simply double-click the installer executable:
```
tinyexplorer-facedetectionapp-0.1.0-setup.exe
```

### 2. Silent Installation with Console Output
Run the installer from Command Prompt or PowerShell with the `/S` flag:
```cmd
tinyexplorer-facedetectionapp-0.1.0-setup.exe /S
```

This will:
- Install the application silently without GUI
- Display progress messages in the console
- Use default installation directory

### 3. Silent Installation with Custom Directory
Specify a custom installation directory:
```cmd
tinyexplorer-facedetectionapp-0.1.0-setup.exe /S /D=C:\MyApps\TinyExplorer
```

### 4. Installation with Logging
Create a detailed log file:
```cmd
tinyexplorer-facedetectionapp-0.1.0-setup.exe /S /LOG=installation.log
```

## Console Output Messages

During console installation, you'll see messages like:
```
TinyExplorer FaceDetectionApp installation starting...
Version: 0.1.0
Architecture: x64
Running in silent mode with console output
Installing application files...
Setting up Python environments...
  - YOLO environment
  - RetinaFace environment
Creating model storage directories...
Setting up shortcuts...
Installation completed successfully
```

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `/S` | Silent installation (no GUI) | `/S` |
| `/D=path` | Custom installation directory | `/D=C:\Program Files\MyApp` |
| `/LOG=file` | Log installation to file | `/LOG=install.log` |
| `/NCRC` | Skip CRC check (faster) | `/NCRC` |
| `/?` | Show help (when not combined with `/S`) | `/?` |

## Uninstallation

### Silent Uninstall
```cmd
"C:\Program Files\TinyExplorer FaceDetectionApp\Uninstall.exe" /S
```

### With Console Output
The uninstaller also supports console output:
```
TinyExplorer FaceDetectionApp uninstallation starting...
Removing application files...
Cleaning up model cache...
Preserving model cache at C:\Users\Username\AppData\Local\TinyExplorerFaceDetection\models
Uninstallation completed
```

## PowerShell Examples

### Install and Wait for Completion
```powershell
Start-Process -FilePath ".\tinyexplorer-facedetectionapp-0.1.0-setup.exe" `
              -ArgumentList "/S", "/D=C:\Apps\TinyExplorer" `
              -Wait -NoNewWindow
```

### Capture Console Output
```powershell
$output = & ".\tinyexplorer-facedetectionapp-0.1.0-setup.exe" /S 2>&1
Write-Host $output
```

## Batch Script Example

```batch
@echo off
echo Installing TinyExplorer FaceDetectionApp...
start /wait tinyexplorer-facedetectionapp-0.1.0-setup.exe /S /LOG=install.log
if %ERRORLEVEL% == 0 (
    echo Installation successful!
) else (
    echo Installation failed with error code %ERRORLEVEL%
)
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | User cancelled (GUI mode only) |
| 3 | Insufficient permissions |
| 4 | Disk space error |

## Troubleshooting

1. **No console output visible**: Ensure you're running from a real console (cmd.exe or PowerShell), not from Windows Explorer

2. **Permission errors**: Run the console as Administrator:
   ```cmd
   runas /user:Administrator "cmd /c tinyexplorer-facedetectionapp-0.1.0-setup.exe /S"
   ```

3. **Installation hangs**: Use `/NCRC` to skip CRC verification if the download was trusted

4. **View detailed logs**: Use the `/LOG=` option to create a detailed log file for debugging

## CI/CD Integration

For GitHub Actions or other CI systems:
```yaml
- name: Install TinyExplorer
  run: |
    Start-Process -FilePath "installer.exe" -ArgumentList "/S" -Wait -NoNewWindow
  shell: pwsh
```

## Model Cache Note

The installer preserves downloaded face detection models during reinstallation or uninstallation. Models are stored at:
- `%LOCALAPPDATA%\TinyExplorerFaceDetection\models`

To completely remove all data including models, manually delete this directory after uninstallation.