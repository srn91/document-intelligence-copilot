from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import InvoiceExtraction, ValidationIssue


MANUAL_REVIEW_THRESHOLD = Decimal("10000.00")
SUPPORTED_CURRENCIES = {"USD", "EUR"}


def validate_invoice(extraction: InvoiceExtraction) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    invoice_date = date.fromisoformat(extraction.invoice_date.value)
    due_date = date.fromisoformat(extraction.due_date.value)

    if due_date < invoice_date:
        issues.append(
            ValidationIssue(
                code="due_date_before_invoice_date",
                message="Due date occurs before invoice date.",
                severity="critical",
            )
        )

    if extraction.currency.value not in SUPPORTED_CURRENCIES:
        issues.append(
            ValidationIssue(
                code="unsupported_currency",
                message=f"Currency {extraction.currency.value} is outside the supported set.",
                severity="critical",
            )
        )

    if extraction.total_amount >= MANUAL_REVIEW_THRESHOLD:
        issues.append(
            ValidationIssue(
                code="manual_review_amount_threshold",
                message="Invoice total exceeds the manual-review threshold.",
                severity="warning",
            )
        )

    if not extraction.line_items:
        issues.append(
            ValidationIssue(
                code="missing_line_items",
                message="No invoice line items were extracted for subtotal reconciliation.",
                severity="warning",
            )
        )
    else:
        for item in extraction.line_items:
            computed_total = item.quantity * item.unit_price
            if computed_total != item.line_total:
                issues.append(
                    ValidationIssue(
                        code="line_item_total_mismatch",
                        message=(
                            f"Line item '{item.description}' declares {item.line_total:.2f} but quantity x unit price"
                            f" equals {computed_total:.2f}."
                        ),
                        severity="critical",
                    )
                )

        if extraction.line_item_subtotal != extraction.total_amount:
            issues.append(
                ValidationIssue(
                    code="invoice_total_reconciliation_mismatch",
                    message=(
                        f"Line-item subtotal {extraction.line_item_subtotal:.2f} does not reconcile with invoice total"
                        f" {extraction.total_amount:.2f}."
                    ),
                    severity="critical",
                )
            )

    if extraction.purchase_order is None:
        issues.append(
            ValidationIssue(
                code="missing_purchase_order",
                message="Purchase order was not found in the document text.",
                severity="warning",
            )
        )

    return issues
