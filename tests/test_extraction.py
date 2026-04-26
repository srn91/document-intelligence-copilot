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
    assert len(extraction.line_items) == 3
    assert f"{extraction.line_item_subtotal:.2f}" == "18450.75"

    issues = validate_invoice(extraction)
    packet = build_review_packet(SAMPLE_INVOICE_PATH.name, extraction, issues)

    assert packet.status == "needs_review"
    assert any(issue.code == "manual_review_amount_threshold" for issue in issues)
    assert all(issue.code != "invoice_total_reconciliation_mismatch" for issue in issues)


def test_validation_flags_line_item_reconciliation_errors() -> None:
    extraction = extract_invoice(
        "\n".join(
            [
                "Vendor: Tailspin Components",
                "Invoice Number: INV-3001",
                "Invoice Date: 2026-08-04",
                "Due Date: 2026-09-03",
                "Currency: USD",
                "Terms: Net 30",
                "Purchase Order: PO-4102",
                "Total Amount: 1000.00",
                "",
                "Line Items",
                "- Analyzer core | Qty 2 | Unit Price 200.00 | Line Total 450.00",
                "- Calibration labor | Qty 1 | Unit Price 300.00 | Line Total 300.00",
            ]
        )
    )

    issues = validate_invoice(extraction)

    assert any(issue.code == "line_item_total_mismatch" for issue in issues)
    assert any(issue.code == "invoice_total_reconciliation_mismatch" for issue in issues)


def test_review_packet_serialization_includes_correction_ready_fields() -> None:
    extraction = extract_invoice(SAMPLE_INVOICE_PATH.read_text(encoding="utf-8"))
    packet = build_review_packet(SAMPLE_INVOICE_PATH.name, extraction, validate_invoice(extraction))

    payload = packet.to_dict()

    assert payload["document_name"] == SAMPLE_INVOICE_PATH.name
    assert payload["status"] == "needs_review"
    assert "vendor_name" in payload["extraction"]
