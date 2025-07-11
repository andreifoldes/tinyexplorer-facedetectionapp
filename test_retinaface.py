#!/usr/bin/env python3
"""
Test script to verify RetinaFace is working in the target conda environment
"""
import os
import sys
import cv2
import numpy as np
from datetime import datetime

def test_retinaface():
    """Test RetinaFace model with the provided test image"""
    print("=" * 60)
    print("RetinaFace Model Test")
    print("=" * 60)
    
    # Print system information
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print()
    
    # Test image path
    test_image_path = "tests/faces_folder/my-passport-photo.jpg"
    
    # Check if test image exists
    if not os.path.exists(test_image_path):
        print(f"❌ Error: Test image not found at {test_image_path}")
        return False
    
    print(f"✅ Test image found: {test_image_path}")
    
    # Try to import required libraries
    print("\n🔍 Checking dependencies...")
    
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow: {tf.__version__}")
        # Suppress TensorFlow logging
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    except ImportError as e:
        print(f"❌ TensorFlow not available: {e}")
        return False
    
    try:
        from retinaface import RetinaFace
        print("✅ RetinaFace imported successfully")
    except ImportError as e:
        print(f"❌ RetinaFace not available: {e}")
        print("   Install with: pip install retina-face")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV not available: {e}")
        return False
    
    # Load and validate the test image
    print(f"\n📷 Loading test image: {test_image_path}")
    
    try:
        image = cv2.imread(test_image_path)
        if image is None:
            print(f"❌ Error: Could not load image from {test_image_path}")
            return False
        
        height, width, channels = image.shape
        print(f"✅ Image loaded successfully: {width}x{height}x{channels}")
        
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return False
    
    # Test RetinaFace initialization
    print("\n🚀 Testing RetinaFace initialization...")
    
    try:
        # Test with a small dummy image first
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        _ = RetinaFace.detect_faces(test_img)
        print("✅ RetinaFace initialized successfully")
        
    except Exception as e:
        print(f"❌ RetinaFace initialization failed: {e}")
        
        # Try with different TensorFlow configurations
        print("🔄 Trying alternative initialization...")
        try:
            tf.keras.backend.clear_session()
            tf.keras.backend.set_learning_phase(0)
            test_img = np.ones((224, 224, 3), dtype=np.uint8) * 128
            _ = RetinaFace.detect_faces(test_img, threshold=0.9)
            print("✅ RetinaFace initialized with alternative method")
        except Exception as e2:
            print(f"❌ Alternative initialization also failed: {e2}")
            return False
    
    # Test face detection on the actual image
    print(f"\n🔍 Testing face detection on {os.path.basename(test_image_path)}...")
    
    try:
        start_time = datetime.now()
        
        # Test with different confidence thresholds
        confidence_thresholds = [0.9, 0.8, 0.7, 0.5]
        
        for threshold in confidence_thresholds:
            print(f"  Testing with confidence threshold: {threshold}")
            
            detections = RetinaFace.detect_faces(image, threshold=threshold)
            
            if detections:
                num_faces = len(detections)
                print(f"  ✅ Found {num_faces} face(s) with confidence >= {threshold}")
                
                # Print detection details
                for i, (key, detection) in enumerate(detections.items()):
                    facial_area = detection["facial_area"]
                    confidence = detection["score"]
                    x, y, w, h = facial_area[0], facial_area[1], facial_area[2] - facial_area[0], facial_area[3] - facial_area[1]
                    
                    print(f"    Face {i+1}: x={x}, y={y}, w={w}, h={h}, confidence={confidence:.3f}")
                
                break  # Stop at first successful detection
            else:
                print(f"  ⚠️  No faces detected with confidence >= {threshold}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        if not any(RetinaFace.detect_faces(image, threshold=t) for t in confidence_thresholds):
            print("⚠️  Warning: No faces detected at any confidence threshold")
            print("   This might indicate:")
            print("   - The image doesn't contain clearly visible faces")
            print("   - The model needs different parameters")
            print("   - There might be an issue with the model")
            return False
        
    except Exception as e:
        print(f"❌ Error during face detection: {e}")
        return False
    
    # Test saving results (optional)
    print("\n💾 Testing result saving...")
    
    try:
        # Create results directory
        results_dir = "test_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Detect faces again for visualization
        detections = RetinaFace.detect_faces(image, threshold=0.7)
        
        if detections:
            result_img = image.copy()
            
            # Draw bounding boxes
            for key, detection in detections.items():
                facial_area = detection["facial_area"]
                confidence = detection["score"]
                x, y, w, h = facial_area[0], facial_area[1], facial_area[2] - facial_area[0], facial_area[3] - facial_area[1]
                
                # Draw rectangle and confidence score
                cv2.rectangle(result_img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
                cv2.putText(result_img, f"{confidence:.2f}", (int(x), int(y - 5)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Save result image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_path = os.path.join(results_dir, f"retinaface_test_result_{timestamp}.jpg")
            cv2.imwrite(result_path, result_img)
            print(f"✅ Result saved to: {result_path}")
        else:
            print("⚠️  No faces to visualize")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        # This is not critical, so we don't return False
    
    print("\n🎉 RetinaFace test completed successfully!")
    print("=" * 60)
    return True

def check_environment():
    """Check if we're in the correct conda environment"""
    print("🌍 Environment Check:")
    
    # Check if we're in a conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"✅ Conda environment: {conda_env}")
    else:
        print("⚠️  Not in a conda environment (or CONDA_DEFAULT_ENV not set)")
    
    # Check virtual environment
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        print(f"✅ Virtual environment: {venv}")
    
    print(f"Python path: {sys.executable}")
    print(f"Python version: {sys.version}")
    print()

if __name__ == "__main__":
    print("🧪 Starting RetinaFace Test Suite")
    print()
    
    check_environment()
    
    success = test_retinaface()
    
    if success:
        print("\n✅ All tests passed! RetinaFace is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! There are issues with RetinaFace setup.")
        sys.exit(1) 