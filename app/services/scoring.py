"""Scoring engine — computes maturity scores and risk ratings."""

from typing import List, Dict, Optional

# Maps response status to a numeric score (0–4 scale)
STATUS_SCORES: Dict[str, float] = {
    "compliant": 4.0,
    "partial": 2.0,
    "non_compliant": 0.0,
    "na": None,          # Excluded from calculation
    "not_assessed": None, # Excluded from calculation
}

SEVERITY_LABELS = {
    (20, 25): "Critical",
    (15, 19): "High",
    (8, 14): "Medium",
    (3, 7): "Low",
    (1, 2): "Informational",
}

MATURITY_LEVELS = [
    (0.0, 20.0, "Level 1 — Initial"),
    (20.0, 40.0, "Level 2 — Developing"),
    (40.0, 60.0, "Level 3 — Defined"),
    (60.0, 80.0, "Level 4 — Managed"),
    (80.0, 101.0, "Level 5 — Optimizing"),
]


def score_for_status(status: str) -> Optional[float]:
    return STATUS_SCORES.get(status)


def compute_project_score(responses: List) -> Dict:
    """
    Given a list of AssessmentResponse ORM objects, compute:
      - overall_score (0–100%)
      - maturity_level string
      - per-status counts
      - category scores (if control_id has category prefix like GV.OC-01)
    """
    scored = [r for r in responses if STATUS_SCORES.get(r.status) is not None]
    counts = {
        "compliant": 0,
        "partial": 0,
        "non_compliant": 0,
        "na": 0,
        "not_assessed": 0,
        "total": len(responses),
    }
    for r in responses:
        key = r.status if r.status in counts else "not_assessed"
        counts[key] += 1

    if not scored:
        return {
            "overall_score": 0.0,
            "maturity_level": "Level 1 — Initial",
            "counts": counts,
            "percent_complete": 0.0,
        }

    total_possible = len(scored) * 4.0
    earned = sum(STATUS_SCORES[r.status] for r in scored)
    overall_pct = (earned / total_possible) * 100.0 if total_possible else 0.0

    # Determine assessed (not na / not_assessed)
    assessed = counts["compliant"] + counts["partial"] + counts["non_compliant"]
    percent_complete = (assessed / counts["total"] * 100.0) if counts["total"] else 0.0

    maturity_level = "Level 1 — Initial"
    for lo, hi, label in MATURITY_LEVELS:
        if lo <= overall_pct < hi:
            maturity_level = label
            break

    return {
        "overall_score": round(overall_pct, 1),
        "maturity_level": maturity_level,
        "counts": counts,
        "percent_complete": round(percent_complete, 1),
    }


def compute_risk_score(likelihood: int, impact: int) -> float:
    return float(max(1, min(5, likelihood)) * max(1, min(5, impact)))


def severity_from_risk_score(risk_score: float) -> str:
    score = int(risk_score)
    for (lo, hi), label in SEVERITY_LABELS.items():
        if lo <= score <= hi:
            return label
    return "Informational"


def severity_from_status(status: str) -> str:
    """Suggest a default severity when auto-generating a finding."""
    mapping = {
        "non_compliant": "high",
        "partial": "medium",
    }
    return mapping.get(status, "medium")


def next_finding_ref(existing_refs: List[str]) -> str:
    """Generate the next sequential finding ref like F-001, F-002, etc."""
    nums = []
    for ref in existing_refs:
        try:
            nums.append(int(ref.split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(nums) + 1 if nums else 1
    return f"F-{next_num:03d}"
