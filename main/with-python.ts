import childProcess from "child_process";
import crossSpawn from "cross-spawn";
import Electron, { app, dialog, ipcMain } from "electron"; // tslint:disable-line
import fs from "fs";
import getPort from "get-port";
import * as path from "path";
import superagent from "superagent";
import uuid from "uuid";

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
    // dialog.showErrorBox("success", "initializeApi");
    const availablePort = await getPort();
    apiDetails.port = isDev ? 5000 : availablePort;
    const key = isDev ? "devkey" : uuid.v4();
    apiDetails.signingKey = key;
    const srcPath = path.join(__dirname, "..", PY_FOLDER, PY_MODULE + ".py");
    const launcherPath = path.join(__dirname, "..", PY_FOLDER, PY_LAUNCHER);
    const distLauncherPath = path.join(__dirname, "..", PY_DIST_FOLDER, "python", PY_LAUNCHER);
    
    if (__dirname.indexOf("app.asar") > 0) {
        // dialog.showErrorBox("info", "packaged");
        if (fs.existsSync(distLauncherPath)) {
            pyProc = crossSpawn("python", [distLauncherPath, "--apiport", String(apiDetails.port), "--signingkey", apiDetails.signingKey]);
        } else {
            dialog.showErrorBox("Error", "Packaged python launcher not found at: " + distLauncherPath);
        }
    } else {
        // dialog.showErrorBox("info", "unpackaged");
        if (fs.existsSync(srcPath)) {
            pyProc = crossSpawn("python", [srcPath, "--apiport", String(apiDetails.port), "--signingkey", apiDetails.signingKey]);
        } else if (fs.existsSync(launcherPath)) {
            pyProc = crossSpawn("python", [launcherPath, "--apiport", String(apiDetails.port), "--signingkey", apiDetails.signingKey]);
        } else {
            dialog.showErrorBox("Error", "Unpackaged python source not found");
        }
    }
    if (pyProc === null || pyProc === undefined) {
        dialog.showErrorBox("Error", "unable to start python server");
    } else {
        console.log("Server running at http://127.0.0.1:" + apiDetails.port);
    }
    console.log("leaving initializeApi()");
};

ipcMain.on("getApiDetails", (event:Electron.Event) => {
    if (apiDetails.signingKey !== "") {
        event.sender.send("apiDetails", JSON.stringify(apiDetails));
    } else {
        initializeApi()
            .then(() => {
                event.sender.send("apiDetails", JSON.stringify(apiDetails));
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
