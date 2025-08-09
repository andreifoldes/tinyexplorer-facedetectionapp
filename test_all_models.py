#!/usr/bin/env python3
"""
Comprehensive test suite for all face detection models.
Tests each YOLO model variant and RetinaFace individually.
"""

import subprocess
import json
import time
import os
import sys
import base64
import cv2
import numpy as np

def create_test_image():
    """Create a simple test image with a rectangle (simulating a face)"""
    # Create a white image with a dark rectangle in the center
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (200, 150), (440, 330), (100, 100, 100), -1)
    
    # Add some features to make it more face-like
    # Eyes
    cv2.circle(img, (260, 200), 20, (50, 50, 50), -1)
    cv2.circle(img, (380, 200), 20, (50, 50, 50), -1)
    
    # Nose
    cv2.rectangle(img, (310, 230), (330, 260), (70, 70, 70), -1)
    
    # Mouth
    cv2.rectangle(img, (270, 280), (370, 300), (60, 60, 60), -1)
    
    # Save test image
    test_image_path = 'test_face_detection.jpg'
    cv2.imwrite(test_image_path, img)
    return test_image_path

def test_model(model_name, env_type='yolo', python_path=None):
    """Test a specific model"""
    print(f"\n{'='*60}")
    print(f"Testing {model_name}")
    print(f"{'='*60}")
    
    # Determine Python executable based on environment type
    if python_path is None:
        if env_type == 'retinaface':
            python_path = './retinaface-env/bin/python'
        else:
            python_path = './yolo-env/bin/python'
    
    # Set environment variable for model type
    env = os.environ.copy()
    env['MODEL_TYPE'] = env_type
    
    # Start Python subprocess
    proc = subprocess.Popen(
        [python_path, 'python/subprocess_api.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        bufsize=1
    )
    
    results = {
        'model': model_name,
        'environment': env_type,
        'load_success': False,
        'process_success': False,
        'faces_detected': 0,
        'error': None,
        'timing': {}
    }
    
    try:
        # Wait for ready signal
        start_time = time.time()
        ready = False
        
        while time.time() - start_time < 30:  # 30 second timeout for initialization
            line = proc.stdout.readline()
            if line:
                try:
                    msg = json.loads(line.strip())
                    if msg.get('type') == 'ready':
                        ready = True
                        print(f"✅ Python subprocess ready")
                        break
                except json.JSONDecodeError:
                    pass
        
        if not ready:
            results['error'] = "Subprocess failed to initialize"
            print(f"❌ Subprocess failed to initialize within 30 seconds")
            return results
        
        # Test 1: Load the model
        print(f"📦 Loading model: {model_name}")
        load_start = time.time()
        
        load_command = {
            "type": "load_model",
            "data": {"model_path": model_name},
            "id": 1
        }
        
        proc.stdin.write(json.dumps(load_command) + '\n')
        proc.stdin.flush()
        
        # Wait for load response
        load_response = wait_for_response(proc, 1, timeout=60)
        load_time = time.time() - load_start
        results['timing']['load'] = load_time
        
        if load_response and load_response.get('response', {}).get('status') == 'success':
            results['load_success'] = True
            print(f"✅ Model loaded successfully in {load_time:.2f}s")
        else:
            error_msg = load_response.get('response', {}).get('error', 'Unknown error') if load_response else 'No response'
            results['error'] = f"Failed to load model: {error_msg}"
            print(f"❌ Failed to load model: {error_msg}")
            return results
        
        # Test 2: Process test image
        test_image = create_test_image()
        print(f"🖼️  Processing test image: {test_image}")
        
        process_start = time.time()
        
        # For RetinaFace, we need a higher confidence threshold
        confidence = 0.9 if env_type == 'retinaface' else 0.5
        
        process_command = {
            "type": "start_processing",
            "data": {
                "files": [os.path.abspath(test_image)],
                "output_folder": os.path.abspath('.'),
                "confidence_threshold": confidence,
                "model": model_name
            },
            "id": 2
        }
        
        proc.stdin.write(json.dumps(process_command) + '\n')
        proc.stdin.flush()
        
        # Wait for processing to complete
        process_response = None
        process_events = []
        timeout = 120  # 2 minutes timeout for processing
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            line = proc.stdout.readline()
            if line:
                try:
                    msg = json.loads(line.strip())
                    
                    if msg.get('type') == 'response' and msg.get('id') == 2:
                        process_response = msg
                        break
                    elif msg.get('type') == 'event':
                        event_data = msg.get('event', {}).get('data', '')
                        process_events.append(event_data)
                        if '✅' in event_data or 'Completed' in event_data:
                            print(f"  {event_data}")
                except json.JSONDecodeError:
                    pass
        
        process_time = time.time() - process_start
        results['timing']['process'] = process_time
        
        if process_response and process_response.get('response', {}).get('status') == 'success':
            results['process_success'] = True
            print(f"✅ Image processed successfully in {process_time:.2f}s")
            
            # Check for completion event with face count
            for event in process_events:
                if 'Completed processing' in event and 'detected' in event:
                    # Extract face count from event message
                    import re
                    match = re.search(r'(\d+)\s+face', event)
                    if match:
                        results['faces_detected'] = int(match.group(1))
            
            print(f"👤 Faces detected: {results['faces_detected']}")
        else:
            error_msg = process_response.get('response', {}).get('error', 'Unknown error') if process_response else 'No response'
            results['error'] = f"Failed to process image: {error_msg}"
            print(f"❌ Failed to process image: {error_msg}")
        
        # Send exit command
        proc.stdin.write(json.dumps({"type": "exit"}) + '\n')
        proc.stdin.flush()
        
    except Exception as e:
        results['error'] = str(e)
        print(f"❌ Error during test: {e}")
    
    finally:
        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    
    return results

def wait_for_response(proc, command_id, timeout=30):
    """Wait for a specific response from the subprocess"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if line:
            try:
                msg = json.loads(line.strip())
                if msg.get('type') == 'response' and msg.get('id') == command_id:
                    return msg
            except json.JSONDecodeError:
                pass
    
    return None

def main():
    """Run tests for all models"""
    print("🚀 Starting comprehensive model testing suite")
    print("=" * 60)
    
    # Define all models to test
    yolo_models = [
        "yolov8n-face.pt",
        "yolov8m-face.pt", 
        "yolov8l-face.pt",
        "yolov11m-face.pt",
        "yolov11l-face.pt",
        "yolov12l-face.pt"
    ]
    
    retinaface_models = ["RetinaFace"]
    
    all_results = []
    
    # Test YOLO models
    print("\n📦 Testing YOLO Models")
    print("=" * 60)
    
    for model in yolo_models:
        result = test_model(model, env_type='yolo')
        all_results.append(result)
        time.sleep(2)  # Brief pause between tests
    
    # Test RetinaFace
    print("\n📦 Testing RetinaFace Model")
    print("=" * 60)
    
    for model in retinaface_models:
        result = test_model(model, env_type='retinaface')
        all_results.append(result)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    
    successful_models = []
    failed_models = []
    
    for result in all_results:
        model_name = result['model']
        if result['load_success'] and result['process_success']:
            successful_models.append(model_name)
            status = "✅ PASS"
            details = f"Loaded in {result['timing'].get('load', 0):.2f}s, " \
                     f"Processed in {result['timing'].get('process', 0):.2f}s, " \
                     f"Detected {result['faces_detected']} faces"
        else:
            failed_models.append(model_name)
            status = "❌ FAIL"
            details = result.get('error', 'Unknown error')
        
        print(f"{status} {model_name:20s} - {details}")
    
    print("\n" + "=" * 60)
    print(f"✅ Successful: {len(successful_models)}/{len(all_results)}")
    print(f"❌ Failed: {len(failed_models)}/{len(all_results)}")
    
    if successful_models:
        print(f"\n✅ Working models: {', '.join(successful_models)}")
    
    if failed_models:
        print(f"\n❌ Failed models: {', '.join(failed_models)}")
    
    # Clean up test image
    if os.path.exists('test_face_detection.jpg'):
        os.remove('test_face_detection.jpg')
    
    print("\n🎯 Testing complete!")
    
    # Return exit code based on results
    return 0 if len(failed_models) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())