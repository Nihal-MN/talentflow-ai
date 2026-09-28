"""Deterministic, rule-based job-description parsing.

This is the offline "mock" intelligence: same input → same output, no network,
no key. It exists so the whole product (and its tests) work without OpenAI
credentials, and is clearly labeled as ``mock`` wherever results are shown.

Heuristics: section detection (must-have vs preferred), skill lexicon matching,
years/degree/location/domain patterns. Precision over recall — unknown text is
kept as category="other" rather than guessed at.
"""

from __future__ import annotations

import re

from app.ai.base import ExtractedJob, ExtractedRequirement
from app.ai.cities import CITIES
from app.services.skills import extract_skills

_YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\b", re.IGNORECASE)
_DEGREE_RE = re.compile(r"\b(bachelor|master|bsc|msc|mba|phd|degree|diploma)\b", re.IGNORECASE)
_CERT_RE = re.compile(r"\b(certified|certification|certificate)\b", re.IGNORECASE)
_LOCATION_LINE_RE = re.compile(r"\b(location|based in|office)\b", re.IGNORECASE)
_REMOTE_RE = re.compile(r"\bremote\b", re.IGNORECASE)

_SENIORITY_RE = [
    ("principal", r"\bprincipal\b"),
    ("lead", r"\b(lead|staff|head of)\b"),
    ("senior", r"\b(senior|sr\.?)\b"),
    ("junior", r"\b(junior|entry[- ]level|graduate|intern)\b"),
]

_DOMAIN_KEYWORDS = {
    "logistics": ["logistics", "freight", "supply chain", "shipping", "warehous", "fleet", "3pl"],
    "fintech": ["fintech", "payments", "banking", "financial services", "ledger"],
    "healthcare": ["healthcare", "health tech", "clinical", "medical"],
    "e-commerce": ["e-commerce", "ecommerce", "marketplace", "retail"],
    "saas": ["saas", "b2b software", "platform as a service"],
    "education": ["edtech", "education", "e-learning"],
    "energy": ["energy", "oil & gas", "renewables", "solar"],
    "travel": ["travel", "hospitality", "booking"],
}

_CITIES = CITIES

_MUST_SECTION_HINTS = (
    "requirement",
    "must have",
    "must-have",
    "required",
    "qualification",
    "what you bring",
    "what you'll need",
    "what you will need",
    "who you are",
    "you have",
    "skills",
    "minimum",
)
_PREF_SECTION_HINTS = (
    "nice to have",
    "nice-to-have",
    "preferred",
    "bonus",
    "good to have",
    "desirable",
    "a plus",
    "plus points",
)
_SKIP_SECTION_HINTS = (
    "responsibilit",
    "what you'll do",
    "what you will do",
    "you will",
    "about us",
    "about the company",
    "who we are",
    "benefit",
    "perks",
    "we offer",
    "how to apply",
    "compensation",
    "salary",
    "equal opportunity",
    "our stack",
    "why join",
)
_PREF_LINE_HINTS = ("nice to have", "preferred", "bonus", "a plus", "good to have", "desirable")
_MUST_LINE_HINTS = ("required", "must have", "must-have", "minimum", "at least")

_BULLET_RE = re.compile(r"^\s*(?:[-*•·▪]|(?:\d{1,2}[.)]))\s+")
_HEADER_MAX_WORDS = 6


def _clean_line(line: str) -> str:
    return _BULLET_RE.sub("", line).strip()


def _is_section_header(line: str) -> str | None:
    """Return the section type ("must" | "pref" | "skip") if the line is a header.

    Handles both "Requirements:" style and bare "Requirements" / "Nice to have"
    headers (short lines matching the known hint phrases).
    """
    raw = line.strip()
    stripped = raw.strip(":").lower().rstrip(":")
    if not stripped or len(stripped.split()) > _HEADER_MAX_WORDS:
        return None
    starts_with_hint = stripped.startswith(
        _MUST_SECTION_HINTS + _PREF_SECTION_HINTS + _SKIP_SECTION_HINTS
    )
    headerish = raw.endswith(":") or raw.isupper() or starts_with_hint
    if not headerish:
        return None
    for hint in _PREF_SECTION_HINTS:
        if hint in stripped:
            return "pref"
    for hint in _SKIP_SECTION_HINTS:
        if stripped.startswith(hint) or hint in stripped:
            return "skip"
    for hint in _MUST_SECTION_HINTS:
        if hint in stripped:
            return "must"
    return None


def _line_kind(line: str, section: str | None) -> str:
    lowered = line.lower()
    if any(hint in lowered for hint in _PREF_LINE_HINTS):
        return "preferred"
    if any(hint in lowered for hint in _MUST_LINE_HINTS):
        return "must_have"
    if section == "pref":
        return "preferred"
    return "must_have"


def _detect_seniority(title: str) -> str | None:
    lowered = title.lower()
    for name, pattern in _SENIORITY_RE:
        if re.search(pattern, lowered):
            return name
    return "mid"


def _detect_domain(text: str) -> str | None:
    lowered = text.lower()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return domain
    return None


def _detect_location(text: str) -> str | None:
    lowered = text.lower()
    for city in _CITIES:
        if re.search(rf"(?<![a-z]){re.escape(city)}(?![a-z])", lowered):
            return city.title()
    if _REMOTE_RE.search(lowered[:4000]):
        return "Remote"
    return None


def parse_job(jd_text: str, *, fallback_title: str | None = None) -> ExtractedJob:
    """Parse a job description into a structured job with requirements."""
    lines = [line.rstrip() for line in jd_text.replace("\r", "").split("\n")]

    title = None
    company = None
    for line in lines[:15]:
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^(?:job\s*)?title\s*[:\-]\s*(.+)$", stripped, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            break
        if re.match(r"^(?:position|role)\s*[:\-]\s*(.+)$", stripped, re.IGNORECASE):
            title = re.match(r"^(?:position|role)\s*[:\-]\s*(.+)$", stripped, re.IGNORECASE).group(
                1
            )
            break
        if not title and len(stripped) <= 80 and _looks_like_title(stripped):
            title = stripped
            break

    for line in lines[:15]:
        match = re.match(r"^\s*company\s*[:\-]\s*(.+)$", line.strip(), re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            break

    title = title or fallback_title
    if not title:
        first_meaningful = next((line.strip() for line in lines if line.strip()), "Untitled role")
        title = first_meaningful[:120]

    requirements: list[ExtractedRequirement] = []
    seen_skills: set[str] = set()
    seen_labels: set[str] = set()
    section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        header = _is_section_header(line)
        if header:
            section = header
            continue
        if section == "skip":
            continue

        content = _clean_line(line)
        if not content or len(content) < 3:
            continue
        # Requirements live in bullets or recognized sections; skip prose
        # paragraphs entirely (they are context, not requirements) — except
        # explicit metadata labels like "Location:".
        is_bullet = bool(_BULLET_RE.match(line))
        in_req_section = section in ("must", "pref")
        is_metadata_label = bool(
            re.match(r"^(?:location|employment type|job type|work type)\b", content, re.IGNORECASE)
        )
        if not (is_bullet or in_req_section or is_metadata_label):
            continue

        kind = _line_kind(content, section)
        skills = extract_skills(content)
        added = False

        for skill in skills:
            if skill.canonical in seen_skills:
                continue
            seen_skills.add(skill.canonical)
            requirements.append(
                ExtractedRequirement(
                    kind=kind,
                    category="skill",
                    label=content[:240],
                    normalized_skill=skill.canonical,
                    keywords=[skill.canonical, skill.found_as],
                )
            )
            added = True

        years_match = _YEARS_RE.search(content)
        if years_match and not added:
            label_key = f"years:{years_match.group(1)}"
            if label_key not in seen_labels:
                seen_labels.add(label_key)
                requirements.append(
                    ExtractedRequirement(
                        kind=kind,
                        category="experience",
                        label=content[:240],
                        min_years=float(years_match.group(1)),
                        keywords=["years", "experience"],
                    )
                )
            continue

        if not added and _DEGREE_RE.search(content):
            label_key = f"edu:{content[:80]}"
            if label_key not in seen_labels:
                seen_labels.add(label_key)
                requirements.append(
                    ExtractedRequirement(
                        kind=kind,
                        category="education",
                        label=content[:240],
                        keywords=[_DEGREE_RE.search(content).group(1).lower()],
                    )
                )
            continue

        if not added and _CERT_RE.search(content):
            label_key = f"cert:{content[:80]}"
            if label_key not in seen_labels:
                seen_labels.add(label_key)
                requirements.append(
                    ExtractedRequirement(
                        kind=kind,
                        category="certification",
                        label=content[:240],
                        keywords=["certified", "certification"],
                    )
                )
            continue

        if not added and (
            _LOCATION_LINE_RE.search(content)
            or (content.count(",") == 1 and any(city in content.lower() for city in _CITIES))
        ):
            label_key = f"loc:{content[:80]}"
            if label_key not in seen_labels:
                seen_labels.add(label_key)
                requirements.append(
                    ExtractedRequirement(
                        kind="must_have"
                        if "must" in content.lower() or section == "must"
                        else kind,
                        category="location",
                        label=content[:240],
                        keywords=[word.lower() for word in re.findall(r"[A-Za-z]+", content)][:6],
                    )
                )
            continue

        if not added and section == "must" and len(requirements) < 30:
            label_key = f"other:{content[:80]}"
            if label_key not in seen_labels and len(content.split()) <= 25:
                seen_labels.add(label_key)
                requirements.append(
                    ExtractedRequirement(
                        kind=kind,
                        category="other",
                        label=content[:240],
                        keywords=[word.lower() for word in re.findall(r"[A-Za-z]{4,}", content)][
                            :6
                        ],
                    )
                )

    # Fallback: no must-have requirements found — use whole-text skills.
    if not any(req.kind == "must_have" for req in requirements):
        for skill in extract_skills(jd_text):
            if skill.canonical in seen_skills:
                continue
            seen_skills.add(skill.canonical)
            requirements.append(
                ExtractedRequirement(
                    kind="must_have",
                    category="skill",
                    label=f"Experience with {skill.canonical}",
                    normalized_skill=skill.canonical,
                    keywords=[skill.canonical],
                )
            )

    # Order: must-haves first, then preferred; keep insertion order within kind.
    requirements = [r for r in requirements if r.kind == "must_have"] + [
        r for r in requirements if r.kind != "must_have"
    ]
    for requirement in requirements:
        requirement.keywords = requirement.keywords[:6]
    domain = _detect_domain(jd_text)
    if domain and not any(req.category == "domain" for req in requirements):
        requirements.append(
            ExtractedRequirement(
                kind="preferred",
                category="domain",
                label=f"Experience in {domain}",
                keywords=list(_DOMAIN_KEYWORDS[domain][:4]),
            )
        )

    return ExtractedJob(
        title=title[:200],
        company=company,
        location=_detect_location(jd_text),
        employment_type=_detect_employment_type(jd_text),
        seniority=_detect_seniority(title),
        domain=domain,
        summary=None,
        requirements=requirements[:40],
    )


def _looks_like_title(line: str) -> bool:
    lowered = line.lower()
    role_words = (
        "engineer",
        "developer",
        "designer",
        "analyst",
        "manager",
        "scientist",
        "architect",
        "consultant",
        "specialist",
        "recruiter",
        "marketer",
        "administrator",
        "lead",
        "director",
        "officer",
        "intern",
    )
    return any(word in lowered for word in role_words)


def _detect_employment_type(text: str) -> str | None:
    lowered = text.lower()
    if re.search(r"\bpart[- ]time\b", lowered):
        return "part_time"
    if re.search(r"\b(contract|contractor|freelance)\b", lowered):
        return "contract"
    if re.search(r"\binternship\b", lowered):
        return "internship"
    if re.search(r"\bfull[- ]time\b", lowered):
        return "full_time"
    return None
