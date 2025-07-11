import childProcess from "child_process";
import crossSpawn from "cross-spawn";
import Electron, { app, dialog, ipcMain } from "electron"; // tslint:disable-line
import fs from "fs";
import getPort from "get-port";
import * as path from "path";
import superagent from "superagent";
import uuid from "uuid";
import http from "http";

const PY_DIST_FOLDER = "pythondist";
const PY_FOLDER = "python";
const PY_MODULE = "api"; // without .py suffix
const PY_LAUNCHER = "launch.py";

const isDev = (process.env.NODE_ENV === "development");

let pyProc = null as any;

const apiDetails = {
    port:0,
    signingKey:"",
};

const initializeApi = async () => {
    console.log("Starting initializeApi()");
    // dialog.showErrorBox("success", "initializeApi");
    const availablePort = await getPort();
    apiDetails.port = isDev ? 5000 : availablePort;
    const key = isDev ? "devkey" : uuid.v4();
    apiDetails.signingKey = key;
    const srcPath = path.join(__dirname, "..", PY_FOLDER, PY_MODULE + ".py");
    const launcherPath = path.join(__dirname, "..", PY_FOLDER, PY_LAUNCHER);
    const distLauncherPath = path.join(__dirname, "..", PY_DIST_FOLDER, "python", PY_LAUNCHER);
    
    console.log("__dirname:", __dirname);
    console.log("isDev:", isDev);
    console.log("srcPath:", srcPath);
    console.log("launcherPath:", launcherPath);
    console.log("distLauncherPath:", distLauncherPath);
    
    if (__dirname.indexOf("app.asar") > 0) {
        console.log("Running in packaged mode");
        // dialog.showErrorBox("info", "packaged");
        if (fs.existsSync(distLauncherPath)) {
            console.log("Starting Python server from dist launcher");
            pyProc = crossSpawn("python", [distLauncherPath, "--apiport", String(apiDetails.port), "--signingkey", apiDetails.signingKey]);
        } else {
            console.log("Packaged python launcher not found at:", distLauncherPath);
            dialog.showErrorBox("Error", "Packaged python launcher not found at: " + distLauncherPath);
        }
    } else {
        console.log("Running in unpackaged mode");
        // dialog.showErrorBox("info", "unpackaged");
        if (fs.existsSync(srcPath)) {
            console.log("Starting Python server from src:", srcPath);
            pyProc = crossSpawn("/home/tamas.foldes/miniconda3/envs/electron-python-sample/bin/python", [srcPath, "--apiport", String(apiDetails.port), "--signingkey", apiDetails.signingKey]);
        } else if (fs.existsSync(launcherPath)) {
            console.log("Starting Python server from launcher:", launcherPath);
            pyProc = crossSpawn("/home/tamas.foldes/miniconda3/envs/electron-python-sample/bin/python", [launcherPath, "--apiport", String(apiDetails.port), "--signingkey", apiDetails.signingKey]);
        } else {
            console.log("No python source found. Checking files...");
            console.log("srcPath exists:", fs.existsSync(srcPath));
            console.log("launcherPath exists:", fs.existsSync(launcherPath));
            dialog.showErrorBox("Error", "Unpackaged python source not found");
        }
    }
    
    if (pyProc === null || pyProc === undefined) {
        console.log("Failed to start Python server");
        dialog.showErrorBox("Error", "unable to start python server");
    } else {
        console.log("Python process started, PID:", pyProc.pid);
        console.log("Server running at http://127.0.0.1:" + apiDetails.port);
        
        // Add error handling for the Python process
        pyProc.on('error', (error: any) => {
            console.error('Python process error:', error);
        });
        
        pyProc.stderr.on('data', (data: any) => {
            console.error('Python stderr:', data.toString());
        });
        
        pyProc.stdout.on('data', (data: any) => {
            console.log('Python stdout:', data.toString());
        });
    }
    console.log("leaving initializeApi()");
};

const waitForPythonServer = async (port: number, maxRetries: number = 10): Promise<boolean> => {
    for (let i = 0; i < maxRetries; i++) {
        try {
            await new Promise<void>((resolve, reject) => {
                const req = http.get(`http://127.0.0.1:${port}/health/`, (res) => {
                    if (res.statusCode === 200) {
                        resolve();
                    } else {
                        reject(new Error(`Status code: ${res.statusCode}`));
                    }
                });
                req.on('error', reject);
                req.setTimeout(1000, () => {
                    req.destroy();
                    reject(new Error('Timeout'));
                });
            });
            console.log(`Python server is ready on port ${port}`);
            return true;
        } catch (error) {
            console.log(`Waiting for Python server... attempt ${i + 1}/${maxRetries}`);
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }
    console.log('Python server failed to start within timeout');
    return false;
};

ipcMain.on("getApiDetails", (event:Electron.Event) => {
    if (apiDetails.signingKey !== "") {
        event.sender.send("apiDetails", JSON.stringify(apiDetails));
    } else {
        initializeApi()
            .then(async () => {
                // Wait for Python server to be ready
                const isReady = await waitForPythonServer(apiDetails.port);
                if (isReady) {
                    event.sender.send("apiDetails", JSON.stringify(apiDetails));
                } else {
                    event.sender.send("apiDetailsError", "Python server failed to start");
                }
            })
            .catch(() => {
                event.sender.send("apiDetailsError", "Error initializing API");
            });
    }
});

const exitPyProc = () => {
    //
    // NOTE: killing processes in node is surprisingly tricky and a simple
    //             pyProc.kill() totally isn't enough. Instead send a message to
    //             the pyProc web server telling it to exit
    //
    superagent.get("http://127.0.0.1:" + apiDetails.port + "/graphql/?query=%7Bexit(signingkey:\"" + apiDetails.signingKey + "\")%7D").then().catch();
    pyProc = null;
};

app.on("will-quit", exitPyProc);
