import os
import tempfile
import urllib.request
from retinaface import RetinaFace
from ultralytics import YOLO

IMAGE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"


def download_sample_image() -> str:
    """Download a sample image and return the local path."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(tmp_fd)
    urllib.request.urlretrieve(IMAGE_URL, tmp_path)
    return tmp_path


def detect_with_retinaface(image_path: str) -> int:
    """Run face detection using RetinaFace and return number of faces."""
    results = RetinaFace.detect_faces(image_path)
    return len(results)


def detect_with_yolo(image_path: str) -> int:
    """Run face detection using YOLO-face and return number of faces."""
    model = YOLO("yolov8n-face.pt")
    detections = model(image_path)
    count = 0
    for res in detections:
        count += len(res.boxes)
    return count


def main():
    image_path = download_sample_image()
    print(f"Downloaded sample image to {image_path}")

    retina_count = detect_with_retinaface(image_path)
    print(f"RetinaFace detected {retina_count} face(s)")

    yolo_count = detect_with_yolo(image_path)
    print(f"YOLO-face detected {yolo_count} face(s)")

    os.remove(image_path)


if __name__ == "__main__":
    main()
