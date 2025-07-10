import { InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient } from "apollo-client";
import { HttpLink } from "apollo-link-http";
import gql from "graphql-tag";
import fetch from "isomorphic-fetch";
import React, { useMemo, useState, useEffect, useCallback } from "react";
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
    const [progress, setProgress] = useState(0);
    const [progressMessages, setProgressMessages] = useState<string[]>([]);
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [results, setResults] = useState<any[]>([]);

    const appGlobalClient = useMemo(() => {
        if (apiPort === 0) {
            if (ipcRenderer) {
                ipcRenderer.on("apiDetails", (_event: any, argString:string) => {
                    const arg:{ port:number, signingKey:string } = JSON.parse(argString);
                    setApiPort(arg.port);
                    setApiSigningKey(arg.signingKey);
                });
                ipcRenderer.on("apiDetailsError", (_event: any, errorMessage:string) => {
                    console.error("Python server error:", errorMessage);
                    setProgressMessages(prev => [...prev, `Python server error: ${errorMessage}`]);
                });
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
        
        try {
            const { data } = await appGlobalClient.query({
                query: gql`query getModels($signingkey: String!) {
                    getModels(signingkey: $signingkey)
                }`,
                variables: { signingkey: apiSigningKey }
            });
            
            // Check if response is valid JSON
            if (data.getModels && data.getModels !== "invalid signature") {
                try {
                    const models = JSON.parse(data.getModels);
                    setAvailableModels(models);
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
    }, [appGlobalClient, apiSigningKey]);

    const checkProgress = useCallback(async () => {
        if (!appGlobalClient || !apiSigningKey) return;
        
        try {
            const [statusResponse, progressResponse] = await Promise.all([
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
                })
            ]);

            // Parse status response
            let status = { is_processing: false, results_count: 0 };
            let messages = [];
            
            try {
                if (statusResponse.data.getStatus && statusResponse.data.getStatus !== "invalid signature") {
                    status = JSON.parse(statusResponse.data.getStatus);
                }
            } catch (parseError) {
                console.error("Error parsing status JSON:", parseError);
            }
            
            try {
                if (progressResponse.data.getProgress && progressResponse.data.getProgress !== "invalid signature") {
                    messages = JSON.parse(progressResponse.data.getProgress);
                }
            } catch (parseError) {
                console.error("Error parsing progress JSON:", parseError);
            }
            
            setIsProcessing(status.is_processing);
            setProgressMessages(messages);
            setProgress(status.results_count);

            if (!status.is_processing) {
                // Get final results
                const resultsResponse = await appGlobalClient.query({
                    query: gql`query getResults($signingkey: String!) {
                        getResults(signingkey: $signingkey)
                    }`,
                    variables: { signingkey: apiSigningKey }
                });
                
                try {
                    if (resultsResponse.data.getResults && resultsResponse.data.getResults !== "invalid signature") {
                        setResults(JSON.parse(resultsResponse.data.getResults));
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
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [isProcessing, appGlobalClient, apiSigningKey, checkProgress]);

    const handleBrowseFolder = () => {
        if (ipcRenderer) {
            ipcRenderer.send("browse-folder");
            ipcRenderer.on("selected-folder", (event: any, folderPath: string) => {
                if (folderPath) {
                    setSelectedFolder(folderPath);
                }
            });
        }
    };

    const handleBrowseFile = () => {
        if (ipcRenderer) {
            ipcRenderer.send("browse-file");
            ipcRenderer.on("selected-folder", (event: any, filePath: string) => {
                if (filePath) {
                    setSelectedFolder(filePath);
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
        if (!appGlobalClient || !selectedFolder || !apiSigningKey) return;
        
        setIsProcessing(true);
        setResults([]);
        setProgressMessages([]);
        
        try {
            const { data } = await appGlobalClient.query({
                query: gql`query startProcessing($signingkey: String!, $folderPath: String!, $confidence: Float!, $model: String!) {
                    startProcessing(signingkey: $signingkey, folderPath: $folderPath, confidence: $confidence, model: $model)
                }`,
                variables: {
                    signingkey: apiSigningKey,
                    folderPath: selectedFolder,
                    confidence: confidenceThreshold,
                    model: selectedModel
                }
            });
            
            if (data.startProcessing.startsWith("error")) {
                setProgressMessages(prev => [...prev, data.startProcessing]);
                setIsProcessing(false);
            }
        } catch (error) {
            console.error("Error starting processing:", error);
            setProgressMessages(prev => [...prev, `Error starting processing: ${error}`]);
            setIsProcessing(false);
        }
    };

    const handleStopProcessing = async () => {
        if (!appGlobalClient || !apiSigningKey) return;
        
        try {
            await appGlobalClient.query({
                query: gql`query stopProcessing($signingkey: String!) {
                    stopProcessing(signingkey: $signingkey)
                }`,
                variables: { signingkey: apiSigningKey }
            });
            setIsProcessing(false);
        } catch (error) {
            console.error("Error stopping processing:", error);
        }
    };

    if (!appGlobalClient) {
        return <div style={{padding: '20px', fontSize: '18px', color: '#333'}}>Connecting to Python backend... (Port: {apiPort})</div>;
    }

    return (
        <div className="App">
            <div className="app-container">
                <div className="left-panel">
                    <h2>Face Recognition App</h2>
                    
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
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="model-select"
                        >
                            {availableModels.map(model => (
                                <option key={model} value={model}>{model}</option>
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
                                step="0.1" 
                                value={confidenceThreshold}
                                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                                className="threshold-slider"
                            />
                            <span className="threshold-value">{confidenceThreshold.toFixed(1)}</span>
                        </div>
                    </div>

                    <div className="control-section">
                        {!isProcessing ? (
                            <button 
                                onClick={handleStartProcessing}
                                disabled={!selectedFolder}
                                className="start-btn"
                            >
                                Start Recognition
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

                    {isProcessing && (
                        <div className="progress-section">
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill" 
                                    style={{ width: `${Math.min(progress * 2, 100)}%` }}
                                />
                            </div>
                            <div className="progress-text">{progress}%</div>
                        </div>
                    )}
                </div>

                <div className="right-panel">
                    <div className="results-container">
                        {progressMessages.length > 0 && (
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
                                <h3>Results: {results.length} face detections found</h3>
                                <div className="results-window">
                                    {results.map((result, index) => (
                                        <div key={index}>
                                            Image: {result.image_path} | 
                                            Confidence: {result.confidence.toFixed(3)} | 
                                            BBox: [{result.bbox.join(', ')}]
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {!progressMessages.length && !results.length && (
                            <div className="empty-state">
                                <p>Select a file or folder and start recognition to see results here.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default App;
