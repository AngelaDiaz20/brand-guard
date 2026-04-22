import unittest

import cv2
import numpy as np

from app.services.yolo_region_detector_service import detect_regions_with_yolo


class YoloRegionDetectorServiceTests(unittest.TestCase):
    def test_returns_empty_when_no_model_path(self) -> None:
        img = np.full((64, 64, 3), 255, dtype=np.uint8)
        ok, buf = cv2.imencode(".jpg", img)
        self.assertTrue(ok)
        regions = detect_regions_with_yolo(image_bytes=buf.tobytes(), model_path=None)
        self.assertEqual(regions, [])


if __name__ == "__main__":
    unittest.main()

