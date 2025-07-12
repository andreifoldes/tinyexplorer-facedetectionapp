import os
import tempfile
import urllib.request
import torch
from retinaface import RetinaFace
import json

# Use the specific passport photo instead of downloading
IMAGE_PATH = "test_imgs/my-passport-photo copy 2.jpg"


def setup_torch_compatibility():
    """Setup PyTorch compatibility for loading YOLO models with PyTorch 2.7+"""
    try:
        # Add all necessary safe globals for Ultralytics YOLO models
        safe_globals = [
            'ultralytics.nn.tasks.DetectionModel',
            'ultralytics.nn.modules.Detect',
            'ultralytics.nn.modules.Conv',
            'ultralytics.nn.modules.C2f',
            'ultralytics.nn.modules.SPPF',
            'ultralytics.nn.modules.Bottleneck',
            'ultralytics.nn.modules.Concat',
            'ultralytics.nn.modules.DFL',
            'torch.nn.modules.conv.Conv2d',
            'torch.nn.modules.batchnorm.BatchNorm2d',
            'torch.nn.modules.activation.SiLU',
            'torch.nn.modules.pooling.MaxPool2d',
            'torch.nn.modules.upsampling.Upsample',
            'torch.nn.modules.container.Sequential',
            'torch.nn.modules.container.ModuleList',
            'collections.OrderedDict',
            'torch._utils._rebuild_tensor_v2',
            'torch._utils._rebuild_parameter',
            'torch.Size',
            'torch.FloatStorage',
            'torch.HalfStorage',
            'torch.LongStorage',
            '__builtin__.set'
        ]
        
        # Add safe globals
        torch.serialization.add_safe_globals(safe_globals)
        print("✓ Added PyTorch safe globals for YOLO model loading")
        
        # Also set environment variable as backup
        os.environ['TORCH_SERIALIZATION_SAFE_GLOBALS'] = '1'
        
        return True
    except Exception as e:
        print(f"⚠ Warning: Could not setup PyTorch compatibility: {e}")
        return False


def create_torch_load_wrapper():
    """Create a wrapper for torch.load that handles weights_only parameter"""
    original_load = torch.load
    
    def safe_torch_load(*args, **kwargs):
        """Wrapper for torch.load that sets weights_only=False for model files"""
        # For .pt files (PyTorch models), set weights_only=False
        if len(args) > 0 and isinstance(args[0], str) and args[0].endswith('.pt'):
            kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    
    return original_load, safe_torch_load


def check_image_exists(image_path: str) -> bool:
    """Check if the specified image file exists."""
    if os.path.exists(image_path):
        print(f"✓ Found image: {image_path}")
        return True
    else:
        print(f"✗ Image not found: {image_path}")
        return False


def detect_with_retinaface(image_path: str) -> dict:
    """Run face detection using RetinaFace and return detailed results."""
    try:
        results = RetinaFace.detect_faces(image_path)
        
        # Format results for display
        detection_info = {
            'model': 'RetinaFace',
            'face_count': len(results),
            'detections': []
        }
        
        for face_id, face_data in results.items():
            detection = {
                'face_id': face_id,
                'confidence': face_data.get('score', 'N/A'),
                'bbox': face_data.get('facial_area', 'N/A'),
                'landmarks': face_data.get('landmarks', 'N/A')
            }
            detection_info['detections'].append(detection)
        
        return detection_info
    except Exception as e:
        print(f"Error with RetinaFace detection: {e}")
        return {'model': 'RetinaFace', 'face_count': 0, 'detections': [], 'error': str(e)}


def test_yolo_installation() -> bool:
    """Test if YOLO/Ultralytics is properly installed with PyTorch compatibility fix."""
    try:
        # Setup PyTorch compatibility
        setup_torch_compatibility()
        
        # Create torch.load wrapper
        original_load, safe_load = create_torch_load_wrapper()
        torch.load = safe_load
        
        from ultralytics import YOLO
        print("✓ Ultralytics YOLO is installed")
        
        # Try to create a basic YOLO model
        model = YOLO("yolov8n.pt")
        print("✓ Basic YOLO model loaded successfully")
        
        # Restore original torch.load
        torch.load = original_load
        
        return True
    except Exception as e:
        print(f"✗ YOLO installation test failed: {e}")
        # Restore original torch.load in case of error
        try:
            torch.load = original_load
        except:
            pass
        return False


def detect_with_yolo_general(image_path: str) -> dict:
    """Run object detection using general YOLO model and return detailed results."""
    try:
        # Setup PyTorch compatibility
        setup_torch_compatibility()
        
        # Create torch.load wrapper
        original_load, safe_load = create_torch_load_wrapper()
        torch.load = safe_load
        
        from ultralytics import YOLO
        
        # Use general object detection model
        model = YOLO("yolov8n.pt")
        
        # Run detection
        results = model(image_path)
        
        # Restore original torch.load
        torch.load = original_load
        
        # Format results for display
        detection_info = {
            'model': 'YOLO-General',
            'person_count': 0,
            'detections': []
        }
        
        for result in results:
            if hasattr(result, 'boxes') and result.boxes is not None:
                for i, box in enumerate(result.boxes):
                    if hasattr(box, 'cls') and box.cls is not None:
                        class_id = int(box.cls)
                        confidence = float(box.conf) if hasattr(box, 'conf') else 'N/A'
                        bbox = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else 'N/A'
                        
                        # Get class name
                        class_name = model.names.get(class_id, f'class_{class_id}')
                        
                        detection = {
                            'detection_id': i,
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': confidence,
                            'bbox': bbox  # [x1, y1, x2, y2]
                        }
                        detection_info['detections'].append(detection)
                        
                        # Count persons (class 0)
                        if class_id == 0:
                            detection_info['person_count'] += 1
        
        return detection_info
    except Exception as e:
        print(f"Error with YOLO general detection: {e}")
        # Restore original torch.load in case of error
        try:
            torch.load = original_load
        except:
            pass
        return {'model': 'YOLO-General', 'person_count': 0, 'detections': [], 'error': str(e)}


def download_yolo_face_model() -> str:
    """Download a YOLO face detection model."""
    model_path = "yolov8n-face.pt"
    
    if os.path.exists(model_path):
        print(f"✓ Using existing YOLO face model: {model_path}")
        return model_path
    
    # Try to download from akanametov repository
    model_url = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt"
    
    try:
        print("📥 Downloading YOLO face detection model...")
        urllib.request.urlretrieve(model_url, model_path)
        print(f"✓ Downloaded YOLO face model: {model_path}")
        return model_path
    except Exception as e:
        print(f"✗ Failed to download YOLO face model: {e}")
        return None


def detect_with_yolo_face(image_path: str) -> dict:
    """Run face detection using YOLO face model and return detailed results."""
    try:
        # Download face model if needed
        model_path = download_yolo_face_model()
        if not model_path:
            return {'model': 'YOLO-Face', 'face_count': 0, 'detections': [], 'error': 'Model not available'}
        
        # Setup PyTorch compatibility
        setup_torch_compatibility()
        
        # Create torch.load wrapper
        original_load, safe_load = create_torch_load_wrapper()
        torch.load = safe_load
        
        from ultralytics import YOLO
        
        # Use face detection model
        model = YOLO(model_path)
        
        # Run detection
        results = model(image_path)
        
        # Restore original torch.load
        torch.load = original_load
        
        # Format results for display
        detection_info = {
            'model': 'YOLO-Face',
            'face_count': 0,
            'detections': []
        }
        
        for result in results:
            if hasattr(result, 'boxes') and result.boxes is not None:
                for i, box in enumerate(result.boxes):
                    confidence = float(box.conf) if hasattr(box, 'conf') else 'N/A'
                    bbox = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else 'N/A'
                    
                    detection = {
                        'detection_id': i,
                        'confidence': confidence,
                        'bbox': bbox  # [x1, y1, x2, y2]
                    }
                    detection_info['detections'].append(detection)
                    detection_info['face_count'] += 1
        
        return detection_info
    except Exception as e:
        print(f"Error with YOLO face detection: {e}")
        # Restore original torch.load in case of error
        try:
            torch.load = original_load
        except:
            pass
        return {'model': 'YOLO-Face', 'face_count': 0, 'detections': [], 'error': str(e)}


def print_detection_results(detection_info: dict):
    """Print detailed detection results in a formatted way."""
    print(f"\n📋 {detection_info['model']} Detection Results:")
    print("=" * 60)
    
    if 'error' in detection_info:
        print(f"❌ Error: {detection_info['error']}")
        return
    
    # Print summary
    if detection_info['model'] == 'YOLO-General':
        print(f"👥 Persons detected: {detection_info['person_count']}")
        print(f"📦 Total detections: {len(detection_info['detections'])}")
    else:
        face_count = detection_info.get('face_count', 0)
        print(f"👤 Faces detected: {face_count}")
    
    # Print detailed detections
    if detection_info['detections']:
        print("\n🔍 Detailed Detection Information:")
        print("-" * 60)
        
        for detection in detection_info['detections']:
            if detection_info['model'] == 'RetinaFace':
                print(f"Face ID: {detection['face_id']}")
                print(f"  Confidence: {detection['confidence']}")
                print(f"  Bounding Box: {detection['bbox']}")
                if detection['landmarks'] != 'N/A':
                    print(f"  Landmarks: {detection['landmarks']}")
                print()
            
            elif detection_info['model'] == 'YOLO-General':
                print(f"Detection {detection['detection_id']}:")
                print(f"  Class: {detection['class_name']} (ID: {detection['class_id']})")
                print(f"  Confidence: {detection['confidence']:.3f}")
                print(f"  Bounding Box: [x1={detection['bbox'][0]:.1f}, y1={detection['bbox'][1]:.1f}, "
                      f"x2={detection['bbox'][2]:.1f}, y2={detection['bbox'][3]:.1f}]")
                print()
            
            elif detection_info['model'] == 'YOLO-Face':
                print(f"Face {detection['detection_id']}:")
                print(f"  Confidence: {detection['confidence']:.3f}")
                print(f"  Bounding Box: [x1={detection['bbox'][0]:.1f}, y1={detection['bbox'][1]:.1f}, "
                      f"x2={detection['bbox'][2]:.1f}, y2={detection['bbox'][3]:.1f}]")
                print()
    else:
        print("No detections found.")


def main():
    print("🔍 Face Detection Test - Detailed Results")
    print("=" * 70)
    
    # Check if the image exists
    if not check_image_exists(IMAGE_PATH):
        print(f"❌ Cannot proceed - image file not found!")
        print(f"Please make sure the file exists at: {IMAGE_PATH}")
        return

    print(f"📷 Using image: {IMAGE_PATH}")

    # Test RetinaFace (specialized face detection)
    print("\n🎯 Testing RetinaFace (Face Detection)")
    print("-" * 50)
    retina_results = detect_with_retinaface(IMAGE_PATH)
    print(f"Result: RetinaFace detected {retina_results['face_count']} face(s)")
    print_detection_results(retina_results)

    # Test YOLO installation
    print("\n🔧 Testing YOLO Installation (with PyTorch fix)")
    print("-" * 50)
    yolo_installed = test_yolo_installation()

    if yolo_installed:
        # Test YOLO general object detection
        print("\n🎯 Testing YOLO (General Object Detection)")
        print("-" * 50)
        yolo_general_results = detect_with_yolo_general(IMAGE_PATH)
        print(f"Result: YOLO detected {yolo_general_results['person_count']} person(s)")
        print_detection_results(yolo_general_results)

        # Test YOLO face detection
        print("\n🎯 Testing YOLO (Face Detection)")
        print("-" * 50)
        yolo_face_results = detect_with_yolo_face(IMAGE_PATH)
        print(f"Result: YOLO-Face detected {yolo_face_results['face_count']} face(s)")
        print_detection_results(yolo_face_results)
    else:
        print("Result: YOLO tests skipped due to installation issues")
        yolo_general_results = {'model': 'YOLO-General', 'person_count': 0, 'detections': []}
        yolo_face_results = {'model': 'YOLO-Face', 'face_count': 0, 'detections': []}

    # Summary comparison
    print("\n📊 Summary Comparison")
    print("=" * 70)
    print(f"Image: {IMAGE_PATH}")
    print(f"RetinaFace (Face Detection): {retina_results['face_count']} face(s)")
    print(f"YOLO (Person Detection): {yolo_general_results['person_count']} person(s)")
    print(f"YOLO-Face (Face Detection): {yolo_face_results['face_count']} face(s)")
    print(f"YOLO Installation: {'✓ Working' if yolo_installed else '✗ Issues'}")
    
    # Analysis
    print("\n🔍 Analysis")
    print("-" * 50)
    if retina_results['face_count'] > 0:
        print("✓ RetinaFace successfully detected faces in the passport photo")
        if retina_results['face_count'] == 1:
            print("  → Perfect! Exactly 1 face detected as expected for a passport photo")
        else:
            print(f"  → Note: {retina_results['face_count']} faces detected (unusual for a passport photo)")
    else:
        print("⚠ RetinaFace did not detect any faces in the passport photo")
    
    if yolo_installed:
        if yolo_general_results['person_count'] > 0:
            print("✓ YOLO successfully detected people in the passport photo")
        else:
            print("⚠ YOLO did not detect any people (this can happen with passport photos)")
        
        if yolo_face_results['face_count'] > 0:
            print("✓ YOLO-Face successfully detected faces in the passport photo")
            if yolo_face_results['face_count'] == retina_results['face_count']:
                print("  → Excellent! YOLO-Face and RetinaFace agree on face count")
            else:
                print(f"  → Note: Different face counts (YOLO: {yolo_face_results['face_count']}, RetinaFace: {retina_results['face_count']})")
        else:
            print("⚠ YOLO-Face did not detect any faces")
    
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    main()