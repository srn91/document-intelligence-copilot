from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Literal


Status = Literal["ready", "needs_review"]


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
class InvoiceExtraction:
    vendor_name: ExtractedField
    invoice_id: ExtractedField
    invoice_date: ExtractedField
    due_date: ExtractedField
    total_amount: Decimal
    currency: ExtractedField
    payment_terms: ExtractedField
    purchase_order: ExtractedField | None


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
        return payload
