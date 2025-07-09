import { app, BrowserWindow, ipcMain, dialog } from "electron"; // tslint:disable-line
import * as path from "path";
import "./with-python";

const isDev = (process.env.NODE_ENV === "development");

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});

app.on("ready", () => {
    if (isDev) {
        const sourceMapSupport = require("source-map-support"); // tslint:disable-line
        sourceMapSupport.install();
    }
    createWindow();
});

function createWindow() {
    const win = new BrowserWindow({
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });
    
    if (isDev) {
        win.webContents.openDevTools();
    }
    
    if (isDev) {
        win.loadURL("http://localhost:3000/index.html");
    } else {
        win.loadURL(`file://${path.join(__dirname, "/../build/index.html")}`);
    }

    // Handle folder browsing
    ipcMain.on("browse-folder", (event: any) => {
        dialog.showOpenDialog(win, {
            properties: ["openDirectory"]
        }, (filePaths?: string[]) => {
            if (filePaths && filePaths.length > 0) {
                event.reply("selected-folder", filePaths[0]);
            } else {
                event.reply("selected-folder", null);
            }
        });
    });

    // Handle file browsing
    ipcMain.on("browse-file", (event: any) => {
        dialog.showOpenDialog(win, {
            properties: ["openFile"],
            filters: [
                { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        }, (filePaths?: string[]) => {
            if (filePaths && filePaths.length > 0) {
                event.reply("selected-folder", filePaths[0]);
            } else {
                event.reply("selected-folder", null);
            }
        });
    });
}
