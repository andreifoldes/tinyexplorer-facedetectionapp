# Understanding Results

## CSV Output
### results.csv
#### Single File Mode (Image or Video)
- **filename** – processed file or video frame name
- **face_detected** – 1 if a face was found, 0 otherwise
- **face_count** – number of faces in the image or frame
- **face_X_x**, **face_X_y** – center coordinates of each face bounding box
- **face_X_width**, **face_X_height** – dimensions of each face bounding box
- **face_X_confidence** – confidence score for each detected face

#### Folder Mode
Same columns as single file mode but includes entries for every processed file or video frame in the folder.

### summary.csv
#### Single File Mode
- **path** – name of the processed file
- **type** – `image` or `video`
- **total_processed_frames** – number of frames processed (1 for images)
- **total_duration** – video duration in seconds (N/A for images)
- **processed_frames_with_faces** – frames where faces were detected
- **face_percentage** – percentage of frames with faces
- **model** – detection model used
- **confidence_threshold** – threshold applied during detection

#### Folder Mode
Same columns as single file mode but provides two rows summarising:
1. All images in the folder
2. All videos in the folder

Each row contains aggregate values for path, type, total processed frames, total duration, frames with faces, face percentage, model, and confidence threshold.

## Image Output
The application saves visual outputs for all images and video frames with detected faces.

### Bounding Boxes
- Green rectangles show each detected face and match the coordinates in `results.csv`

### Confidence Scores
- Each bounding box displays the detection confidence between 0 and 1
- Values correspond to `face_X_confidence` in `results.csv`

### Output File Names
- For images, the output file retains the original name
- For videos, each processed frame is saved separately using the format `[video_name]_[frame_number]_[timestamp].jpg`

These outputs make it easy to verify detection results and assess model performance.
