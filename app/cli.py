from __future__ import annotations

from app.config import SAMPLE_INVOICE_PATH
from app.extraction import extract_invoice
from app.review import build_review_packet, write_review_outputs
from app.validation import validate_invoice


def review_sample() -> None:
    text = SAMPLE_INVOICE_PATH.read_text(encoding="utf-8")
    extraction = extract_invoice(text)
    issues = validate_invoice(extraction)
    packet = build_review_packet(SAMPLE_INVOICE_PATH.name, extraction, issues)
    json_path, markdown_path = write_review_outputs(SAMPLE_INVOICE_PATH.name, packet)
    print(f"status={packet.status}")
    print(f"json_path={json_path}")
    print(f"markdown_path={markdown_path}")


def main() -> None:
    import sys

    if len(sys.argv) != 2 or sys.argv[1] != "review":
        raise SystemExit("usage: python3 -m app.cli review")

    review_sample()


if __name__ == "__main__":
    main()
