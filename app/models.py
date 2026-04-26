from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Literal


Status = Literal["ready", "needs_review"]
ImageReadinessStatus = Literal["ready", "needs_review", "not_ready"]


@dataclass(frozen=True)
class ExtractedField:
    value: str
    confidence: float
    source_span: str


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: Literal["warning", "critical"]


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class InvoiceExtraction:
    vendor_name: ExtractedField
    invoice_id: ExtractedField
    invoice_date: ExtractedField
    due_date: ExtractedField
    total_amount: Decimal
    currency: ExtractedField
    payment_terms: ExtractedField
    purchase_order: ExtractedField | None
    line_items: list[LineItem]
    line_item_subtotal: Decimal


@dataclass(frozen=True)
class ReviewPacket:
    document_name: str
    status: Status
    extraction: InvoiceExtraction
    issues: list[ValidationIssue]
    recommended_action: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["extraction"]["total_amount"] = f"{self.extraction.total_amount:.2f}"
        payload["extraction"]["line_item_subtotal"] = f"{self.extraction.line_item_subtotal:.2f}"
        for item in payload["extraction"]["line_items"]:
            item["quantity"] = f"{Decimal(item['quantity']):.2f}"
            item["unit_price"] = f"{Decimal(item['unit_price']):.2f}"
            item["line_total"] = f"{Decimal(item['line_total']):.2f}"
        return payload


@dataclass(frozen=True)
class ReviewerCorrection:
    document_name: str
    field_name: str
    original_value: str
    corrected_value: str
    reviewer_name: str | None
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ImageMetadata:
    format: str
    color_mode: str
    width: int
    height: int
    file_size_bytes: int
    aspect_ratio: float
    orientation: Literal["portrait", "landscape", "square"]


@dataclass(frozen=True)
class ImageQualityAssessment:
    brightness_mean: float
    contrast_stddev: float
    edge_density: float
    foreground_ratio: float
    resolution_score: float
    brightness_score: float
    contrast_score: float
    sharpness_score: float
    coverage_score: float
    ocr_readiness_score: float
    status: ImageReadinessStatus
    warnings: list[str]


@dataclass(frozen=True)
class PreprocessingArtifact:
    step: str
    path: str


@dataclass(frozen=True)
class ImageAnalysisPacket:
    document_name: str
    status: ImageReadinessStatus
    metadata: ImageMetadata
    quality: ImageQualityAssessment
    preprocessing_steps: list[str]
    preprocessing_artifacts: list[PreprocessingArtifact]
    recommended_action: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        metadata = payload["metadata"]
        metadata["aspect_ratio"] = round(float(metadata["aspect_ratio"]), 4)

        quality = payload["quality"]
        for field_name in (
            "brightness_mean",
            "contrast_stddev",
            "edge_density",
            "foreground_ratio",
            "resolution_score",
            "brightness_score",
            "contrast_score",
            "sharpness_score",
            "coverage_score",
            "ocr_readiness_score",
        ):
            quality[field_name] = round(float(quality[field_name]), 4)

        return payload
