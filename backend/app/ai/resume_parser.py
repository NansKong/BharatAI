"""Resume parsing and skill extraction utilities."""

from __future__ import annotations

import io
import re
from functools import lru_cache
from typing import Iterable, Optional

import bleach
import fitz
import pdfplumber
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

SKILL_NORMALIZATION_MAP: dict[str, str] = {
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "machine-learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "react": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "vlsi": "VLSI",
    "embedded systems": "Embedded Systems",
    "cad": "CAD",
    "autocad": "AutoCAD",
    "finance": "Finance",
    "valuation": "Valuation",
    "excel": "Excel",
    "product management": "Product Management",
    "public policy": "Public Policy",
}

DEGREE_PATTERNS = [
    r"\bB\.?Tech\b",
    r"\bM\.?Tech\b",
    r"\bB\.?E\b",
    r"\bM\.?E\b",
    r"\bBSc\b",
    r"\bMSc\b",
    r"\bBCA\b",
    r"\bMCA\b",
    r"\bMBA\b",
    r"\bLLB\b",
    r"\bLLM\b",
    r"\bPhD\b",
]

COLLEGE_PATTERN = re.compile(
    r"\b(?:IIT|NIT|IIIT|IISc|IIM|BITS|Delhi University|JNU|Anna University|VIT)\b[^\n,]{0,80}",
    flags=re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"\b(20[2-4]\d)\b")


def extract_text_from_pdf_bytes(content: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber then PyMuPDF fallback."""
    if not content:
        return ""

    text_parts: list[str] = []

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text)
    except Exception:
        text_parts = []

    if not text_parts:
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            try:
                for page in doc:
                    page_text = page.get_text("text") or ""
                    if page_text.strip():
                        text_parts.append(page_text)
            finally:
                doc.close()
        except Exception:
            return ""

    return re.sub(r"\s+", " ", " ".join(text_parts)).strip()


def normalize_skill(skill: str) -> Optional[str]:
    cleaned = bleach.clean(skill or "", tags=[], strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None

    lookup_key = cleaned.lower().replace("_", " ")
    if lookup_key in SKILL_NORMALIZATION_MAP:
        return SKILL_NORMALIZATION_MAP[lookup_key]

    if len(cleaned) > 50:
        return None

    # Preserve acronym-like tokens while still normalizing regular words.
    if cleaned.isupper() and len(cleaned) <= 5:
        return cleaned
    return cleaned.title()


def sanitize_skills(skills: Iterable[str], max_skills: int = 30) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for skill in skills:
        canonical = normalize_skill(skill)
        if not canonical:
            continue
        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(canonical)
        if len(normalized) >= max_skills:
            break

    return normalized


@lru_cache(maxsize=1)
def _skill_matcher() -> tuple[English, PhraseMatcher]:
    nlp = English()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(term) for term in SKILL_NORMALIZATION_MAP]
    matcher.add("SKILLS", patterns)
    return nlp, matcher


def extract_skills(text: str) -> list[str]:
    if not text.strip():
        return []

    nlp, matcher = _skill_matcher()
    doc = nlp(text)
    raw_skills = {doc[start:end].text for _, start, end in matcher(doc)}
    return sanitize_skills(raw_skills)


def extract_profile_entities(text: str) -> dict[str, Optional[str | int]]:
    if not text.strip():
        return {"college": None, "degree": None, "graduation_year": None}

    college_match = COLLEGE_PATTERN.search(text)
    college = college_match.group(0).strip() if college_match else None

    degree = None
    for pattern in DEGREE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            degree = match.group(0).replace(" ", "")
            break

    graduation_year = None
    all_years = [int(value) for value in YEAR_PATTERN.findall(text)]
    if all_years:
        graduation_year = max(all_years)

    return {
        "college": college,
        "degree": degree,
        "graduation_year": graduation_year,
    }


def parse_resume(content: bytes) -> dict[str, object]:
    text = extract_text_from_pdf_bytes(content)
    skills = extract_skills(text)
    entities = extract_profile_entities(text)

    return {
        "text": text,
        "skills": skills,
        "college": entities["college"],
        "degree": entities["degree"],
        "graduation_year": entities["graduation_year"],
    }
