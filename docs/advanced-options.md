# Advanced Options

## Batch Processing
Process entire folders of images and videos in one run.

### Steps

!!! info "Before You Start"
    See [Supported File Formats](main-features.md#supported-file-formats) for compatible image and video types.

1. **Select Input Type**  
   In the input section, choose **Folder** (instead of **File**)
   
2. **Choose Your Folder**  
   Select a folder containing supported images and/or videos
   
3. **Configure Detection Settings**  
   - Pick a **Model** from the dropdown
   - Set the **Confidence Threshold** using the slider
   
4. **Start Processing**  
   Click **Start Detection** to begin batch processing

### Outputs
- A timestamped results folder is created.
- Processed images (and extracted video frames, if enabled) are saved under `results/`.
- A comprehensive `detection_results.csv` contains all detections with coordinates and scores.
- A `summary.csv` provides per-file statistics and overall counts.

Tip: Close other intensive applications for faster batch runs, especially with large videos or high-resolution imagery.

## Performance Considerations
- **Model Selection:** YOLOv8n-face offers faster processing; YOLOv8l-face provides higher accuracy.
- **Video Processing:** Videos take longer than images—ensure your hardware can handle large batches.
- **Memory Usage:** High-resolution media can consume significant memory. Close other intensive applications for best performance.
