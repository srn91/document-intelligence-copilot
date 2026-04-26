from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_sample_invoice_endpoint_returns_review_packet() -> None:
    response = client.get("/extract/sample-invoice")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_review"
    assert body["extraction"]["invoice_id"]["value"] == "INV-2048"
    assert body["extraction"]["line_item_subtotal"] == "18450.75"
    assert len(body["extraction"]["line_items"]) == 3


def test_extract_endpoint_handles_custom_text() -> None:
    payload = {
        "document_name": "invoice.txt",
        "text": "\n".join(
            [
                "Vendor: Tailspin Components",
                "Invoice Number: INV-3001",
                "Invoice Date: 2026-08-04",
                "Due Date: 2026-09-03",
                "Currency: USD",
                "Terms: Net 30",
                "Purchase Order: PO-4102",
                "Total Amount: 980.25",
                "",
                "Line Items",
                "- Precision gasket | Qty 3 | Unit Price 210.00 | Line Total 630.00",
                "- Freight | Qty 1 | Unit Price 350.25 | Line Total 350.25",
            ]
        ),
    }

    response = client.post("/extract", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["issues"] == []
    assert body["extraction"]["line_item_subtotal"] == "980.25"


def test_corrections_endpoint_persists_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.corrections.CORRECTIONS_PATH", tmp_path / "reviewer_corrections.jsonl")

    response = client.post(
        "/corrections",
        json={
            "document_name": "invoice.txt",
            "field_name": "vendor_name",
            "original_value": "Northwind Industrial Supply",
            "corrected_value": "Northwind Industrial Supply Co.",
            "reviewer_name": "srn91",
            "note": "Vendor suffix should be preserved for future extraction tuning.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "recorded"
    assert body["correction"]["field_name"] == "vendor_name"
    assert body["correction_path"].endswith("reviewer_corrections.jsonl")
    assert tmp_path.joinpath("reviewer_corrections.jsonl").read_text(encoding="utf-8").strip()
