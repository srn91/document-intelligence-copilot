from __future__ import annotations

import base64

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def test_root_endpoint_lists_demo_paths() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "document-intelligence-copilot"
    assert body["endpoints"]["sample_invoice"] == "/extract/sample-invoice"


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


def test_sample_image_analysis_endpoint_returns_quality_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.vision.GENERATED_DIR", tmp_path)

    response = client.get("/analyze/sample-invoice-image")

    assert response.status_code == 200
    body = response.json()
    assert body["document_name"] == "sample_invoice_scan.pgm"
    assert body["metadata"]["width"] == 900
    assert body["metadata"]["height"] == 1200
    assert body["quality"]["ocr_readiness_score"] > 0.5
    assert body["preprocessing_artifacts"]
    assert body["analysis_path"].endswith("sample_invoice_scan_image_analysis.json")


def test_analyze_image_endpoint_accepts_base64_image(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.vision.GENERATED_DIR", tmp_path)

    image = Image.new("L", (1200, 1600), color=244)
    for y in range(140, 1180, 95):
        for row in range(y, y + 12):
            for x in range(90, 1080):
                image.putpixel((x, row), 38)
    for y in range(1260, 1460, 55):
        for row in range(y, y + 10):
            for x in range(90, 920):
                image.putpixel((x, row), 52)

    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    payload = {
        "document_name": "ad_hoc_invoice.png",
        "image_base64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
        "persist_artifacts": True,
    }

    response = client.post("/analyze-image", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["format"] == "PNG"
    assert body["quality"]["ocr_readiness_score"] >= 0.5
    assert len(body["preprocessing_artifacts"]) == 2
    assert body["analysis_path"].endswith("ad_hoc_invoice_image_analysis.json")


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
