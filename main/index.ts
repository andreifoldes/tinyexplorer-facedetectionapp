import { app, BrowserWindow, ipcMain, dialog, shell } from "electron"; // tslint:disable-line
import * as path from "path";

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
    
    // Import Python subprocess handler after app is ready
    require("./with-python-subprocess");
    
    createWindow();
});

// Disable GPU acceleration for better compatibility with remote displays
app.disableHardwareAcceleration();

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
    ipcMain.on("browse-folder", async (event: any) => {
        const result = await dialog.showOpenDialog(win, {
            properties: ["openDirectory"]
        });
        if (!result.canceled && result.filePaths && result.filePaths.length > 0) {
            event.sender.send("selected-folder", result.filePaths[0]);
        } else {
            event.sender.send("selected-folder", null);
        }
    });

    // Handle file browsing
    ipcMain.on("browse-file", async (event: any) => {
        const result = await dialog.showOpenDialog(win, {
            properties: ["openFile"],
            filters: [
                { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'] },
                { name: 'Videos', extensions: ['mp4', 'avi', 'mov'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });
        if (!result.canceled && result.filePaths && result.filePaths.length > 0) {
            event.sender.send("selected-folder", result.filePaths[0]);
        } else {
            event.sender.send("selected-folder", null);
        }
    });

    // Handle CSV file saving
    ipcMain.on("save-csv", async (event: any) => {
        const result = await dialog.showSaveDialog(win, {
            filters: [
                { name: 'CSV Files', extensions: ['csv'] },
                { name: 'All Files', extensions: ['*'] }
            ],
            defaultPath: 'face_detection_results.csv'
        });
        if (!result.canceled && result.filePath) {
            event.sender.send("selected-save-path", result.filePath);
        } else {
            event.sender.send("selected-save-path", null);
        }
    });

    // Handle opening folder in system file manager
    ipcMain.on("open-folder", async (event: any, folderPath: string) => {
        try {
            const result = await shell.openPath(folderPath);
            if (result) {
                console.log("Successfully opened folder:", folderPath);
            } else {
                console.error("Failed to open folder:", folderPath);
            }
        } catch (error) {
            console.error("Error opening folder:", error);
        }
    });
}
