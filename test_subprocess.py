#!/usr/bin/env python3

import subprocess
import json
import time
import sys

def test_face_detection():
    # Start the subprocess
    proc = subprocess.Popen(
        ['/home/tamas.foldes/miniconda3/envs/electron-python-sample/bin/python', 'python/subprocess_api.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    print("Started subprocess")
    
    # Read the ready message
    line = proc.stdout.readline()
    print(f"Ready message: {line}")
    
    # Test simple ping command
    print("Sending ping command...")
    ping_cmd = json.dumps({"type": "ping", "id": 1}) + "\n"
    proc.stdin.write(ping_cmd)
    proc.stdin.flush()
    
    # Read response
    response = proc.stdout.readline()
    print(f"Ping response: {response}")
    
    # Test get_models command
    print("Sending get_models command...")
    models_cmd = json.dumps({"type": "get_models", "id": 2}) + "\n"
    proc.stdin.write(models_cmd)
    proc.stdin.flush()
    
    # Read response
    response = proc.stdout.readline()
    print(f"Models response: {response}")
    
    # Test start_processing command with test folder
    print("Sending start_processing command...")
    processing_cmd = json.dumps({
        "type": "start_processing",
        "id": 3,
        "data": {
            "folder_path": "tests/faces_folder",
            "confidence": 0.5,
            "model": "yolov8n.pt",
            "save_results": False
        }
    }) + "\n"
    proc.stdin.write(processing_cmd)
    proc.stdin.flush()
    
    # Read initial response
    response = proc.stdout.readline()
    print(f"Processing start response: {response}")
    
    # Keep reading for progress/completion events
    print("Listening for events...")
    event_count = 0
    max_events = 20  # Limit to prevent infinite loop
    
    while event_count < max_events:
        try:
            line = proc.stdout.readline()
            if not line:
                break
            print(f"Event {event_count + 1}: {line}")
            event_count += 1
            
            # Parse the event to see if processing is complete
            try:
                event_data = json.loads(line)
                if (event_data.get('type') == 'event' and 
                    event_data.get('event', {}).get('type') == 'completion' and
                    event_data.get('event', {}).get('data', {}).get('status') in ['completed', 'finished']):
                    print("Processing completed!")
                    break
            except:
                pass
                
        except Exception as e:
            print(f"Error reading event: {e}")
            break
    
    # Send exit command
    print("Sending exit command...")
    exit_cmd = json.dumps({"type": "exit", "id": 99}) + "\n"
    proc.stdin.write(exit_cmd)
    proc.stdin.flush()
    
    # Wait for process to finish
    proc.wait(timeout=5)
    print("Test completed")

if __name__ == "__main__":
    test_face_detection()