# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Important
Always use Playwright MCP tools to check the app is rendering before asking me to look.

## Project Overview

This is an Electron application that integrates Python Flask backend with a React frontend. The app spawns a Python Flask server that provides both GraphQL endpoints and WebSocket communication for real-time face recognition processing using YOLO models.

## Key Architecture Components

### Electron Main Process (`main/`)
- `main/index.ts`: Main Electron process that creates the window and handles IPC communication
- `main/with-python.ts`: Critical component that manages Python process lifecycle, spawning Flask server with authentication tokens and handling process cleanup

### Python Backend (`python/`)
- `python/api.py`: Flask server with GraphQL endpoints and WebSocket support (Flask-SocketIO)
- `python/launch.py`: Launcher script that sets up bundled dependencies for packaged builds
- `python/face_recognition.py`: YOLO-based face detection processor with real-time progress events
- Python server uses signing keys for authentication between Electron and Flask
- WebSocket events: `start_recognition`, `stop_recognition`, `get_status`, `face_recognition_event`

### React Frontend (`src/`)
- `src/App.tsx`: Main React component with Apollo GraphQL client and WebSocket client (socket.io-client)
- Hybrid communication: WebSocket for real-time updates, GraphQL as fallback
- Handles face recognition UI, model selection, and real-time progress tracking

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
npm run python-build     # Bundle Python dependencies
npm run react-build      # Build React app  
npm run main-build       # Compile TypeScript and create Electron package
```

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
- Test files in `tests/` directory test both browser and Electron modes
- `npm run test:gui` for headless testing, `npm run test:gui:headed` for headed mode
- Tests include app loading, UI components, network requests, and GraphQL initialization

## Communication Architecture

### Real-time Communication
- **WebSocket (Primary)**: Bidirectional real-time communication for face recognition events
- **Server-Sent Events (Fallback)**: Unidirectional real-time updates
- **GraphQL (Fallback)**: HTTP-based queries for compatibility

### Authentication Flow
- Electron main process generates random signing keys (development uses "devkey")
- All communication (GraphQL, WebSocket) requires valid signing key
- Python server validates signing keys before processing requests

### Face Recognition Pipeline
1. User selects files/folders through Electron file dialogs
2. WebSocket sends `start_recognition` event to Python backend
3. Python processes images/videos with YOLO models
4. Real-time progress events sent via WebSocket (`face_recognition_event`)
5. UI updates progress bar and shows live results
6. Completion events trigger final results display

## Important Implementation Details

- Python process lifecycle managed by `main/with-python.ts` with different handling for packaged vs. unpackaged scenarios
- Uses `__dirname.indexOf("app.asar")` to detect if running from packaged app
- Python server exits gracefully via GraphQL endpoint when Electron shuts down
- Face recognition supports multiple YOLO models with configurable confidence thresholds
- WebSocket connection includes automatic fallback to GraphQL for reliability
- Progress events are throttled to prevent UI overwhelming during batch processing
- Python bundling script creates optimized distribution with essential packages only