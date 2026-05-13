from __future__ import annotations

import base64
import binascii

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.corrections import record_reviewer_correction
from app.config import SAMPLE_INVOICE_IMAGE_PATH, SAMPLE_INVOICE_PATH
from app.extraction import extract_invoice
from app.models import ReviewerCorrection
from app.review import build_review_packet
from app.validation import validate_invoice
from app.vision import analyze_invoice_image_bytes, analyze_invoice_image_file, write_image_analysis_output


class ExtractionRequest(BaseModel):
    document_name: str = Field(min_length=3)
    text: str = Field(min_length=20)


class CorrectionRequest(BaseModel):
    document_name: str = Field(min_length=3)
    field_name: str = Field(min_length=2)
    original_value: str = Field(min_length=1)
    corrected_value: str = Field(min_length=1)
    reviewer_name: str | None = None
    note: str = Field(min_length=3)


class ImageAnalysisRequest(BaseModel):
    document_name: str = Field(min_length=3)
    image_base64: str = Field(min_length=20)
    persist_artifacts: bool = True


app = FastAPI(
    title="Document Intelligence Copilot",
    description="A local-first document extraction workflow with a separate invoice image quality and preprocessing lane.",
    version="0.1.0",
)


def _packet_for_text(document_name: str, text: str) -> dict[str, object]:
    extraction = extract_invoice(text)
    issues = validate_invoice(extraction)
    packet = build_review_packet(document_name, extraction, issues)
    return packet.to_dict()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> dict[str, object]:
    return {
        "project": "document-intelligence-copilot",
        "status": "ready",
        "endpoints": {
            "health": "/health",
            "sample_documents": "/sample-documents",
            "sample_invoice": "/extract/sample-invoice",
            "sample_invoice_image": "/analyze/sample-invoice-image",
            "docs": "/docs",
        },
    }


@app.get("/sample-documents")
def sample_documents() -> dict[str, list[str]]:
    return {"documents": [SAMPLE_INVOICE_PATH.name], "images": [SAMPLE_INVOICE_IMAGE_PATH.name]}


@app.get("/extract/sample-invoice")
def extract_sample_invoice() -> dict[str, object]:
    return _packet_for_text(SAMPLE_INVOICE_PATH.name, SAMPLE_INVOICE_PATH.read_text(encoding="utf-8"))


@app.get("/analyze/sample-invoice-image")
def analyze_sample_invoice_image() -> dict[str, object]:
    packet = analyze_invoice_image_file(SAMPLE_INVOICE_IMAGE_PATH)
    analysis_path = write_image_analysis_output(packet)
    payload = packet.to_dict()
    payload["analysis_path"] = analysis_path
    return payload


@app.post("/extract")
def extract_document(request: ExtractionRequest) -> dict[str, object]:
    return _packet_for_text(request.document_name, request.text)


@app.post("/analyze-image")
def analyze_image(request: ImageAnalysisRequest) -> dict[str, object]:
    try:
        image_bytes = base64.b64decode(request.image_base64.encode("utf-8"), validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=400, detail="image_base64 must contain valid base64-encoded image bytes.") from exc

    packet = analyze_invoice_image_bytes(
        image_bytes,
        document_name=request.document_name,
        persist_artifacts=request.persist_artifacts,
    )
    payload = packet.to_dict()
    if request.persist_artifacts:
        payload["analysis_path"] = write_image_analysis_output(packet)
    return payload


@app.post("/corrections")
def capture_correction(request: CorrectionRequest) -> dict[str, object]:
    correction = ReviewerCorrection(
        document_name=request.document_name,
        field_name=request.field_name,
        original_value=request.original_value,
        corrected_value=request.corrected_value,
        reviewer_name=request.reviewer_name,
        note=request.note,
    )
    correction_path = record_reviewer_correction(correction)
    return {"status": "recorded", "correction_path": correction_path, "correction": correction.to_dict()}
