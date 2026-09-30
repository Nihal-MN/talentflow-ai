"""Deterministic, rule-based resume parsing (mock provider internals).

Parses common resume layouts: contact block, summary, experience entries
(header + date range + bullets), education, skills and certifications.
Best-effort by design — it favors precise, traceable output over guessing, and
mirrors the schema the OpenAI provider returns. The resume text is untrusted
data: it is only ever scanned, never interpreted as instructions.
"""

from __future__ import annotations

import re

from app.ai.base import (
    ExtractedCandidate,
    ExtractedCertification,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedSkill,
)
from app.ai.cities import CITIES
from app.core.dates import compute_years_experience, parse_partial_date
from app.services.skills import canonicalize, category_of, extract_skills

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_LINKEDIN_RE = re.compile(r"(?:https?://)?(?:[a-z]{2,3}\.)?linkedin\.com/in/[\w-]+", re.IGNORECASE)
_GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w.-]+", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s,)]+", re.IGNORECASE)

_DATE_PART = (
    r"(?:(?:[A-Z][a-z]{2,9}\.?\s+)?\d{1,2}\.\d{1,2}\.\d{4}"  # 01.04.2021
    r"|(?:[A-Z][a-z]{2,9}\.?\s+)?\d{1,2}\.\d{4}"  # 10.2015
    r"|(?:[A-Z][a-z]{2,9}\.?\s+)?\d{4}"  # Apr 2021 / 2021
    r")"
)
_DATE_RANGE_RE = re.compile(
    rf"({_DATE_PART})\s*(?:[–—-]+\s*|\bto\b\s*)({_DATE_PART}|present|current|now)",
    re.IGNORECASE,
)
_DEGREE_RE = re.compile(
    r"\b(bachelor|master|b\.?\s?sc\.?|m\.?\s?sc\.?|bsc|msc|mba|phd|diploma|diplom"
    r"|b\.?a\.?|b\.?eng|m\.?eng)\b",
    re.IGNORECASE,
)
_UNIVERSITY_RE = re.compile(r"\b(university|college|institute|school|academy)\b", re.IGNORECASE)
_CERT_RE = re.compile(r"\b(certified|certification|certificate|license)\b", re.IGNORECASE)
_FIELD_RE = re.compile(r"\b(?:in|of)\s+([A-Za-z &/]+)", re.IGNORECASE)
_YEARS_STATEMENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\b", re.IGNORECASE)

_ROLE_WORDS = (
    "engineer",
    "developer",
    "designer",
    "analyst",
    "manager",
    "scientist",
    "architect",
    "consultant",
    "specialist",
    "administrator",
    "lead",
    "director",
    "recruiter",
    "marketer",
    "intern",
    "associate",
    "coordinator",
    "officer",
)
_SECTION_PATTERNS = {
    "summary": re.compile(
        r"^\s*(?:professional\s+)?(summary|profile|objective|about(?:\s+me)?"
        r"|profil|zusammenfassung|perfil)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^\s*(?:work\s+|professional\s+)?(experience|employment(?:\s+history)?"
        r"|work\s+history|career|berufserfahrung|werdegang|expérience|experiencia)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^\s*(education|academic(?:\s+background)?|qualifications"
        r"|ausbildung|formation|educación)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^\s*(?:technical\s+|core\s+|key\s+)?(skills|technologies|tech\s+stack|tools"
        r"|kenntnisse|kompetenzen|fähigkeiten|compétences|habilidades)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^\s*(certifications?|licenses?|courses?|zertifizier(?:ung|ungen)"
        r"|certificaciones)\s*:?\s*$",
        re.IGNORECASE,
    ),
}
_CITIES = CITIES
_ISSUERS = (
    "aws",
    "amazon",
    "google",
    "microsoft",
    "azure",
    "scrum alliance",
    "pmi",
    "pmp",
    "hubspot",
    "coursera",
    "databricks",
    "oracle",
    "cisco",
    "comptia",
    "kaggle",
    "deeplearning.ai",
    "datacamp",
)


def _is_role(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in _ROLE_WORDS)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip(" |,;•-–—")


def parse_resume(resume_text: str, *, source_filename: str | None = None) -> ExtractedCandidate:
    """Parse resume text into a structured candidate profile."""
    lines = [line.rstrip() for line in resume_text.replace("\r", "").split("\n")]
    non_empty = [line for line in lines if line.strip()]

    email = _first_match(_EMAIL_RE, resume_text)
    phone = _find_phone(resume_text)
    linkedin = _first_match(_LINKEDIN_RE, resume_text)
    github = _first_match(_GITHUB_RE, resume_text)
    website = next(
        (
            url
            for url in _URL_RE.findall(resume_text)
            if "linkedin.com" not in url and "github.com" not in url
        ),
        None,
    )

    name = _extract_name(non_empty, source_filename)
    location = _extract_location(non_empty)
    sections = _split_sections(lines)

    experiences = _parse_experiences(sections.get("experience", []))
    educations = _parse_educations(
        sections.get("education", [])
        or [line for line in lines if _DEGREE_RE.search(line) or _UNIVERSITY_RE.search(line)]
    )
    skills = _parse_skills(resume_text, sections.get("skills", []))
    certifications = _parse_certifications(lines)

    headline = None
    for line in non_empty[:14]:
        cleaned = _clean(line)
        if cleaned == name or _EMAIL_RE.search(cleaned) or _PHONE_RE.search(cleaned):
            continue
        if _is_role(cleaned) and len(cleaned) <= 90 and not _DATE_RANGE_RE.search(cleaned):
            headline = cleaned
            break
    if headline is None and experiences:
        headline = experiences[0].title

    summary = None
    summary_lines = sections.get("summary", [])
    if summary_lines:
        summary = " ".join(_clean(line) for line in summary_lines if line.strip())[:1200] or None

    years = compute_years_experience(experiences)
    if years is None:
        statement = next(
            (match for line in non_empty[:30] if (match := _YEARS_STATEMENT_RE.search(line))),
            None,
        )
        if statement:
            years = float(statement.group(1))

    return ExtractedCandidate(
        full_name=name,
        email=email,
        phone=phone,
        location=location,
        headline=headline,
        summary=summary,
        years_experience=years,
        linkedin_url=linkedin,
        github_url=github,
        website_url=website,
        experiences=experiences,
        educations=educations,
        skills=skills,
        certifications=certifications,
    )


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0).strip() if match else None


def _find_phone(text: str) -> str | None:
    """First phone-like match with a plausible digit count (9-15)."""
    for match in _PHONE_RE.finditer(text):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 9 <= len(digits) <= 15:
            return candidate
    return None


def _extract_name(non_empty: list[str], source_filename: str | None) -> str:
    for line in non_empty[:6]:
        cleaned = _clean(line)
        cleaned = re.sub(r"^(?:name|candidate)\s*[:\-]\s*", "", cleaned, flags=re.IGNORECASE)
        if not cleaned or len(cleaned) > 60:
            continue
        if (
            _EMAIL_RE.search(cleaned)
            or _URL_RE.search(cleaned)
            or any(ch.isdigit() for ch in cleaned)
        ):
            continue
        words = cleaned.split()
        if 1 < len(words) <= 5 and all(
            re.fullmatch(r"[A-Za-z][A-Za-z'’.-]*", word) for word in words
        ):
            lowered = cleaned.lower()
            if any(
                word in lowered
                for word in ("resume", "curriculum", "vitae", "engineer", "developer", "analyst")
            ):
                continue
            return cleaned.title() if cleaned.isupper() else cleaned
    if source_filename:
        stem = re.sub(r"[_\-.]+", " ", source_filename.rsplit(".", 1)[0])
        stem = re.sub(r"(?i)\b(resume|cv|pdf|docx)\b", "", stem).strip()
        if stem:
            return stem.title()
    return "Unknown Candidate"


def _extract_location(non_empty: list[str]) -> str | None:
    # First pass: an explicit "City, Country" span anywhere in the top lines —
    # including contact lines that also carry email/phone/links, which is where
    # resumes most commonly put their location.
    for line in non_empty[:14]:
        cleaned = _clean(line)
        for city in _CITIES:
            match = re.search(
                rf"(?<![A-Za-z]){re.escape(city)}(?![A-Za-z]),\s*([A-Z][A-Za-z .'-]+)",
                cleaned,
                re.IGNORECASE,
            )
            if match:
                return cleaned[match.start() : match.end()].strip()[:120]
    for line in non_empty[:14]:
        cleaned = _clean(line)
        if _EMAIL_RE.search(cleaned) or _URL_RE.search(cleaned):
            continue
        match = re.match(r"^(?:location|based in|address)\s*[:\-]\s*(.+)$", cleaned, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:120]
        if re.search(r"\b\d{4}\b", cleaned) or _DATE_RANGE_RE.search(cleaned):
            continue
        for city in _CITIES:
            if (
                re.search(rf"(?<![a-z]){re.escape(city)}(?![a-z])", cleaned.lower())
                and len(cleaned) <= 60
            ):
                return cleaned
    return None


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        stripped = line.strip()
        matched_header = False
        for key, pattern in _SECTION_PATTERNS.items():
            if pattern.match(stripped):
                current = key
                sections.setdefault(key, [])
                matched_header = True
                break
        if matched_header:
            continue
        if current is not None and stripped:
            sections.setdefault(current, []).append(stripped)
    return sections


def _parse_date_range(line: str) -> tuple[object, object, bool]:
    match = _DATE_RANGE_RE.search(line)
    if not match:
        return None, None, False
    start = parse_partial_date(match.group(1))
    end_raw = match.group(2).strip().lower()
    if end_raw in ("present", "current", "now"):
        return start, None, True
    end = parse_partial_date(match.group(2))
    return start, end, False


def _parse_experiences(section_lines: list[str]) -> list[ExtractedExperience]:
    entries: list[ExtractedExperience] = []
    pending_header: str | None = None
    current: dict | None = None

    for raw in section_lines:
        line = raw.strip()
        if not line:
            continue
        is_bullet = bool(re.match(r"^[-*•·▪]\s", line))
        date_match = _DATE_RANGE_RE.search(line)

        if date_match:
            start, end, is_current = _parse_date_range(line)
            header = pending_header
            inline_header = _DATE_RANGE_RE.sub("", line).strip(" |,–—-")
            if len(inline_header.split()) >= 3 and _is_role(inline_header):
                header = inline_header
            if header:
                current = {
                    "header": header,
                    "bullets": [],
                    "start": start,
                    "end": end,
                    "current": is_current,
                }
                entries.append(_build_experience(current))
            elif current is not None:
                current["start"], current["end"], current["current"] = start, end, is_current
                _refresh_experience(entries, current)
            pending_header = None
            continue

        if is_bullet or (
            current is not None
            and len(line) > 40
            and not _is_role(line[:60])
            and _DATE_RANGE_RE.search(line) is None
        ):
            if current is not None:
                current["bullets"].append(_clean(line))
                _refresh_experience(entries, current)
            continue

        pending_header = line
        current = None

    return [entry for entry in entries if entry.title or entry.company]


def _build_experience(state: dict) -> ExtractedExperience:
    title, company, location = _split_header(state["header"])
    return ExtractedExperience(
        company=company,
        title=title,
        location=location,
        start_date=state["start"],
        end_date=state["end"],
        is_current=state["current"],
        description="\n".join(state["bullets"]) or None,
    )


def _refresh_experience(entries: list[ExtractedExperience], state: dict) -> None:
    if not entries:
        return
    title, company, location = _split_header(state["header"])
    entry = entries[-1]
    entry.title = title or entry.title
    entry.company = company or entry.company
    entry.location = location or entry.location
    entry.description = "\n".join(state["bullets"]) or None


def _split_header(header: str) -> tuple[str | None, str | None, str | None]:
    location = None
    match = re.search(r"\(([^)]{2,60})\)\s*$", header)
    if match:
        location = match.group(1).strip()
        header = header[: match.start()].strip()
    parts = [
        part.strip() for part in re.split(r"\s+(?:—|–|\||@|·)\s+|\s+at\s+", header) if part.strip()
    ]
    if not parts:
        return None, None, location
    if len(parts) == 1:
        # "Title - Company" with hyphen fallback (avoid splitting hyphenated words)
        hyphen_parts = [part.strip() for part in re.split(r"\s+-\s+", header) if part.strip()]
        if len(hyphen_parts) >= 2:
            parts = hyphen_parts
        else:
            return _clean(parts[0]) or None, None, location
    first, second = _clean(parts[0]), _clean(parts[1])
    if _is_role(first) and not _is_role(second):
        return first or None, second or None, location
    if _is_role(second) and not _is_role(first):
        return second or None, first or None, location
    return first or None, second or None, location


def _parse_educations(lines: list[str]) -> list[ExtractedEducation]:
    entries: list[ExtractedEducation] = []
    current: ExtractedEducation | None = None
    for raw in lines:
        line = _clean(raw)
        if not line or len(line) > 200:
            continue
        years = [int(match) for match in re.findall(r"\b(?:19|20)\d{2}\b", line)]
        degree_match = _DEGREE_RE.search(line)
        university_match = _UNIVERSITY_RE.search(line)
        if degree_match:
            field_match = _FIELD_RE.search(line)
            current = ExtractedEducation(
                institution=None,
                degree=line[:150],
                field_of_study=(field_match.group(1).strip()[:120] if field_match else None),
                start_year=min(years) if years else None,
                end_year=max(years) if years else None,
            )
            if university_match:
                current.institution = line[:150]
            entries.append(current)
            continue
        if university_match:
            if current is not None and not current.institution:
                current.institution = line[:150]
                if years:
                    current.start_year = current.start_year or min(years)
                    current.end_year = current.end_year or max(years)
            else:
                entries.append(
                    ExtractedEducation(
                        institution=line[:150],
                        start_year=min(years) if years else None,
                        end_year=max(years) if years else None,
                    )
                )
    return entries


def _parse_skills(resume_text: str, skills_section: list[str]) -> list[ExtractedSkill]:
    results: list[ExtractedSkill] = []
    seen: set[str] = set()

    for hit in extract_skills(resume_text):
        if hit.canonical in seen:
            continue
        seen.add(hit.canonical)
        results.append(
            ExtractedSkill(
                name=hit.found_as,
                normalized_name=hit.canonical,
                category=category_of(hit.canonical),
                evidence=hit.evidence,
            )
        )

    if skills_section:
        blob = " , ".join(skills_section)
        tokens = re.split(r"[,;•|/·]|\s{2,}", blob)
        extras = 0
        for token in tokens:
            cleaned = _clean(
                re.sub(
                    r"(?i)\b(proficient in|experienced with|familiar with|expertise in)\b",
                    "",
                    token,
                )
            )
            cleaned = cleaned.strip(" .:-")
            if not cleaned or len(cleaned) > 40 or len(cleaned) < 2 or extras >= 15:
                continue
            canonical = canonicalize(cleaned)
            key = canonical or cleaned.lower()
            if key in seen:
                continue
            if not re.search(r"[A-Za-z]", cleaned):
                continue
            seen.add(key)
            results.append(
                ExtractedSkill(
                    name=cleaned,
                    normalized_name=key,
                    category=category_of(key) if canonical else "other",
                    evidence=None,
                )
            )
            extras += 1
    return results[:50]


def _parse_certifications(lines: list[str]) -> list[ExtractedCertification]:
    results: list[ExtractedCertification] = []
    for raw in lines:
        line = _clean(raw)
        if not line or not _CERT_RE.search(line) or len(line) > 200:
            continue
        year_match = re.search(r"\b(?:19|20)\d{2}\b", line)
        issuer = next((name.title() for name in _ISSUERS if name in line.lower()), None)
        results.append(
            ExtractedCertification(
                name=line[:180],
                issuer=issuer,
                year=int(year_match.group(0)) if year_match else None,
            )
        )
    return results[:10]
