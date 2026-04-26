from __future__ import annotations

from app.config import SAMPLE_INVOICE_IMAGE_PATH, SAMPLE_INVOICE_PATH
from app.extraction import extract_invoice
from app.review import build_review_packet, write_review_outputs
from app.validation import validate_invoice
from app.vision import analyze_invoice_image_file, write_image_analysis_output


def review_sample() -> None:
    text = SAMPLE_INVOICE_PATH.read_text(encoding="utf-8")
    extraction = extract_invoice(text)
    issues = validate_invoice(extraction)
    packet = build_review_packet(SAMPLE_INVOICE_PATH.name, extraction, issues)
    json_path, markdown_path = write_review_outputs(SAMPLE_INVOICE_PATH.name, packet)
    print(f"status={packet.status}")
    print(f"json_path={json_path}")
    print(f"markdown_path={markdown_path}")


def analyze_sample_image() -> None:
    packet = analyze_invoice_image_file(SAMPLE_INVOICE_IMAGE_PATH)
    analysis_path = write_image_analysis_output(packet)
    print(f"status={packet.status}")
    print(f"ocr_readiness_score={packet.quality.ocr_readiness_score:.4f}")
    print(f"analysis_path={analysis_path}")
    for artifact in packet.preprocessing_artifacts:
        print(f"{artifact.step}_path={artifact.path}")


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 -m app.cli [review|analyze-image]")

    command = sys.argv[1]
    if command == "review":
        review_sample()
        return
    if command == "analyze-image":
        analyze_sample_image()
        return

    raise SystemExit("usage: python3 -m app.cli [review|analyze-image]")


if __name__ == "__main__":
    main()
