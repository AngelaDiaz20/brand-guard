from __future__ import annotations

"""Detección semántica de regiones con YOLO (Ultralytics).

Esta capa es opcional y defensiva:
- Si `ultralytics` no está instalado, o no hay pesos configurados, retorna [].
- Nunca debe romper el flujo actual.

Salida:
[
  { "id": "yolo_1", "className": "product_photo_area", "bbox": [x,y,w,h], "confidence": 0.81, "source": "yolo" }
]
"""

from pathlib import Path
from typing import Any

import cv2
import numpy as np


def _decode_bgr(image_bytes: bytes) -> np.ndarray | None:
    if not image_bytes:
        return None
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return bgr


def _xyxy_to_xywh(xyxy: list[float], w: int, h: int) -> list[int]:
    x1, y1, x2, y2 = [float(v) for v in xyxy]
    x1 = max(0.0, min(x1, float(w - 1)))
    y1 = max(0.0, min(y1, float(h - 1)))
    x2 = max(0.0, min(x2, float(w)))
    y2 = max(0.0, min(y2, float(h)))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return [int(round(x1)), int(round(y1)), max(1, int(round(x2 - x1))), max(1, int(round(y2 - y1)))]


def detect_regions_with_yolo(
    *,
    image_bytes: bytes,
    model_path: str | None,
    conf: float = 0.25,
    iou: float = 0.55,
    max_det: int = 30,
) -> list[dict[str, Any]]:
    """
    Returns detected semantic regions as a list of dicts.

    Notes:
    - `model_path` must point to a local YOLO weights file (e.g., .pt).
    - No downloading is performed here.
    """
    if not model_path:
        return []
    path = Path(model_path)
    if not path.exists() or not path.is_file():
        return []

    bgr = _decode_bgr(image_bytes)
    if bgr is None:
        return []
    h, w = bgr.shape[:2]
    if h <= 1 or w <= 1:
        return []

    try:
        from ultralytics import YOLO  # type: ignore
    except Exception:
        return []

    try:
        model = YOLO(str(path))
        results = model.predict(
            source=bgr,
            conf=float(conf),
            iou=float(iou),
            max_det=int(max_det),
            verbose=False,
            imgsz=max(h, w),
        )
    except Exception:
        return []

    if not results:
        return []
    r0 = results[0]

    # Ultralytics result schema: r0.boxes.xyxy, r0.boxes.conf, r0.boxes.cls
    boxes = getattr(r0, "boxes", None)
    names = getattr(r0, "names", None) or getattr(model, "names", None) or {}
    if boxes is None:
        return []

    xyxy = getattr(boxes, "xyxy", None)
    confs = getattr(boxes, "conf", None)
    clss = getattr(boxes, "cls", None)
    if xyxy is None or confs is None or clss is None:
        return []

    try:
        xyxy_list = xyxy.detach().cpu().numpy().tolist()
        conf_list = confs.detach().cpu().numpy().tolist()
        cls_list = clss.detach().cpu().numpy().tolist()
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for i, (bb, c, cls_id) in enumerate(zip(xyxy_list, conf_list, cls_list, strict=False), start=1):
        try:
            cls_int = int(round(float(cls_id)))
            label = names.get(cls_int, str(cls_int))
            out.append(
                {
                    "id": f"yolo_{i}",
                    "className": str(label),
                    "bbox": _xyxy_to_xywh(list(bb), w=w, h=h),
                    "confidence": round(float(c), 4),
                    "source": "yolo",
                }
            )
        except Exception:
            continue

    # Stable order: top-to-bottom, left-to-right.
    out.sort(key=lambda d: (d["bbox"][1] + d["bbox"][3] / 2.0, d["bbox"][0] + d["bbox"][2] / 2.0))
    return out

