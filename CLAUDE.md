# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Important
Always use Playwright MCP tools to check the app is rendering before asking me to look.

## Project Overview

This is an Electron application that integrates Python Flask backend with a React frontend. The app spawns a Python Flask server that provides GraphQL endpoints for face recognition processing using YOLO models.

## Key Architecture Components

### Electron Main Process (`main/`)
- `main/index.ts`: Main Electron process that creates the window and handles IPC communication
- `main/with-python.ts`: Critical component that manages Python process lifecycle, spawning Flask server with authentication tokens and handling process cleanup

### Python Backend (`python/`)
- `python/api.py`: Flask GraphQL server with face recognition endpoints
- `python/launch.py`: Launcher script that sets up bundled dependencies for packaged builds
- `python/face_recognition.py`: YOLO-based face detection processor
- Python server uses signing keys for authentication between Electron and Flask

### React Frontend (`src/`)
- `src/App.tsx`: Main React component with Apollo GraphQL client for Python backend communication
- Uses Apollo Client to communicate with Python GraphQL server
- Handles face recognition UI, model selection, and progress tracking

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
```

## Python Environment Setup

The project requires conda environment setup:

```bash
conda env create -f environment.yml
conda activate electron-python-sample
```

## Build Process

1. `npm run python-build` - Bundles Python dependencies into `pythondist/`
2. `npm run react-build` - Builds React app
3. `npm run main-build` - Compiles TypeScript and creates Electron package

## Testing

- Uses Playwright for GUI testing
- Test files in `tests/` directory
- Run `npm run test:gui` for headless testing

## Important Implementation Details

- Python process lifecycle is managed by `main/with-python.ts` which handles differences between packaged and unpackaged scenarios
- Uses `__dirname.indexOf("app.asar")` to detect if running from packaged app
- Authentication between Electron and Python uses randomly generated signing keys
- Python server exits gracefully via GraphQL endpoint when Electron shuts down
- Face recognition uses YOLO models with configurable confidence thresholds