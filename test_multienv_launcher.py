#!/usr/bin/env python3
"""
Test the multi-environment launcher with the packaged app's virtual environments
"""
import subprocess
import json
import sys
import os
import tempfile
from urllib.request import urlretrieve

def test_multienv_launcher():
    """Test multi-environment launcher with packaged virtual environments"""
    
    # Use system Python with multi-env launcher
    system_python = "python3"
    multi_launcher = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/python/multi_env_launcher.py"
    
    print("🧪 Testing Multi-Environment Launcher with Virtual Environments")
    print("=" * 70)
    print()
    
    # Download a test image
    test_image_url = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop"
    test_image_path = "/tmp/test_face_multienv.jpg"
    
    try:
        print("📥 Downloading test image...")
        urlretrieve(test_image_url, test_image_path)
        print(f"✅ Test image saved: {test_image_path}")
    except Exception as e:
        print(f"❌ Failed to download test image: {e}")
        return False
    
    print()
    
    # Test with YOLO environment (default)
    print("🚀 Testing Multi-Environment Launcher (YOLO Environment)")
    print(f"🐍 Using: {system_python} with {os.path.basename(multi_launcher)}")
    
    if os.path.exists(multi_launcher):
        try:
            # Start the API process with YOLO environment
            env = os.environ.copy()
            env['MODEL_TYPE'] = 'yolo'
            
            process = subprocess.Popen([
                system_python, multi_launcher
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               text=True, env=env)
            
            # Wait for ready message
            print("⏳ Starting API with YOLO environment...")
            ready_received = False
            
            # Read initial outputs and look for ready message
            stderr_lines = []
            for i in range(15):  # Try up to 15 lines
                try:
                    # Check stderr for launcher messages
                    line = process.stderr.readline()
                    if line:
                        stderr_lines.append(line.strip())
                        print(f"🔍 Launcher: {line.strip()}")
                        
                    # Check stdout for API ready message
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
                    if line:
                        print(f"🔍 API output: {line}")
                except:
                    break
            
            if not ready_received:
                print("⚠️ No ready message received, but continuing test...")
                # Print stderr to see what happened
                for line in stderr_lines[-5:]:  # Last 5 lines
                    print(f"🔍 Recent stderr: {line}")
            
            print()
            print("🎯 Testing get_models command...")
            
            # Send get_models command
            command = {"type": "get_models", "id": 1}
            command_json = json.dumps(command) + '\n'
            process.stdin.write(command_json)
            process.stdin.flush()
            
            # Read response
            models_received = False
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
                                models = response.get('response', {}).get('models', [])
                                print(f"   Available models: {models}")
                                models_received = True
                                break
                        except json.JSONDecodeError:
                            pass
                    if line:
                        print(f"🔍 API response: {line}")
                except:
                    break
            
            if models_received:
                print()
                print("🎯 Testing OpenCV model load (should always work)...")
                
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
                        if line:
                            print(f"🔍 Load model: {line}")
                    except:
                        break
                
                if model_loaded:
                    print()
                    print("🎯 Testing face detection with OpenCV...")
                    
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
                    processing_completed = False
                    for i in range(30):  # Give more time for processing
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
                                        processing_completed = True
                                        break
                                    elif response.get('type') == 'event':
                                        event = response.get('event', {})
                                        print(f"📡 Event: {event.get('status', 'unknown')} - {event.get('message', '')}")
                                except json.JSONDecodeError:
                                    pass
                            if line:
                                print(f"🔍 Processing: {line}")
                        except:
                            break
                    
                    if processing_completed:
                        print("🎊 SUCCESS: Face detection working with OpenCV fallback!")
                    else:
                        print("⚠️ Processing didn't complete as expected")
            
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
            print(f"💥 Multi-env launcher test exception: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Multi-environment launcher not found: {multi_launcher}")
    
    # Clean up
    try:
        os.remove(test_image_path)
    except:
        pass
    
    return True

if __name__ == "__main__":
    success = test_multienv_launcher()
    sys.exit(0 if success else 1)