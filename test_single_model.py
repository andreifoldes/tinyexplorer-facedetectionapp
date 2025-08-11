#!/usr/bin/env python3
"""
Quick test for a single model
"""

import subprocess
import json
import time
import sys
import os

def test_single_model(model_name="yolov8n-face.pt"):
    """Test a single model quickly"""
    print(f"🔬 Testing {model_name}")
    
    # Start subprocess
    env = os.environ.copy()
    env['MODEL_TYPE'] = 'yolo'
    
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
        print("⏳ Waiting for subprocess...")
        start_time = time.time()
        ready = False
        
        while time.time() - start_time < 10:
            line = proc.stdout.readline()
            if line:
                print(f"  Response: {line.strip()}")
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
            return False
        
        # Load model
        print(f"📦 Loading model {model_name}...")
        load_cmd = {
            "type": "load_model",
            "data": {"model_path": model_name},
            "id": 1
        }
        
        proc.stdin.write(json.dumps(load_cmd) + '\n')
        proc.stdin.flush()
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < 30:
            line = proc.stdout.readline()
            if line:
                print(f"  Response: {line.strip()}")
                try:
                    msg = json.loads(line.strip())
                    if msg.get('type') == 'response' and msg.get('id') == 1:
                        if msg.get('response', {}).get('status') == 'success':
                            print(f"✅ Model {model_name} loaded successfully!")
                            return True
                        else:
                            print(f"❌ Failed to load: {msg}")
                            return False
                except:
                    pass
        
        print("❌ Timeout loading model")
        return False
        
    finally:
        proc.terminate()
        proc.wait(timeout=2)

if __name__ == "__main__":
    success = test_single_model()
    sys.exit(0 if success else 1)