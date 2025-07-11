from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from graphene import ObjectType, String, Schema, Float, List, Boolean
from calc import calc as real_calc
from face_detection import FaceDetectionProcessor
import argparse
import os
import threading
import json
import queue
import time

#
# Notes on setting up a flask GraphQL server
# https://codeburst.io/how-to-build-a-graphql-wrapper-for-a-restful-api-in-python-b49767676630
#
# Notes on using pyinstaller to package a flask server (discussing issues that don't come up
# in this simple example but likely would come up in a more real application)
# for making pyinstaller see https://mapopa.blogspot.com/2013/10/flask-and-pyinstaller-notice.html
# and https://github.com/pyinstaller/pyinstaller/issues/1071
# and https://elc.github.io/posts/executable-flask-pyinstaller/
#

class Query(ObjectType):

#
# IMPORTANT - There is currently nothing preventing a malicious web page
#             running in the users web browser from making requests of this
#             server. If you add additional code here you will need to make
#             sure its either code that is appropriate for a malicious web
#             page to be able to run (like the calculator example below) or
#             that you wrap some kind of security model around the python
#             web server before adding the code.
#

    awake = String(description="Awake")
    def resolve_awake(self, args):
        return "Awake"

    exit = String(description="Exit", signingkey=String(required=True))
    def resolve_exit(self, info, signingkey):
        if signingkey != apiSigningKey:
            return
        os._exit(0)
        return

    hello = String(description="Hello", signingkey=String(required=True))
    def resolve_hello(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        return "World"
    
    calc = String(description="Calculator", signingkey=String(required=True), math=String(required=True))
    def resolve_calc(self, info, signingkey, math):
        """based on the input text, return the int result"""
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            return real_calc(math)
        except Exception:
            return 0.0
    
    echo = String(description="Echo", signingkey=String(required=True), text=String(required=True))
    def resolve_echo(self, info, signingkey, text):
        if signingkey != apiSigningKey:
            return "invalid signature"
        """echo any text"""
        return text
    
    # Face Detection endpoints
    load_model = String(description="Load YOLO model", signingkey=String(required=True), model_path=String(required=True))
    def resolve_load_model(self, info, signingkey, model_path):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            success = face_processor.load_model(model_path)
            return "success" if success else "failed"
        except Exception as e:
            return f"error: {str(e)}"
    
    get_models = String(description="Get available models", signingkey=String(required=True))
    def resolve_get_models(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            models = face_processor.get_available_models()
            return json.dumps(models)
        except Exception as e:
            return f"error: {str(e)}"
    
    start_processing = String(description="Start face detection processing",
                             signingkey=String(required=True), 
                             folder_path=String(required=True),
                             confidence=Float(required=True),
                             model=String(required=True),
                             save_results=Boolean(),
                             results_folder=String())
    def resolve_start_processing(self, info, signingkey, folder_path, confidence, model, save_results=False, results_folder=None):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            # Start processing in a separate thread
            # The processing_started event will be sent from the process_folder method
            thread = threading.Thread(target=face_processor.process_folder, 
                                    args=(folder_path, confidence, model, save_results, results_folder))
            thread.start()
            return "processing started"
        except Exception as e:
            return f"error: {str(e)}"
    
    stop_processing = String(description="Stop processing", signingkey=String(required=True))
    def resolve_stop_processing(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            face_processor.stop_processing()
            return "processing stopped"
        except Exception as e:
            return f"error: {str(e)}"
    
    get_results = String(description="Get processing results", signingkey=String(required=True))
    def resolve_get_results(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            results = face_processor.get_results()
            return json.dumps(results)
        except Exception as e:
            return f"error: {str(e)}"
    
    get_status = String(description="Get processing status", signingkey=String(required=True))
    def resolve_get_status(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            status = {
                "is_processing": face_processor.is_processing,
                "results_count": len(face_processor.results)
            }
            return json.dumps(status)
        except Exception as e:
            return f"error: {str(e)}"
    
    get_progress = String(description="Get progress messages", signingkey=String(required=True))
    def resolve_get_progress(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            messages = progress_messages[-10:]  # Get last 10 messages
            return json.dumps(messages)
        except Exception as e:
            return f"error: {str(e)}"
    
    get_logs = String(description="Get Python logs", signingkey=String(required=True))
    def resolve_get_logs(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            logs = python_logs[-20:]  # Get last 20 log messages
            return json.dumps(logs)
        except Exception as e:
            return f"error: {str(e)}"
    
    export_csv = String(description="Export results to CSV", 
                       signingkey=String(required=True),
                       output_path=String(required=True))
    def resolve_export_csv(self, info, signingkey, output_path):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            results = face_processor.get_results()
            success = face_processor.export_results_to_csv(results, output_path)
            return "success" if success else "failed"
        except Exception as e:
            return f"error: {str(e)}"
    
    process_video = String(description="Process single video file",
                          signingkey=String(required=True),
                          video_path=String(required=True),
                          confidence=Float(required=True),
                          result_folder=String())
    def resolve_process_video(self, info, signingkey, video_path, confidence, result_folder=None):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            # Start video processing in a separate thread
            if not result_folder:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_folder = os.path.join(os.getcwd(), f"video_processing_{timestamp}")
                os.makedirs(result_folder, exist_ok=True)
            
            thread = threading.Thread(target=face_processor.process_video,
                                    args=(video_path, confidence, result_folder))
            thread.start()
            return "video processing started"
        except Exception as e:
            return f"error: {str(e)}"
    
    get_model_info = String(description="Get current model information", signingkey=String(required=True))
    def resolve_get_model_info(self, info, signingkey):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            info = {
                "current_model": face_processor.current_model_path,
                "model_type": face_processor.model_type,
                "retinaface_available": "RetinaFace" in face_processor.get_available_models()
            }
            return json.dumps(info)
        except Exception as e:
            return f"error: {str(e)}"

parser = argparse.ArgumentParser()
parser.add_argument("--apiport", type=int, default=5000)
parser.add_argument("--signingkey", type=str, default="")
args = parser.parse_args()

apiSigningKey = args.signingkey

# Initialize face recognition processor
progress_messages = []
python_logs = []

# Event system for real-time updates
event_queues = []  # List of queues for SSE clients

def add_event_queue():
    """Add a new event queue for SSE client"""
    q = queue.Queue()
    event_queues.append(q)
    return q

def remove_event_queue(q):
    """Remove event queue when client disconnects"""
    if q in event_queues:
        event_queues.remove(q)

def broadcast_event(event_type, data):
    """Broadcast an event to all connected clients (both SSE and WebSocket)"""
    event_data = {
        'type': event_type,
        'data': data,
        'timestamp': time.time()
    }
    
    print(f"Broadcasting event '{event_type}' to {len(event_queues)} SSE clients and WebSocket clients")
    
    # SSE clients
    queues_to_remove = []
    for q in event_queues:
        try:
            q.put(event_data, timeout=0.1)
            print(f"Successfully sent event to SSE client")
        except queue.Full:
            print(f"SSE client queue full, marking for removal")
            queues_to_remove.append(q)
    
    for q in queues_to_remove:
        event_queues.remove(q)
        print(f"Removed disconnected SSE client")
    
    # WebSocket clients
    try:
        socketio.emit('face_detection_event', event_data)
        print(f"Successfully sent event to WebSocket clients")
    except Exception as e:
        print(f"Error sending WebSocket event: {e}")

def progress_callback(message):
    progress_messages.append(message)
    python_logs.append(f"Progress: {message}")
    print(f"Progress: {message}")
    
    # Broadcast progress event
    broadcast_event('progress', message)

def completion_callback(data):
    """Called when processing completes"""
    print(f"Processing completed: {data}")
    print(f"Number of SSE clients connected: {len(event_queues)}")
    
    # Broadcast completion event
    broadcast_event('completion', data)
    print(f"Broadcasted completion event: {data}")

# Capture stdout for logging
import sys
class StdoutCapture:
    def __init__(self):
        self.original_stdout = sys.stdout
        
    def write(self, text):
        if text.strip():  # Only log non-empty lines
            python_logs.append(f"Python stdout: {text.strip()}")
        self.original_stdout.write(text)
        
    def flush(self):
        self.original_stdout.flush()

# Install stdout capture
sys.stdout = StdoutCapture()

face_processor = FaceDetectionProcessor(progress_callback, completion_callback)

app = Flask(__name__)
CORS(app) # Allows all domains to access the flask server via CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', engineio_logger=False, socketio_logger=False, transports=['websocket'])

schema = Schema(query=Query)

@app.route('/health/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Python server is running'})

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'Face Detection API Server'})

@app.route('/events/<signing_key>/', methods=['GET'])
def events_stream(signing_key):
    """Server-Sent Events endpoint for real-time updates"""
    if signing_key != apiSigningKey:
        return jsonify({'error': 'invalid signature'}), 403
    
    def event_stream():
        # Add this client to the event queues
        client_queue = add_event_queue()
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'data': 'SSE connection established'})}\n\n"
            
            while True:
                try:
                    # Wait for events with timeout
                    event = client_queue.get(timeout=30)  # 30 second timeout for heartbeat
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'data': 'ping'})}\n\n"
                except GeneratorExit:
                    break
        finally:
            # Clean up when client disconnects
            remove_event_queue(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*'})

@app.route('/graphql/', methods=['POST', 'GET', 'OPTIONS'])
def graphql():
    print(f"GraphQL request: {request.method} from {request.remote_addr}")
    
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        print("Handling CORS preflight request")
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    
    if request.method == 'POST':
        data = request.get_json()
        query = data.get('query')
        variables = data.get('variables')
        
        try:
            result = schema.execute(query, variables=variables)
            return jsonify({
                'data': result.data,
                'errors': [str(error) for error in result.errors] if result.errors else None
            })
        except Exception as e:
            return jsonify({'errors': [str(e)]})
    
    elif request.method == 'GET':
        query = request.args.get('query')
        variables = request.args.get('variables')
        
        if variables:
            try:
                variables = json.loads(variables)
            except:
                variables = None
        
        try:
            result = schema.execute(query, variables=variables)
            return jsonify({
                'data': result.data,
                'errors': [str(error) for error in result.errors] if result.errors else None
            })
        except Exception as e:
            return jsonify({'errors': [str(e)]})
    
    return jsonify({'error': 'Method not allowed'})

@app.route('/graphiql/', methods=['GET'])
def graphiql():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>GraphiQL</title>
        <style>
            body { margin: 0; font-family: Arial, sans-serif; }
            #graphiql { height: 100vh; }
        </style>
    </head>
    <body>
        <div id="graphiql">GraphiQL interface would be here</div>
    </body>
    </html>
    '''

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print(f"WebSocket client connected: {request.sid}")
    emit('connected', {'message': 'WebSocket connection established'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"WebSocket client disconnected: {request.sid}")

@socketio.on('start_detection')
def handle_start_detection(data):
    """Handle start detection request via WebSocket"""
    print(f"WebSocket start_detection received: {data}")
    
    # Validate signing key
    if data.get('signingkey') != apiSigningKey:
        emit('error', {'message': 'Invalid signature'})
        return
    
    try:
        # Start processing in a separate thread
        thread = threading.Thread(target=face_processor.process_folder, 
                                args=(data['folderPath'], data['confidence'], data['model'], 
                                     data.get('saveResults', False), data.get('resultsFolder')))
        thread.start()
        emit('processing_started', {'message': 'Processing started successfully'})
    except Exception as e:
        emit('error', {'message': f'Error starting processing: {str(e)}'})

@socketio.on('stop_detection')
def handle_stop_detection(data):
    """Handle stop detection request via WebSocket"""
    print(f"WebSocket stop_detection received: {data}")
    
    # Validate signing key
    if data.get('signingkey') != apiSigningKey:
        emit('error', {'message': 'Invalid signature'})
        return
    
    try:
        face_processor.stop_processing()
        emit('processing_stopped', {'message': 'Processing stopped successfully'})
    except Exception as e:
        emit('error', {'message': f'Error stopping processing: {str(e)}'})

@socketio.on('get_status')
def handle_get_status(data):
    """Handle status request via WebSocket"""
    # Validate signing key
    if data.get('signingkey') != apiSigningKey:
        emit('error', {'message': 'Invalid signature'})
        return
    
    try:
        status = {
            "is_processing": face_processor.is_processing,
            "results_count": len(face_processor.results)
        }
        emit('status_update', status)
    except Exception as e:
        emit('error', {'message': f'Error getting status: {str(e)}'})

if __name__ == "__main__":
    socketio.run(app, port=args.apiport, debug=False, allow_unsafe_werkzeug=True)
