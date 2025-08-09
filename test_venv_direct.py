#!/usr/bin/env python3
"""
Test the virtual environments by directly running their Python executables
"""
import subprocess
import sys
import os

def test_venv_direct():
    """Test virtual environments using their python executables directly"""
    
    # Paths to the virtual environment Python executables
    yolo_python = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/yolo-env/bin/python"
    retinaface_python = "/Users/apgroup/Documents/Dev/electron-python-face-recognition/dist/mac/TinyExplorer FaceDetectionApp.app/Contents/Resources/pythondist/retinaface-env/bin/python"
    
    print("🧪 Testing Virtual Environment Python Executables Directly")
    print("=" * 60)
    print()
    
    # Test YOLO environment
    print("🚀 Testing YOLO Environment")
    print(f"📍 Python: {yolo_python}")
    
    if os.path.exists(yolo_python):
        # Test torch and torchvision
        try:
            result = subprocess.run([
                yolo_python, '-c', 
                'import torch, torchvision; print(f"✅ PyTorch {torch.__version__} and torchvision {torchvision.__version__} work!")'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ YOLO Environment: PyTorch imports successful!")
                print(f"   {result.stdout.strip()}")
            else:
                print("❌ YOLO Environment: PyTorch import failed")
                print(f"   Error: {result.stderr.strip()}")
        
        except Exception as e:
            print(f"💥 YOLO Environment: Exception - {e}")
            
        # Test ultralytics specifically
        try:
            result = subprocess.run([
                yolo_python, '-c', 
                'try:\n    from ultralytics import YOLO\n    print("✅ Ultralytics YOLO class imported successfully!")\nexcept Exception as e:\n    print(f"❌ Ultralytics failed: {e}")'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"🎯 YOLO Class Test: {result.stdout.strip()}")
            else:
                print("❌ YOLO Class Test: Failed")
                print(f"   Error: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"💥 YOLO Class Test: Exception - {e}")
    else:
        print(f"❌ YOLO Python executable not found: {yolo_python}")
    
    print()
    
    # Test RetinaFace environment  
    print("🚀 Testing RetinaFace Environment")
    print(f"📍 Python: {retinaface_python}")
    
    if os.path.exists(retinaface_python):
        # Test TensorFlow
        try:
            result = subprocess.run([
                retinaface_python, '-c', 
                'try:\n    import tensorflow as tf\n    print(f"✅ TensorFlow {tf.__version__} imported successfully!")\nexcept Exception as e:\n    print(f"❌ TensorFlow failed: {e}")'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ RetinaFace Environment: {result.stdout.strip()}")
            else:
                print("❌ RetinaFace Environment: TensorFlow import failed")
                print(f"   Error: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"💥 RetinaFace Environment: Exception - {e}")
            
        # Test RetinaFace library
        try:
            result = subprocess.run([
                retinaface_python, '-c', 
                'try:\n    from retinaface import RetinaFace\n    print("✅ RetinaFace library imported successfully!")\nexcept Exception as e:\n    print(f"❌ RetinaFace failed: {e}")'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"🎯 RetinaFace Library Test: {result.stdout.strip()}")
            else:
                print("❌ RetinaFace Library Test: Failed")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
                    
        except Exception as e:
            print(f"💥 RetinaFace Library Test: Exception - {e}")
    else:
        print(f"❌ RetinaFace Python executable not found: {retinaface_python}")
    
    print()
    print("🎉 Direct virtual environment testing completed!")

if __name__ == "__main__":
    test_venv_direct()