import childProcess from "child_process";
import crossSpawn from "cross-spawn";
import Electron, { app, dialog, ipcMain } from "electron";
import fs from "fs";
import * as path from "path";

const PY_DIST_FOLDER = "pythondist";
const PY_FOLDER = "python";
const PY_MODULE = "subprocess_api"; // New subprocess API module

const isDev = (process.env.NODE_ENV === "development");

let pyProc: childProcess.ChildProcess | null = null;
let pythonReady = false;
let commandQueue: Array<{command: any, callback: Function}> = [];

const initializePython = async () => {
    console.log("Starting Python subprocess...");
    
    const srcPath = path.join(__dirname, "..", PY_FOLDER, PY_MODULE + ".py");
    const distPath = path.join(__dirname, "..", PY_DIST_FOLDER, "python", PY_MODULE + ".py");
    
    console.log("isDev:", isDev);
    console.log("srcPath:", srcPath);
    console.log("distPath:", distPath);
    
    let pythonPath: string;
    let scriptPath: string;
    
    if (__dirname.indexOf("app.asar") > 0) {
        // Packaged mode
        console.log("Running in packaged mode");
        if (fs.existsSync(distPath)) {
            pythonPath = "python";
            scriptPath = distPath;
        } else {
            console.log("Packaged python script not found at:", distPath);
            dialog.showErrorBox("Error", "Packaged python script not found at: " + distPath);
            return;
        }
    } else {
        // Development mode
        console.log("Running in development mode");
        if (fs.existsSync(srcPath)) {
            pythonPath = "/home/tamas.foldes/miniconda3/envs/electron-python-sample/bin/python";
            scriptPath = srcPath;
        } else {
            console.log("Python source not found at:", srcPath);
            dialog.showErrorBox("Error", "Python source not found at: " + srcPath);
            return;
        }
    }
    
    console.log("Starting Python subprocess:", pythonPath, scriptPath);
    
    pyProc = crossSpawn(pythonPath, [scriptPath], {
        stdio: ['pipe', 'pipe', 'pipe']
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
        pythonReady = false;
    });
    
    pyProc.on('close', (code: number) => {
        console.log(`Python subprocess exited with code ${code}`);
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
        
        // Process queued commands
        while (commandQueue.length > 0) {
            const { command, callback } = commandQueue.shift()!;
            sendCommandToPython(command, callback);
        }
    } else if (message.type === 'response') {
        // Handle command response
        // For now, we'll emit this to the renderer process
        // In a more sophisticated implementation, we'd track command IDs
        console.log("Python command response:", message.response);
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

const sendCommandToPython = (command: any, callback?: Function) => {
    if (!pyProc || !pythonReady) {
        console.log("Python not ready, queuing command:", command);
        if (callback) {
            commandQueue.push({ command, callback });
        }
        return;
    }
    
    try {
        const commandJson = JSON.stringify(command) + '\n';
        if (pyProc.stdin) {
            pyProc.stdin.write(commandJson);
        }
        console.log("Sent command to Python:", command);
        
        if (callback) {
            // For now, we'll call the callback immediately
            // In a more sophisticated implementation, we'd track command IDs and responses
            callback(null, { status: 'sent' });
        }
    } catch (error) {
        console.error("Error sending command to Python:", error);
        if (callback) {
            callback(error, null);
        }
    }
};

// IPC handlers
ipcMain.on("python-command", (event: Electron.Event, command: any) => {
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

ipcMain.on("getPythonStatus", (event: Electron.Event) => {
    event.sender.send("pythonStatus", {
        ready: pythonReady,
        pid: pyProc ? pyProc.pid : undefined
    });
});

const exitPyProc = () => {
    if (pyProc) {
        console.log("Terminating Python subprocess...");
        
        // Send exit command first
        sendCommandToPython({ type: 'exit' });
        
        // Give it a moment to exit gracefully
        setTimeout(() => {
            if (pyProc && !pyProc.killed) {
                pyProc.kill();
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