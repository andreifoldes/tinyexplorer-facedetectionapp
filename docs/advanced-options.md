# Advanced Options

## Batch Processing
The app can process multiple files at once:
1. Select **Folder** instead of **File** in the input section.
2. Browse to a folder containing images and/or videos.
3. Choose the detection model and set the confidence threshold.
4. Click **Start Detection** to process all supported files.
5. A results folder is created containing processed images, a comprehensive `results.csv`, and a summary CSV.

## Performance Considerations
- **Model Selection:** YOLOv8n-face offers faster processing; YOLOv8l-face provides higher accuracy.
- **Video Processing:** Videos take longer than images—ensure your hardware can handle large batches.
- **Memory Usage:** High-resolution media can consume significant memory. Close other intensive applications for best performance.
