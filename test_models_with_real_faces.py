#!/usr/bin/env python3
"""
Advanced test suite for all face detection models using real face images.
Tests each model's ability to detect faces in various conditions.
"""

import subprocess
import json
import time
import os
import sys
import urllib.request
import cv2
import numpy as np
from typing import Dict, List, Tuple

def download_test_images() -> List[str]:
    """Download test images with faces or use existing ones"""
    test_images = []
    
    # First check if we have existing test images
    existing_images = [
        'test_face.jpg',
        'test_imgs/test1.jpg',
        'test_imgs/test2.jpg',
        'test_imgs/test3.jpg'
    ]
    
    for img_path in existing_images:
        if os.path.exists(img_path):
            test_images.append(os.path.abspath(img_path))
            print(f"✅ Found existing test image: {img_path}")
    
    # If no test images found, create synthetic ones
    if not test_images:
        print("📦 Creating synthetic test images...")
        
        # Create test directory
        os.makedirs('test_imgs', exist_ok=True)
        
        # Create multiple test images with different characteristics
        test_scenarios = [
            {"name": "single_face", "faces": 1},
            {"name": "two_faces", "faces": 2},
            {"name": "group", "faces": 3}
        ]
        
        for scenario in test_scenarios:
            img_path = f"test_imgs/{scenario['name']}.jpg"
            create_synthetic_face_image(img_path, num_faces=scenario['faces'])
            test_images.append(os.path.abspath(img_path))
            print(f"✅ Created synthetic test image: {img_path} with {scenario['faces']} face(s)")
    
    return test_images

def create_synthetic_face_image(output_path: str, num_faces: int = 1):
    """Create a synthetic image with face-like patterns"""
    # Create a white background
    img = np.ones((600, 800, 3), dtype=np.uint8) * 240
    
    # Define face positions
    face_positions = [
        (200, 200),  # Top-left
        (500, 200),  # Top-right  
        (350, 400),  # Bottom-center
    ]
    
    for i in range(min(num_faces, len(face_positions))):
        x, y = face_positions[i]
        draw_synthetic_face(img, x, y)
    
    cv2.imwrite(output_path, img)

def draw_synthetic_face(img, center_x, center_y, size=120):
    """Draw a synthetic face-like pattern"""
    # Face outline (oval)
    cv2.ellipse(img, (center_x, center_y), (size//2, int(size*0.7)), 
                0, 0, 360, (200, 180, 170), -1)
    
    # Add some shading
    cv2.ellipse(img, (center_x, center_y), (size//2-5, int(size*0.7)-5), 
                0, 0, 360, (220, 200, 190), -1)
    
    # Eyes
    eye_y = center_y - size//5
    eye_spacing = size//4
    # Left eye
    cv2.ellipse(img, (center_x - eye_spacing, eye_y), (15, 10), 
                0, 0, 360, (50, 50, 50), -1)
    cv2.ellipse(img, (center_x - eye_spacing, eye_y), (8, 5), 
                0, 0, 360, (20, 20, 20), -1)
    
    # Right eye
    cv2.ellipse(img, (center_x + eye_spacing, eye_y), (15, 10), 
                0, 0, 360, (50, 50, 50), -1)
    cv2.ellipse(img, (center_x + eye_spacing, eye_y), (8, 5), 
                0, 0, 360, (20, 20, 20), -1)
    
    # Nose
    nose_y = center_y + size//10
    points = np.array([
        [center_x, nose_y - 10],
        [center_x - 8, nose_y + 10],
        [center_x + 8, nose_y + 10]
    ], np.int32)
    cv2.fillPoly(img, [points], (180, 160, 150))
    
    # Mouth
    mouth_y = center_y + size//3
    cv2.ellipse(img, (center_x, mouth_y), (25, 12), 
                0, 0, 180, (150, 100, 100), 2)

def test_model_on_images(model_name: str, test_images: List[str], 
                        env_type: str = 'yolo') -> Dict:
    """Test a model on multiple images"""
    print(f"\n{'='*70}")
    print(f"🔬 Testing {model_name}")
    print(f"Environment: {env_type}")
    print(f"Test images: {len(test_images)}")
    print(f"{'='*70}")
    
    # Determine Python executable
    python_path = './retinaface-env/bin/python' if env_type == 'retinaface' else './yolo-env/bin/python'
    
    # Set environment
    env = os.environ.copy()
    env['MODEL_TYPE'] = env_type
    
    # Start subprocess
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
        'total_images': len(test_images),
        'successful_processes': 0,
        'total_faces_detected': 0,
        'load_time': 0,
        'process_times': [],
        'errors': [],
        'image_results': []
    }
    
    try:
        # Wait for ready
        if not wait_for_ready(proc):
            results['errors'].append("Failed to initialize subprocess")
            return results
        
        print("✅ Subprocess ready")
        
        # Load model
        print(f"📦 Loading {model_name}...")
        load_start = time.time()
        
        if not load_model(proc, model_name):
            results['errors'].append(f"Failed to load model {model_name}")
            return results
        
        results['load_time'] = time.time() - load_start
        print(f"✅ Model loaded in {results['load_time']:.2f}s")
        
        # Process each image
        for img_path in test_images:
            print(f"\n🖼️  Processing: {os.path.basename(img_path)}")
            
            img_result = process_image(proc, model_name, img_path, env_type)
            results['image_results'].append(img_result)
            
            if img_result['success']:
                results['successful_processes'] += 1
                results['total_faces_detected'] += img_result['faces_detected']
                results['process_times'].append(img_result['process_time'])
                print(f"  ✅ Detected {img_result['faces_detected']} face(s) in {img_result['process_time']:.2f}s")
            else:
                results['errors'].append(f"Failed on {os.path.basename(img_path)}: {img_result['error']}")
                print(f"  ❌ Failed: {img_result['error']}")
        
        # Send exit command
        proc.stdin.write(json.dumps({"type": "exit"}) + '\n')
        proc.stdin.flush()
        
    except Exception as e:
        results['errors'].append(f"Exception: {str(e)}")
        print(f"❌ Exception during test: {e}")
    
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    
    return results

def wait_for_ready(proc, timeout=30) -> bool:
    """Wait for subprocess to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if line:
            try:
                msg = json.loads(line.strip())
                if msg.get('type') == 'ready':
                    return True
            except json.JSONDecodeError:
                pass
    
    return False

def load_model(proc, model_name: str, timeout=60) -> bool:
    """Load a model and wait for confirmation"""
    command = {
        "type": "load_model",
        "data": {"model": model_name},
        "id": 1
    }
    
    proc.stdin.write(json.dumps(command) + '\n')
    proc.stdin.flush()
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if line:
            try:
                msg = json.loads(line.strip())
                if msg.get('type') == 'response' and msg.get('id') == 1:
                    return msg.get('response', {}).get('status') == 'success'
            except json.JSONDecodeError:
                pass
    
    return False

def process_image(proc, model_name: str, image_path: str, env_type: str) -> Dict:
    """Process a single image and return results"""
    result = {
        'image': os.path.basename(image_path),
        'success': False,
        'faces_detected': 0,
        'process_time': 0,
        'error': None
    }
    
    # Set confidence threshold based on model type
    confidence = 0.9 if env_type == 'retinaface' else 0.5
    
    command = {
        "type": "start_processing",
        "data": {
            "files": [image_path],
            "output_folder": os.path.dirname(image_path) or '.',
            "confidence_threshold": confidence,
            "model": model_name
        },
        "id": 2
    }
    
    proc.stdin.write(json.dumps(command) + '\n')
    proc.stdin.flush()
    
    start_time = time.time()
    timeout = 60
    
    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if line:
            try:
                msg = json.loads(line.strip())
                
                if msg.get('type') == 'response' and msg.get('id') == 2:
                    result['process_time'] = time.time() - start_time
                    
                    if msg.get('response', {}).get('status') == 'success':
                        result['success'] = True
                        # Try to extract face count from response
                        summary = msg.get('response', {}).get('summary', {})
                        result['faces_detected'] = summary.get('total_faces', 0)
                    else:
                        result['error'] = msg.get('response', {}).get('error', 'Unknown error')
                    
                    return result
                
                elif msg.get('type') == 'event':
                    # Check for completion events that might contain face count
                    event_data = msg.get('event', {}).get('data', '')
                    if 'Completed processing' in event_data:
                        import re
                        match = re.search(r'(\d+)\s+face', event_data)
                        if match:
                            result['faces_detected'] = int(match.group(1))
                            
            except json.JSONDecodeError:
                pass
    
    result['error'] = 'Timeout waiting for response'
    return result

def generate_report(all_results: List[Dict]):
    """Generate a comprehensive test report"""
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE MODEL TEST REPORT")
    print("="*70)
    
    # Separate YOLO and RetinaFace results
    yolo_results = [r for r in all_results if r['environment'] == 'yolo']
    retina_results = [r for r in all_results if r['environment'] == 'retinaface']
    
    # YOLO Summary
    if yolo_results:
        print("\n🔷 YOLO Models Performance")
        print("-"*50)
        
        for result in yolo_results:
            model = result['model']
            success_rate = (result['successful_processes'] / result['total_images'] * 100) if result['total_images'] > 0 else 0
            avg_time = np.mean(result['process_times']) if result['process_times'] else 0
            
            status = "✅" if success_rate == 100 else "⚠️" if success_rate > 0 else "❌"
            
            print(f"{status} {model:20s}")
            print(f"   Load Time: {result['load_time']:.2f}s")
            print(f"   Success Rate: {success_rate:.0f}% ({result['successful_processes']}/{result['total_images']})")
            print(f"   Total Faces: {result['total_faces_detected']}")
            print(f"   Avg Process Time: {avg_time:.2f}s")
            
            if result['errors']:
                print(f"   ⚠️ Errors: {len(result['errors'])}")
    
    # RetinaFace Summary
    if retina_results:
        print("\n🔶 RetinaFace Model Performance")
        print("-"*50)
        
        for result in retina_results:
            model = result['model']
            success_rate = (result['successful_processes'] / result['total_images'] * 100) if result['total_images'] > 0 else 0
            avg_time = np.mean(result['process_times']) if result['process_times'] else 0
            
            status = "✅" if success_rate == 100 else "⚠️" if success_rate > 0 else "❌"
            
            print(f"{status} {model:20s}")
            print(f"   Load Time: {result['load_time']:.2f}s")
            print(f"   Success Rate: {success_rate:.0f}% ({result['successful_processes']}/{result['total_images']})")
            print(f"   Total Faces: {result['total_faces_detected']}")
            print(f"   Avg Process Time: {avg_time:.2f}s")
            
            if result['errors']:
                print(f"   ⚠️ Errors: {len(result['errors'])}")
    
    # Overall Summary
    print("\n" + "="*70)
    print("📈 OVERALL SUMMARY")
    print("-"*50)
    
    total_models = len(all_results)
    perfect_models = sum(1 for r in all_results if r['successful_processes'] == r['total_images'])
    partial_models = sum(1 for r in all_results if 0 < r['successful_processes'] < r['total_images'])
    failed_models = sum(1 for r in all_results if r['successful_processes'] == 0)
    
    print(f"Total Models Tested: {total_models}")
    print(f"✅ Perfect (100% success): {perfect_models}")
    print(f"⚠️  Partial success: {partial_models}")
    print(f"❌ Failed completely: {failed_models}")
    
    # Performance comparison
    if all_results:
        fastest_load = min(all_results, key=lambda x: x['load_time'])
        print(f"\n⚡ Fastest to load: {fastest_load['model']} ({fastest_load['load_time']:.2f}s)")
        
        valid_results = [r for r in all_results if r['process_times']]
        if valid_results:
            fastest_process = min(valid_results, key=lambda x: np.mean(x['process_times']))
            print(f"⚡ Fastest processing: {fastest_process['model']} ({np.mean(fastest_process['process_times']):.2f}s avg)")
            
            most_accurate = max(valid_results, key=lambda x: x['total_faces_detected'])
            print(f"👁️  Most faces detected: {most_accurate['model']} ({most_accurate['total_faces_detected']} total)")

def main():
    """Main test execution"""
    print("🚀 Starting Comprehensive Face Detection Model Testing")
    print("="*70)
    
    # Get test images
    test_images = download_test_images()
    
    if not test_images:
        print("❌ No test images available")
        return 1
    
    print(f"\n📸 Using {len(test_images)} test image(s)")
    
    # Define models to test
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
    print("\n" + "="*70)
    print("🔷 TESTING YOLO MODELS")
    print("="*70)
    
    for model in yolo_models:
        result = test_model_on_images(model, test_images, env_type='yolo')
        all_results.append(result)
        time.sleep(1)  # Brief pause between models
    
    # Test RetinaFace
    print("\n" + "="*70)
    print("🔶 TESTING RETINAFACE MODEL")
    print("="*70)
    
    for model in retinaface_models:
        result = test_model_on_images(model, test_images, env_type='retinaface')
        all_results.append(result)
    
    # Generate report
    generate_report(all_results)
    
    print("\n🎯 Testing Complete!")
    print("="*70)
    
    # Return exit code
    failed_count = sum(1 for r in all_results if r['successful_processes'] == 0)
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())