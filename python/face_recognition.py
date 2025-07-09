import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import threading
import time
from typing import List, Dict, Optional, Callable

class FaceRecognitionProcessor:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.model = None
        self.progress_callback = progress_callback
        self.is_processing = False
        self.results = []
        
    def load_model(self, model_path: str = "yolov8n.pt"):
        """Load YOLO model for face detection"""
        try:
            self.model = YOLO(model_path)
            if self.progress_callback:
                self.progress_callback("Model loaded successfully")
            return True
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Error loading model: {str(e)}")
            return False
    
    def process_image(self, image_path: str, confidence_threshold: float = 0.5) -> List[Dict]:
        """Process a single image for face detection"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Run inference
            results = self.model(image, conf=confidence_threshold)
            
            # Extract face detections
            detections = []
            for result in results:
                for box in result.boxes:
                    if box.cls == 0:  # Assuming class 0 is person/face
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': float(confidence),
                            'image_path': image_path
                        })
            
            return detections
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Error processing {image_path}: {str(e)}")
            return []
    
    def process_folder(self, folder_path: str, confidence_threshold: float = 0.5):
        """Process all images in a folder"""
        self.is_processing = True
        self.results = []
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            if self.progress_callback:
                self.progress_callback("No image files found in the specified folder")
            self.is_processing = False
            return
        
        total_files = len(image_files)
        if self.progress_callback:
            self.progress_callback(f"Found {total_files} image files to process")
        
        # Process each image
        for i, image_path in enumerate(image_files):
            if not self.is_processing:  # Check if processing was cancelled
                break
                
            if self.progress_callback:
                self.progress_callback(f"Processing {os.path.basename(image_path)} ({i+1}/{total_files})")
            
            detections = self.process_image(image_path, confidence_threshold)
            self.results.extend(detections)
        
        if self.progress_callback:
            self.progress_callback(f"Processing complete. Found {len(self.results)} face detections")
        
        self.is_processing = False
    
    def stop_processing(self):
        """Stop the current processing"""
        self.is_processing = False
        if self.progress_callback:
            self.progress_callback("Processing stopped by user")
    
    def get_results(self) -> List[Dict]:
        """Get the current results"""
        return self.results
    
    def get_available_models(self) -> List[str]:
        """Get list of available YOLO models"""
        return [
            "yolov8n.pt",
            "yolov8s.pt", 
            "yolov8m.pt",
            "yolov8l.pt",
            "yolov8x.pt"
        ]