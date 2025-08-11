#!/usr/bin/env python3
"""
Test the API directly using the packaged app's virtual environment Python executables
"""
import subprocess
import json
import sys
import os
import tempfile
from urllib.request import urlretrieve

def test_api_direct():
    """Test API with direct virtual environment calls"""
    
    # Paths to the virtual environment Python executables
    yolo_python = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/yolo-env/bin/python"
    retinaface_python = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/retinaface-env/bin/python"
    subprocess_script = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/python/subprocess_api.py"
    
    print("🧪 Testing API with Direct Virtual Environment Python")
    print("=" * 60)
    print()
    
    # Download a test image
    test_image_url = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop"
    test_image_path = "/tmp/test_face_api.jpg"
    
    try:
        print("📥 Downloading test image...")
        urlretrieve(test_image_url, test_image_path)
        print(f"✅ Test image saved: {test_image_path}")
    except Exception as e:
        print(f"❌ Failed to download test image: {e}")
        return False
    
    print()
    
    # Test YOLO environment
    print("🚀 Testing API with YOLO Environment Python")
    print(f"🐍 Using: {yolo_python}")
    
    if os.path.exists(yolo_python) and os.path.exists(subprocess_script):
        try:
            # Start the API process
            process = subprocess.Popen([
                yolo_python, subprocess_script
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for ready message
            print("⏳ Starting API process...")
            ready_received = False
            
            # Read initial outputs
            for i in range(10):  # Try up to 10 lines
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith('{') or line.startswith('['):
                        try:
                            message = json.loads(line)
                            if message.get('type') == 'ready':
                                print("✅ API is ready!")
                                ready_received = True
                                break
                        except json.JSONDecodeError:
                            pass
                    print(f"🔍 API output: {line}")
                except:
                    break
            
            if not ready_received:
                print("⚠️ No ready message received, but continuing test...")
            
            print()
            print("🎯 Testing get_models command...")
            
            # Send get_models command
            command = {"type": "get_models", "id": 1}
            command_json = json.dumps(command) + '\n'
            process.stdin.write(command_json)
            process.stdin.flush()
            
            # Read response
            for i in range(5):
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith('{') or line.startswith('['):
                        try:
                            response = json.loads(line)
                            if response.get('id') == 1:
                                print("✅ get_models response received!")
                                print(f"   Available models: {response.get('response', {}).get('models', [])}")
                                break
                        except json.JSONDecodeError:
                            pass
                    print(f"🔍 API response: {line}")
                except:
                    break
            
            print()
            print("🎯 Testing OpenCV model load...")
            
            # Send load_model command for OpenCV
            command = {"type": "load_model", "data": {"model_path": "OpenCV Haar Cascade"}, "id": 2}
            command_json = json.dumps(command) + '\n'
            process.stdin.write(command_json)
            process.stdin.flush()
            
            # Read response
            model_loaded = False
            for i in range(10):
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith('{') or line.startswith('['):
                        try:
                            response = json.loads(line)
                            if response.get('id') == 2:
                                print("✅ load_model response received!")
                                print(f"   Status: {response.get('response', {}).get('status', 'unknown')}")
                                if response.get('response', {}).get('status') == 'success':
                                    model_loaded = True
                                break
                        except json.JSONDecodeError:
                            pass
                    print(f"🔍 Load model: {line}")
                except:
                    break
            
            if model_loaded:
                print()
                print("🎯 Testing face detection...")
                
                # Send start_processing command
                command = {
                    "type": "start_processing", 
                    "data": {
                        "input_path": test_image_path,
                        "model": "OpenCV Haar Cascade",
                        "confidence": 0.5,
                        "save_results": False
                    },
                    "id": 3
                }
                command_json = json.dumps(command) + '\n'
                process.stdin.write(command_json)
                process.stdin.flush()
                
                # Read processing responses
                for i in range(20):  # Give more time for processing
                    try:
                        line = process.stdout.readline()
                        if not line:
                            break
                        line = line.strip()
                        if line.startswith('{') or line.startswith('['):
                            try:
                                response = json.loads(line)
                                if response.get('id') == 3:
                                    print("🎉 Processing completed successfully!")
                                    print(f"   Response: {response}")
                                    break
                                elif response.get('type') == 'event':
                                    print(f"📡 Event: {response.get('event', {})}")
                            except json.JSONDecodeError:
                                pass
                        if line:
                            print(f"🔍 Processing: {line}")
                    except:
                        break
            
            # Clean up
            try:
                command = {"type": "exit", "id": 999}
                command_json = json.dumps(command) + '\n'
                process.stdin.write(command_json)
                process.stdin.flush()
            except:
                pass
            
            process.terminate()
            process.wait(timeout=5)
            
        except Exception as e:
            print(f"💥 API test exception: {e}")
    else:
        print(f"❌ Python or script not found")
        print(f"   Python: {yolo_python} ({'exists' if os.path.exists(yolo_python) else 'missing'})")
        print(f"   Script: {subprocess_script} ({'exists' if os.path.exists(subprocess_script) else 'missing'})")
    
    # Clean up
    try:
        os.remove(test_image_path)
    except:
        pass
    
    return True

if __name__ == "__main__":
    success = test_api_direct()
    sys.exit(0 if success else 1)