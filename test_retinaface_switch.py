#!/usr/bin/env python3
"""
Test script to verify RetinaFace environment switching works in development mode.
This simulates the Electron app switching from YOLO to RetinaFace environment.
"""

import subprocess
import json
import time
import os
import signal

def test_environment_switch():
    """Test switching from YOLO to RetinaFace environment"""
    
    print("🔬 Testing environment switching functionality...")
    
    # Test 1: Start with YOLO environment (default)
    print("\n1️⃣ Testing YOLO environment...")
    yolo_env = os.environ.copy()
    yolo_env['MODEL_TYPE'] = 'yolo'
    
    yolo_proc = subprocess.Popen(
        ['./yolo-env/bin/python', 'python/multi_env_launcher.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=yolo_env
    )
    
    # Send get_models command
    yolo_command = json.dumps({"type": "get_models", "id": 1}) + "\n"
    
    try:
        yolo_stdout, yolo_stderr = yolo_proc.communicate(input=yolo_command, timeout=15)
        
        print(f"✅ YOLO Environment - stderr: {yolo_stderr.strip()}")
        
        if "YOLO/Ultralytics loaded successfully" in yolo_stderr:
            print("✅ YOLO environment loaded successfully")
        else:
            print("⚠️  YOLO environment may have issues")
            
        if yolo_stdout.strip():
            print(f"✅ YOLO Response: {yolo_stdout.strip()}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  YOLO environment test timed out")
        yolo_proc.kill()
    except Exception as e:
        print(f"❌ YOLO environment test failed: {e}")
    
    # Test 2: Switch to RetinaFace environment
    print("\n2️⃣ Testing RetinaFace environment...")
    retina_env = os.environ.copy()
    retina_env['MODEL_TYPE'] = 'retinaface'
    
    retina_proc = subprocess.Popen(
        ['./retinaface-env/bin/python', 'python/multi_env_launcher.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=retina_env
    )
    
    # Send get_models command
    retina_command = json.dumps({"type": "get_models", "id": 1}) + "\n"
    
    try:
        retina_stdout, retina_stderr = retina_proc.communicate(input=retina_command, timeout=15)
        
        print(f"✅ RetinaFace Environment - stderr: {retina_stderr.strip()}")
        
        if "RetinaFace loaded successfully" in retina_stderr:
            print("✅ RetinaFace environment loaded successfully")
        else:
            print("⚠️  RetinaFace environment may have issues")
            
        if "YOLO/Ultralytics not available" in retina_stderr:
            print("✅ Confirmed YOLO not available in RetinaFace environment (correct isolation)")
            
        if retina_stdout.strip():
            print(f"✅ RetinaFace Response: {retina_stdout.strip()}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  RetinaFace environment test timed out")
        retina_proc.kill()
    except Exception as e:
        print(f"❌ RetinaFace environment test failed: {e}")

    print("\n🎯 Environment switching test complete!")
    print("Both environments should be working independently with proper dependency isolation.")

if __name__ == "__main__":
    test_environment_switch()