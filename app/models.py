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
