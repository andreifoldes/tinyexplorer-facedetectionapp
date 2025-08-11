#!/usr/bin/env python3
"""
Direct test of the packaged virtual environments
"""
import subprocess
import sys
import os

def test_environment(env_path, env_name, packages_to_test):
    """Test a specific environment"""
    python_exe = os.path.join(env_path, 'bin', 'python')
    
    print(f"🧪 Testing {env_name} environment")
    print(f"📍 Path: {env_path}")
    print(f"🐍 Python: {python_exe}")
    
    if not os.path.exists(python_exe):
        print(f"❌ Python executable not found: {python_exe}")
        return False
    
    success = True
    
    # Test each package
    for package in packages_to_test:
        print(f"📦 Testing import: {package}")
        try:
            result = subprocess.run(
                [python_exe, '-c', f'import {package}; print(f"✅ {package} imported successfully")'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ {package}: SUCCESS")
                if result.stdout.strip():
                    print(f"   Output: {result.stdout.strip()}")
            else:
                print(f"❌ {package}: FAILED")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                success = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {package}: TIMEOUT")
            success = False
        except Exception as e:
            print(f"💥 {package}: EXCEPTION - {e}")
            success = False
    
    print()
    return success

def main():
    """Test both environments"""
    base_path = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist"
    
    print("🚀 Testing Packaged Virtual Environments")
    print("=" * 50)
    print()
    
    # Test YOLO environment
    yolo_path = os.path.join(base_path, "yolo-env")
    yolo_packages = ["torch", "torchvision", "ultralytics", "cv2", "numpy", "PIL"]
    
    yolo_success = test_environment(yolo_path, "YOLO", yolo_packages)
    
    # Test RetinaFace environment
    retinaface_path = os.path.join(base_path, "retinaface-env")
    retinaface_packages = ["tensorflow", "retinaface", "cv2", "numpy", "PIL"]
    
    retinaface_success = test_environment(retinaface_path, "RetinaFace", retinaface_packages)
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 20)
    print(f"YOLO Environment: {'✅ PASS' if yolo_success else '❌ FAIL'}")
    print(f"RetinaFace Environment: {'✅ PASS' if retinaface_success else '❌ FAIL'}")
    
    overall_success = yolo_success and retinaface_success
    print(f"Overall Result: {'🎉 ALL TESTS PASSED' if overall_success else '💥 SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)