from __future__ import annotations

from app.config import SAMPLE_INVOICE_PATH
from app.extraction import extract_invoice
from app.review import build_review_packet
from app.validation import validate_invoice


def test_sample_invoice_extraction_and_validation() -> None:
    extraction = extract_invoice(SAMPLE_INVOICE_PATH.read_text(encoding="utf-8"))

    assert extraction.vendor_name.value == "Northwind Industrial Supply"
    assert extraction.invoice_id.value == "INV-2048"
    assert f"{extraction.total_amount:.2f}" == "18450.75"

    issues = validate_invoice(extraction)
    packet = build_review_packet(SAMPLE_INVOICE_PATH.name, extraction, issues)

    assert packet.status == "needs_review"
    assert any(issue.code == "manual_review_amount_threshold" for issue in issues)
