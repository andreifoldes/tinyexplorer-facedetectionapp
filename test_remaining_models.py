#!/usr/bin/env python3
"""
Test the remaining failing YOLO models
"""

import subprocess
import json
import time
import os

def test_specific_model(model_name):
    print(f"🔬 Testing {model_name} with detailed logging...")
    
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
        ready = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            line = proc.stdout.readline()
            if line:
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
        load_cmd = {
            "type": "load_model", 
            "data": {"model_path": model_name},
            "id": 1
        }
        
        proc.stdin.write(json.dumps(load_cmd) + '\n')
        proc.stdin.flush()
        
        # Wait for response and collect all output
        start_time = time.time()
        all_messages = []
        
        while time.time() - start_time < 30:
            line = proc.stdout.readline()
            if line:
                line_str = line.strip()
                print(f"OUTPUT: {line_str}")
                try:
                    msg = json.loads(line_str)
                    all_messages.append(msg)
                    
                    if msg.get('type') == 'response' and msg.get('id') == 1:
                        print(f"FINAL RESPONSE: {json.dumps(msg, indent=2)}")
                        response = msg.get('response', {})
                        if response.get('status') == 'success':
                            print(f"✅ {model_name} loaded successfully!")
                            return True
                        else:
                            print(f"❌ {model_name} failed: {response}")
                            return False
                            
                except Exception as e:
                    print(f"Non-JSON output: {line_str}")
        
        # Check stderr for any errors
        try:
            stderr_output = proc.stderr.read()
            if stderr_output.strip():
                print(f"STDERR: {stderr_output}")
        except:
            pass
            
        print(f"❌ Timeout waiting for {model_name} response")
        return False
        
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()

if __name__ == "__main__":
    # Test the still failing models
    failing_models = ["yolov11m-face.pt", "yolov12l-face.pt"]
    
    for model in failing_models:
        print(f"\n{'='*60}")
        result = test_specific_model(model)
        print(f"Result: {'SUCCESS' if result else 'FAILED'}")
        time.sleep(2)