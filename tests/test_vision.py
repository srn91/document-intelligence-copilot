from __future__ import annotations

from pathlib import Path

from app.config import SAMPLE_INVOICE_IMAGE_PATH, SAMPLE_LOW_QUALITY_IMAGE_PATH
from app.vision import analyze_invoice_image_file, write_image_analysis_output


def test_sample_invoice_image_analysis_produces_preprocessing_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.vision.GENERATED_DIR", tmp_path)

    packet = analyze_invoice_image_file(SAMPLE_INVOICE_IMAGE_PATH)
    analysis_path = write_image_analysis_output(packet)

    assert packet.metadata.width == 900
    assert packet.metadata.height == 1200
    assert packet.metadata.orientation == "portrait"
    assert packet.quality.ocr_readiness_score > 0.5
    assert packet.status in {"ready", "needs_review"}
    assert len(packet.preprocessing_artifacts) == 2
    assert Path(tmp_path, "sample_invoice_scan_ocr_binarized.png").exists()
    assert analysis_path.endswith("sample_invoice_scan_image_analysis.json")


def test_low_quality_sample_image_is_flagged_for_ocr_readiness_review(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.vision.GENERATED_DIR", tmp_path)

    packet = analyze_invoice_image_file(SAMPLE_LOW_QUALITY_IMAGE_PATH)

    assert packet.metadata.width == 420
    assert packet.metadata.height == 540
    assert packet.quality.resolution_score < 0.55
    assert packet.quality.ocr_readiness_score < 0.6
    assert packet.status in {"needs_review", "not_ready"}
    assert any("resolution" in warning.lower() or "contrast" in warning.lower() for warning in packet.quality.warnings)
