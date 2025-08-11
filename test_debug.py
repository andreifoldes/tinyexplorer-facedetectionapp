#!/usr/bin/env python3
"""
Debug test for YOLO model loading
"""

import subprocess
import json
import time
import os

# Set environment 
env = os.environ.copy()
env['MODEL_TYPE'] = 'yolo'

# Start subprocess
proc = subprocess.Popen(
    ['./yolo-env/bin/python', 'python/subprocess_api.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)

try:
    # Wait for ready
    print("🔬 Starting debug test...")
    print("⏳ Waiting for subprocess...")
    
    ready = False
    start_time = time.time()
    
    while time.time() - start_time < 10:
        line = proc.stdout.readline()
        if line:
            print(f"OUT: {line.strip()}")
            try:
                msg = json.loads(line.strip())
                if msg.get('type') == 'ready':
                    ready = True
                    print("✅ Subprocess ready")
                    break
            except:
                pass
    
    if not ready:
        print("❌ Subprocess not ready")
        exit(1)
    
    # Load model with debug info
    print(f"📦 Loading yolov8n-face.pt...")
    load_cmd = {
        "type": "load_model",
        "data": {"model_path": "yolov8n-face.pt"},
        "id": 1
    }
    
    proc.stdin.write(json.dumps(load_cmd) + '\n')
    proc.stdin.flush()
    print(f"SENT: {json.dumps(load_cmd)}")
    
    # Wait for response with full debug output
    start_time = time.time()
    while time.time() - start_time < 30:
        line = proc.stdout.readline()
        if line:
            print(f"OUT: {line.strip()}")
            try:
                msg = json.loads(line.strip())
                if msg.get('type') == 'response' and msg.get('id') == 1:
                    print(f"✅ Got response: {msg}")
                    if msg.get('response', {}).get('status') == 'success':
                        print("✅ Model loaded successfully!")
                    else:
                        print(f"❌ Model load failed: {msg}")
                    break
            except Exception as e:
                print(f"JSON parse error: {e} for line: {line.strip()}")

    # Check stderr for errors
    stderr_data = proc.stderr.read()
    if stderr_data:
        print(f"STDERR: {stderr_data}")

finally:
    proc.terminate()
    proc.wait(timeout=2)