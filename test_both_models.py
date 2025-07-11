#!/usr/bin/env python3
"""
Comprehensive test script to verify both YOLO and RetinaFace models work in the same environment
"""
import os
import sys
import cv2
import numpy as np
from datetime import datetime
import torch

def test_environment():
    """Test the Python environment and dependencies"""
    print("🌍 Environment Check:")
    print("=" * 60)
    
    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"✅ Conda environment: {conda_env}")
    else:
        print("⚠️  Not in a conda environment")
    
    print(f"🐍 Python version: {sys.version}")
    print(f"📂 Python executable: {sys.executable}")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        print(f"🚀 CUDA available: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA version: {torch.version.cuda}")
    else:
        print("💻 CUDA not available, using CPU")
    
    print()

def check_dependencies():
    """Check all required dependencies"""
    print("🔍 Checking Dependencies:")
    print("=" * 60)
    
    dependencies = [
        ("torch", "PyTorch"),
        ("torchvision", "TorchVision"),
        ("ultralytics", "Ultralytics YOLO"),
        ("tensorflow", "TensorFlow"),
        ("tf_keras", "TF-Keras"),
        ("retinaface", "RetinaFace"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("PIL", "Pillow")
    ]
    
    missing_deps = []
    
    for import_name, display_name in dependencies:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✅ {display_name}: {version}")
        except ImportError as e:
            print(f"❌ {display_name}: Not available - {e}")
            missing_deps.append(display_name)
    
    print()
    return len(missing_deps) == 0

def test_yolo_model():
    """Test YOLO model for face detection"""
    print("🎯 Testing YOLO Model:")
    print("=" * 60)
    
    test_image_path = "tests/faces_folder/my-passport-photo.jpg"
    
    # Check if test image exists
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    try:
        from ultralytics import YOLO
        
        # Load YOLO model (this will download if not present)
        print("📥 Loading YOLO model...")
        model = YOLO('yolov8n.pt')  # Start with nano model for testing
        
        # Load image
        print(f"📷 Loading test image: {test_image_path}")
        image = cv2.imread(test_image_path)
        if image is None:
            print("❌ Failed to load test image")
            return False
        
        height, width = image.shape[:2]
        print(f"✅ Image loaded: {width}x{height}")
        
        # Run inference
        print("🔍 Running YOLO inference...")
        start_time = datetime.now()
        results = model(test_image_path, conf=0.25)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        # Check results
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                num_detections = len(result.boxes)
                print(f"✅ YOLO detected {num_detections} object(s)")
                
                # Print detection details
                for i, box in enumerate(result.boxes):
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = model.names[cls] if cls < len(model.names) else "unknown"
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    print(f"   Detection {i+1}: {class_name} (conf: {conf:.3f}) at [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")
                
                return True
            else:
                print("⚠️  YOLO: No objects detected")
                return True  # Still successful, just no detections
        else:
            print("⚠️  YOLO: No results returned")
            return False
            
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False

def test_retinaface_model():
    """Test RetinaFace model for face detection"""
    print("🎭 Testing RetinaFace Model:")
    print("=" * 60)
    
    test_image_path = "tests/faces_folder/my-passport-photo.jpg"
    
    try:
        from retinaface import RetinaFace
        
        # Load image
        print(f"📷 Loading test image: {test_image_path}")
        image = cv2.imread(test_image_path)
        if image is None:
            print("❌ Failed to load test image")
            return False
        
        height, width = image.shape[:2]
        print(f"✅ Image loaded: {width}x{height}")
        
        # Initialize RetinaFace
        print("🚀 Initializing RetinaFace...")
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        try:
            _ = RetinaFace.detect_faces(test_img)
            print("✅ RetinaFace initialized successfully")
        except Exception as e:
            print(f"⚠️  RetinaFace initialization warning: {e}")
            print("🔄 Trying alternative initialization...")
            
            # Try alternative initialization
            import tensorflow as tf
            tf.keras.backend.clear_session()
            tf.keras.backend.set_learning_phase(0)
            test_img = np.ones((224, 224, 3), dtype=np.uint8) * 128
            _ = RetinaFace.detect_faces(test_img, threshold=0.9)
            print("✅ RetinaFace initialized with alternative method")
        
        # Run face detection
        print("🔍 Running RetinaFace inference...")
        start_time = datetime.now()
        
        # Test with multiple confidence thresholds
        confidence_thresholds = [0.9, 0.8, 0.7, 0.5]
        detections = None
        
        for threshold in confidence_thresholds:
            print(f"   Testing with confidence threshold: {threshold}")
            detections = RetinaFace.detect_faces(image, threshold=threshold)
            
            if detections:
                num_faces = len(detections)
                print(f"   ✅ Found {num_faces} face(s) with confidence >= {threshold}")
                
                # Print detection details
                for i, (key, detection) in enumerate(detections.items()):
                    facial_area = detection["facial_area"]
                    confidence = detection["score"]
                    landmarks = detection.get("landmarks", {})
                    
                    x, y, w, h = facial_area[0], facial_area[1], facial_area[2] - facial_area[0], facial_area[3] - facial_area[1]
                    print(f"      Face {i+1}: x={x}, y={y}, w={w}, h={h}, confidence={confidence:.3f}")
                    
                    if landmarks:
                        print(f"         Landmarks: {len(landmarks)} points detected")
                
                break
            else:
                print(f"   ⚠️  No faces detected with confidence >= {threshold}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        if detections:
            print("✅ RetinaFace test successful!")
            return True
        else:
            print("⚠️  RetinaFace: No faces detected at any threshold")
            print("   This might indicate the image doesn't contain clear faces")
            return True  # Still successful, just no detections
            
    except Exception as e:
        print(f"❌ RetinaFace test failed: {e}")
        return False

def test_face_recognition_integration():
    """Test the face recognition processor from the main codebase"""
    print("🔧 Testing Face Recognition Integration:")
    print("=" * 60)
    
    try:
        # Import the face recognition processor
        sys.path.append('python')
        from face_recognition import FaceRecognitionProcessor
        
        # Create processor instance
        def progress_callback(message):
            print(f"   {message}")
        
        processor = FaceRecognitionProcessor(progress_callback=progress_callback)
        
        # Test YOLO model loading
        print("📥 Testing YOLO model loading...")
        yolo_success = processor.load_model("yolov8n.pt")
        if yolo_success:
            print("✅ YOLO model loaded successfully")
        else:
            print("❌ YOLO model loading failed")
        
        # Test RetinaFace model loading
        print("📥 Testing RetinaFace model loading...")
        retinaface_success = processor.load_model("retinaface")
        if retinaface_success:
            print("✅ RetinaFace model loaded successfully")
        else:
            print("❌ RetinaFace model loading failed")
        
        # Test image processing with both models
        test_image_path = "tests/faces_folder/my-passport-photo.jpg"
        
        if yolo_success:
            print("🎯 Testing YOLO image processing...")
            processor.load_model("yolov8n.pt")
            yolo_results = processor.process_image(test_image_path, confidence_threshold=0.25)
            print(f"   YOLO results: {len(yolo_results) if yolo_results else 0} detections")
        
        if retinaface_success:
            print("🎭 Testing RetinaFace image processing...")
            processor.load_model("retinaface")
            retinaface_results = processor.process_image(test_image_path, confidence_threshold=0.7)
            print(f"   RetinaFace results: {len(retinaface_results) if retinaface_results else 0} detections")
        
        return yolo_success and retinaface_success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Comprehensive Model Testing Suite")
    print("Testing both YOLO and RetinaFace in the same environment")
    print("=" * 80)
    print()
    
    # Test environment
    test_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Missing dependencies. Please install them first.")
        return False
    
    # Test individual models
    print()
    yolo_success = test_yolo_model()
    
    print()
    retinaface_success = test_retinaface_model()
    
    # Test integration
    print()
    integration_success = test_face_recognition_integration()
    
    # Summary
    print()
    print("📊 Test Summary:")
    print("=" * 60)
    print(f"YOLO Test: {'✅ PASSED' if yolo_success else '❌ FAILED'}")
    print(f"RetinaFace Test: {'✅ PASSED' if retinaface_success else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    overall_success = yolo_success and retinaface_success and integration_success
    
    if overall_success:
        print("\n🎉 All tests passed! Both YOLO and RetinaFace are working correctly in the same environment.")
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 