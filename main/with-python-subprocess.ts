import childProcess from "child_process";
import crossSpawn from "cross-spawn";
import Electron, { app, dialog, ipcMain } from "electron";
import fs from "fs";
import * as path from "path";

const PY_DIST_FOLDER = "pythondist";
const PY_FOLDER = "python";
const PY_MODULE = "subprocess_api"; // Full subprocess API with face detection
const PY_LAUNCHER = "launcher"; // Launcher script for packaged mode

const isDev = (process.env.NODE_ENV === "development");

let pyProc: childProcess.ChildProcess | null = null;
let pythonReady = false;
let commandQueue: Array<{command: any, callback: Function}> = [];
let isShuttingDown = false;
let currentModelType = 'retinaface'; // Track current environment

const detectModelType = (command: any): string => {
    // Check if this is a processing command with model selection
    if (command && command.type === 'start_processing' && command.data && command.data.model) {
        const model = command.data.model.toLowerCase();
        return model.includes('retinaface') ? 'retinaface' : 'yolo';
    }
    return currentModelType; // Keep current type if not specified
};

const restartPythonIfNeeded = async (requiredModelType: string): Promise<boolean> => {
    if (requiredModelType === currentModelType && pythonReady) {
        return false; // No restart needed
    }
    
    // Need to restart with different environment
    try { console.log(`Switching from ${currentModelType} to ${requiredModelType} environment`); } catch (e) {}
    
    // Stop current process
    if (pyProc && !isShuttingDown) {
        exitPyProc();
        // Wait a bit for cleanup
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Update model type and restart
    currentModelType = requiredModelType;
    await initializePython();
    return true;
};

const initializePython = async () => {
    try { console.log("Starting Python subprocess..."); } catch (e) {}
    
    const srcPath = path.join(__dirname, "..", PY_FOLDER, PY_MODULE + ".py");
    const launcherPath = path.join(__dirname, "..", PY_FOLDER, PY_LAUNCHER + ".py");
    const distPath = path.join(__dirname, "..", PY_DIST_FOLDER, "python", PY_MODULE + ".py");
    const resourcesPath = path.join(process.resourcesPath, PY_DIST_FOLDER, "python", PY_MODULE + ".py");
    const resourcesLauncherPath = path.join(process.resourcesPath, PY_DIST_FOLDER, "python", PY_LAUNCHER + ".py");
    
    try { console.log("isDev:", isDev); } catch (e) {}
    try { console.log("srcPath:", srcPath); } catch (e) {}
    try { console.log("distPath:", distPath); } catch (e) {}
    try { console.log("resourcesPath:", resourcesPath); } catch (e) {}
    try { console.log("resourcesLauncherPath:", resourcesLauncherPath); } catch (e) {}
    
    let pythonPath: string = "";
    let scriptPath: string = "";
    
    if (__dirname.indexOf("app.asar") > 0) {
        // Packaged mode - use virtual environment Python directly for better isolation
        try { console.log("Running in packaged mode"); } catch (e) {}
        
        const resourcesBase = process.resourcesPath;
        const yoloVenvPython = path.join(resourcesBase, PY_DIST_FOLDER, "yolo-env", "bin", process.platform === "win32" ? "python.exe" : "python");
        const yoloVenvPython3 = path.join(resourcesBase, PY_DIST_FOLDER, "yolo-env", "bin", process.platform === "win32" ? "python.exe" : "python3");
        const retinafaceVenvPython = path.join(resourcesBase, PY_DIST_FOLDER, "retinaface-env", "bin", process.platform === "win32" ? "python.exe" : "python");
        const retinafaceVenvPython3 = path.join(resourcesBase, PY_DIST_FOLDER, "retinaface-env", "bin", process.platform === "win32" ? "python.exe" : "python3");
        const subprocessScriptPath = path.join(resourcesBase, PY_DIST_FOLDER, "python", "subprocess_api.py");
        
        // Check for bundled standalone Python first
        const standalonePythonDir = path.join(resourcesBase, PY_DIST_FOLDER, "python-standalone");
        const standalonePython = process.platform === "win32" 
            ? path.join(standalonePythonDir, "python.exe")
            : path.join(standalonePythonDir, "bin", "python3.10");
        
        // Choose Python executable based on model type - use venv directly
        const pickExisting = (...candidates: string[]): string | "" => {
            for (const c of candidates) {
                if (c && fs.existsSync(c)) return c;
            }
            return "";
        };

        if (currentModelType === 'retinaface' && (fs.existsSync(retinafaceVenvPython) || fs.existsSync(retinafaceVenvPython3))) {
            pythonPath = pickExisting(retinafaceVenvPython, retinafaceVenvPython3);
            scriptPath = subprocessScriptPath;
            try { console.log(`Using RetinaFace venv Python directly: ${pythonPath}`); } catch (e) {}
        } else if (currentModelType === 'yolo' && (fs.existsSync(yoloVenvPython) || fs.existsSync(yoloVenvPython3))) {
            pythonPath = pickExisting(yoloVenvPython, yoloVenvPython3);
            scriptPath = subprocessScriptPath;
            try { console.log(`Using YOLO venv Python directly: ${pythonPath}`); } catch (e) {}
        } else if (fs.existsSync(standalonePython)) {
            // Use standalone Python with multi-environment launcher
            const multiEnvLauncherPath = path.join(resourcesBase, PY_DIST_FOLDER, "python", "multi_env_launcher.py");
            
            if (fs.existsSync(multiEnvLauncherPath)) {
                pythonPath = standalonePython;
                scriptPath = multiEnvLauncherPath;
                try { console.log(`Using bundled standalone Python: ${pythonPath}`); } catch (e) {}
                try { console.log("With multi-environment launcher"); } catch (e) {}
            } else {
                try { console.log("Multi-environment launcher not found"); } catch (e) {}
                dialog.showErrorBox("Error", "Python environment not properly packaged");
                return;
            }
        } else {
            // Last resort fallback - should not happen with proper bundling
            try { console.error("No bundled Python found! This should not happen in packaged mode."); } catch (e) {}
            dialog.showErrorBox("Python Not Found", "The application was not packaged correctly. Python interpreter is missing.");
            return;
        }
    } else {
        // Development mode - support dual environment switching
        try { console.log("Running in development mode"); } catch (e) {}
        if (fs.existsSync(srcPath)) {
            // Check for virtual environments in project directory first (most specific)
            const projectDir = path.join(__dirname, "..");
            const yoloVenvPath = path.join(projectDir, "yolo-env", "bin", "python");
            const retinaVenvPath = path.join(projectDir, "retinaface-env", "bin", "python");
            
            // Check for conda environments in common locations
            const possibleCondaPaths = [
                // macOS
                `${process.env.HOME}/miniconda3/envs`,
                `${process.env.HOME}/anaconda3/envs`,
                `/opt/homebrew/anaconda3/envs`,
                `/opt/homebrew/miniconda3/envs`,
                // Linux
                `/home/${process.env.USER}/miniconda3/envs`,
                `/home/${process.env.USER}/anaconda3/envs`,
                // Windows
                `${process.env.USERPROFILE}\\miniconda3\\envs`,
                `${process.env.USERPROFILE}\\anaconda3\\envs`,
            ].filter(Boolean); // Remove any undefined paths
            
            // First try project-local virtual environments
            if (currentModelType === 'retinaface' && fs.existsSync(retinaVenvPath)) {
                pythonPath = retinaVenvPath;
                try { console.log(`Using project RetinaFace virtual environment: ${pythonPath}`); } catch (e) {}
            } else if (currentModelType === 'yolo' && fs.existsSync(yoloVenvPath)) {
                pythonPath = yoloVenvPath;
                try { console.log(`Using project YOLO virtual environment: ${pythonPath}`); } catch (e) {}
            } else {
                // Fallback to conda environments
                let condaBasePath: string | null = null;
                for (const testPath of possibleCondaPaths) {
                    if (fs.existsSync(testPath)) {
                        condaBasePath = testPath;
                        try { console.log(`Found conda environments at: ${condaBasePath}`); } catch (e) {}
                        break;
                    }
                }
                
                // Try to find the appropriate conda environment
                if (condaBasePath) {
                    const pythonExe = process.platform === "win32" ? "python.exe" : "python";
                    const yoloEnvPath = path.join(condaBasePath, "electron-python-yolo", "bin", pythonExe);
                    const retinaEnvPath = path.join(condaBasePath, "electron-python-retinaface", "bin", pythonExe);
                    const fallbackPath = path.join(condaBasePath, "electron-python-sample", "bin", pythonExe);
                    
                    // Choose environment based on current model type
                    if (currentModelType === 'retinaface' && fs.existsSync(retinaEnvPath)) {
                        pythonPath = retinaEnvPath;
                        try { console.log(`Using RetinaFace conda environment: ${pythonPath}`); } catch (e) {}
                    } else if (currentModelType === 'yolo' && fs.existsSync(yoloEnvPath)) {
                        pythonPath = yoloEnvPath;
                        try { console.log(`Using YOLO conda environment: ${pythonPath}`); } catch (e) {}
                    } else if (fs.existsSync(fallbackPath)) {
                        // Fallback to combined environment if dual environments not available
                        pythonPath = fallbackPath;
                        try { console.log(`Using fallback combined conda environment: ${pythonPath}`); } catch (e) {}
                    } else {
                        // Use system Python as last resort
                        pythonPath = process.platform === "win32" ? "python" : "python3";
                        try { console.log(`Using system Python: ${pythonPath}`); } catch (e) {}
                    }
                } else {
                    // No conda found, use system Python
                    pythonPath = process.platform === "win32" ? "python" : "python3";
                    try { console.log(`No conda environments found, using system Python: ${pythonPath}`); } catch (e) {}
                }
            }
            
            // Use multi_env_launcher in development too for consistency
            const multiEnvLauncherPath = path.join(__dirname, "..", PY_FOLDER, "multi_env_launcher.py");
            if (fs.existsSync(multiEnvLauncherPath)) {
                scriptPath = multiEnvLauncherPath;
                try { console.log("Using multi-environment launcher for development"); } catch (e) {}
            } else {
                scriptPath = srcPath;
                try { console.log("Multi-env launcher not found, using direct script"); } catch (e) {}
            }
        } else {
            try { console.log("Python source not found at:", srcPath); } catch (e) {}
            dialog.showErrorBox("Error", "Python source not found at: " + srcPath);
            return;
        }
    }
    
    // Ensure we have valid paths before proceeding
    if (!pythonPath || !scriptPath) {
        try { console.error("Invalid Python configuration - pythonPath:", pythonPath, "scriptPath:", scriptPath); } catch (e) {}
        dialog.showErrorBox("Configuration Error", "Failed to configure Python environment");
        return;
    }
    
    try { console.log("Starting Python subprocess:", pythonPath, scriptPath); } catch (e) {}
    try { console.log("Working directory:", process.cwd()); } catch (e) {}
    try { console.log("__dirname:", __dirname); } catch (e) {}
    
    // Prepare a sanitized environment for Python to avoid leaking user PYTHONPATH/site-packages
    const resourcesBase = (__dirname.indexOf("app.asar") > 0)
        ? process.resourcesPath
        : path.join(__dirname, "..");
    const bundledDepsDir = path.join(resourcesBase, PY_DIST_FOLDER, "python-deps");
    const bundledPyDir = path.join(resourcesBase, PY_DIST_FOLDER, "python");

    const spawnEnv = {
        ...process.env,
        // Ensure we don't pick up user's PYTHONPATH or user site-packages
        PYTHONNOUSERSITE: "1",
        PYTHONPATH: `${bundledDepsDir}:${bundledPyDir}`,
        // Detach from any active virtual environment from the user's shell
        VIRTUAL_ENV: "",
        PYTHONHOME: "",
        MODEL_TYPE: currentModelType, // Pass current model type to Python
    } as NodeJS.ProcessEnv;

    pyProc = crossSpawn(pythonPath, [scriptPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.dirname(scriptPath), // Set working directory to script location
        env: spawnEnv,
    });
    
    if (!pyProc) {
        try { console.log("Failed to start Python subprocess"); } catch (e) {}
        dialog.showErrorBox("Error", "Failed to start Python subprocess");
        return;
    }
    
    try { console.log("Python subprocess started, PID:", pyProc.pid); } catch (e) {}
    
    // Handle subprocess output
    if (pyProc.stdout) {
        pyProc.stdout.on('data', (data: Buffer) => {
            const output = data.toString();
            // Do not spam logs with entire buffer; handle line-by-line
            const lines = output.split('\n');
            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) continue;
                // Only parse lines that look like JSON; ignore other stdout noise from native libs
                if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                    try {
                        const message = JSON.parse(trimmed);
                        handlePythonMessage(message);
                    } catch (e) {
                        try { console.error('Error parsing Python message:', e, 'Raw:', trimmed); } catch (e) {}
                    }
                } else {
                    try { console.log('Python stdout (non-JSON):', trimmed); } catch (e) {}
                }
            }
        });
    }
    
    if (pyProc.stderr) {
        pyProc.stderr.on('data', (data: Buffer) => {
            try {
                console.warn('Python stderr:', data.toString());
            } catch (e) {
                // Ignore EPIPE errors when process is shutting down
            }
        });
    }
    
    pyProc.on('error', (error: Error) => {
        try { console.error('Python subprocess error:', error); } catch (e) {}
        dialog.showErrorBox("Python Error", `Failed to start Python: ${error.message}`);
        pythonReady = false;
    });
    
    pyProc.on('close', (code: number | null) => {
        try { console.log(`Python subprocess exited with code ${code}`); } catch (e) {}
        // Only show error dialog if it's an unexpected exit (not during app shutdown)
        // and the exit code indicates an actual error
        if (code !== 0 && code !== null && !isShuttingDown) {
            // Don't show dialog for signal-based terminations (negative codes on Unix)
            if (code > 0) {
                try { console.error(`Python process exited unexpectedly with code ${code}`); } catch (e) {}
                // Only show dialog if app is still running
                if (!(app as any).isQuitting && Electron.BrowserWindow.getAllWindows().length > 0) {
                    dialog.showErrorBox("Python Process Error", 
                        `The Python backend stopped unexpectedly (code ${code}). The application may not function correctly.`);
                }
            }
        }
        pythonReady = false;
        pyProc = null;
    });
    
    // Wait for Python to be ready
    await new Promise<void>((resolve) => {
        const checkReady = () => {
            if (pythonReady) {
                resolve();
            } else {
                setTimeout(checkReady, 100);
            }
        };
        checkReady();
    });
    
    try { console.log("Python subprocess is ready!"); } catch (e) {}
};

const handlePythonMessage = (message: any) => {
    try { console.log("Received Python message:", message); } catch (e) {}
    
    if (message.type === 'ready') {
        pythonReady = true;
        try { console.log("Python subprocess is ready"); } catch (e) {}
        
        // Notify all renderer processes that Python is ready
        const allWindows = Electron.BrowserWindow.getAllWindows();
        allWindows.forEach(window => {
            window.webContents.send('pythonStatus', {
                ready: pythonReady,
                pid: pyProc ? pyProc.pid : undefined
            });
        });
        
        // Process queued commands
        while (commandQueue.length > 0) {
            const { command, callback } = commandQueue.shift()!;
            sendCommandToPython(command, callback);
        }
    } else if (message.type === 'response') {
        // Handle command response
        try { console.log("Python command response:", message.response); } catch (e) {}
        
        // If there's a command ID, call the specific callback
        if (message.id && pendingCommands.has(message.id)) {
            const callback = pendingCommands.get(message.id);
            pendingCommands.delete(message.id);
            if (callback) {
                callback(null, message.response);
            }
        }
    } else if (message.type === 'event') {
        // Handle Python events (progress, completion, etc.)
        try { console.log("Python event:", message.event); } catch (e) {}
        // Forward event to renderer process
        const allWindows = Electron.BrowserWindow.getAllWindows();
        allWindows.forEach(window => {
            window.webContents.send('python-event', message.event);
        });
    } else if (message.type === 'error') {
        try { console.error("Python error:", message.message); } catch (e) {}
    }
};

// Track pending commands with unique IDs
let commandCounter = 0;
const pendingCommands = new Map<number, Function>();

const sendCommandToPython = async (command: any, callback?: Function) => {
    // Check if we need to restart Python with a different environment
    const requiredModelType = detectModelType(command);
    if (requiredModelType !== currentModelType) {
        try { console.log(`Model type change detected: ${currentModelType} -> ${requiredModelType}`); } catch (e) {}
        await restartPythonIfNeeded(requiredModelType);
    }
    
    if (!pyProc || !pythonReady) {
        try { console.log("Python not ready, queuing command:", command); } catch (e) {}
        if (callback) {
            commandQueue.push({ command, callback });
        }
        return;
    }
    
    try {
        // Add unique ID to track responses
        const commandId = ++commandCounter;
        const commandWithId = { ...command, id: commandId };
        
        const commandJson = JSON.stringify(commandWithId) + '\n';
        if (pyProc.stdin) {
            pyProc.stdin.write(commandJson);
        }
        try { console.log("Sent command to Python:", commandWithId); } catch (e) {}
        
        if (callback) {
            // Store callback to be called when response arrives
            pendingCommands.set(commandId, callback);
        }
    } catch (error) {
        try { console.error("Error sending command to Python:", error); } catch (e) {}
        if (callback) {
            callback(error, null);
        }
    }
};

// IPC handlers
ipcMain.on("python-command", (event: any, command: any) => {
    try { console.log("Received IPC command:", command); } catch (e) {}
    
    sendCommandToPython(command, (error: any, response: any) => {
        if (error) {
            event.sender.send("python-response", { 
                error: error.message,
                command: command
            });
        } else {
            event.sender.send("python-response", {
                response: response,
                command: command
            });
        }
    });
});

ipcMain.on("getPythonStatus", (event: any) => {
    event.sender.send("pythonStatus", {
        ready: pythonReady,
        pid: pyProc ? pyProc.pid : undefined
    });
});

const exitPyProc = () => {
    if (pyProc) {
        try { console.log("Terminating Python subprocess..."); } catch (e) {}
        isShuttingDown = true;
        
        // Send exit command first for graceful shutdown
        sendCommandToPython({ type: 'exit' });
        
        // Give it a moment to exit gracefully, then force kill if necessary
        setTimeout(() => {
            if (pyProc && !pyProc.killed) {
                try { console.log("Force killing Python subprocess..."); } catch (e) {}
                pyProc.kill('SIGTERM');
                // If still not dead after another second, use SIGKILL
                setTimeout(() => {
                    if (pyProc && !pyProc.killed) {
                        pyProc.kill('SIGKILL');
                    }
                }, 1000);
            }
        }, 1000);
        
        pyProc = null;
        pythonReady = false;
    }
};

// Initialize Python when app is ready
app.whenReady().then(() => {
    initializePython().catch((e) => { try { console.error(e); } catch (e) {} });
});

app.on("will-quit", exitPyProc);

export { initializePython, sendCommandToPython, exitPyProc };