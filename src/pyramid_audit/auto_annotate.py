from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from PIL import Image, ImageFilter


@dataclass
class AutoAnnotateConfig:
    threshold: int = 140
    scale: float = 0.5
    min_area: int = 80
    dilation: int = 3
    margin: int = 4


def _mask_from_image(img: Image.Image, cfg: AutoAnnotateConfig) -> np.ndarray:
    gray = img.convert("L")
    if cfg.scale != 1.0:
        gray = gray.resize((int(gray.width * cfg.scale), int(gray.height * cfg.scale)), Image.BILINEAR)
    if cfg.dilation > 1:
        gray = gray.filter(ImageFilter.MaxFilter(cfg.dilation))
    arr = np.array(gray)
    return arr < cfg.threshold


def _components(mask: np.ndarray, cfg: AutoAnnotateConfig) -> List[Tuple[int, int, int, int, int]]:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    comps: List[Tuple[int, int, int, int, int]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            stack = [(y, x)]
            visited[y, x] = True
            minx = maxx = x
            miny = maxy = y
            area = 0
            while stack:
                cy, cx = stack.pop()
                area += 1
                if cx < minx:
                    minx = cx
                if cx > maxx:
                    maxx = cx
                if cy < miny:
                    miny = cy
                if cy > maxy:
                    maxy = cy
                for ny in (cy - 1, cy, cy + 1):
                    for nx in (cx - 1, cx, cx + 1):
                        if ny < 0 or ny >= height or nx < 0 or nx >= width:
                            continue
                        if mask[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
            if area >= cfg.min_area:
                comps.append((minx, miny, maxx, maxy, area))
    return comps


def segment_glyph_clusters(img: Image.Image, cfg: AutoAnnotateConfig) -> List[Tuple[int, int, int, int]]:
    mask = _mask_from_image(img, cfg)
    comps = _components(mask, cfg)
    boxes: List[Tuple[int, int, int, int]] = []
    for minx, miny, maxx, maxy, _area in comps:
        # scale back to original coordinates
        x1 = int(minx / cfg.scale)
        y1 = int(miny / cfg.scale)
        x2 = int(maxx / cfg.scale)
        y2 = int(maxy / cfg.scale)
        # add margin
        x1 = max(0, x1 - cfg.margin)
        y1 = max(0, y1 - cfg.margin)
        x2 = min(img.width - 1, x2 + cfg.margin)
        y2 = min(img.height - 1, y2 + cfg.margin)
        boxes.append((x1, y1, x2, y2))
    # sort left-to-right
    boxes.sort(key=lambda b: (b[0], b[1]))
    return boxes


def auto_annotate_line(
    image_path: Path,
    line_id: str,
    cfg: AutoAnnotateConfig,
) -> List[Dict[str, Any]]:
    img = Image.open(image_path)
    boxes = segment_glyph_clusters(img, cfg)
    signs: List[Dict[str, Any]] = []
    for idx, (x1, y1, x2, y2) in enumerate(boxes, start=1):
        signs.append(
            {
                "sign_id": f"auto-{line_id}-{idx}",
                "description": "auto-segmented glyph cluster (uninterpreted)",
                "bbox": [x1, y1, x2, y2],
                "confidence": 0.2,
            }
        )
    return signs
