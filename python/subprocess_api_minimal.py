#!/usr/bin/env python3
"""
Minimal subprocess communication API for testing Python connection.
"""

import json
import sys
import os
import threading
import time

class MinimalSubprocessAPI:
    def __init__(self):
        self.running = True
        
        # Setup logging to stderr to avoid conflicts with stdout communication
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging to stderr to avoid conflicts with stdout communication"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        self.logger = logging.getLogger(__name__)
        
    def send_response(self, response_data):
        """Send JSON response to stdout"""
        try:
            json_response = json.dumps(response_data)
            print(json_response, flush=True)
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            
    def handle_command(self, command):
        """Handle incoming command from Electron"""
        try:
            cmd_type = command.get('type')
            data = command.get('data', {})
            
            if cmd_type == 'ping':
                return {'status': 'success', 'message': 'pong'}
                
            elif cmd_type == 'echo':
                return {'status': 'success', 'message': data.get('text', '')}
                
            elif cmd_type == 'get_info':
                return {
                    'status': 'success', 
                    'info': {
                        'python_version': sys.version,
                        'platform': sys.platform,
                        'cwd': os.getcwd(),
                        'script_location': __file__
                    }
                }
                
            elif cmd_type == 'exit':
                self.running = False
                return {'status': 'success', 'message': 'Exiting...'}
                
            else:
                return {'status': 'error', 'message': f'Unknown command type: {cmd_type}'}
                
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            return {'status': 'error', 'message': str(e)}
            
    def run(self):
        """Main subprocess loop - read commands from stdin and send responses to stdout"""
        self.logger.info("Starting minimal subprocess API...")
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"Working directory: {os.getcwd()}")
        self.logger.info(f"Script location: {__file__}")
        
        # Send ready signal
        self.send_response({'type': 'ready', 'message': 'Python subprocess ready (minimal)'})
        
        while self.running:
            try:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # Parse JSON command
                try:
                    command = json.loads(line)
                except json.JSONDecodeError as e:
                    self.send_response({
                        'type': 'error',
                        'message': f'Invalid JSON: {e}'
                    })
                    continue
                    
                # Handle command
                response = self.handle_command(command)
                
                # Send response with command ID if present
                response_data = {
                    'type': 'response',
                    'response': response
                }
                if 'id' in command:
                    response_data['id'] = command['id']
                
                self.send_response(response_data)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.send_response({
                    'type': 'error',
                    'message': str(e)
                })
                
        self.logger.info("Minimal subprocess API shutting down...")

if __name__ == "__main__":
    api = MinimalSubprocessAPI()
    api.run()