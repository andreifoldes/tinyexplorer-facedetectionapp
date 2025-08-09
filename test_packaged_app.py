#!/usr/bin/env python3
"""
Test script to directly test the packaged app's Python subprocess API
"""
import json
import subprocess
import sys
import os
import time

def test_python_subprocess():
    """Test the Python subprocess API from the packaged app"""
    
    # Path to the packaged multi_env_launcher.py
    launcher_path = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/python/multi_env_launcher.py"
    
    if not os.path.exists(launcher_path):
        print("❌ ERROR: Launcher script not found at:", launcher_path)
        return False
    
    print("🚀 Testing packaged Python subprocess API...")
    print("📍 Launcher path:", launcher_path)
    print()
    
    # Test both YOLO and RetinaFace environments
    test_cases = [
        ("yolo", "yolov8n-face.pt"),
        ("retinaface", "RetinaFace")
    ]
    
    for env_type, model_name in test_cases:
        print(f"🧪 Testing {env_type.upper()} environment with model: {model_name}")
        print("=" * 60)
        
        # Set environment variable for model type
        env = os.environ.copy()
        env['MODEL_TYPE'] = env_type
        
        # Start the Python subprocess
        try:
            proc = subprocess.Popen(
                ['python3', launcher_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd="/Users/apgroup/Documents/Dev/electron-python-face-recognition"
            )
            
            # Wait a moment for startup
            time.sleep(2)
            
            # Send get_models command
            command = {"type": "get_models", "id": 1}
            command_json = json.dumps(command) + '\n'
            
            print(f"📤 Sending command: {command}")
            
            # Send command and get response
            proc.stdin.write(command_json)
            proc.stdin.flush()
            
            # Read response with timeout
            response_received = False
            stderr_lines = []
            
            for _ in range(10):  # Wait up to 5 seconds
                # Check if process has terminated
                if proc.poll() is not None:
                    break
                
                # Try to read stdout (non-blocking)
                try:
                    proc.stdout.settimeout(0.5)
                except:
                    pass
                
                # Check for stderr output
                try:
                    while True:
                        stderr_line = proc.stderr.readline()
                        if not stderr_line:
                            break
                        stderr_lines.append(stderr_line.strip())
                except:
                    pass
                
                # Check for stdout response
                try:
                    stdout_line = proc.stdout.readline()
                    if stdout_line.strip():
                        try:
                            response = json.loads(stdout_line.strip())
                            print(f"📥 Response: {response}")
                            response_received = True
                            
                            if response.get('type') == 'response' and 'models' in response.get('response', {}):
                                models = response['response']['models']
                                print(f"✅ SUCCESS: Found {len(models)} models")
                                print(f"📋 Available models: {models}")
                                
                                # Check if the expected model is available
                                if model_name in models:
                                    print(f"✅ Model {model_name} is available!")
                                else:
                                    print(f"⚠️ Model {model_name} not found in available models")
                            break
                        except json.JSONDecodeError:
                            if stdout_line.strip().startswith('{'):
                                print(f"⚠️ Failed to parse JSON: {stdout_line.strip()}")
                except:
                    pass
                
                time.sleep(0.5)
            
            # Print stderr output
            if stderr_lines:
                print("📝 Python stderr output:")
                for line in stderr_lines:
                    if line:
                        if "not available" in line.lower() or "error" in line.lower():
                            print(f"❌ {line}")
                        elif "added" in line.lower() or "environment" in line.lower():
                            print(f"🔧 {line}")
                        else:
                            print(f"ℹ️ {line}")
            
            if not response_received:
                print("❌ No response received from subprocess")
                
                # Check if process is still running
                if proc.poll() is None:
                    print("⚠️ Process is still running, terminating...")
                    proc.terminate()
                else:
                    print(f"💀 Process exited with code: {proc.poll()}")
            
            # Send exit command
            try:
                exit_command = {"type": "exit", "id": 2}
                proc.stdin.write(json.dumps(exit_command) + '\n')
                proc.stdin.flush()
                time.sleep(1)
            except:
                pass
            
            # Clean up
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
            
        except Exception as e:
            print(f"❌ ERROR: Failed to test {env_type}: {e}")
            return False
        
        print()
    
    print("🎉 Testing completed!")
    return True

if __name__ == "__main__":
    success = test_python_subprocess()
    sys.exit(0 if success else 1)