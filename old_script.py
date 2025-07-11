import os
import csv
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
# Only set TensorFlow environment variables for logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logging

# Import packages after environment setup
from retinaface import RetinaFace
from ultralytics import YOLO
from threading import Thread
import sys
import subprocess
from datetime import datetime
import shutil
import cv2
import torch
import os
import requests
from tqdm import tqdm
import threading
import logging
import numpy
import tensorflow as tf

# Close splash screen at startup (if running as compiled app)
try:
    import pyi_splash
    pyi_splash.update_text('Loading application...')
    pyi_splash.close()
except (ImportError, ModuleNotFoundError, RuntimeError):
    # Not running as compiled app with splash screen, or splash screen failed to initialize
    pass

print("Python version")
print(sys.version)
print("Version info.")
print(sys.version_info)

# Configure the logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Create a logger for your application
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Text redirector class to display log information in the UI
class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, str, (self.tag,))
        self.widget.configure(state='disabled')
        self.widget.see(tk.END)

    def flush(self):
        pass

# Face detection application class
class FaceDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TinyExplorer Face Detection App")
        self.root.geometry("800x600")  # Set initial window size
        self.root.minsize(600, 400)  # Set minimum window size
        
        # Set the icon for the application window
        icon_path = resource_path("graphics/icon_Z71_icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            logger.warning(f"Icon file not found at {icon_path}")
        
        # Initialize variables
        self.image_dir = ""
        self.confidence = 0.1
        self.file_paths = []
        self.model_path = "yolov8l-face.pt"  # Default model path
        self.model_type = "YOLOv8"  # Default model type
        self.save_dir = ""  # Directory to save results
        
        # Unicode status symbols
        self.status_symbols = {
            "info": "ℹ️ ",
            "success": "✅ ",
            "error": "❌ ",
            "warning": "⚠️ ",
            "processing": "⏳ ",
            "download": "📥 ",
            "folder": "📁 ",
            "image": "🖼️ ",
            "video": "🎬 ",
            "detection": "🔍 ",
            "face": "👤 ",
            "progress": "🔄 ",
            "complete": "🏁 "
        }

        # Create UI elements
        self.create_widgets()

        # Redirect stdout and stderr
        sys.stdout = TextRedirector(self.result_text)
        sys.stderr = TextRedirector(self.result_text)

    def create_widgets(self):
        # Create a main frame to hold all widgets
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create left frame for controls
        left_frame = tk.Frame(main_frame, width=300)  # Set width for left frame
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)  # Prevent frame from shrinking

        # Create right frame for result text
        right_frame = tk.Frame(main_frame, width=300)  # Set minimum width
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right_frame.pack_propagate(False)  # Prevent frame from shrinking

        # File and folder selection
        self.folder_label = tk.Label(left_frame, text="Select File or Folder:")
        self.folder_label.pack(anchor=tk.W, pady=(0, 5))

        self.folder_path = tk.Entry(left_frame, width=30)  # Reduce width
        self.folder_path.pack(fill=tk.X, pady=(0, 5))

        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.browse_file_button = tk.Button(button_frame, text="Browse File", command=self.browse_file)
        self.browse_file_button.pack(side=tk.LEFT, padx=(0, 5))

        self.browse_folder_button = tk.Button(button_frame, text="Browse Folder", command=self.browse_folder)
        self.browse_folder_button.pack(side=tk.LEFT)

        # Model selection
        self.model_label = tk.Label(left_frame, text="Select Model:")
        self.model_label.pack(anchor=tk.W, pady=(0, 5))

        self.model_combobox = ttk.Combobox(left_frame, values=["yolov8n-face.pt", "yolov8m-face.pt", "yolov8l-face.pt", "yolov11m-face.pt", "yolov11l-face.pt", "RetinaFace"], width=28)  # Reduce width
        self.model_combobox.pack(fill=tk.X, pady=(0, 5))
        self.model_combobox.current(2)  # Set default value
        self.model_combobox.bind("<<ComboboxSelected>>", self.update_model)

        # Confidence selection
        self.conf_label = tk.Label(left_frame, text="Select Confidence Threshold:")
        self.conf_label.pack(anchor=tk.W, pady=(0, 5))

        self.conf_slider = tk.Scale(left_frame, from_=0.0, to=1.0, orient="horizontal", command=self.update_conf_value, resolution=0.01, length=200)  # Set specific length
        self.conf_slider.pack(fill=tk.X, pady=(0, 10))
        self.conf_slider.set(0.7)

        # Start button
        self.start_button = tk.Button(left_frame, text="Start Detection", command=self.start_detection)
        self.start_button.pack(fill=tk.X, pady=(0, 10))

        # Progress bar container
        self.progress_frame = tk.Frame(left_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        # Progress bar
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=200, mode="determinate")  # Reduce length
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Progress percentage label
        self.progress_label = tk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=10)

        # Result text box with scrollbar
        text_frame = tk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Use a font that supports Unicode characters
        text_font = ('Segoe UI', 10)  # Windows default font with good Unicode support
        
        self.result_text = tk.Text(text_frame, height=20, width=60, font=text_font)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_text.configure(state='disabled')  # Make it read-only

        # Add scrollbar to result text box
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)

        # Configure right frame grid
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

    # Browse file
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("Image and Video files", "*.jpg;*.jpeg;*.png;*.bmp;*.mp4;*.avi;*.mov")]
        )
        if file_path:
            self.file_paths = [file_path]
            self.folder_path.delete(0, tk.END)
            self.folder_path.insert(0, file_path)
            self.update_status(f"Selected file: {file_path}", "info")

    # Browse folder
    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            self.file_paths = [folder_path]
            self.folder_path.delete(0, tk.END)
            self.folder_path.insert(0, folder_path)
            self.update_status(f"Selected folder: {folder_path}", "folder")

    # Update confidence value
    def update_conf_value(self, val):
        self.confidence = float(val)

    # Update model
    def update_model(self, event):
        selected_model = self.model_combobox.get()
        if selected_model == "RetinaFace":
            self.model_type = "RetinaFace"
            self.model_path = selected_model
            self.conf_slider.set(0.9)  # Set default confidence for RetinaFace
        else:
            self.model_type = "YOLOv8" if "yolov8" in selected_model else "YOLOv11"
            self.model_path = selected_model
            if selected_model == "yolov8n-face.pt":
                self.conf_slider.set(0.3)  # Set default confidence for YOLOv8-nano
            elif selected_model == "yolov8m-face.pt":
                self.conf_slider.set(0.5)  # Set default confidence for YOLOv8-medium
            elif selected_model == "yolov8l-face.pt":
                self.conf_slider.set(0.7)  # Set default confidence for YOLOv8-large
            elif selected_model == "yolov11m-face.pt":
                self.conf_slider.set(0.6)  # Set default confidence for YOLOv11-medium
            elif selected_model == "yolov11l-face.pt":
                self.conf_slider.set(0.8)  # Set default confidence for YOLOv11-large
        
        # Update the confidence value
        self.update_conf_value(self.conf_slider.get())
    
    def update_progress(self, value):
        # Ensure the value is between 0 and 100
        progress_percent = max(0, min(value, 100))
        
        self.progress['value'] = progress_percent
        self.progress_label.config(text=f"{int(progress_percent)}%")
        
        # Update status with progress message at certain intervals
        if progress_percent % 25 == 0 and progress_percent > 0:
            if progress_percent == 25:
                self.update_status(f"Processing: {int(progress_percent)}% complete", "progress")
            elif progress_percent == 50:
                self.update_status(f"Halfway there: {int(progress_percent)}% complete", "progress")
            elif progress_percent == 75:
                self.update_status(f"Almost done: {int(progress_percent)}% complete", "progress")
            elif progress_percent == 100:
                self.update_status(f"Processing complete: {int(progress_percent)}%", "success")
                
        self.root.update_idletasks()

    # Reset stdout and stderr redirection
    def reset_stdout_stderr(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    # Start detection
    def start_detection(self):
        if not self.file_paths:
            messagebox.showerror("Error", "Please select a file or folder")
            return

        self.save_dir = filedialog.askdirectory(title="Select Folder to Save Results")
        if not self.save_dir:
            messagebox.showerror("Error", "Please select a folder to save results")
            return

        self.start_button.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.update_status("Starting face detection process...", "detection")

        # Reset stdout and stderr redirection
        self.reset_stdout_stderr()

        # Download and initialize the model
        try:
            self.download_and_init_model()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download or initialize model: {str(e)}")
            self.start_button.config(state=tk.NORMAL)
            return

        # Start the detection process in a separate thread
        Thread(target=self.detect_faces).start()

    def download_and_init_model(self):
        self.update_status("Initializing model...", "info")
        
        # Always use models from the data directory
        model_filename = os.path.basename(self.model_path)
        data_model_path = os.path.join('data', model_filename)
        
        # For PyInstaller bundled app, use resource_path
        bundled_model_path = resource_path(data_model_path)
        
        if self.model_type == "RetinaFace":
            # RetinaFace doesn't need a local model file, it's loaded via the package
            try:
                # For packaged apps, use special handling
                if getattr(sys, 'frozen', False):
                    self.update_status("Initializing RetinaFace in packaged mode...", "info")
                    
                    # Configure TensorFlow for packaged environment
                    if hasattr(tf.compat.v1, 'disable_eager_execution'):
                        self.update_status("Configuring TensorFlow for packaged environment...", "info")
                        # Only disable eager execution in packaged mode
                        tf.compat.v1.disable_eager_execution()
                        # Force inference mode
                        tf.keras.backend.set_learning_phase(0)
                    
                    # Use a very small test image
                    test_img = numpy.zeros((224, 224, 3), dtype=numpy.uint8)
                    _ = RetinaFace.detect_faces(test_img, threshold=0.9)
                    self.update_status("Successfully initialized RetinaFace in packaged mode", "success")
                else:
                    # Running as normal Python script - use default config
                    self.update_status("Initializing RetinaFace in standard mode...", "info")
                    test_img = numpy.zeros((100, 100, 3), dtype=numpy.uint8)
                    _ = RetinaFace.detect_faces(test_img)
                    self.update_status("Successfully initialized RetinaFace", "success")
            except Exception as e:
                error_msg = str(e)
                self.update_status(f"Error initializing RetinaFace: {error_msg}", "error")
                
                # Try fallback initialization for packaged app
                if getattr(sys, 'frozen', False):
                    try:
                        self.update_status("Attempting fallback initialization for RetinaFace...", "info")
                        
                        # If error contains KerasTensor, apply specific workaround
                        if "KerasTensor" in error_msg:
                            self.update_status("Applying KerasTensor workaround...", "info")
                            
                            # Reset TensorFlow graph and session
                            tf.compat.v1.reset_default_graph()
                            tf.compat.v1.keras.backend.clear_session()
                            
                            # Force inference mode
                            tf.keras.backend.set_learning_phase(0)
                            
                            # Try to monkey patch RetinaFace for packaged environment
                            try:
                                # Create a patch for the keras tensor issue
                                from retinaface.commons import postprocess
                                original_fn = postprocess.tf_fn
                                
                                def wrapped_tf_fn(tensor):
                                    # Handle both tensor types
                                    if hasattr(tensor, 'numpy'):
                                        return tensor.numpy()
                                    return original_fn(tensor)
                                
                                # Apply the patch
                                postprocess.tf_fn = wrapped_tf_fn
                                self.update_status("Applied TensorFlow function patch", "info")
                            except Exception as patch_error:
                                self.update_status(f"Could not apply patch: {str(patch_error)}", "warning")
                        
                        # Try with a real image instead of zeros
                        test_img = numpy.ones((300, 300, 3), dtype=numpy.uint8) * 128
                        _ = RetinaFace.detect_faces(test_img, threshold=0.9)
                        self.update_status("Successfully initialized RetinaFace with fallback method", "success")
                    except Exception as fallback_error:
                        self.update_status(f"Fallback also failed: {str(fallback_error)}", "error")
                        messagebox.showerror("Error", 
                                           f"RetinaFace initialization failed.\n\nError details: {error_msg}\n\nPlease try a YOLO model instead.")
                        self.start_button.config(state=tk.NORMAL)
                        return
                else:
                    # In standard mode, just show the error
                    messagebox.showerror("Error", f"Failed to initialize RetinaFace: {error_msg}")
                    self.start_button.config(state=tk.NORMAL)
                    return
        else:
            # For YOLO models, check if file exists
            if os.path.exists(bundled_model_path):
                self.update_status(f"Using model: {bundled_model_path}", "info")
                self.model_path = bundled_model_path
            else:
                # If not found in bundled path, try regular path
                if os.path.exists(data_model_path):
                    self.update_status(f"Using model: {data_model_path}", "info")
                    self.model_path = data_model_path
                else:
                    raise FileNotFoundError(f"Model file not found in data folder: {model_filename}")
            
            # Initialize YOLO model
            if "yolov8" in self.model_path.lower() or "yolov11" in self.model_path.lower():
                self.model = YOLO(self.model_path).to('cuda:0' if torch.cuda.is_available() else 'cpu')
                self.update_status(f"Successfully loaded model: {self.model_path}", "success")

    def recognize_with_yolo(self, file_path, result_folder, save_results=True):
        # Use the existing model instance instead of creating a new one
        results = self.model.predict(source=file_path, conf=self.confidence, save=save_results, save_txt=save_results, save_conf=save_results)
        
        # Copy results to the new result folder
        if results and results[0].save_dir and save_results:
            yolo_result_dir = results[0].save_dir
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

            # Delete original YOLOv8 results directory
            shutil.rmtree(yolo_result_dir)

        faces = []
        label_file = os.path.join(result_folder, "results", "labels", os.path.splitext(os.path.basename(file_path))[0] + ".txt")
        if os.path.exists(label_file):
            with open(label_file, 'r') as lf:
                lines = lf.readlines()
                for line in lines:
                    class_id, x_center, y_center, width, height, confidence = map(float, line.strip().split())
                    face = {'x': x_center, 'y': y_center, 'width': width, 'height': height, 'confidence': confidence}
                    faces.append(face)
                    print(face)
            
            # Update status with face detection results
            if len(faces) > 0:
                self.update_status(f"Detected {len(faces)} {'face' if len(faces) == 1 else 'faces'} in {os.path.basename(file_path)}", "face")
        else:
            self.update_status(f"No faces detected in {os.path.basename(file_path)}", "info")
            print("No faces detected.")

        return faces

    # Recognize using RetinaFace
    def recognize_with_retinaface(self, file_path, result_folder, save_results=True):
        try:
            self.update_status(f"Processing with RetinaFace: {os.path.basename(file_path)}", "info")
            img = cv2.imread(file_path)
            if img is None:
                self.update_status(f"Error: Could not read image file: {file_path}", "error")
                return []
            
            # Handle packaged mode differently
            if getattr(sys, 'frozen', False):
                try:
                    # Reset the TensorFlow session for each detection to avoid memory issues
                    tf.keras.backend.clear_session()
                    
                    # Resize large images for better performance in packaged mode
                    max_size = 1200  # Maximum dimension for the image
                    height, width = img.shape[:2]
                    
                    # Only resize if the image is very large
                    if max(height, width) > max_size:
                        scale = max_size / max(height, width)
                        new_height = int(height * scale)
                        new_width = int(width * scale)
                        self.update_status(f"Resizing large image for detection ({width}x{height} → {new_width}x{new_height})", "info")
                        img_resized = cv2.resize(img, (new_width, new_height))
                        
                        # Use a higher threshold in packaged mode
                        detections = RetinaFace.detect_faces(img_resized, threshold=max(0.8, self.confidence))
                        
                        # Scale detection results back to original image size
                        scaled_detections = {}
                        for key, detection in detections.items():
                            facial_area = detection["facial_area"]
                            scaled_facial_area = [
                                int(facial_area[0] / scale),
                                int(facial_area[1] / scale),
                                int(facial_area[2] / scale),
                                int(facial_area[3] / scale)
                            ]
                            detection["facial_area"] = scaled_facial_area
                            scaled_detections[key] = detection
                            
                        detections = scaled_detections
                    else:
                        # Not resizing, use original image
                        detections = RetinaFace.detect_faces(img, threshold=max(0.8, self.confidence))
                        
                except Exception as e:
                    self.update_status(f"Error in packaged detection: {str(e)}", "error")
                    detections = {}
            else:
                # Standard execution mode - use normal settings
                detections = RetinaFace.detect_faces(img, threshold=self.confidence)
            
            if not detections:
                self.update_status(f"No faces detected in {os.path.basename(file_path)}", "info")
                return []
                
            result_img = img.copy()

            faces = []
            for key, detection in detections.items():
                facial_area = detection["facial_area"]
                confidence = detection["score"]
                x, y, w, h = facial_area[0], facial_area[1], facial_area[2] - facial_area[0], facial_area[3] - facial_area[1]
                faces.append({'confidence': confidence, 'x': x, 'y': y, 'width': w, 'height': h})
                if save_results:
                    cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(result_img, f"{confidence:.2f}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Save result image
            if save_results:
                # Create subdirectories if they don't exist
                result_img_dir = os.path.join(result_folder, "results")
                os.makedirs(result_img_dir, exist_ok=True)
                result_img_path = os.path.join(result_img_dir, os.path.basename(file_path))
                cv2.imwrite(result_img_path, result_img)
                
            # Update status with face detection results
            if len(faces) > 0:
                self.update_status(f"Detected {len(faces)} {'face' if len(faces) == 1 else 'faces'} in {os.path.basename(file_path)}", "face")
            
            return faces
            
        except Exception as e:
            error_msg = str(e)
            self.update_status(f"Error processing with RetinaFace: {error_msg}", "error")
            
            # Additional details for debugging
            if "KerasTensor" in error_msg:
                self.update_status("This appears to be a TensorFlow compatibility issue.", "error")
                
            # In normal mode, we might want to try a different approach
            if not getattr(sys, 'frozen', False):
                self.update_status("Attempting alternative detection approach...", "info")
                try:
                    # Try with a more basic approach
                    img = cv2.imread(file_path)
                    if img is None:
                        return []
                        
                    # Clear the session
                    tf.keras.backend.clear_session()
                    
                    # Try with higher threshold
                    detections = RetinaFace.detect_faces(img, threshold=0.9)
                    
                    if not detections:
                        return []
                        
                    faces = []
                    for key, detection in detections.items():
                        facial_area = detection["facial_area"]
                        confidence = detection["score"]
                        x, y, w, h = facial_area[0], facial_area[1], facial_area[2] - facial_area[0], facial_area[3] - facial_area[1]
                        faces.append({'confidence': confidence, 'x': x, 'y': y, 'width': w, 'height': h})
                        
                    return faces
                    
                except Exception as alt_error:
                    self.update_status(f"Alternative approach also failed: {str(alt_error)}", "error")
                    return []
            
            return []

    # Show results
    def show_results(self, csv_file):
        df = pd.read_csv(csv_file)
        self.result_text.configure(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, df.to_string(index=False))
        self.result_text.configure(state='disabled')

    # Open results folder
    def open_results_folder(self, path):
        try:
            if sys.platform == "win32": # More specific check for Windows
                os.startfile(path)
            elif sys.platform == "darwin": # Check for macOS
                subprocess.Popen(['open', path])
            else: # Assume Linux/other POSIX with xdg-open
                subprocess.Popen(['xdg-open', path])
        except FileNotFoundError:
            # Handle case where 'open' or 'xdg-open' might not be found
            error_msg = f"Could not automatically open the results folder. Please navigate to: {path}"
            self.update_status(error_msg, "warning")
            logger.warning(f"Could not find command to open folder for platform: {sys.platform}")
            messagebox.showwarning("Info", error_msg)
        except Exception as e:
            # Catch other potential errors during folder opening
            error_msg = f"An error occurred while trying to open the results folder: {e}. Please navigate to: {path}"
            self.update_status(error_msg, "error")
            logger.error(f"Error opening results folder: {e}", exc_info=True)
            messagebox.showerror("Error", error_msg)

    # Detect faces
    def detect_faces(self):
        headers = ['filename', 'face_detected', 'face_count']
        summary_headers = ['path', 'type', 'total_processed_frames', 'total_duration', 'processed_frames_with_faces', 'face_percentage', 'model', 'confidence_threshold']
        max_faces = 0
        results = []
        summary_results = []

        total_files = len(self.file_paths)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Validate save directory within the thread
        if not self.save_dir or not os.path.isdir(self.save_dir):
            error_msg = f"Invalid or inaccessible save directory selected: '{self.save_dir}'. Please select a valid folder where the application can write."
            self.update_status(f"Error: {error_msg}", "error")
            logger.error(error_msg)
            # Use messagebox from the main thread if possible or just log and re-enable button
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.start_button.config(state=tk.NORMAL) # Re-enable button
            return # Stop the thread

        result_folder = os.path.join(self.save_dir, current_time)
        logger.debug(f"Attempting to create result folder: {result_folder}")

        try:
            os.makedirs(result_folder)
            os.makedirs(os.path.join(result_folder, "results"))
        except OSError as e:
            error_msg = f"Failed to create result folder '{result_folder}'. Error: {e}. Check permissions and path validity."
            self.update_status(f"Error: {error_msg}", "error")
            logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.start_button.config(state=tk.NORMAL) # Re-enable button
            return # Stop the thread

        for idx, file_path in enumerate(self.file_paths):
            print(f"Processing file {idx + 1}/{total_files}: {file_path}")
            if os.path.isdir(file_path):
                summary = self.detect_faces_in_folder(file_path, result_folder)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                summary = self.detect_faces_in_video(file_path, result_folder)
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                if self.model_type == "YOLOv8" or self.model_type == "YOLOv11":
                    faces = self.recognize_with_yolo(file_path, result_folder)
                else:
                    faces = self.recognize_with_retinaface(file_path, result_folder)
                summary = [file_path,  'image', 'N/A', 'N/A', 1, 'N/A', self.model_path, self.confidence]

            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')): 
                print(f"Faces detected: {len(faces)}")

                face_detected = 1 if len(faces) > 0 else 0
                face_count = len(faces)
                result = [os.path.basename(file_path), face_detected, face_count]

                for face in faces:
                    result.extend([face['x'], face['y'], face['width'], face['height'], face['confidence']])
                results.append(result)

                if len(faces) > max_faces:
                    max_faces = len(faces)

                # Update progress bar and percentage label
                progress_percent = ((idx + 1) / total_files) * 100
                self.update_progress(progress_percent)

                for i in range(max_faces):
                    headers.extend([f'face_{i+1}_x', f'face_{i+1}_y', f'face_{i+1}_width', f'face_{i+1}_height', f'face_{i+1}_confidence'])

                with open(os.path.join(result_folder, "results.csv"), 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                    for result in results:
                        while len(result) < len(headers):
                            result.append('')
                        writer.writerow(result)

            summary_results.append(summary)
            with open(os.path.join(result_folder, "summary.csv"), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(summary_headers)
                
                for summary in summary_results:
                    print(summary)
                    if isinstance(summary[0], list):  # If summary is a list of lists
                        for sub_summary in summary:
                            print(sub_summary)
                            writer.writerow(sub_summary)
                    else:  # If summary is a single list
                        writer.writerow(summary)

        self.update_status("Face detection completed successfully!", "complete")
        messagebox.showinfo("Completed", "Face detection completed successfully!")
        self.start_button.config(state=tk.NORMAL)
        
        # Open results folder
        self.open_results_folder(result_folder)
        
        # Restore stdout and stderr redirection
        sys.stdout = TextRedirector(self.result_text)
        sys.stderr = TextRedirector(self.result_text)

    # Detect faces in video
    def detect_faces_in_video(self, video_path, result_folder):
        self.update_status(f"Processing video: {video_path}", "video")
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps
        
        # Calculate the number of frames to skip to get 1 frame per second
        frames_to_skip = int(fps)

        frames_with_faces = 0
        processed_frames = 0
        results = []
        video_faces = 0
        
        for frame_idx in range(0, frame_count, frames_to_skip):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            processed_frames += 1
            temp_file_path = os.path.join(result_folder, f'{os.path.splitext(os.path.basename(video_path))[0]}_{frame_idx}.jpg')
            cv2.imwrite(temp_file_path, frame)

            if self.model_type == "YOLOv8" or self.model_type == "YOLOv11":
                detected_faces = self.recognize_with_yolo(temp_file_path, result_folder, save_results=True)
            else:
                detected_faces = self.recognize_with_retinaface(temp_file_path, result_folder, save_results=True)

            os.remove(temp_file_path)

            num_faces = len(detected_faces) if detected_faces else 0
            video_faces += num_faces
            if num_faces > 0:
                frames_with_faces += 1

                row = {
                    'filename': f'{os.path.splitext(os.path.basename(video_path))[0]}_{frame_idx}.jpg',
                    'face_detected': 1,
                    'face_count': num_faces
                }

                for i, face in enumerate(detected_faces or [], start=1):
                    row[f'face{i}_x'] = face['x']
                    row[f'face{i}_y'] = face['y']
                    row[f'face{i}_width'] = face['width']
                    row[f'face{i}_height'] = face['height']
                    row[f'face{i}_confidence'] = face['confidence']
                    
                results.append(row)
            else:
                results.append({
                'filename': f'{os.path.splitext(os.path.basename(video_path))[0]}_{frame_idx}.jpg',
                'face_detected': 0,
                'face_count': 0
                })

            # Update progress bar
            progress_percent = (processed_frames / (duration)) * 100
            self.update_progress(progress_percent)

        cap.release()

        df = pd.DataFrame(results)
        csv_path = os.path.join(result_folder, 'results.csv')
        df.to_csv(csv_path, index=False)
        
        face_percentage = (frames_with_faces / processed_frames) * 100 if processed_frames > 0 else 0

        return [os.path.basename(video_path), "video", processed_frames, duration, frames_with_faces, face_percentage, self.model_path, self.confidence]

    # Detect faces in folder
    def detect_faces_in_folder(self, folder_path, result_folder):
        self.update_status(f"Processing folder: {folder_path}", "folder")
        summary_data = []
        
        # Find all image files in the folder
        image_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    image_files.append(os.path.join(root, file))
                    
        # Update status showing how many images are found
        if len(image_files) > 0:
            self.update_status(f"Found {len(image_files)} images in folder.", "image")
            
        # Find all video files in the folder
        video_files = []
        total_video_frames = 0
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.mp4', '.avi', '.mov')):
                    video_files.append(os.path.join(root, file))
                    
        if len(video_files) > 0:
            self.update_status(f"Found {len(video_files)} videos in folder.", "video")
            for video_file in video_files:
                cap = cv2.VideoCapture(video_file)
                total_video_frames += int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
            
        images_with_faces = 0      
        frames_with_faces = 0
        total_processed_video_frames = 0
        results = []
        
        # Process image files
        for idx, image_file in enumerate(image_files):
            self.update_status(f"Processing image {idx + 1}/{len(image_files)}: {os.path.basename(image_file)}", "image")
            
            if self.model_type == "YOLOv8" or self.model_type == "YOLOv11":
                detected_faces = self.recognize_with_yolo(image_file, result_folder, save_results=True)
            elif self.model_type == "RetinaFace":
                detected_faces = self.recognize_with_retinaface(image_file, result_folder, save_results=True)

            num_faces = len(detected_faces) if detected_faces else 0
            
            if num_faces > 0:
                images_with_faces += 1
                
                row = {
                    'filename': os.path.basename(image_file),
                    'face_detected': 1,
                    'face_count': num_faces
                }
                
                for i, face in enumerate(detected_faces, start=1):
                    row[f'face{i}_x'] = face['x']
                    row[f'face{i}_y'] = face['y']
                    row[f'face{i}_width'] = face['width']
                    row[f'face{i}_height'] = face['height']
                    row[f'face{i}_confidence'] = face['confidence']
                
                results.append(row)
            else:
                results.append({
                    'filename': os.path.basename(image_file),
                    'face_detected': 0,
                    'face_count': 0
                })
                
            # Update progress bar
            progress_percent = ((idx + 1) / len(image_files)) * 100
            self.update_progress(progress_percent)
            
        # Process video files
        total_duration = 0
        if video_files:
            total_duration = sum(cv2.VideoCapture(video_file).get(cv2.CAP_PROP_FRAME_COUNT) / cv2.VideoCapture(video_file).get(cv2.CAP_PROP_FPS) 
                            for video_file in video_files)
        
        for idx, video_file in enumerate(video_files):
            self.update_status(f"Processing video {idx + 1}/{len(video_files)}: {os.path.basename(video_file)}", "video")
            cap = cv2.VideoCapture(video_file)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps
            
            # Calculate the number of frames to skip to get 1 frame per second
            frames_to_skip = max(1, int(fps))

            for frame_idx in range(0, frame_count, frames_to_skip):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                total_processed_video_frames += 1
                temp_file_path = os.path.join(result_folder, f'{os.path.splitext(os.path.basename(video_file))[0]}_{frame_idx}.jpg')
                cv2.imwrite(temp_file_path, frame)

                if self.model_type == "YOLOv8" or self.model_type == "YOLOv11":
                    detected_faces = self.recognize_with_yolo(temp_file_path, result_folder, save_results=True)
                elif self.model_type == "RetinaFace":
                    detected_faces = self.recognize_with_retinaface(temp_file_path, result_folder, save_results=True)

                os.remove(temp_file_path)

                num_faces = len(detected_faces) if detected_faces else 0

                if num_faces > 0:
                    frames_with_faces += 1

                    row = {
                        'filename': f'{os.path.splitext(os.path.basename(video_file))[0]}_{frame_idx}.jpg',
                        'face_detected': 1,
                        'face_count': num_faces
                    }

                    for i, face in enumerate(detected_faces or [], start=1):
                        row[f'face{i}_x'] = face['x']
                        row[f'face{i}_y'] = face['y']
                        row[f'face{i}_width'] = face['width']
                        row[f'face{i}_height'] = face['height']
                        row[f'face{i}_confidence'] = face['confidence']
                        
                    results.append(row)
                else:
                    results.append({
                        'filename': f'{os.path.splitext(os.path.basename(video_file))[0]}_{frame_idx}.jpg',
                        'face_detected': 0,
                        'face_count': 0
                    })

                # Update progress bar
                if total_duration > 0:
                    progress_percent = (total_processed_video_frames / total_duration) * 100
                    self.update_progress(progress_percent)

            cap.release()

        # caclulate face percentage
        if len(image_files) > 0:
            face_percentage_images = (images_with_faces / len(image_files)) * 100 if len(image_files) > 0 else 0
            summary_images = [folder_path, 'image(s)', len(image_files), 'N/A', images_with_faces, face_percentage_images, self.model_path, self.confidence]
            summary_data.append(summary_images)
            
        if len(video_files) > 0:
            face_percentage_videos = (frames_with_faces / total_processed_video_frames) * 100 if total_processed_video_frames > 0 else 0
            summary_videos = [folder_path, 'video(s)', total_processed_video_frames, total_duration, frames_with_faces, face_percentage_videos, self.model_path, self.confidence]
            summary_data.append(summary_videos)

        # Create DataFrame and save to CSV
        df = pd.DataFrame(results)
        csv_path = os.path.join(result_folder, 'results.csv')
        df.to_csv(csv_path, index=False)

        return summary_data

    def update_status(self, message, status_type="info"):
        """Update status with Unicode art based on message type"""
        symbol = self.status_symbols.get(status_type, self.status_symbols["info"])
        formatted_message = f"{symbol} {message}"
        
        self.result_text.configure(state='normal')
        self.result_text.insert(tk.END, f"{formatted_message}\n")
        self.result_text.see(tk.END)
        self.result_text.configure(state='disabled')
        self.root.update_idletasks()

def main():
    
    logger.debug("Starting application")

    # Close splash screen if using PyInstaller
    try:
        if getattr(sys, 'frozen', False):
            import pyi_splash
            pyi_splash.close()
    except (ImportError, ModuleNotFoundError, RuntimeError):
        # Splash screen already closed or not available
        pass
        
    root = tk.Tk()
    root.title("TinyExplorer Face Detection App")

    
    icon_path = resource_path("graphics/icon_Z71_icon.png")
    if os.path.exists(icon_path):
        img = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, img)
        # log the icon file path
        print(f"Icon file found at {icon_path}")
    else:
        logger.warning(f"Icon file not found at {icon_path}")
    app = FaceDetectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()