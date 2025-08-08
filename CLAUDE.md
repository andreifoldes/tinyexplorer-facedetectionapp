# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Important
Always use Playwright MCP tools to check the app is rendering before asking me to look.

## Project Overview

This is an Electron application that integrates Python Flask backend with a React frontend. The app spawns a Python Flask server that provides both GraphQL endpoints and WebSocket communication for real-time face recognition processing using YOLO models.

## Key Architecture Components

### Electron Main Process (`main/`)
- `main/index.ts`: Main Electron process that creates the window, handles IPC communication, manages tray functionality, and implements file/folder dialogs
- `main/with-python-subprocess.ts`: Critical component that manages Python subprocess lifecycle using stdin/stdout JSON communication, handles cross-platform Python execution, and manages graceful shutdown

### Python Backend (`python/`)
- `python/subprocess_api.py`: Main subprocess API that handles JSON commands via stdin/stdout communication
- `python/launcher.py`: Launcher script that sets up bundled dependencies for packaged builds
- `python/face_detection.py`: Advanced face detection processor supporting both YOLO and RetinaFace models with real-time progress callbacks
- `python/calc.py`: Simple calculator module for testing subprocess communication
- Communication via JSON messages over stdin/stdout (no HTTP server required)
- Commands: `get_models`, `load_model`, `start_processing`, `stop_processing`, `get_results`, `export_csv`

### React Frontend (`src/`)
- `src/App.tsx`: Main React component that communicates with Python subprocess via Electron IPC
- Direct IPC communication: No HTTP/WebSocket overhead, all communication through Electron's IPC system
- Features: File/folder selection, model selection, confidence threshold adjustment, real-time progress tracking
- Supports both single file and batch folder processing, handles image and video files

## Development Commands

```bash
# Start development (runs both React and Electron)
npm run start

# Build everything (Python bundle, React, Electron)
npm run build

# Lint code
npm run lint

# Run GUI tests
npm run test:gui
npm run test:gui:headed

# Watch mode for development
npm run watch

# Individual component builds
npm run python-build        # Bundle Python dependencies
npm run python-build-minimal # Copy Python files without bundling dependencies
npm run react-build         # Build React app  
npm run main-build          # Compile TypeScript and create Electron package

# TypeScript watching
npm run main-watch          # Watch and compile Electron main process
npm run react-watch         # Watch React TypeScript compilation
```

## Testing and Validation Workflow

After each modification to the codebase:

1. **Rebuild the application**: `npm run build`
2. **Test the macOS x64 application**: The built app is located at `dist/mac/TinyExplorer FaceDetectionApp.app`
3. **Verify core functionality**: 
   - Launch the packaged app
   - Test file/folder selection
   - Verify Python subprocess communication
   - Run face detection on sample images
   - Confirm results export functionality

## Python Environment Setup

The project requires conda environment setup:

```bash
conda env create -f environment.yml
conda activate electron-python-sample
```

Key Python dependencies include:
- Flask + Flask-CORS + Flask-SocketIO for web server
- GraphQL (graphene, flask-graphql) for API
- Computer vision (opencv-python, ultralytics, torch)
- Face detection models (YOLO variants, RetinaFace)

## Remote Display Configuration

For remote development (SSH with X11 forwarding), configure `.env` file:

```bash
# .env
BROWSER=none
DISPLAY=your.remote.host:0.0
```

The Playwright configuration automatically detects `DISPLAY` environment variable and:
- Enables headed mode when `DISPLAY` is set
- Adds Chrome args for X11 forwarding compatibility (`--no-sandbox`, `--disable-dev-shm-usage`)
- Enables remote debugging on port 9222

This allows GUI testing and Electron development over SSH connections with X11 forwarding (e.g., MobaXterm, X11 forwarding).

## Build Process and Packaging

1. `npm run python-build` - Bundles Python dependencies into `pythondist/` using `scripts/bundle-python.js`
2. `npm run react-build` - Builds React app with legacy OpenSSL support
3. `npm run main-build` - Compiles TypeScript and creates Electron package
4. Python bundling creates essential package subset to reduce distribution size

## Testing

- Uses Playwright for GUI testing with custom configuration
- Test files in `tests/` directory (`gui-components.spec.js`, `served-gui-test.spec.js`, `mcp-debug-test.spec.js`)
- `npm run test:gui` for headless testing, `npm run test:gui:headed` for headed mode
- Tests include app loading, UI components, Python subprocess communication, and face detection functionality
- Additional Python standalone tests: `test_subprocess.py`, `test_both_models.py`, `test_compatibility.py`
- Playwright config automatically detects X11 forwarding for remote development

## Communication Architecture

### IPC-based Communication (No HTTP Server)
- **Electron IPC**: Primary communication between React frontend and Electron main process
- **Subprocess stdin/stdout**: JSON message communication between Electron and Python subprocess
- **Real-time Events**: Python sends progress events via stdout, forwarded to React via IPC
- No authentication required - communication is process-local and secure by design

### Subprocess Command Flow
1. React sends commands to main process via `ipcRenderer.send("python-command", command)`
2. Main process forwards commands to Python subprocess via stdin JSON
3. Python subprocess processes commands and sends responses via stdout JSON
4. Main process forwards responses back to React via `ipcRenderer.on("python-response")`
5. Progress events are emitted separately via `ipcRenderer.on("python-event")`

### Face Recognition Pipeline
1. User selects files/folders through Electron file dialogs (`browse-folder`, `browse-file` IPC)
2. User selects results output folder
3. IPC sends `start_processing` command to Python subprocess with parameters
4. Python processes images/videos with selected model (YOLO or RetinaFace)
5. Real-time progress events sent via stdout, forwarded to React via `python-event` IPC
6. UI updates progress bar and displays real-time progress messages
7. Completion events trigger final results display and enable "Open Results Folder" button

## Important Implementation Details

- Python process lifecycle managed by `main/with-python-subprocess.ts` with different handling for packaged vs. unpackaged scenarios
- Uses `__dirname.indexOf("app.asar")` to detect if running from packaged app
- Python subprocess exits gracefully via `exit` command when Electron shuts down
- Face recognition supports multiple YOLO models (yolov8n-face, yolov8l-face, etc.) and RetinaFace with configurable confidence thresholds
- Models are automatically downloaded from GitHub releases on first use if not found locally
- Progress events include emoji symbols for better UX (🖼️ for images, 🎬 for videos, ✅ for success, etc.)
- Python bundling script creates optimized distribution with essential packages only
- Cross-platform Python executable detection (handles different Python binary names)
- Tray functionality with show/hide/quit options
- System file manager integration for opening results folders