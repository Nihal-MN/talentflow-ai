"""Synthetic demo candidates (parts A + B) — the full fictional roster."""

from __future__ import annotations

from app.seed.demo_candidates_a import CANDIDATES_A
from app.seed.demo_candidates_b import CANDIDATES_B

#: All demo candidates, in display order.
CANDIDATES: list[dict] = [*CANDIDATES_A, *CANDIDATES_B]

#: Application plan: (candidate full name, job slug, target stage, note).
#: Stages beyond NEW are built through the real move_stage() service, so the
#: audit trail (PipelineStageEvent) is complete and realistic.
APPLICATION_PLAN: list[tuple[str, str, str, str | None]] = [
    (
        "Amira Haddad",
        "senior-full-stack-engineer",
        "SHORTLISTED",
        "Strongest full-stack match; moving straight to shortlist.",
    ),
    (
        "Daniel Okafor",
        "senior-full-stack-engineer",
        "SCREENING",
        "Great backend depth — verify frontend work on the call.",
    ),
    ("Priya Nair", "senior-full-stack-engineer", "NEW", None),
    (
        "Elena Vasquez",
        "senior-full-stack-engineer",
        "REJECTED",
        "Frontend-only profile; no Python/FastAPI — not a fit for this role.",
    ),
    (
        "Lucas Meyer",
        "data-analyst",
        "INTERVIEW",
        "Excellent analytics stack fit; scheduling business interview.",
    ),
    ("Sofia Petrova", "data-analyst", "SHORTLISTED", "Retail BI background maps perfectly."),
    (
        "Marco Rossi",
        "data-analyst",
        "SCREENING",
        "Strong statistics; confirm dashboarding experience.",
    ),
    (
        "Omar Al Farsi",
        "devops-engineer",
        "INTERVIEW",
        "Meets every must-have with AWS + CKA certifications.",
    ),
    ("Chen Wei", "devops-engineer", "NEW", None),
    (
        "Fatima Noor",
        "machine-learning-engineer",
        "SCREENING",
        "Rare production-LLM depth in the region.",
    ),
]

#: Candidate tags: full name → (tag, color) pairs.
TAG_PLAN: list[tuple[str, str, str]] = [
    ("Amira Haddad", "top-match", "emerald"),
    ("Omar Al Farsi", "top-match", "emerald"),
    ("Lucas Meyer", "strong-analytics", "sky"),
    ("Priya Nair", "needs-follow-up", "amber"),
    ("Fatima Noor", "gcc-based", "violet"),
    ("Amira Haddad", "gcc-based", "violet"),
    ("Omar Al Farsi", "gcc-based", "violet"),
]

#: Extra recruiter notes (candidate name, job slug or None, author, body).
NOTE_PLAN: list[tuple[str, str | None, str, str]] = [
    (
        "Amira Haddad",
        "senior-full-stack-engineer",
        "Nihal",
        "Portfolio is excellent — logistics dashboards look exactly like our ops tooling.",
    ),
    (
        "Amira Haddad",
        "senior-full-stack-engineer",
        "Nihal",
        "References checked: strong ownership, ships fast.",
    ),
    (
        "Omar Al Farsi",
        "devops-engineer",
        "Nihal",
        "Ran the exact stack we use (EKS + Terraform + Grafana). Discuss salary band next.",
    ),
    (
        "Daniel Okafor",
        "senior-full-stack-engineer",
        "Nihal",
        "Ask about any production React work — profile reads backend-heavy.",
    ),
    (
        "Priya Nair",
        "senior-full-stack-engineer",
        "Nihal",
        "Promising mid-level profile; keep warm for a junior-mid opening.",
    ),
]
