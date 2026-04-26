from __future__ import annotations

import json
from pathlib import Path

from app.config import GENERATED_DIR
from app.models import ReviewPacket


def build_review_packet(document_name: str, extraction, issues) -> ReviewPacket:
    status = "needs_review" if issues else "ready"
    recommended_action = (
        "Route to human review before approval."
        if issues
        else "Document can proceed without manual intervention."
    )
    return ReviewPacket(
        document_name=document_name,
        status=status,
        extraction=extraction,
        issues=issues,
        recommended_action=recommended_action,
    )


def _portable(path: Path) -> str:
    cwd = Path.cwd()
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)


def render_markdown(packet: ReviewPacket) -> str:
    issues = ["None"] if not packet.issues else [f"- `{issue.severity}` {issue.code}: {issue.message}" for issue in packet.issues]
    po_value = packet.extraction.purchase_order.value if packet.extraction.purchase_order else "not found"
    line_items = (
        ["- none extracted"]
        if not packet.extraction.line_items
        else [
            f"- {item.description}: qty `{item.quantity:.2f}` x unit `{item.unit_price:.2f}` = `{item.line_total:.2f}`"
            for item in packet.extraction.line_items
        ]
    )
    return "\n".join(
        [
            f"# Review Packet: {packet.document_name}",
            "",
            f"Status: `{packet.status}`",
            "",
            "## Extracted Fields",
            "",
            f"- vendor: `{packet.extraction.vendor_name.value}`",
            f"- invoice id: `{packet.extraction.invoice_id.value}`",
            f"- invoice date: `{packet.extraction.invoice_date.value}`",
            f"- due date: `{packet.extraction.due_date.value}`",
            f"- total amount: `{packet.extraction.total_amount:.2f} {packet.extraction.currency.value}`",
            f"- line-item subtotal: `{packet.extraction.line_item_subtotal:.2f} {packet.extraction.currency.value}`",
            f"- payment terms: `{packet.extraction.payment_terms.value}`",
            f"- purchase order: `{po_value}`",
            "",
            "## Line Items",
            "",
            *line_items,
            "",
            "## Validation Issues",
            "",
            *issues,
            "",
            "## Recommended Action",
            "",
            packet.recommended_action,
            "",
        ]
    )


def write_review_outputs(document_name: str, packet: ReviewPacket) -> tuple[str, str]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    stem = document_name.removesuffix(".txt")
    json_path = GENERATED_DIR / f"{stem}_review.json"
    markdown_path = GENERATED_DIR / f"{stem}_review.md"
    json_path.write_text(json.dumps(packet.to_dict(), indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(packet), encoding="utf-8")
    return _portable(json_path), _portable(markdown_path)
