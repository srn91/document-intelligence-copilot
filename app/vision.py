from __future__ import annotations

import io
import json
import re
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, ImageStat

from app.config import GENERATED_DIR
from app.models import ImageAnalysisPacket, ImageMetadata, ImageQualityAssessment, PreprocessingArtifact


def _portable(path: Path) -> str:
    cwd = Path.cwd()
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)


def _safe_stem(document_name: str) -> str:
    stem = Path(document_name).stem or "document"
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", stem).strip("_") or "document"


def _clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _score_centered(value: float, *, ideal: float, tolerance: float) -> float:
    if tolerance <= 0:
        return 1.0 if value == ideal else 0.0
    return _clamp(1.0 - (abs(value - ideal) / tolerance))


def _compute_edge_density(image: Image.Image) -> float:
    width, height = image.size
    if width < 2 or height < 2:
        return 0.0

    pixel_access = image.load()
    horizontal = 0
    vertical = 0
    for y in range(height):
        for x in range(width - 1):
            horizontal += abs(pixel_access[x, y] - pixel_access[x + 1, y])

    for y in range(height - 1):
        for x in range(width):
            vertical += abs(pixel_access[x, y] - pixel_access[x, y + 1])

    denominator = ((width - 1) * height) + (width * (height - 1))
    return (horizontal + vertical) / (denominator * 255) if denominator else 0.0


def _build_quality(image: Image.Image) -> ImageQualityAssessment:
    stats = ImageStat.Stat(image)
    width, height = image.size
    mean = float(stats.mean[0])
    stddev = float(stats.stddev[0])
    edge_density = _compute_edge_density(image)

    threshold = 215
    pixel_access = image.load()
    dark_pixels = 0
    for y in range(height):
        for x in range(width):
            if pixel_access[x, y] < threshold:
                dark_pixels += 1
    foreground_ratio = dark_pixels / float(width * height) if width and height else 0.0

    longest_edge = max(width, height)
    shortest_edge = min(width, height)
    resolution_score = _clamp(min(longest_edge / 1600.0, shortest_edge / 1100.0))
    brightness_score = _score_centered(mean, ideal=215.0, tolerance=85.0)
    contrast_score = _clamp(stddev / 72.0)
    sharpness_score = _clamp(edge_density / 0.11)
    coverage_score = _score_centered(foreground_ratio, ideal=0.18, tolerance=0.15)

    ocr_readiness_score = (
        0.30 * resolution_score
        + 0.20 * brightness_score
        + 0.20 * contrast_score
        + 0.20 * sharpness_score
        + 0.10 * coverage_score
    )

    warnings: list[str] = []
    if resolution_score < 0.55:
        warnings.append("Image resolution is low for OCR and may lose small invoice text.")
    if brightness_score < 0.5:
        if mean < 150:
            warnings.append("Image is underexposed and may need brightness correction.")
        else:
            warnings.append("Image background is very bright and may wash out faint text strokes.")
    if contrast_score < 0.45:
        warnings.append("Image contrast is low and text edges may be hard for OCR to separate.")
    if sharpness_score < 0.4:
        warnings.append("Image appears soft or blurry based on edge density.")
    if coverage_score < 0.35:
        warnings.append("Foreground coverage is unusual for a document scan and may indicate cropping or framing issues.")

    if ocr_readiness_score >= 0.75:
        status = "ready"
    elif ocr_readiness_score >= 0.5:
        status = "needs_review"
    else:
        status = "not_ready"

    return ImageQualityAssessment(
        brightness_mean=mean,
        contrast_stddev=stddev,
        edge_density=edge_density,
        foreground_ratio=foreground_ratio,
        resolution_score=resolution_score,
        brightness_score=brightness_score,
        contrast_score=contrast_score,
        sharpness_score=sharpness_score,
        coverage_score=coverage_score,
        ocr_readiness_score=ocr_readiness_score,
        status=status,
        warnings=warnings,
    )


def _build_metadata(image: Image.Image, *, file_size_bytes: int, format_name: str) -> ImageMetadata:
    width, height = image.size
    if width == height:
        orientation = "square"
    elif height > width:
        orientation = "portrait"
    else:
        orientation = "landscape"

    return ImageMetadata(
        format=format_name.upper(),
        color_mode=image.mode,
        width=width,
        height=height,
        file_size_bytes=file_size_bytes,
        aspect_ratio=(width / height) if height else 0.0,
        orientation=orientation,
    )


def _save_preprocessed_artifacts(
    document_name: str,
    grayscale: Image.Image,
    binarized: Image.Image,
) -> list[PreprocessingArtifact]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(document_name)

    grayscale_path = GENERATED_DIR / f"{stem}_ocr_grayscale.png"
    binarized_path = GENERATED_DIR / f"{stem}_ocr_binarized.png"

    grayscale.save(grayscale_path, format="PNG")
    binarized.save(binarized_path, format="PNG")

    return [
        PreprocessingArtifact(step="grayscale_autocontrast", path=_portable(grayscale_path)),
        PreprocessingArtifact(step="median_filter_binarization", path=_portable(binarized_path)),
    ]


def _recommended_action(status: str, artifact_paths: list[PreprocessingArtifact]) -> str:
    if artifact_paths:
        prepared_path = artifact_paths[-1].path
    else:
        prepared_path = "generated preprocessed image"

    if status == "ready":
        return f"Run OCR against {prepared_path} and send the extracted text through the invoice parser."
    if status == "needs_review":
        return (
            f"Use {prepared_path} for OCR, but inspect lighting, contrast, and crop quality before relying on the text output."
        )
    return "Rescan the invoice or correct lighting/crop issues before attempting OCR."


def analyze_invoice_image_bytes(
    image_bytes: bytes,
    *,
    document_name: str,
    persist_artifacts: bool = True,
) -> ImageAnalysisPacket:
    with Image.open(io.BytesIO(image_bytes)) as opened:
        format_name = opened.format or Path(document_name).suffix.lstrip(".") or "unknown"
        image = ImageOps.exif_transpose(opened)
        grayscale = ImageOps.grayscale(image)
        enhanced = ImageOps.autocontrast(grayscale)
        denoised = enhanced.filter(ImageFilter.MedianFilter(size=3))
        binarized = denoised.point(lambda value: 255 if value >= 185 else 0, mode="1").convert("L")

    metadata = _build_metadata(grayscale, file_size_bytes=len(image_bytes), format_name=format_name)
    quality = _build_quality(denoised)
    artifacts = _save_preprocessed_artifacts(document_name, denoised, binarized) if persist_artifacts else []
    steps = [
        "Apply EXIF-aware orientation normalization.",
        "Convert to grayscale and stretch contrast for darker text strokes.",
        "Apply a median filter to suppress small scan noise.",
        "Binarize the page to produce an OCR-ready high-contrast image.",
    ]

    return ImageAnalysisPacket(
        document_name=document_name,
        status=quality.status,
        metadata=metadata,
        quality=quality,
        preprocessing_steps=steps,
        preprocessing_artifacts=artifacts,
        recommended_action=_recommended_action(quality.status, artifacts),
    )


def analyze_invoice_image_file(path: Path, *, persist_artifacts: bool = True) -> ImageAnalysisPacket:
    return analyze_invoice_image_bytes(
        path.read_bytes(),
        document_name=path.name,
        persist_artifacts=persist_artifacts,
    )


def write_image_analysis_output(packet: ImageAnalysisPacket) -> str:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / f"{_safe_stem(packet.document_name)}_image_analysis.json"
    output_path.write_text(json.dumps(packet.to_dict(), indent=2), encoding="utf-8")
    return _portable(output_path)
