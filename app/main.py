from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.config import SAMPLE_INVOICE_PATH
from app.extraction import extract_invoice
from app.review import build_review_packet
from app.validation import validate_invoice


class ExtractionRequest(BaseModel):
    document_name: str = Field(min_length=3)
    text: str = Field(min_length=20)


app = FastAPI(
    title="Document Intelligence Copilot",
    description="A local-first document extraction and review workflow for OCR-exported invoice text.",
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


@app.get("/sample-documents")
def sample_documents() -> dict[str, list[str]]:
    return {"documents": [SAMPLE_INVOICE_PATH.name]}


@app.get("/extract/sample-invoice")
def extract_sample_invoice() -> dict[str, object]:
    return _packet_for_text(SAMPLE_INVOICE_PATH.name, SAMPLE_INVOICE_PATH.read_text(encoding="utf-8"))


@app.post("/extract")
def extract_document(request: ExtractionRequest) -> dict[str, object]:
    return _packet_for_text(request.document_name, request.text)
