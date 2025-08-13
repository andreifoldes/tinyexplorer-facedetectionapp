# Main Features

## File and Folder Selection
- Browse and select individual image or video files
- Browse and select entire folders containing multiple images and videos

## Model Selection
Choose from multiple face detection models:
- **YOLOv8n-face (Nano)** – fastest inference, smallest model (2.7MB), lower accuracy, ideal for real-time or limited resources
- **YOLOv8m-face (Medium)** – balanced speed and accuracy, moderate size (27.3MB), suitable for most tasks
- **YOLOv8l-face (Large)** – highest accuracy, larger model (59.2MB), slower inference, best for high precision
- **RetinaFace** – different architecture providing facial landmarks, good speed and accuracy for feature localization

The app automatically downloads models when needed.

## Confidence Threshold Adjustment
- Adjustable slider from 0.0 to 1.0
- Default confidence values tailored to each model

## Face Recognition Process
- Works with images and videos
- Batch processing for multiple files in a folder
- Real-time progress bar and percentage display
- Detailed logging of the recognition process

## Results and Output
- Timestamped results folder
- CSV output with detailed detection data
- Summary CSV with overall statistics
- Visual results saved for images and video frames
- Results folder opens automatically when processing completes

## User Interface
- Intuitive GUI with file/folder selection, model choice, and confidence adjustment
- Real-time status updates in the window
- Error handling and user notifications

## Supported File Formats
**Images**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)

**Videos**
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)

You can select individual files or folders containing these formats for processing.
