from flask import Flask
from flask_cors import CORS
from graphene import ObjectType, String, Schema, Float, List, Boolean
from flask_graphql import GraphQLView
from calc import calc as real_calc
from face_recognition import FaceRecognitionProcessor
import argparse
import os
import threading
import json

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
    
    # Face Recognition endpoints
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
    
    start_processing = String(description="Start face recognition processing", 
                             signingkey=String(required=True), 
                             folder_path=String(required=True),
                             confidence=Float(required=True))
    def resolve_start_processing(self, info, signingkey, folder_path, confidence):
        if signingkey != apiSigningKey:
            return "invalid signature"
        try:
            # Start processing in a separate thread
            thread = threading.Thread(target=face_processor.process_folder, 
                                    args=(folder_path, confidence))
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

view_func = GraphQLView.as_view("graphql", schema=Schema(query=Query), graphiql=True)

parser = argparse.ArgumentParser()
parser.add_argument("--apiport", type=int, default=5000)
parser.add_argument("--signingkey", type=str, default="")
args = parser.parse_args()

apiSigningKey = args.signingkey

# Initialize face recognition processor
progress_messages = []
def progress_callback(message):
    progress_messages.append(message)
    print(f"Progress: {message}")

face_processor = FaceRecognitionProcessor(progress_callback)

app = Flask(__name__)
app.add_url_rule("/graphql/", view_func=view_func)
app.add_url_rule("/graphiql/", view_func=view_func) # for compatibility with other samples
CORS(app) # Allows all domains to access the flask server via CORS

if __name__ == "__main__":
    app.run(port=args.apiport)
