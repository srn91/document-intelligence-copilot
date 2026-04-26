from __future__ import annotations

import re
from decimal import Decimal

from app.models import ExtractedField, InvoiceExtraction


def _extract_field(pattern: str, text: str, confidence: float) -> ExtractedField:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"pattern not found: {pattern}")
    value = match.group("value").strip()
    return ExtractedField(value=value, confidence=confidence, source_span=match.group(0).strip())


def extract_invoice(text: str) -> InvoiceExtraction:
    vendor_name = _extract_field(r"Vendor:\s*(?P<value>.+)", text, 0.99)
    invoice_id = _extract_field(r"Invoice Number:\s*(?P<value>INV-\d+)", text, 0.98)
    invoice_date = _extract_field(r"Invoice Date:\s*(?P<value>\d{4}-\d{2}-\d{2})", text, 0.97)
    due_date = _extract_field(r"Due Date:\s*(?P<value>\d{4}-\d{2}-\d{2})", text, 0.97)
    currency = _extract_field(r"Currency:\s*(?P<value>[A-Z]{3})", text, 0.95)
    payment_terms = _extract_field(r"Terms:\s*(?P<value>.+)", text, 0.93)

    purchase_order_match = re.search(r"Purchase Order:\s*(?P<value>PO-\d+)", text, flags=re.MULTILINE)
    purchase_order = None
    if purchase_order_match:
        purchase_order = ExtractedField(
            value=purchase_order_match.group("value").strip(),
            confidence=0.91,
            source_span=purchase_order_match.group(0).strip(),
        )

    amount_match = re.search(r"Total Amount:\s*(?P<value>\d+\.\d{2})", text, flags=re.MULTILINE)
    if not amount_match:
        raise ValueError("total amount not found")
    total_amount = Decimal(amount_match.group("value"))

    return InvoiceExtraction(
        vendor_name=vendor_name,
        invoice_id=invoice_id,
        invoice_date=invoice_date,
        due_date=due_date,
        total_amount=total_amount,
        currency=currency,
        payment_terms=payment_terms,
        purchase_order=purchase_order,
    )
