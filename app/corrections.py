from __future__ import annotations

import json
from pathlib import Path

from app.config import GENERATED_DIR
from app.models import ReviewerCorrection


CORRECTIONS_PATH = GENERATED_DIR / "reviewer_corrections.jsonl"


def record_reviewer_correction(correction: ReviewerCorrection) -> str:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    with CORRECTIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(correction.to_dict()) + "\n")
    return _portable(CORRECTIONS_PATH)


def _portable(path: Path) -> str:
    cwd = Path.cwd()
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)
