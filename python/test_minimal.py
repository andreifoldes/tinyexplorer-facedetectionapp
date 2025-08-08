#!/usr/bin/env python3
"""Minimal test script to check subprocess behavior"""
import json
import sys

def handle_command(command):
    cmd_type = command.get('type')
    data = command.get('data', {})
    
    if cmd_type == 'ping':
        return {'status': 'success', 'message': 'pong'}
    elif cmd_type == 'start_processing':
        # Simulate processing without YOLO
        folder_path = data.get('folder_path', '/tmp')
        return {'status': 'success', 'message': f'Processing started for {folder_path}'}
    elif cmd_type == 'exit':
        return {'status': 'success', 'message': 'Exiting...'}
    else:
        return {'status': 'error', 'message': f'Unknown command: {cmd_type}'}

def main():
    # Send ready signal
    print(json.dumps({'type': 'ready', 'message': 'Test subprocess ready'}))
    sys.stdout.flush()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            command = json.loads(line.strip())
            response = handle_command(command)
            
            print(json.dumps({'type': 'response', 'response': response}))
            sys.stdout.flush()
            
            if command.get('type') == 'exit':
                break
                
        except Exception as e:
            print(json.dumps({'type': 'error', 'message': str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()