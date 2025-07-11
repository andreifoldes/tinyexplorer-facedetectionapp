#!/usr/bin/env python3
"""
Compatibility test script to find the right combination of packages for both YOLO and RetinaFace
"""
import os
import sys
import subprocess
import importlib.util

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"🔄 Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def check_import(module_name, display_name=None):
    """Check if a module can be imported"""
    if display_name is None:
        display_name = module_name
    
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✅ {display_name}: {version}")
            return True
        else:
            print(f"❌ {display_name}: Not found")
            return False
    except Exception as e:
        print(f"❌ {display_name}: Import error - {e}")
        return False

def test_retinaface():
    """Test RetinaFace functionality"""
    print("\n🎭 Testing RetinaFace:")
    print("-" * 40)
    
    try:
        from retinaface import RetinaFace
        import numpy as np
        
        # Test initialization with a dummy image
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = RetinaFace.detect_faces(test_img)
        print("✅ RetinaFace basic test passed")
        return True
        
    except Exception as e:
        print(f"❌ RetinaFace test failed: {e}")
        return False

def test_yolo():
    """Test YOLO functionality"""
    print("\n🎯 Testing YOLO:")
    print("-" * 40)
    
    try:
        from ultralytics import YOLO
        import torch
        
        # Create a simple YOLO model
        model = YOLO('yolov8n.pt')
        print("✅ YOLO basic test passed")
        return True
        
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False

def test_combination_1():
    """Test combination 1: TensorFlow 2.15.0 + older packages"""
    print("\n🧪 Testing Combination 1: TensorFlow 2.15.0 + Compatible packages")
    print("=" * 70)
    
    packages = [
        "tensorflow==2.15.0",
        "opencv-python",
        "numpy",
        "pillow",
        "retina-face",
        "torch",
        "torchvision", 
        "ultralytics"
    ]
    
    # Install packages
    for package in packages:
        if not install_package(package):
            print(f"❌ Combination 1 failed during installation of {package}")
            return False
    
    # Check imports
    if not check_import("tensorflow", "TensorFlow"):
        return False
    if not check_import("cv2", "OpenCV"):
        return False
    if not check_import("retinaface", "RetinaFace"):
        return False
    if not check_import("torch", "PyTorch"):
        return False
    if not check_import("ultralytics", "Ultralytics"):
        return False
    
    # Test functionality
    retinaface_ok = test_retinaface()
    yolo_ok = test_yolo()
    
    success = retinaface_ok and yolo_ok
    print(f"\n📊 Combination 1 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success

def test_combination_2():
    """Test combination 2: TensorFlow 2.13.0 + stable packages"""
    print("\n🧪 Testing Combination 2: TensorFlow 2.13.0 + Stable packages")
    print("=" * 70)
    
    packages = [
        "tensorflow==2.13.0",
        "keras==2.13.1",
        "opencv-python==4.8.1.78",
        "numpy==1.24.3",
        "pillow",
        "retina-face",
        "torch==2.0.1",
        "torchvision==0.15.2",
        "ultralytics"
    ]
    
    # Install packages
    for package in packages:
        if not install_package(package):
            print(f"❌ Combination 2 failed during installation of {package}")
            return False
    
    # Check imports
    if not check_import("tensorflow", "TensorFlow"):
        return False
    if not check_import("cv2", "OpenCV"):
        return False
    if not check_import("retinaface", "RetinaFace"):
        return False
    if not check_import("torch", "PyTorch"):
        return False
    if not check_import("ultralytics", "Ultralytics"):
        return False
    
    # Test functionality
    retinaface_ok = test_retinaface()
    yolo_ok = test_yolo()
    
    success = retinaface_ok and yolo_ok
    print(f"\n📊 Combination 2 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success

def test_combination_3():
    """Test combination 3: TensorFlow 2.12.0 + known working versions"""
    print("\n🧪 Testing Combination 3: TensorFlow 2.12.0 + Known working versions")
    print("=" * 70)
    
    packages = [
        "tensorflow==2.12.0",
        "opencv-python",
        "numpy<2.0",
        "pillow",
        "retina-face",
        "torch",
        "torchvision",
        "ultralytics"
    ]
    
    # Install packages
    for package in packages:
        if not install_package(package):
            print(f"❌ Combination 3 failed during installation of {package}")
            return False
    
    # Check imports
    if not check_import("tensorflow", "TensorFlow"):
        return False
    if not check_import("cv2", "OpenCV"):
        return False
    if not check_import("retinaface", "RetinaFace"):
        return False
    if not check_import("torch", "PyTorch"):
        return False
    if not check_import("ultralytics", "Ultralytics"):
        return False
    
    # Test functionality
    retinaface_ok = test_retinaface()
    yolo_ok = test_yolo()
    
    success = retinaface_ok and yolo_ok
    print(f"\n📊 Combination 3 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success

def create_environment_yml(working_combination):
    """Create environment.yml for the working combination"""
    if working_combination == 1:
        content = """name: retinaface-yolo-working
channels:
  - defaults
dependencies:
  - python=3.9
  - pip
  - pip:
    - tensorflow==2.15.0
    - opencv-python
    - numpy
    - pillow
    - retina-face
    - torch
    - torchvision
    - ultralytics
    - flask
    - flask-cors
    - graphene
    - flask-graphql
"""
    elif working_combination == 2:
        content = """name: retinaface-yolo-working
channels:
  - defaults
dependencies:
  - python=3.9
  - pip
  - pip:
    - tensorflow==2.13.0
    - keras==2.13.1
    - opencv-python==4.8.1.78
    - numpy==1.24.3
    - pillow
    - retina-face
    - torch==2.0.1
    - torchvision==0.15.2
    - ultralytics
    - flask
    - flask-cors
    - graphene
    - flask-graphql
"""
    elif working_combination == 3:
        content = """name: retinaface-yolo-working
channels:
  - defaults
dependencies:
  - python=3.9
  - pip
  - pip:
    - tensorflow==2.12.0
    - opencv-python
    - numpy<2.0
    - pillow
    - retina-face
    - torch
    - torchvision
    - ultralytics
    - flask
    - flask-cors
    - graphene
    - flask-graphql
"""
    
    with open("environment-working.yml", "w") as f:
        f.write(content)
    
    print(f"✅ Created environment-working.yml for combination {working_combination}")

def main():
    """Main compatibility testing function"""
    print("🧪 RetinaFace + YOLO Compatibility Testing Suite")
    print("=" * 80)
    
    # Check current environment
    print(f"🐍 Python version: {sys.version}")
    print(f"📂 Python executable: {sys.executable}")
    
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"🌍 Conda environment: {conda_env}")
    
    print()
    
    # Test different combinations
    combinations_tested = []
    working_combination = None
    
    # Test combination 1
    try:
        if test_combination_1():
            working_combination = 1
            combinations_tested.append((1, True))
        else:
            combinations_tested.append((1, False))
    except Exception as e:
        print(f"❌ Combination 1 crashed: {e}")
        combinations_tested.append((1, False))
    
    # If combination 1 didn't work, try combination 2
    if working_combination is None:
        try:
            if test_combination_2():
                working_combination = 2
                combinations_tested.append((2, True))
            else:
                combinations_tested.append((2, False))
        except Exception as e:
            print(f"❌ Combination 2 crashed: {e}")
            combinations_tested.append((2, False))
    
    # If combination 2 didn't work, try combination 3
    if working_combination is None:
        try:
            if test_combination_3():
                working_combination = 3
                combinations_tested.append((3, True))
            else:
                combinations_tested.append((3, False))
        except Exception as e:
            print(f"❌ Combination 3 crashed: {e}")
            combinations_tested.append((3, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 COMPATIBILITY TEST SUMMARY")
    print("=" * 80)
    
    for combo_num, success in combinations_tested:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"Combination {combo_num}: {status}")
    
    if working_combination:
        print(f"\n🎉 SUCCESS! Combination {working_combination} works!")
        print("Creating environment.yml file for the working combination...")
        create_environment_yml(working_combination)
        
        print("\n💡 Next steps:")
        print("1. Use the generated environment-working.yml to create a new environment")
        print("2. conda env create -f environment-working.yml")
        print("3. conda activate retinaface-yolo-working")
        print("4. Test your face recognition application")
        
        return True
    else:
        print("\n❌ No working combination found.")
        print("💡 Suggestions:")
        print("1. Try different Python versions (3.8, 3.10)")
        print("2. Check for newer RetinaFace alternatives")
        print("3. Consider using only YOLO for face detection")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 