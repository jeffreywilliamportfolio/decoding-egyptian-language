from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
from urllib.request import urlopen

import fitz
from PIL import Image


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def render_pdf_page(doc: fitz.Document, page_number: int, scale: float) -> Image.Image:
    if page_number < 1 or page_number > doc.page_count:
        raise ValueError(f"page_number {page_number} out of range")
    page = doc.load_page(page_number - 1)
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    mode = "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)

def _image_from_bytes(data: bytes) -> Image.Image:
    from io import BytesIO

    return Image.open(BytesIO(data)).convert("RGB")


def build_evidence(manifest: Dict[str, Any], output_root: Path) -> None:
    pdf_cache: Dict[Path, fitz.Document] = {}
    for source in manifest.get("sources", []):
        source_type = source.get("type")
        if source_type == "pdf":
            pdf_path = output_root / source["local_path"]
            if pdf_path not in pdf_cache:
                pdf_cache[pdf_path] = fitz.open(pdf_path)
            doc = pdf_cache[pdf_path]
            for item in source.get("items", []):
                page_number = item["page"]
                rendered_by_scale: Dict[float, Image.Image] = {}
                for evidence in item.get("evidence", []):
                    render_cfg = evidence.get("render", {})
                    scale = float(render_cfg.get("scale", 2.0))
                    if scale not in rendered_by_scale:
                        rendered_by_scale[scale] = render_pdf_page(doc, page_number, scale)
                    img = rendered_by_scale[scale]
                    out_path = output_root / evidence["output_path"]
                    _ensure_parent(out_path)
                    kind = evidence["kind"]
                    if kind == "page_image":
                        img.save(out_path)
                    elif kind == "crop":
                        bbox = evidence.get("bbox")
                        if not bbox or len(bbox) != 4:
                            raise ValueError(f"crop evidence missing bbox: {evidence['evidence_id']}")
                        crop = img.crop(tuple(bbox))
                        crop.save(out_path)
                    else:
                        raise ValueError(f"unsupported evidence kind: {kind}")
        elif source_type in {"image", "iiif"}:
            image_cache: Dict[str, Image.Image] = {}
            for item in source.get("items", []):
                for evidence in item.get("evidence", []):
                    source_url = evidence.get("source_url")
                    if not source_url:
                        raise ValueError(f"image evidence missing source_url: {evidence['evidence_id']}")
                    out_path = output_root / evidence["output_path"]
                    if out_path.exists():
                        continue
                    if source_url not in image_cache:
                        with urlopen(source_url) as resp:
                            data = resp.read()
                        image_cache[source_url] = _image_from_bytes(data)
                    img = image_cache[source_url]
                    _ensure_parent(out_path)
                    kind = evidence["kind"]
                    if kind == "page_image":
                        img.save(out_path)
                    elif kind == "crop":
                        bbox = evidence.get("bbox")
                        if not bbox or len(bbox) != 4:
                            raise ValueError(f"crop evidence missing bbox: {evidence['evidence_id']}")
                        crop = img.crop(tuple(bbox))
                        crop.save(out_path)
                    else:
                        raise ValueError(f"unsupported evidence kind: {kind}")
        else:
            continue

    for doc in pdf_cache.values():
        doc.close()
