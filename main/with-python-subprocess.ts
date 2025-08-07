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

const initializePython = async () => {
    console.log("Starting Python subprocess...");
    
    const srcPath = path.join(__dirname, "..", PY_FOLDER, PY_MODULE + ".py");
    const launcherPath = path.join(__dirname, "..", PY_FOLDER, PY_LAUNCHER + ".py");
    const distPath = path.join(__dirname, "..", PY_DIST_FOLDER, "python", PY_MODULE + ".py");
    const resourcesPath = path.join(process.resourcesPath, PY_DIST_FOLDER, "python", PY_MODULE + ".py");
    const resourcesLauncherPath = path.join(process.resourcesPath, PY_DIST_FOLDER, "python", PY_LAUNCHER + ".py");
    
    console.log("isDev:", isDev);
    console.log("srcPath:", srcPath);
    console.log("distPath:", distPath);
    console.log("resourcesPath:", resourcesPath);
    console.log("resourcesLauncherPath:", resourcesLauncherPath);
    
    let pythonPath: string;
    let scriptPath: string;
    
    if (__dirname.indexOf("app.asar") > 0) {
        // Packaged mode - use launcher script to set up Python path
        console.log("Running in packaged mode");
        
        // Check if launcher exists, fall back to direct script if not
        if (fs.existsSync(resourcesLauncherPath)) {
            scriptPath = resourcesLauncherPath;
            console.log("Using launcher script for packaged mode");
        } else if (fs.existsSync(resourcesPath)) {
            scriptPath = resourcesPath;
            console.log("Launcher not found, using direct script");
        } else {
            console.log("Packaged python script not found at:", resourcesPath);
            dialog.showErrorBox("Error", "Packaged python script not found at: " + resourcesPath);
            return;
        }
        
        // Try multiple Python executable names
        if (process.platform === "win32") {
            const pythonCandidates = ["python", "python.exe", "python3", "python3.exe"];
            pythonPath = pythonCandidates[0]; // Start with first candidate
        } else {
            pythonPath = "python3";
        }
    } else {
        // Development mode
        console.log("Running in development mode");
        if (fs.existsSync(srcPath)) {
            // Use platform-specific development Python path
            if (process.platform === "win32") {
                pythonPath = "python"; // Assume Python is in PATH on Windows dev
            } else {
                pythonPath = "/home/tamas.foldes/miniconda3/envs/electron-python-sample/bin/python";
            }
            scriptPath = srcPath;
        } else {
            console.log("Python source not found at:", srcPath);
            dialog.showErrorBox("Error", "Python source not found at: " + srcPath);
            return;
        }
    }
    
    console.log("Starting Python subprocess:", pythonPath, scriptPath);
    console.log("Working directory:", process.cwd());
    console.log("__dirname:", __dirname);
    
    pyProc = crossSpawn(pythonPath, [scriptPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.dirname(scriptPath) // Set working directory to script location
    });
    
    if (!pyProc) {
        console.log("Failed to start Python subprocess");
        dialog.showErrorBox("Error", "Failed to start Python subprocess");
        return;
    }
    
    console.log("Python subprocess started, PID:", pyProc.pid);
    
    // Handle subprocess output
    if (pyProc.stdout) {
        pyProc.stdout.on('data', (data: Buffer) => {
            const output = data.toString().trim();
            console.log('Python stdout:', output);
            
            // Parse JSON messages from Python
            const lines = output.split('\n');
            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const message = JSON.parse(line);
                        handlePythonMessage(message);
                    } catch (e) {
                        console.error('Error parsing Python message:', e, 'Raw:', line);
                    }
                }
            }
        });
    }
    
    if (pyProc.stderr) {
        pyProc.stderr.on('data', (data: Buffer) => {
            console.error('Python stderr:', data.toString());
        });
    }
    
    pyProc.on('error', (error: Error) => {
        console.error('Python subprocess error:', error);
        dialog.showErrorBox("Python Error", `Failed to start Python: ${error.message}`);
        pythonReady = false;
    });
    
    pyProc.on('close', (code: number | null) => {
        console.log(`Python subprocess exited with code ${code}`);
        // Only show error dialog if it's an unexpected exit (not during app shutdown)
        // and the exit code indicates an actual error
        if (code !== 0 && code !== null && !isShuttingDown) {
            // Don't show dialog for signal-based terminations (negative codes on Unix)
            if (code > 0) {
                console.error(`Python process exited unexpectedly with code ${code}`);
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
    
    console.log("Python subprocess is ready!");
};

const handlePythonMessage = (message: any) => {
    console.log("Received Python message:", message);
    
    if (message.type === 'ready') {
        pythonReady = true;
        console.log("Python subprocess is ready");
        
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
        console.log("Python command response:", message.response);
        
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
        console.log("Python event:", message.event);
        // Forward event to renderer process
        const allWindows = Electron.BrowserWindow.getAllWindows();
        allWindows.forEach(window => {
            window.webContents.send('python-event', message.event);
        });
    } else if (message.type === 'error') {
        console.error("Python error:", message.message);
    }
};

// Track pending commands with unique IDs
let commandCounter = 0;
const pendingCommands = new Map<number, Function>();

const sendCommandToPython = (command: any, callback?: Function) => {
    if (!pyProc || !pythonReady) {
        console.log("Python not ready, queuing command:", command);
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
        console.log("Sent command to Python:", commandWithId);
        
        if (callback) {
            // Store callback to be called when response arrives
            pendingCommands.set(commandId, callback);
        }
    } catch (error) {
        console.error("Error sending command to Python:", error);
        if (callback) {
            callback(error, null);
        }
    }
};

// IPC handlers
ipcMain.on("python-command", (event: any, command: any) => {
    console.log("Received IPC command:", command);
    
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
        console.log("Terminating Python subprocess...");
        isShuttingDown = true;
        
        // Send exit command first for graceful shutdown
        sendCommandToPython({ type: 'exit' });
        
        // Give it a moment to exit gracefully, then force kill if necessary
        setTimeout(() => {
            if (pyProc && !pyProc.killed) {
                console.log("Force killing Python subprocess...");
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
    initializePython().catch(console.error);
});

app.on("will-quit", exitPyProc);

export { initializePython, sendCommandToPython, exitPyProc };