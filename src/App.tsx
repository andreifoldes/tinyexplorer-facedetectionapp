import React, { useState, useEffect, useCallback } from "react";
import "./App.css";

const ipcRenderer = (window as any).isInElectronRenderer
    ? (window as any).nodeRequire("electron").ipcRenderer
    : (window as any).ipcRendererStub;

const App = () => {
    const [selectedFolder, setSelectedFolder] = useState("");
    const [selectedModel, setSelectedModel] = useState("yolov8n.pt");
    const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [progress, setProgress] = useState(0);
    const [progressMessages, setProgressMessages] = useState<string[]>([]);
    const [hasProgressMessages, setHasProgressMessages] = useState(false);
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [results, setResults] = useState<any[]>([]);
    const [resultsFolder, setResultsFolder] = useState("");
    const [isVideoFile, setIsVideoFile] = useState(false);
    const [pythonReady, setPythonReady] = useState(false);

    // Send command to Python via IPC
    const sendPythonCommand = useCallback((command: any): Promise<any> => {
        return new Promise((resolve, reject) => {
            if (!ipcRenderer) {
                reject(new Error("IPC not available"));
                return;
            }

            const timeout = setTimeout(() => {
                reject(new Error("Command timeout"));
            }, 30000); // 30 second timeout

            // Listen for response
            const handleResponse = (event: any, data: any) => {
                clearTimeout(timeout);
                ipcRenderer.removeListener("python-response", handleResponse);
                
                if (data.error) {
                    reject(new Error(data.error));
                } else {
                    resolve(data.response);
                }
            };

            ipcRenderer.on("python-response", handleResponse);
            ipcRenderer.send("python-command", command);
        });
    }, []);

    // Load available models
    const loadAvailableModels = useCallback(async () => {
        try {
            console.log("Loading available models...");
            const response = await sendPythonCommand({ type: 'get_models' });
            
            if (response.status === 'success') {
                console.log("Available models loaded:", response.models);
                setAvailableModels(response.models);
                
                // Set better default if face models are available
                if (response.models.includes("yolov8l-face.pt") && selectedModel === "yolov8n.pt") {
                    console.log("Auto-selecting better face model: yolov8l-face.pt");
                    setSelectedModel("yolov8l-face.pt");
                    setConfidenceThreshold(0.7);
                }
            } else {
                console.error("Failed to load models:", response.message);
                setAvailableModels(["yolov8n.pt"]); // Fallback
            }
        } catch (error) {
            console.error("Error loading models:", error);
            setAvailableModels(["yolov8n.pt"]); // Fallback
        }
    }, [sendPythonCommand, selectedModel]);

    // Check Python status
    const checkPythonStatus = useCallback(() => {
        if (ipcRenderer) {
            ipcRenderer.send("getPythonStatus");
        }
    }, []);

    // Handle Python events
    useEffect(() => {
        if (!ipcRenderer) return;

        const handlePythonEvent = (event: any, eventData: any) => {
            console.log("Python event received:", eventData);
            
            switch (eventData.type) {
                case 'progress':
                    if (!eventData.data.includes('ℹ️ DEBUG:')) {
                        setProgressMessages(prev => [...prev, eventData.data]);
                        setHasProgressMessages(true);
                    }
                    break;
                    
                case 'completion':
                    handleCompletionEvent(eventData.data);
                    break;
                    
                default:
                    console.log("Unknown event type:", eventData.type);
            }
        };

        const handlePythonStatus = (event: any, statusData: any) => {
            console.log("Python status:", statusData);
            setPythonReady(statusData.ready);
            
            if (statusData.ready && availableModels.length === 0) {
                // Load models when Python becomes ready
                loadAvailableModels();
            }
        };

        ipcRenderer.on("python-event", handlePythonEvent);
        ipcRenderer.on("pythonStatus", handlePythonStatus);

        // Check status immediately
        checkPythonStatus();

        return () => {
            ipcRenderer.removeListener("python-event", handlePythonEvent);
            ipcRenderer.removeListener("pythonStatus", handlePythonStatus);
        };
    }, [availableModels.length, checkPythonStatus, loadAvailableModels]);

    const handleCompletionEvent = useCallback((data: any) => {
        console.log("Completion event:", data);
        
        switch (data.status) {
            case 'processing_started':
                console.log("Backend processing started");
                setIsProcessing(true);
                setIsStarting(false);
                setProgress(0);
                break;
                
            case 'image_completed':
                setProgress(data.progress_percent);
                console.log(`Image ${data.image_index}/${data.total_images} completed: ${data.detections_in_image} faces found`);
                break;
                
            case 'frame_completed':
                setProgress(data.progress_percent);
                console.log(`Frame ${data.frame_index} at ${data.timestamp.toFixed(1)}s: ${data.detections_in_frame} faces found`);
                break;
                
            case 'completed':
            case 'finished':
                console.log("Processing completed, fetching final results");
                setIsProcessing(false);
                setIsStarting(false);
                setProgress(100);
                
                // Fetch final results
                fetchResults();
                break;
                
            case 'error':
                console.error("Processing error:", data.error);
                setIsProcessing(false);
                setIsStarting(false);
                setProgressMessages(prev => [...prev, `❌ Error: ${data.error}`]);
                setHasProgressMessages(true);
                break;
        }
    }, []);

    const fetchResults = useCallback(async () => {
        try {
            const response = await sendPythonCommand({ type: 'get_results' });
            
            if (response.status === 'success') {
                console.log("Final results received:", response.results.length, "detections");
                setResults(response.results);
            } else {
                console.error("Failed to fetch results:", response.message);
            }
        } catch (error) {
            console.error("Error fetching results:", error);
        }
    }, [sendPythonCommand]);

    const handleSelectResultsFolder = () => {
        console.log("Prompting user to select results folder");
        if (ipcRenderer) {
            ipcRenderer.removeAllListeners("selected-folder");
            
            ipcRenderer.send("browse-folder");
            ipcRenderer.once("selected-folder", (event: any, folderPath: string) => {
                if (folderPath) {
                    console.log("User selected results folder:", folderPath);
                    setResultsFolder(folderPath);
                }
            });
        }
    };

    const handleBrowseFolder = () => {
        console.log("User clicked 'Browse Folder' button");
        if (ipcRenderer) {
            ipcRenderer.removeAllListeners("selected-folder");
            
            ipcRenderer.send("browse-folder");
            ipcRenderer.once("selected-folder", (event: any, folderPath: string) => {
                if (folderPath) {
                    console.log("User selected folder:", folderPath);
                    setSelectedFolder(folderPath);
                    setIsVideoFile(false);
                    
                    // Prompt for results folder
                    setTimeout(() => {
                        handleSelectResultsFolder();
                    }, 100);
                }
            });
        }
    };

    const handleBrowseFile = () => {
        console.log("User clicked 'Browse File' button");
        if (ipcRenderer) {
            ipcRenderer.removeAllListeners("selected-folder");
            
            ipcRenderer.send("browse-file");
            ipcRenderer.once("selected-folder", (event: any, filePath: string) => {
                if (filePath) {
                    console.log("User selected file:", filePath);
                    setSelectedFolder(filePath);
                    
                    // Check if it's a video file
                    const videoExtensions = ['.mp4', '.avi', '.mov'];
                    const isVideo = videoExtensions.some(ext => filePath.toLowerCase().endsWith(ext));
                    setIsVideoFile(isVideo);
                    console.log("Video file detected:", isVideo);
                    
                    // Prompt for results folder
                    setTimeout(() => {
                        handleSelectResultsFolder();
                    }, 100);
                }
            });
        }
    };

    const handleModelChange = (newModel: string) => {
        console.log("User changed model from", selectedModel, "to", newModel);
        setSelectedModel(newModel);
        
        // Set appropriate confidence thresholds based on model
        if (newModel === "RetinaFace") {
            setConfidenceThreshold(0.9);
        } else if (newModel.includes("face")) {
            if (newModel.includes("yolov8n-face")) {
                setConfidenceThreshold(0.3);
            } else if (newModel.includes("yolov8m-face")) {
                setConfidenceThreshold(0.5);
            } else if (newModel.includes("yolov8l-face")) {
                setConfidenceThreshold(0.7);
            } else if (newModel.includes("yolov11m-face")) {
                setConfidenceThreshold(0.6);
            } else if (newModel.includes("yolov11l-face")) {
                setConfidenceThreshold(0.8);
            }
        } else {
            setConfidenceThreshold(0.5);
        }
    };

    const handleStartProcessing = async () => {
        console.log("User clicked 'Start Detection' button");
        console.log("Processing parameters:", {
            folder: selectedFolder,
            model: selectedModel,
            confidence: confidenceThreshold,
            resultsFolder: resultsFolder
        });
        
        if (!selectedFolder || !pythonReady) return;
        
        if (!resultsFolder) {
            console.log("No results folder selected, prompting user");
            handleSelectResultsFolder();
            return;
        }
        
        setIsStarting(true);
        setResults([]);
        setProgress(0);
        setProgressMessages([]);
        setHasProgressMessages(true);
        
        try {
            const response = await sendPythonCommand({
                type: 'start_processing',
                data: {
                    folder_path: selectedFolder,
                    confidence: confidenceThreshold,
                    model: selectedModel,
                    save_results: true,
                    results_folder: resultsFolder
                }
            });
            
            if (response.status === 'success') {
                console.log("Processing started successfully");
                // Processing state will be updated by events
            } else {
                console.error("Failed to start processing:", response.message);
                setProgressMessages(prev => [...prev, `❌ Error: ${response.message}`]);
                setIsStarting(false);
            }
        } catch (error) {
            console.error("Error starting processing:", error);
            setProgressMessages(prev => [...prev, `❌ Error: ${error}`]);
            setIsStarting(false);
        }
    };

    const handleStopProcessing = async () => {
        console.log("User clicked 'Stop Processing' button");
        
        try {
            const response = await sendPythonCommand({ type: 'stop_processing' });
            
            if (response.status === 'success') {
                console.log("Processing stopped successfully");
                setIsProcessing(false);
                setIsStarting(false);
            } else {
                console.error("Failed to stop processing:", response.message);
            }
        } catch (error) {
            console.error("Error stopping processing:", error);
        }
    };

    const handleOpenResults = () => {
        console.log("User clicked 'Open Results' button");
        if (!resultsFolder) {
            console.log("No results folder to open");
            return;
        }
        
        console.log("Opening results folder:", resultsFolder);
        if (ipcRenderer) {
            ipcRenderer.send("open-folder", resultsFolder);
        }
    };

    if (!pythonReady) {
        return (
            <div style={{padding: '20px', fontSize: '18px', color: '#333'}}>
                Connecting to Python backend...
            </div>
        );
    }

    return (
        <div className="App">
            <div className="app-container">
                <div className="left-panel">
                    <h2>TinyExplorer FaceDetectionApp</h2>
                    <div className="connection-status">
                        <span className={`status-indicator ${pythonReady ? 'connected' : 'disconnected'}`}>
                            {pythonReady ? '✅' : '❌'}
                        </span>
                        <span className="status-text">
                            {pythonReady ? 'Python Ready' : 'Python Not Ready'}
                        </span>
                    </div>
                    
                    <div className="control-section">
                        <label>Select File or Folder:</label>
                        <div className="file-input-group">
                            <input 
                                type="text" 
                                value={selectedFolder} 
                                readOnly 
                                placeholder="No file or folder selected..."
                                className="file-input"
                            />
                        </div>
                        <div className="button-group">
                            <button onClick={handleBrowseFile} className="browse-btn">Browse File</button>
                            <button onClick={handleBrowseFolder} className="browse-btn">Browse Folder</button>
                        </div>
                    </div>

                    <div className="control-section">
                        <label>Select Model:</label>
                        <select 
                            value={selectedModel} 
                            onChange={(e) => handleModelChange(e.target.value)}
                            className="model-select"
                        >
                            {availableModels.map(model => (
                                <option key={model} value={model}>
                                    {model === "RetinaFace" ? "RetinaFace (High Accuracy)" : model}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="control-section">
                        <label>Select Confidence Threshold:</label>
                        <div className="threshold-control">
                            <input 
                                type="range" 
                                min="0.1" 
                                max="1.0" 
                                step="0.01" 
                                value={confidenceThreshold}
                                onChange={(e) => {
                                    const newValue = parseFloat(e.target.value);
                                    console.log("User adjusted confidence threshold from", confidenceThreshold, "to", newValue);
                                    setConfidenceThreshold(newValue);
                                }}
                                className="threshold-slider"
                            />
                            <span className="threshold-value">{confidenceThreshold.toFixed(2)}</span>
                        </div>
                    </div>

                    <div className="control-section">
                        <label>Results will be saved to:</label>
                        <div className="file-input-group">
                            <input 
                                type="text" 
                                value={resultsFolder} 
                                readOnly 
                                placeholder="No results folder selected..."
                                className="file-input"
                            />
                            <button onClick={handleSelectResultsFolder} className="browse-btn">Select Results Folder</button>
                        </div>
                        {isVideoFile && (
                            <div className="file-info">
                                <small><span role="img" aria-label="movie camera">🎬</span> Video file detected - will process 1 frame per second</small>
                            </div>
                        )}
                    </div>

                    <div className="control-section">
                        {!isProcessing && !isStarting ? (
                            <button 
                                onClick={handleStartProcessing}
                                disabled={!selectedFolder || !pythonReady}
                                className="start-btn"
                            >
                                Start Detection
                            </button>
                        ) : isStarting ? (
                            <button 
                                disabled
                                className="start-btn starting"
                            >
                                Starting...
                            </button>
                        ) : (
                            <button 
                                onClick={handleStopProcessing}
                                className="stop-btn"
                            >
                                Stop Processing
                            </button>
                        )}
                    </div>

                    {(isProcessing || isStarting) && (
                        <div className="progress-section">
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill" 
                                    style={{ width: `${Math.min(progress, 100)}%` }}
                                />
                            </div>
                            <div className="progress-text">{progress.toFixed(1)}%</div>
                        </div>
                    )}
                </div>

                <div className="right-panel">
                    <div className="results-container">
                        {hasProgressMessages && (
                            <div className="progress-messages">
                                <h3>Progress Updates:</h3>
                                <div className="message-window">
                                    {progressMessages.map((message, index) => (
                                        <div key={index}>{message}</div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {results.length > 0 && (
                            <div className="results-section">
                                <div className="results-header">
                                    <h3>Results: {results.length} face detections found</h3>
                                    <button 
                                        onClick={handleOpenResults}
                                        className="export-btn"
                                        disabled={isProcessing || !resultsFolder}
                                    >
                                        <span role="img" aria-label="folder">📁</span> Open Results
                                    </button>
                                </div>
                                <div className="results-window">
                                    {results.map((result, index) => (
                                        <div key={index} className="result-item">
                                            <div><strong>File:</strong> {result.image_path ? result.image_path.split('/').pop() : 'Unknown'}</div>
                                            <div><strong>Confidence:</strong> {result.confidence ? result.confidence.toFixed(3) : 'N/A'}</div>
                                            <div><strong>Position:</strong> x:{Math.round(result.x || 0)}, y:{Math.round(result.y || 0)}</div>
                                            <div><strong>Size:</strong> {Math.round(result.width || 0)} × {Math.round(result.height || 0)}</div>
                                            {result.frame_idx !== undefined && (
                                                <div><strong>Frame:</strong> {result.frame_idx} (Time: {result.timestamp ? result.timestamp.toFixed(1) : '0.0'}s)</div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {!hasProgressMessages && !results.length && (
                            <div className="empty-state">
                                <p>Select a file or folder and start detection to see results here.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default App;