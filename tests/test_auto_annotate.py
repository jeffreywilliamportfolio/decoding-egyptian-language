from pathlib import Path

from PIL import Image, ImageDraw

from pyramid_audit.auto_annotate import AutoAnnotateConfig, auto_annotate_line


def test_auto_annotate_simple(tmp_path: Path):
    img_path = tmp_path / "line.png"
    img = Image.new("L", (200, 80), color=255)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 30, 40], fill=0)
    draw.rectangle([60, 10, 90, 40], fill=0)
    img.save(img_path)

    cfg = AutoAnnotateConfig(threshold=200, scale=1.0, min_area=20, dilation=1, margin=0)
    signs = auto_annotate_line(img_path, "line-1", cfg)
    assert len(signs) >= 2
    assert signs[0]["bbox"][0] <= signs[1]["bbox"][0]
