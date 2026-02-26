"""Application assistance AI: checklist generation and autofill field mapping."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import Profile, User

# ---------------------------------------------------------------------------
# Checklist generation
# ---------------------------------------------------------------------------

_CHECKLIST_TRIGGERS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"\bresume\b|\bcv\b", re.I),
        "Prepare and attach your latest resume/CV",
    ),
    (
        re.compile(r"\bstatement of purpose\b|\bsop\b|\bpersonal statement\b", re.I),
        "Write a Statement of Purpose (SOP)",
    ),
    (
        re.compile(r"\brecommendation letters?\b|\blor\b|\breference letters?\b", re.I),
        "Arrange recommendation/reference letters",
    ),
    (
        re.compile(r"\btranscript\b|\bgrade sheet\b|\bmarksheet\b", re.I),
        "Obtain official academic transcripts",
    ),
    (
        re.compile(r"\bportfolio\b|\bwork sample\b", re.I),
        "Compile a portfolio / work samples",
    ),
    (
        re.compile(r"\bno[ -]objection\b|\bnoc\b", re.I),
        "Obtain a No-Objection Certificate (NOC) from your institution",
    ),
    (
        re.compile(r"\bpan card\b|\baadhar\b|\bgovernment id\b|\bnational id\b", re.I),
        "Keep a valid government-issued photo ID ready",
    ),
    (re.compile(r"\bpassport\b", re.I), "Ensure your passport is valid and accessible"),
    (
        re.compile(r"\bGPA\b|\bCGPA\b|\bminimum grade\b|\bacademic record\b", re.I),
        "Verify you meet the minimum GPA/CGPA requirement",
    ),
    (
        re.compile(r"\bfinal year\b|\blast year\b|\bfinal semester\b", re.I),
        "Confirm you are in your final year / semester if required",
    ),
    (
        re.compile(r"\bopen[- ]source\b|\bgithub\b|\bcode repository\b", re.I),
        "Share your GitHub profile / open-source contributions",
    ),
    (
        re.compile(r"\bproject report\b|\bproject proposal\b|\bproject plan\b", re.I),
        "Prepare a project report / proposal document",
    ),
    (
        re.compile(r"\bfee\b|\bapplication fee\b|\bregistration fee\b", re.I),
        "Check and pay any application / registration fee",
    ),
    (
        re.compile(r"\bvideo\b|\bintroduction clip\b", re.I),
        "Record a short introduction or demo video if needed",
    ),
    (
        re.compile(
            r"\bcodecheef\b|\bleetcode\b|\bcodeforces\b|\bcoding test\b|\bonline assessment\b",
            re.I,
        ),
        "Prepare for an online coding assessment",
    ),
    (re.compile(r"\binterview\b", re.I), "Prepare for a shortlisting interview"),
    (
        re.compile(r"\bdeadline\b|\blast date\b", re.I),
        "Note the application deadline and submit before the due date",
    ),
]

_GENERIC_CHECKLIST = [
    "Read the full opportunity description carefully",
    "Fill in all required application fields accurately",
    "Review your submission before final submit",
]


def generate_checklist(eligibility_text: str | None) -> list[str]:
    """Generate a checklist from opportunity eligibility text using pattern matching."""
    if not eligibility_text or not eligibility_text.strip():
        return list(_GENERIC_CHECKLIST)

    items: list[str] = []
    seen: set[str] = set()

    for pattern, item in _CHECKLIST_TRIGGERS:
        if pattern.search(eligibility_text) and item not in seen:
            items.append(item)
            seen.add(item)

    # Always add generic baseline items
    for item in _GENERIC_CHECKLIST:
        if item not in seen:
            items.append(item)

    return items


# ---------------------------------------------------------------------------
# Autofill field mapping
# ---------------------------------------------------------------------------

_FIELD_MAP: dict[str, str] = {
    # Identity
    "name": "name",
    "full_name": "name",
    "applicant_name": "name",
    "student_name": "name",
    # Contact
    "email": "email",
    "email_address": "email",
    # Institution
    "college": "college",
    "university": "college",
    "institution": "college",
    "school": "college",
    # Degree
    "degree": "degree",
    "program": "degree",
    "course": "degree",
    "qualification": "degree",
    # Year
    "year": "year",
    "year_of_study": "year",
    "academic_year": "year",
    "semester": "year",
    # Skills
    "skills": "skills",
    "technical_skills": "skills",
    "core_skills": "skills",
    # Links
    "github": "github_url",
    "github_url": "github_url",
    "github_profile": "github_url",
    "linkedin": "linkedin_url",
    "linkedin_url": "linkedin_url",
    "linkedin_profile": "linkedin_url",
}

_PROFILE_SOURCES = {
    "name": lambda user, profile: user.name,
    "email": lambda user, profile: user.email,
    "college": lambda user, profile: user.college or (profile.bio or ""),
    "degree": lambda user, profile: user.degree or "",
    "year": lambda user, profile: str(user.year) if user.year else "",
    "skills": lambda user, profile: ", ".join(profile.skills or []),
    "github_url": lambda user, profile: profile.github_url or "",
    "linkedin_url": lambda user, profile: profile.linkedin_url or "",
}


def generate_autofill(user: "User", profile: "Profile") -> dict[str, str]:
    """Return autofill field suggestions based on the user's profile.

    Returns a dict mapping canonical field names → suggested values.
    Only includes fields with non-empty values.
    """
    result: dict[str, str] = {}
    for canonical_field, source_fn in _PROFILE_SOURCES.items():
        try:
            value = source_fn(user, profile)
            if value and str(value).strip():
                result[canonical_field] = str(value).strip()
        except Exception:
            pass
    return result
