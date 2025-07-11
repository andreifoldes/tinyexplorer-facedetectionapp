import os
import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from typing import List, Dict, Optional, Callable
import csv
from datetime import datetime
import torch
import requests

# RetinaFace temporarily disabled due to tf-keras dependency issue
RETINAFACE_AVAILABLE = False
print("RetinaFace temporarily disabled - using YOLO models only")

class FaceDetectionProcessor:
    def __init__(self, progress_callback: Optional[Callable] = None, completion_callback: Optional[Callable] = None):
        self.model = None
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.is_processing = False
        self.results = []
        self.model_type = "YOLO"
        self.current_model_path = None
        
        # Status symbols for better user feedback
        self.status_symbols = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "processing": "⏳",
            "folder": "📁",
            "image": "🖼️",
            "video": "🎬",
            "detection": "🔍",
            "face": "👤",
            "complete": "🏁"
        }
        
    def _download_face_model(self, model_name: str) -> bool:
        """Download face detection model from GitHub releases"""
        face_models_urls = {
            "yolov8n-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-face.pt",
            "yolov8m-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8m-face.pt",
            "yolov8l-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8l-face.pt",
            "yolov11n-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt",
            "yolov11s-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11s-face.pt",
            "yolov11m-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11m-face.pt",
            "yolov11l-face.pt": "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11l-face.pt"
        }
        
        if model_name not in face_models_urls:
            return False
            
        try:
            url = face_models_urls[model_name]
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['info']} Downloading {model_name} from GitHub...")
            
            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and self.progress_callback:
                            progress = (downloaded / total_size) * 100
                            self.progress_callback(f"{self.status_symbols['processing']} Downloading {model_name}: {progress:.1f}%")
            
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['success']} Downloaded {model_name} successfully")
            return True
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error downloading {model_name}: {str(e)}")
            return False
        
    def load_model(self, model_path: str = "yolov8n.pt"):
        """Load model for face detection (YOLO or RetinaFace)"""
        try:
            if model_path.lower() == "retinaface":
                if not RETINAFACE_AVAILABLE:
                    raise ImportError("RetinaFace not available. Install with: pip install retina-face")
                self.model_type = "RetinaFace"
                self.current_model_path = model_path
                # Test RetinaFace initialization (placeholder)
                # This would test RetinaFace initialization when available
                pass
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['success']} RetinaFace model loaded successfully")
                return True
            else:
                self.model_type = "YOLO"
                self.current_model_path = model_path
                
                # Check if model file exists locally
                if not os.path.exists(model_path):
                    if self.progress_callback:
                        self.progress_callback(f"{self.status_symbols['info']} Model {model_path} not found locally")
                    
                    # Try to download face-specific models from GitHub
                    if "-face.pt" in model_path.lower():
                        if not self._download_face_model(model_path):
                            if self.progress_callback:
                                self.progress_callback(f"{self.status_symbols['error']} Failed to download face model {model_path}")
                            return False
                    else:
                        if self.progress_callback:
                            self.progress_callback(f"{self.status_symbols['info']} Standard YOLO model will be downloaded automatically...")
                
                # YOLO automatically downloads standard models if they don't exist
                self.model = YOLO(model_path).to('cuda:0' if torch.cuda.is_available() else 'cpu')
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['success']} YOLO model loaded successfully: {model_path}")
                return True
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error loading model: {str(e)}")
            return False
    
    def process_image(self, image_path: str, confidence_threshold: float = 0.5, save_results: bool = False, result_folder: str = None) -> List[Dict]:
        """Process a single image for face detection"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            detections = []
            
            if self.model_type == "RetinaFace":
                detections = self._process_with_retinaface(image, image_path, confidence_threshold, save_results, result_folder)
            else:
                detections = self._process_with_yolo(image, image_path, confidence_threshold, save_results, result_folder)
            
            # Log completion of individual image processing
            if self.progress_callback:
                num_faces = len(detections) if detections else 0
                if num_faces > 0:
                    self.progress_callback(f"{self.status_symbols['face']} Found {num_faces} face(s) in {os.path.basename(image_path)}")
                else:
                    self.progress_callback(f"{self.status_symbols['complete']} No faces detected in {os.path.basename(image_path)}")
            
            return detections
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error processing {os.path.basename(image_path)}: {str(e)}")
            return []
    
    def process_folder(self, folder_path: str, confidence_threshold: float = 0.5, model_name: str = "yolov8n.pt", save_results: bool = False, results_folder: str = None):
        """Process all images and videos in a folder or single file"""
        self.is_processing = True
        self.results = []
        
        # Send processing started event
        if self.completion_callback:
            self.completion_callback({
                'status': 'processing_started',
                'folder_path': folder_path,
                'model': model_name,
                'confidence': confidence_threshold
            })
            # Small delay to ensure event is processed before continuing
            import time
            time.sleep(0.1)
        
        try:
            # Create result folder if saving results
            result_folder = None
            if save_results:
                if results_folder:
                    # Use the user-specified results folder
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    result_folder = os.path.join(results_folder, f"face_detection_results_{timestamp}")
                    if self.progress_callback:
                        self.progress_callback(f"{self.status_symbols['folder']} Creating results folder: {result_folder}")
                else:
                    # Fall back to current directory with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    result_folder = os.path.join(os.getcwd(), f"face_detection_results_{timestamp}")
                    if self.progress_callback:
                        self.progress_callback(f"{self.status_symbols['folder']} Creating default results folder: {result_folder}")
                
                os.makedirs(result_folder, exist_ok=True)
                os.makedirs(os.path.join(result_folder, "results"), exist_ok=True)
            
            # Load the specified model
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['info']} Loading model: {model_name}...")
            if not self.load_model(model_name):
                return
            
            # Get all image and video files
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            video_extensions = ['.mp4', '.avi', '.mov']
            image_files = []
            video_files = []
            
            # Check if the path is a file or directory
            if os.path.isfile(folder_path):
                # Single file processing
                if any(folder_path.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(folder_path)
                elif any(folder_path.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(folder_path)
            else:
                # Directory processing
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            image_files.append(file_path)
                        elif any(file.lower().endswith(ext) for ext in video_extensions):
                            video_files.append(file_path)
            
            total_files = len(image_files) + len(video_files)
            if total_files == 0:
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['warning']} No image or video files found in the specified location")
                return
            
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['folder']} Found {len(image_files)} images and {len(video_files)} videos to process")
            
            # Process each image
            for i, image_path in enumerate(image_files):
                if not self.is_processing:
                    if self.progress_callback:
                        self.progress_callback(f"{self.status_symbols['warning']} Processing stopped by user")
                    break
                    
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['image']} Processing image {i+1}/{len(image_files)}: {os.path.basename(image_path)}")
                
                try:
                    detections = self.process_image(image_path, confidence_threshold, save_results, result_folder)
                    if detections:
                        self.results.extend(detections)
                        if self.progress_callback:
                            self.progress_callback(f"{self.status_symbols['face']} Added {len(detections)} detections to results (total: {len(self.results)})")
                    
                    # Progress update after each image
                    progress_percent = ((i + 1) / len(image_files)) * 100
                    if self.progress_callback:
                        self.progress_callback(f"{self.status_symbols['complete']} Image {i+1}/{len(image_files)} complete ({progress_percent:.1f}%)")
                    
                    # Emit per-image completion event
                    if self.completion_callback:
                        self.completion_callback({
                            'status': 'image_completed',
                            'image_index': i + 1,
                            'total_images': len(image_files),
                            'progress_percent': progress_percent,
                            'detections_in_image': len(detections) if detections else 0,
                            'total_detections': len(self.results),
                            'image_path': os.path.basename(image_path)
                        })
                    
                    # Small delay to prevent overwhelming the UI
                    time.sleep(0.05)
                        
                except Exception as image_error:
                    if self.progress_callback:
                        self.progress_callback(f"{self.status_symbols['error']} Failed to process {os.path.basename(image_path)}: {str(image_error)}")
                    continue  # Continue with next image
            
            # Process each video
            for i, video_path in enumerate(video_files):
                if not self.is_processing:
                    break
                    
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['video']} Processing video {i+1}/{len(video_files)}: {os.path.basename(video_path)}")
                
                if result_folder:
                    video_detections = self.process_video(video_path, confidence_threshold, result_folder)
                    self.results.extend(video_detections)
            
            # Export results to CSV if saving results
            if save_results and result_folder and self.results:
                csv_path = os.path.join(result_folder, "detection_results.csv")
                self.export_results_to_csv(self.results, csv_path)
            
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['complete']} Processing complete. Found {len(self.results)} face detections across {total_files} files")
                if save_results and result_folder:
                    self.progress_callback(f"{self.status_symbols['folder']} Results saved to: {result_folder}")
                # Log technical completion message to console only
                print(f"{self.status_symbols['success']} All processing finished - setting is_processing = False")
            
            # Emit completion event
            if self.completion_callback:
                self.completion_callback({
                    'status': 'completed',
                    'results_count': len(self.results),
                    'total_files': total_files,
                    'results_folder': result_folder if save_results else None
                })
                    
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error during processing: {str(e)}")
            # Log technical message to console only
            print(f"{self.status_symbols['warning']} Setting is_processing = False due to error")
            
            # Emit error completion event
            if self.completion_callback:
                self.completion_callback({
                    'status': 'error',
                    'error': str(e),
                    'results_count': len(self.results)
                })
        finally:
            # Always reset the processing flag, regardless of success or failure
            # Log technical messages to console only
            print(f"{self.status_symbols['info']} FINALLY block: Setting is_processing = False (was {self.is_processing})")
            self.is_processing = False
            print(f"{self.status_symbols['success']} is_processing is now: {self.is_processing}")
            
            # Always emit final completion event in finally block
            if self.completion_callback:
                self.completion_callback({
                    'status': 'finished',
                    'is_processing': self.is_processing,
                    'results_count': len(self.results)
                })
    
    def stop_processing(self):
        """Stop the current processing"""
        self.is_processing = False
        if self.progress_callback:
            self.progress_callback("Processing stopped by user")
    
    def get_results(self) -> List[Dict]:
        """Get the current results"""
        return self.results
    
    def _process_with_yolo(self, image, image_path: str, confidence_threshold: float, save_results: bool, result_folder: str) -> List[Dict]:
        """Process image with YOLO model"""
        import shutil
        
        if self.progress_callback:
            self.progress_callback(f"{self.status_symbols['processing']} Running YOLO inference on {os.path.basename(image_path)}...")
        
        # Run inference using predict method (like old_script.py)
        results = self.model.predict(source=image_path, conf=confidence_threshold, save=save_results, save_txt=save_results, save_conf=save_results)
        
        if self.progress_callback:
            self.progress_callback(f"{self.status_symbols['success']} YOLO inference completed for {os.path.basename(image_path)}")
        
        # Copy results to the result folder if save_results is True
        if results and results[0].save_dir and save_results and result_folder:
            yolo_result_dir = results[0].save_dir
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['folder']} Results saved to {yolo_result_dir}")
            
            for item in os.listdir(yolo_result_dir):
                s = os.path.join(yolo_result_dir, item)
                d = os.path.join(result_folder, "results", item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.move(s, d)
                else:
                    if os.path.exists(d):
                        os.remove(d)
                    shutil.move(s, d)
            
            # Delete original YOLO results directory
            shutil.rmtree(yolo_result_dir)
            
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['complete']} Results copied to final location")
        
        # Extract face detections from the YOLO results
        detections = []
        
        # Use the results from the YOLO prediction we already made
        if results and len(results) > 0:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['detection']} Extracting detections from YOLO results...")
            
            # Get detections directly from YOLO results object
            result = results[0]
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['info']} DEBUG: result.boxes = {result.boxes}")
                if result.boxes is not None:
                    self.progress_callback(f"{self.status_symbols['info']} DEBUG: len(result.boxes) = {len(result.boxes)}")
            
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()  # Get bounding boxes in xyxy format
                confidences = result.boxes.conf.cpu().numpy()  # Get confidences
                
                for i in range(len(boxes)):
                    x1, y1, x2, y2 = boxes[i]
                    confidence = confidences[i]
                    
                    # Convert to center coordinates and width/height (like the old method)
                    width = x2 - x1
                    height = y2 - y1
                    x_center = x1 + width / 2
                    y_center = y1 + height / 2
                    
                    detections.append({
                        'x': float(x_center),
                        'y': float(y_center),
                        'width': float(width),
                        'height': float(height),
                        'confidence': float(confidence),
                        'image_path': image_path
                    })
                    
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['face']} Extracted {len(detections)} face detections from YOLO results")
            else:
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['info']} No faces detected in YOLO results")
        
        # Legacy fallback: try to read from saved text files if direct extraction failed
        label_file = None
        if len(detections) == 0:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['warning']} Direct extraction failed, trying text file fallback...")
            
            if save_results and result_folder:
                label_file = os.path.join(result_folder, "results", "labels", os.path.splitext(os.path.basename(image_path))[0] + ".txt")
            elif results and results[0].save_dir:
                # Use the save_dir from the first prediction
                label_file = os.path.join(results[0].save_dir, "labels", os.path.splitext(os.path.basename(image_path))[0] + ".txt")
        
        if label_file and os.path.exists(label_file):
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['info']} Reading detections from text file: {label_file}")
            with open(label_file, 'r') as lf:
                lines = lf.readlines()
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 6:  # class_id, x_center, y_center, width, height, confidence
                        _, x_center, y_center, width, height, confidence = map(float, parts[:6])
                        detections.append({
                            'x': float(x_center),
                            'y': float(y_center),
                            'width': float(width),
                            'height': float(height),
                            'confidence': float(confidence),
                            'image_path': image_path
                        })
        
        # Log completion of YOLO processing
        if self.progress_callback:
            self.progress_callback(f"{self.status_symbols['complete']} YOLO processing completed for {os.path.basename(image_path)} - found {len(detections)} faces")
            self.progress_callback(f"{self.status_symbols['info']} DEBUG: Returning detections: {detections}")
        
        return detections
    
    def _process_with_retinaface(self, image, image_path: str, confidence_threshold: float, save_results: bool, result_folder: str) -> List[Dict]:
        """Process image with RetinaFace model"""
        detections = []
        
        try:
            # Use RetinaFace for detection (placeholder when available)
            # face_detections = RetinaFace.detect_faces(image, threshold=confidence_threshold)
            face_detections = None  # Disabled for now
            
            if face_detections:
                result_img = image.copy()
                
                for key, detection in face_detections.items():
                    facial_area = detection["facial_area"]
                    confidence = detection["score"]
                    x, y, w, h = facial_area[0], facial_area[1], facial_area[2] - facial_area[0], facial_area[3] - facial_area[1]
                    
                    detections.append({
                        'x': float(x),
                        'y': float(y),
                        'width': float(w),
                        'height': float(h),
                        'confidence': float(confidence),
                        'image_path': image_path
                    })
                    
                    # Draw bounding box for visualization
                    if save_results:
                        cv2.rectangle(result_img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
                        cv2.putText(result_img, f"{confidence:.2f}", (int(x), int(y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Save result image
                if save_results and result_folder:
                    result_img_dir = os.path.join(result_folder, "results")
                    os.makedirs(result_img_dir, exist_ok=True)
                    result_img_path = os.path.join(result_img_dir, os.path.basename(image_path))
                    cv2.imwrite(result_img_path, result_img)
                    
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} RetinaFace processing error: {str(e)}")
        
        return detections
    
    def _save_image_with_boxes(self, image, detections: List[Dict], image_path: str, result_folder: str):
        """Save image with bounding boxes drawn"""
        try:
            result_img = image.copy()
            
            for detection in detections:
                x, y, w, h = detection['x'], detection['y'], detection['width'], detection['height']
                confidence = detection['confidence']
                
                # Draw bounding box
                cv2.rectangle(result_img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
                cv2.putText(result_img, f"{confidence:.2f}", (int(x), int(y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Save result image
            result_img_dir = os.path.join(result_folder, "results")
            os.makedirs(result_img_dir, exist_ok=True)
            result_img_path = os.path.join(result_img_dir, os.path.basename(image_path))
            cv2.imwrite(result_img_path, result_img)
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error saving result image: {str(e)}")
    
    def process_video(self, video_path: str, confidence_threshold: float = 0.5, result_folder: str = None) -> List[Dict]:
        """Process video for face detection by sampling frames"""
        try:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['video']} Processing video: {os.path.basename(video_path)}")
            
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps
            
            # Calculate frames to skip (1 frame per second)
            frames_to_skip = int(fps)
            
            frames_with_faces = 0
            processed_frames = 0
            all_detections = []
            
            for frame_idx in range(0, frame_count, frames_to_skip):
                if not self.is_processing:
                    break
                    
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break
                
                processed_frames += 1
                
                # Save frame temporarily
                temp_frame_path = os.path.join(result_folder, f'temp_frame_{frame_idx}.jpg')
                cv2.imwrite(temp_frame_path, frame)
                
                # Process frame
                detections = self.process_image(temp_frame_path, confidence_threshold, save_results=False)
                
                # Clean up temp frame
                os.remove(temp_frame_path)
                
                if detections:
                    frames_with_faces += 1
                    for detection in detections:
                        detection['frame_idx'] = frame_idx
                        detection['timestamp'] = frame_idx / fps
                    all_detections.extend(detections)
                
                # Emit per-frame completion event
                if self.completion_callback:
                    frame_progress = (processed_frames / (frame_count // frames_to_skip)) * 100
                    self.completion_callback({
                        'status': 'frame_completed',
                        'frame_index': frame_idx,
                        'processed_frames': processed_frames,
                        'total_frames': frame_count // frames_to_skip,
                        'progress_percent': frame_progress,
                        'detections_in_frame': len(detections) if detections else 0,
                        'total_detections': len(all_detections),
                        'timestamp': frame_idx / fps,
                        'video_path': os.path.basename(video_path)
                    })
            
            cap.release()
            
            face_percentage = (frames_with_faces / processed_frames) * 100 if processed_frames > 0 else 0
            
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['complete']} Video processing complete. {frames_with_faces}/{processed_frames} frames with faces ({face_percentage:.1f}%)")
            
            return all_detections
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error processing video: {str(e)}")
            return []
    
    def export_results_to_csv(self, results: List[Dict], output_path: str):
        """Export detection results to CSV file"""
        try:
            if not results:
                if self.progress_callback:
                    self.progress_callback(f"{self.status_symbols['warning']} No results to export")
                return False
            
            # Group results by image
            image_results = {}
            for detection in results:
                image_path = detection['image_path']
                if image_path not in image_results:
                    image_results[image_path] = []
                image_results[image_path].append(detection)
            
            # Prepare CSV data
            csv_data = []
            max_faces = max(len(detections) for detections in image_results.values())
            
            # Create headers
            headers = ['filename', 'face_detected', 'face_count']
            for i in range(max_faces):
                headers.extend([f'face_{i+1}_x', f'face_{i+1}_y', f'face_{i+1}_width', f'face_{i+1}_height', f'face_{i+1}_confidence'])
            
            # Create rows
            for image_path, detections in image_results.items():
                row = [os.path.basename(image_path), 1 if detections else 0, len(detections)]
                
                for detection in detections:
                    row.extend([detection['x'], detection['y'], detection['width'], detection['height'], detection['confidence']])
                
                # Pad row to match headers length
                while len(row) < len(headers):
                    row.append('')
                
                csv_data.append(row)
            
            # Write CSV file
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(csv_data)
            
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['success']} Results exported to {output_path}")
            
            return True
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"{self.status_symbols['error']} Error exporting results: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = [
            "yolov8n.pt",
            "yolov8s.pt", 
            "yolov8m.pt",
            "yolov8l.pt",
            "yolov8x.pt",
            "yolov8n-face.pt",
            "yolov8m-face.pt",
            "yolov8l-face.pt",
            "yolov11m-face.pt",
            "yolov11l-face.pt"
        ]
        
        if RETINAFACE_AVAILABLE:
            models.append("RetinaFace")
        
        return models