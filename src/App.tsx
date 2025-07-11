import { InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient } from "apollo-client";
import { HttpLink } from "apollo-link-http";
import gql from "graphql-tag";
import fetch from "isomorphic-fetch";
import React, { useMemo, useState, useEffect, useCallback } from "react";
import * as io from "socket.io-client";
import "./App.css";

const ipcRenderer = (window as any).isInElectronRenderer
        ? (window as any).nodeRequire("electron").ipcRenderer
        : (window as any).ipcRendererStub;

const App = () => {
    const [apiPort, setApiPort] = useState(0);
    const [apiSigningKey, setApiSigningKey] = useState("");
    const [selectedFolder, setSelectedFolder] = useState("");
    const [selectedModel, setSelectedModel] = useState("yolov8n.pt");
    const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [startingTimeoutId, setStartingTimeoutId] = useState<NodeJS.Timeout | null>(null);
    const [progress, setProgress] = useState(0);
    const [progressMessages, setProgressMessages] = useState<string[]>([]);
    const [hasProgressMessages, setHasProgressMessages] = useState(false);
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [results, setResults] = useState<any[]>([]);
    const [resultsFolder, setResultsFolder] = useState("");
    const [isVideoFile, setIsVideoFile] = useState(false);
    const [eventSource, setEventSource] = useState<EventSource | null>(null);
    const [sseConnected, setSseConnected] = useState(false);
    const [socket, setSocket] = useState<SocketIOClient.Socket | null>(null);
    const [wsConnected, setWsConnected] = useState(false);

    const appGlobalClient = useMemo(() => {
        if (apiPort === 0) {
            if (ipcRenderer) {
                ipcRenderer.on("apiDetails", (_event: any, argString:string) => {
                    const arg:{ port:number, signingKey:string } = JSON.parse(argString);
                    console.log("🔗 IPC: Received API details from main process - Port:", arg.port);
                    setApiPort(arg.port);
                    setApiSigningKey(arg.signingKey);
                });
                ipcRenderer.on("apiDetailsError", (_event: any, errorMessage:string) => {
                    console.error("Python server error:", errorMessage);
                    setProgressMessages(prev => [...prev, `Python server error: ${errorMessage}`]);
                    setHasProgressMessages(true);
                });
                console.log("🔗 IPC: Requesting API details from main process");
                ipcRenderer.send("getApiDetails");
            }
            return null;
        }
        return new ApolloClient({
            cache: new InMemoryCache(),
            link: new HttpLink({
                fetch:(fetch as any),
                uri: "http://127.0.0.1:" + apiPort + "/graphql/",
            }),
        });
    }, [apiPort]);

    const loadAvailableModels = useCallback(async () => {
        if (!appGlobalClient || !apiSigningKey) return;
        
        console.log("📡 GraphQL: Loading available models");
        try {
            const { data } = await appGlobalClient.query({
                query: gql`query getModels($signingkey: String!) {
                    getModels(signingkey: $signingkey)
                }`,
                variables: { signingkey: apiSigningKey }
            });
            
            console.log("📡 GraphQL getModels response:", data.getModels);
            
            // Check if response is valid JSON
            if (data.getModels && data.getModels !== "invalid signature") {
                try {
                    const models = JSON.parse(data.getModels);
                    console.log("🤖 Available models loaded:", models);
                    setAvailableModels(models);
                    // Set better default if face models are available
                    if (models.includes("yolov8l-face.pt") && selectedModel === "yolov8n.pt") {
                        console.log("🎯 Auto-selecting better face model: yolov8l-face.pt");
                        setSelectedModel("yolov8l-face.pt");
                        setConfidenceThreshold(0.7);
                    }
                } catch (parseError) {
                    console.error("Error parsing models JSON:", parseError);
                    setAvailableModels(["yolov8n.pt"]); // Fallback to default
                }
            } else {
                console.error("Invalid signature or no models data received");
                setAvailableModels(["yolov8n.pt"]); // Fallback to default
            }
        } catch (error) {
            console.error("Error loading models:", error);
            setAvailableModels(["yolov8n.pt"]); // Fallback to default
        }
    }, [appGlobalClient, apiSigningKey, selectedModel]);

    const checkProgress = useCallback(async () => {
        if (!appGlobalClient || !apiSigningKey) return;
        
        console.log("📡 GraphQL: Checking progress and status");
        try {
            const [statusResponse, progressResponse, logsResponse] = await Promise.all([
                appGlobalClient.query({
                    query: gql`query getStatus($signingkey: String!) {
                        getStatus(signingkey: $signingkey)
                    }`,
                    variables: { signingkey: apiSigningKey }
                }),
                appGlobalClient.query({
                    query: gql`query getProgress($signingkey: String!) {
                        getProgress(signingkey: $signingkey)
                    }`,
                    variables: { signingkey: apiSigningKey }
                }),
                appGlobalClient.query({
                    query: gql`query getLogs($signingkey: String!) {
                        getLogs(signingkey: $signingkey)
                    }`,
                    variables: { signingkey: apiSigningKey }
                })
            ]);

            // Parse status response
            let status = { is_processing: false, results_count: 0 };
            let messages: string[] = [];
            
            try {
                if (statusResponse.data.getStatus && statusResponse.data.getStatus !== "invalid signature") {
                    status = JSON.parse(statusResponse.data.getStatus);
                    console.log("📊 Status update:", status);
                }
            } catch (parseError) {
                console.error("Error parsing status JSON:", parseError);
            }
            
            try {
                if (progressResponse.data.getProgress && progressResponse.data.getProgress !== "invalid signature") {
                    messages = JSON.parse(progressResponse.data.getProgress);
                    console.log("📝 Progress messages:", messages);
                }
            } catch (parseError) {
                console.error("Error parsing progress JSON:", parseError);
            }
            
            // Parse and display Python logs in console
            try {
                if (logsResponse.data.getLogs && logsResponse.data.getLogs !== "invalid signature") {
                    const pythonLogs = JSON.parse(logsResponse.data.getLogs);
                    // Only log new Python logs to avoid spam
                    pythonLogs.forEach((log: string, index: number) => {
                        console.log(`🐍 Python Log ${index + 1}:`, log);
                    });
                }
            } catch (parseError) {
                console.error("Error parsing Python logs JSON:", parseError);
            }
            
            setIsProcessing(status.is_processing);
            // Only add new messages, don't replace existing ones
            if (messages.length > 0) {
                setProgressMessages(prev => {
                    const newMessages = messages
                        .filter(msg => !prev.includes(msg))
                        .filter(msg => !msg.includes('ℹ️ DEBUG:'));
                    return [...prev, ...newMessages];
                });
                setHasProgressMessages(true);
            }
            // Don't update progress here - it's handled by SSE completion events with actual percentages
            
            // Log progress updates to console
            console.log("🔄 Progress Update:", {
                isProcessing: status.is_processing,
                resultsCount: status.results_count,
                progressMessages: messages
            });

            if (!status.is_processing) {
                console.log("📡 GraphQL: Getting final results");
                // Get final results
                const resultsResponse = await appGlobalClient.query({
                    query: gql`query getResults($signingkey: String!) {
                        getResults(signingkey: $signingkey)
                    }`,
                    variables: { signingkey: apiSigningKey }
                });
                
                try {
                    if (resultsResponse.data.getResults && resultsResponse.data.getResults !== "invalid signature") {
                        const results = JSON.parse(resultsResponse.data.getResults);
                        console.log("🎯 Final results received:", results.length, "detections");
                        setResults(results);
                    }
                } catch (parseError) {
                    console.error("Error parsing results JSON:", parseError);
                }
            }
        } catch (error) {
            console.error("Error checking progress:", error);
        }
    }, [appGlobalClient, apiSigningKey]);

    // Load available models on startup
    useEffect(() => {
        if (appGlobalClient && apiSigningKey) {
            loadAvailableModels();
        }
    }, [appGlobalClient, apiSigningKey, loadAvailableModels]);

    // Poll for progress updates when processing
    useEffect(() => {
        if (isProcessing && appGlobalClient && apiSigningKey) {
            const interval = setInterval(() => {
                checkProgress();
            }, 250); // Reduced from 1000ms to 250ms for more responsive updates
            return () => clearInterval(interval);
        } else if (!isProcessing && appGlobalClient && apiSigningKey) {
            // When processing stops, do one final check to get the results
            checkProgress();
        }
    }, [isProcessing, appGlobalClient, apiSigningKey, checkProgress]);

    const handleCompletionEvent = useCallback((data: any) => {
        console.log("🏁 Completion event:", data);
        
        switch (data.status) {
            case 'processing_started':
                // Processing has started on the backend
                console.log("🚀 Backend processing started");
                setIsProcessing(true);
                setIsStarting(false); // Clear the starting state
                setProgress(0);
                // Clear the timeout since we received the event
                if (startingTimeoutId) {
                    clearTimeout(startingTimeoutId);
                    setStartingTimeoutId(null);
                }
                break;
                
            case 'image_completed':
                // Update progress for individual images
                setProgress(data.progress_percent);
                console.log(`📸 Image ${data.image_index}/${data.total_images} completed: ${data.detections_in_image} faces found`);
                break;
                
            case 'frame_completed':
                // Update progress for video frames
                setProgress(data.progress_percent);
                console.log(`🎬 Frame ${data.frame_index} at ${data.timestamp.toFixed(1)}s: ${data.detections_in_frame} faces found`);
                break;
                
            case 'completed':
            case 'finished':
                // Final completion - fetch results and update UI
                console.log("🎯 Processing completed, fetching final results");
                setIsProcessing(false);
                setIsStarting(false); // Clear starting state if still set
                setProgress(100); // Ensure progress shows 100% when complete
                
                // Clear timeout if still active
                if (startingTimeoutId) {
                    clearTimeout(startingTimeoutId);
                    setStartingTimeoutId(null);
                }
                
                // Fetch final results
                if (appGlobalClient && apiSigningKey) {
                    checkProgress(); // This will fetch the final results
                }
                break;
                
            case 'error':
                console.error("❌ Processing error:", data.error);
                setIsProcessing(false);
                setIsStarting(false); // Clear starting state if still set
                setProgressMessages(prev => [...prev, `❌ Error: ${data.error}`]);
                setHasProgressMessages(true);
                
                // Clear timeout if still active
                if (startingTimeoutId) {
                    clearTimeout(startingTimeoutId);
                    setStartingTimeoutId(null);
                }
                break;
        }
    }, [appGlobalClient, apiSigningKey, checkProgress, startingTimeoutId]);

    const setupWebSocket = useCallback(() => {
        if (!apiPort || !apiSigningKey) return;
        
        // Close existing connection
        if (socket) {
            socket.disconnect();
        }
        
        console.log("🔄 Setting up WebSocket connection");
        const newSocket = io.connect(`http://127.0.0.1:${apiPort}`, {
            transports: ['websocket'],
            forceNew: true
        });
        
        newSocket.on('connect', () => {
            console.log("✅ WebSocket connection established");
            setWsConnected(true);
        });
        
        newSocket.on('disconnect', () => {
            console.log("❌ WebSocket disconnected");
            setWsConnected(false);
        });
        
        newSocket.on('connected', (data: any) => {
            console.log("🔗 WebSocket connection confirmed:", data);
        });
        
        newSocket.on('face_detection_event', (data: any) => {
            console.log("📡 WebSocket Event received:", data);
            
            switch (data.type) {
                case 'progress':
                    // Filter out DEBUG messages from the GUI
                    if (!data.data.includes('ℹ️ DEBUG:')) {
                        setProgressMessages(prev => [...prev, data.data]);
                        setHasProgressMessages(true);
                    }
                    break;
                    
                case 'completion':
                    handleCompletionEvent(data.data);
                    break;
                    
                default:
                    console.log("🔍 Unknown WebSocket event type:", data.type);
            }
        });
        
        newSocket.on('processing_started', (data: any) => {
            console.log("🚀 Processing started via WebSocket:", data);
            setIsProcessing(true);
            setIsStarting(false);
            setProgress(0);
            if (startingTimeoutId) {
                clearTimeout(startingTimeoutId);
                setStartingTimeoutId(null);
            }
        });
        
        newSocket.on('processing_stopped', (data: any) => {
            console.log("🛑 Processing stopped via WebSocket:", data);
            setIsProcessing(false);
            setIsStarting(false);
            if (startingTimeoutId) {
                clearTimeout(startingTimeoutId);
                setStartingTimeoutId(null);
            }
        });
        
        newSocket.on('status_update', (data: any) => {
            console.log("📊 Status update via WebSocket:", data);
            setIsProcessing(data.is_processing);
        });
        
        newSocket.on('error', (data: any) => {
            console.error("❌ WebSocket error:", data);
            setProgressMessages(prev => [...prev, `❌ Error: ${data.message}`]);
            setHasProgressMessages(true);
            setIsProcessing(false);
            setIsStarting(false);
            if (startingTimeoutId) {
                clearTimeout(startingTimeoutId);
                setStartingTimeoutId(null);
            }
        });
        
        setSocket(newSocket);
        return newSocket;
    }, [apiPort, apiSigningKey, socket, handleCompletionEvent, startingTimeoutId]);

    const setupEventSource = useCallback(() => {
        if (!apiPort || !apiSigningKey) return;
        
        // Close existing connection
        if (eventSource) {
            eventSource.close();
        }
        
        console.log("🔄 Setting up Server-Sent Events connection");
        const newEventSource = new EventSource(`http://127.0.0.1:${apiPort}/events/${apiSigningKey}/`);
        
        newEventSource.onopen = () => {
            console.log("✅ SSE connection established");
            setSseConnected(true);
        };
        
        newEventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("📡 SSE Event received:", data);
                
                switch (data.type) {
                    case 'connected':
                        console.log("🔗 SSE connection confirmed");
                        break;
                        
                    case 'progress':
                        // Filter out DEBUG messages from the GUI
                        if (!data.data.includes('ℹ️ DEBUG:')) {
                            setProgressMessages(prev => [...prev, data.data]); // Keep all messages
                            setHasProgressMessages(true);
                        }
                        break;
                        
                    case 'completion':
                        handleCompletionEvent(data.data);
                        break;
                        
                    case 'heartbeat':
                        // Ignore heartbeat events
                        break;
                        
                    default:
                        console.log("🔍 Unknown SSE event type:", data.type);
                }
            } catch (error) {
                console.error("Error parsing SSE event:", error);
            }
        };
        
        newEventSource.onerror = (error) => {
            console.error("❌ SSE connection error:", error);
            setSseConnected(false);
            // Don't automatically reconnect to avoid spam
        };
        
        setEventSource(newEventSource);
        return newEventSource;
    }, [apiPort, apiSigningKey, eventSource, handleCompletionEvent]);
    
    // Setup WebSocket connection when API details are available
    useEffect(() => {
        if (apiPort && apiSigningKey && !socket) {
            setupWebSocket();
        }
        
        // Cleanup on unmount
        return () => {
            if (socket) {
                socket.disconnect();
                setWsConnected(false);
            }
            if (eventSource) {
                eventSource.close();
                setSseConnected(false);
            }
        };
    }, [apiPort, apiSigningKey, setupWebSocket, socket]);

    const handleSelectResultsFolder = () => {
        console.log("📁 Prompting user to select results folder");
        if (ipcRenderer) {
            // Remove any existing listeners to avoid conflicts
            ipcRenderer.removeAllListeners("selected-folder");
            
            ipcRenderer.send("browse-folder");
            ipcRenderer.once("selected-folder", (event: any, folderPath: string) => {
                if (folderPath) {
                    console.log("💾 User selected results folder:", folderPath);
                    setResultsFolder(folderPath);
                }
            });
        }
    };

    const handleBrowseFolder = () => {
        console.log("🔍 User clicked 'Browse Folder' button");
        if (ipcRenderer) {
            // Remove any existing listeners to avoid conflicts
            ipcRenderer.removeAllListeners("selected-folder");
            
            ipcRenderer.send("browse-folder");
            ipcRenderer.once("selected-folder", (event: any, folderPath: string) => {
                if (folderPath) {
                    console.log("📁 User selected folder:", folderPath);
                    setSelectedFolder(folderPath);
                    setIsVideoFile(false); // Folders are not video files
                    
                    // Immediately prompt for results folder
                    setTimeout(() => {
                        handleSelectResultsFolder();
                    }, 100);
                }
            });
        }
    };

    const handleModelChange = (newModel: string) => {
        console.log("🤖 User changed model from", selectedModel, "to", newModel);
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
            setConfidenceThreshold(0.5); // Default for general models
        }
        console.log("📊 Confidence threshold auto-adjusted to", confidenceThreshold);
    };

    const handleBrowseFile = () => {
        console.log("🔍 User clicked 'Browse File' button");
        if (ipcRenderer) {
            // Remove any existing listeners to avoid conflicts
            ipcRenderer.removeAllListeners("selected-folder");
            
            ipcRenderer.send("browse-file");
            ipcRenderer.once("selected-folder", (event: any, filePath: string) => {
                if (filePath) {
                    console.log("📄 User selected file:", filePath);
                    setSelectedFolder(filePath);
                    // Check if it's a video file
                    const videoExtensions = ['.mp4', '.avi', '.mov'];
                    const isVideo = videoExtensions.some(ext => filePath.toLowerCase().endsWith(ext));
                    setIsVideoFile(isVideo);
                    console.log("🎬 Video file detected:", isVideo);
                    
                    // Immediately prompt for results folder
                    setTimeout(() => {
                        handleSelectResultsFolder();
                    }, 100);
                }
            });
        }
    };

    // Unused function - commented out to fix linting error
    // const handleLoadModel = async () => {
    //     if (!appGlobalClient) return;
    //     
    //     try {
    //         const { data } = await appGlobalClient.query({
    //             query: gql`query loadModel($signingkey: String!, $modelPath: String!) {
    //                 loadModel(signingkey: $signingkey, modelPath: $modelPath)
    //             }`,
    //             variables: { 
    //                 signingkey: apiSigningKey,
    //                 modelPath: selectedModel
    //             }
    //         });
    //         
    //         if (data.loadModel === "success") {
    //             setProgressMessages(prev => [...prev, `Model ${selectedModel} loaded successfully`]);
    //         } else {
    //             setProgressMessages(prev => [...prev, `Failed to load model: ${data.loadModel}`]);
    //         }
    //     } catch (error) {
    //         console.error("Error loading model:", error);
    //         setProgressMessages(prev => [...prev, `Error loading model: ${error}`]);
    //     }
    // };

    const handleStartProcessing = async () => {
        console.log("🚀 User clicked 'Start Detection' button");
        console.log("📊 Processing parameters:", {
            folder: selectedFolder,
            model: selectedModel,
            confidence: confidenceThreshold,
            resultsFolder: resultsFolder
        });
        
        if (!appGlobalClient || !selectedFolder || !apiSigningKey) return;
        
        if (!resultsFolder) {
            console.log("❌ No results folder selected, prompting user");
            handleSelectResultsFolder();
            return;
        }
        
        // Set initial state - show as "starting" but not fully processing yet
        setIsStarting(true);
        setResults([]);
        setProgress(0); // Reset progress to 0 when starting new processing
        setProgressMessages([]); // Clear previous progress messages
        setHasProgressMessages(true);
        
        // Ensure WebSocket connection is established before starting processing
        if (!wsConnected) {
            console.log("🔄 Ensuring WebSocket connection is established before starting processing");
            const newSocket = setupWebSocket();
            
            // Wait for WebSocket connection to be established (with timeout)
            const connectionTimeout = 5000; // 5 second timeout
            const connectionStart = Date.now();
            
            await new Promise((resolve) => {
                const checkConnection = () => {
                    if (wsConnected) {
                        console.log("✅ WebSocket connection confirmed, proceeding with processing");
                        resolve(true);
                    } else if (Date.now() - connectionStart > connectionTimeout) {
                        console.log("⏰ WebSocket connection timeout, proceeding anyway");
                        resolve(false);
                    } else {
                        // Still connecting, wait a bit more
                        setTimeout(checkConnection, 100);
                    }
                };
                checkConnection();
            });
        }
        
        // Set a timeout to clear the starting state if no SSE event is received
        const timeoutId = setTimeout(() => {
            console.log("⏰ Timeout: No processing_started event received, clearing starting state");
            setIsStarting(false);
            setProgressMessages(prev => [...prev, "⚠️ Warning: Processing may have started but connection lost"]);
        }, 10000); // 10 seconds timeout
        setStartingTimeoutId(timeoutId);
        
        try {
            // Use WebSocket for starting processing
            if (socket && wsConnected) {
                console.log("🚀 Starting processing via WebSocket");
                socket.emit('start_detection', {
                    signingkey: apiSigningKey,
                    folderPath: selectedFolder,
                    confidence: confidenceThreshold,
                    model: selectedModel,
                    saveResults: true,
                    resultsFolder: resultsFolder
                });
            } else {
                // Fallback to GraphQL if WebSocket is not available
                console.log("🔄 WebSocket not available, falling back to GraphQL");
                const { data } = await appGlobalClient.query({
                    query: gql`query startProcessing($signingkey: String!, $folderPath: String!, $confidence: Float!, $model: String!, $saveResults: Boolean, $resultsFolder: String) {
                        startProcessing(signingkey: $signingkey, folderPath: $folderPath, confidence: $confidence, model: $model, saveResults: $saveResults, resultsFolder: $resultsFolder)
                    }`,
                    variables: {
                        signingkey: apiSigningKey,
                        folderPath: selectedFolder,
                        confidence: confidenceThreshold,
                        model: selectedModel,
                        saveResults: true,
                        resultsFolder: resultsFolder
                    }
                });
                
                console.log("📡 GraphQL startProcessing response:", data.startProcessing);
                
                if (data.startProcessing.startsWith("error")) {
                    const errorMessage = data.startProcessing;
                    setProgressMessages(prev => [...prev, errorMessage]);
                    setHasProgressMessages(true);
                    setIsProcessing(false);
                    setIsStarting(false);
                    // Clear timeout on error
                    if (startingTimeoutId) {
                        clearTimeout(startingTimeoutId);
                        setStartingTimeoutId(null);
                    }
                    console.log("❌ Processing Error:", errorMessage);
                } else {
                    console.log("✅ Processing Started Successfully");
                    // The 'processing_started' event will set isProcessing=true when backend confirms processing started
                    // Keep isStarting=true until we receive the processing_started event
                }
            }
        } catch (error) {
            console.error("Error starting processing:", error);
            setProgressMessages(prev => [...prev, `Error starting processing: ${error}`]);
            setHasProgressMessages(true);
            setIsProcessing(false);
            setIsStarting(false);
            // Clear timeout on error
            if (startingTimeoutId) {
                clearTimeout(startingTimeoutId);
                setStartingTimeoutId(null);
            }
        }
    };

    const handleStopProcessing = useCallback(async () => {
        console.log("🛑 User clicked 'Stop Processing' button");
        if (!apiSigningKey) return;
        
        try {
            // Use WebSocket for stopping processing
            if (socket && wsConnected) {
                console.log("🛑 Stopping processing via WebSocket");
                socket.emit('stop_detection', {
                    signingkey: apiSigningKey
                });
            } else {
                // Fallback to GraphQL if WebSocket is not available
                console.log("🔄 WebSocket not available, falling back to GraphQL");
                if (appGlobalClient) {
                    await appGlobalClient.query({
                        query: gql`query stopProcessing($signingkey: String!) {
                            stopProcessing(signingkey: $signingkey)
                        }`,
                        variables: { signingkey: apiSigningKey }
                    });
                    console.log("📡 GraphQL stopProcessing completed");
                    setIsProcessing(false);
                    setIsStarting(false); // Clear starting state
                    // Clear timeout if still active
                    if (startingTimeoutId) {
                        clearTimeout(startingTimeoutId);
                        setStartingTimeoutId(null);
                    }
                }
            }
        } catch (error) {
            console.error("Error stopping processing:", error);
        }
    }, [appGlobalClient, apiSigningKey, startingTimeoutId, socket, wsConnected]);


    const handleOpenResults = () => {
        console.log("📁 User clicked 'Open Results' button");
        if (!resultsFolder) {
            console.log("❌ No results folder to open");
            return;
        }
        
        console.log("📁 Opening results folder:", resultsFolder);
        if (ipcRenderer) {
            ipcRenderer.send("open-folder", resultsFolder);
        }
    };

    if (!appGlobalClient) {
        return <div style={{padding: '20px', fontSize: '18px', color: '#333'}}>Connecting to Python backend... (Port: {apiPort})</div>;
    }

    return (
        <div className="App">
            <div className="app-container">
                <div className="left-panel">
                    <h2>TinyExplorer FaceDetectionApp</h2>
                    <div className="connection-status">
                        <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
                            {wsConnected ? '✅' : '❌'}
                        </span>
                        <span className="status-text">
                            {wsConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
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
                                    console.log("📊 User adjusted confidence threshold from", confidenceThreshold, "to", newValue);
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
                                disabled={!selectedFolder}
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
