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
            ]
        ),
    }

    response = client.post("/extract", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["issues"] == []
