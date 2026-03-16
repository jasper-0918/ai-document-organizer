"""
Vision Module
=============
Uses OpenCV to inspect image files and assign a scene label.
Heuristics used:
  - Aspect ratio → likely screenshot vs photo
  - Color entropy → colorful photo vs grayscale document scan
  - Edge density → diagram vs natural scene
  - SSIM → duplicate/near-duplicate detection
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def _load_image(file_path: Path):
    """Load an image with OpenCV, returning None on failure."""
    try:
        import cv2
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError("cv2.imread returned None — unsupported format or corrupt file.")
        return img
    except ImportError:
        logger.error("opencv-python not installed. Run: pip install opencv-python")
        raise
    except Exception as e:
        logger.warning(f"Could not load image {file_path.name}: {e}")
        return None


def _color_entropy(img) -> float:
    """Return HSV saturation mean as a proxy for 'colorfulness' (0–1)."""
    import cv2
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    return float(saturation.mean()) / 255.0


def _edge_density(img) -> float:
    """Return fraction of pixels that are edges (Canny). High → diagram/scan."""
    import cv2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    return float(np.count_nonzero(edges)) / edges.size


def classify_image(file_path: Path) -> tuple[str, float]:
    """
    Classify an image file into one of:
      screenshot, photo, diagram, document_scan, other_image

    Returns:
        (label, confidence) — simple rule-based confidence 0–1.
    """
    img = _load_image(file_path)
    if img is None:
        return "other_image", 0.0

    h, w = img.shape[:2]
    aspect_ratio = w / max(h, 1)
    saturation = _color_entropy(img)
    edge_density = _edge_density(img)

    # --- Rule-based heuristics ---

    # Document scans: low saturation + high edge density (text lines)
    if saturation < 0.05 and edge_density > 0.10:
        return "document_scan", 0.85

    # Diagrams: moderate saturation + very high edge density
    if edge_density > 0.20:
        return "diagram", 0.80

    # Screenshots: widescreen/square, medium saturation, medium edges
    if 1.2 < aspect_ratio < 2.1 and saturation < 0.25:
        return "screenshot", 0.75

    # Photos: colorful + low edge density
    if saturation > 0.20 and edge_density < 0.10:
        return "photo", 0.80

    return "other_image", 0.50


def compute_image_hash(file_path: Path) -> Optional[str]:
    """
    Compute a perceptual hash (pHash) of the image for duplicate detection.
    Returns hex string or None on failure.
    """
    try:
        import cv2
        img = _load_image(file_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (32, 32))
        mean_val = resized.mean()
        bits = (resized > mean_val).flatten()
        hash_int = int("".join(str(int(b)) for b in bits), 2)
        return format(hash_int, "x")
    except Exception as e:
        logger.warning(f"Hashing failed for {file_path.name}: {e}")
        return None


def images_are_similar(hash_a: str, hash_b: str, threshold: int = 10) -> bool:
    """
    Compare two pHashes by Hamming distance.
    threshold: max bit differences to consider 'similar' (default 10/1024 bits).
    """
    if not hash_a or not hash_b:
        return False
    try:
        a = int(hash_a, 16)
        b = int(hash_b, 16)
        xor = a ^ b
        hamming = bin(xor).count("1")
        return hamming <= threshold
    except ValueError:
        return False
