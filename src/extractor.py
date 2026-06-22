
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz

from .config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from .models import ExtractionResult, Resume

logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{6,}\d")
SECTION_HEADING = re.compile(r"^(experience|education|skills|work experience|education history|contact):?", re.I)
BASE_PROMPT = (
    "Extract resume data and return ONLY JSON with the exact keys: "
    "name, email, phone, skills, education, experience. "
    "Response must be valid JSON without markdown or explanatory text."
)


def _openai_client() -> Any:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise ValueError("openai package is not installed. Run `pip install -r requirements.txt`.") from exc
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def _clean_code_fence(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            return "\n".join(parts[1:-1]).strip()
    return text.strip()


def _normalize_text(text: str) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_line(text: str) -> str:
    cleaned = _normalize_text(text)
    return cleaned.strip(" •●*·-–—:")


def _parse_llm_response(response: Dict[str, Any]) -> Dict[str, Any]:
    content = response.get("message", {}).get("content")
    if isinstance(content, list):
        content = content[0]
    text = _clean_code_fence(str(content))
    return json.loads(text)


def _parse_openai_response(response: Any) -> Dict[str, Any]:
    content = response.choices[0].message.content
    text = _clean_code_fence(str(content))
    return json.loads(text)


def _find_email(text: str) -> Optional[str]:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def _find_phone(text: str) -> Optional[str]:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else None


def _looks_like_contact_line(text: str) -> bool:
    if EMAIL_RE.search(text) or PHONE_RE.search(text):
        return True
    keywords = [
        "email",
        "phone",
        "address",
        "location",
        "linkedin",
        "twitter",
        "homepage",
        "phone-alt",
        "envelope",
        "mailto",
        "map-marker",
        "citizen",
        "nationality",
        "skype",
    ]
    normalized = text.lower()
    return any(keyword in normalized for keyword in keywords)


def _is_section_heading(text: str) -> bool:
    normalized = text.lower().strip()
    if SECTION_HEADING.match(normalized):
        return True
    extras = [
        "about",
        "personal",
        "resume",
        "short res",
        "working experience",
        "work experience",
        "programming",
        "degrees",
        "curriculum",
        "areas of specialization",
        "specialization",
        "study",
        "languages",
        "publications",
        "awards",
        "interests",
        "certificates",
        "volunteer",
        "other activities",
        "activities",
        "projects",
        "education",
        "experience",
        "skills",
        "contact",
    ]
    return any(normalized.startswith(extra) for extra in extras)


def _looks_like_date_or_timeline(text: str) -> bool:
    normalized = text.lower()
    if re.search(r"\b(\d{4}|present|ongoing|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|summer|fall|winter|spring)\b", normalized):
        return True
    if "–" in normalized or "-" in normalized and re.search(r"\d{4}", normalized):
        return True
    return False


def _find_name(lines: List[str], email: Optional[str], phone: Optional[str]) -> str:
    candidates: List[str] = []
    for line in lines[:12]:
        cleaned = _clean_line(line)
        if not cleaned:
            continue
        if email and email in cleaned:
            continue
        if phone and phone in cleaned:
            continue
        if _looks_like_contact_line(cleaned):
            continue
        if _is_section_heading(cleaned):
            continue
        if ":" in cleaned:
            continue
        if any(symbol in cleaned for symbol in ["@", "(", ")", "www.", "http"]):
            continue
        if len(cleaned.split()) >= 2 and re.search(r"[A-Za-z\u4e00-\u9fff]", cleaned) and not _looks_like_date_or_timeline(cleaned):
            return cleaned
        candidates.append(cleaned)
    for candidate in candidates:
        if len(candidate.split()) >= 2 and not _looks_like_date_or_timeline(candidate):
            return candidate
    for candidate in candidates:
        if not _looks_like_date_or_timeline(candidate):
            return candidate
    return lines[0] if lines else "Unknown"


def _parse_list_value(text: str) -> List[str]:
    cleaned_text = _clean_line(text)
    items = re.split(r"[;,•●\n]+", cleaned_text)
    return [item.strip() for item in items if item.strip()]


def _extract_section(lines: List[str], titles: List[str]) -> List[str]:
    captured: List[str] = []
    active = False
    for line in lines:
        cleaned = _clean_line(line)
        normalized = cleaned.lower().strip()
        remainder = None
        for title in titles:
            title_lower = title.lower()
            if normalized == title_lower:
                remainder = ""
                break
            if normalized.startswith(title_lower + ":") or normalized.startswith(title_lower + "："):
                remainder = cleaned[len(title_lower) + 1 :].lstrip(" ")
                break
            if normalized.startswith(title_lower + " ") or normalized.startswith(title_lower + "-") or normalized.startswith(title_lower + "–"):
                remainder = cleaned[len(title_lower) :].lstrip(" :|-–—")
                break
        if remainder is not None:
            active = True
            if remainder:
                captured.append(remainder)
            continue
        if active and _is_section_heading(cleaned):
            break
        if active and cleaned:
            captured.append(cleaned)
    return captured


def _guess_skills(lines: List[str]) -> List[str]:
    skill_lines = _extract_section(
        lines,
        [
            "skills",
            "programming",
            "areas of specialization",
            "specialization",
        ],
    )
    skills: List[str] = []
    for line in skill_lines:
        if _looks_like_contact_line(line):
            continue
        skills.extend(_parse_list_value(line))
    if skills:
        return skills

    for line in lines[:20]:
        cleaned = _clean_line(line)
        if _looks_like_contact_line(cleaned):
            continue
        if "," in cleaned and re.search(r"[A-Za-z]", cleaned):
            parts = [item.strip() for item in cleaned.split(",") if item.strip()]
            if len(parts) >= 3 and all(len(part.split()) <= 4 for part in parts):
                return parts
    return []


def _estimate_confidence(resume: Resume, source: str) -> float:
    score = 0.2
    if resume.name:
        score += 0.2
    if resume.email:
        score += 0.2
    if resume.skills:
        score += 0.15
    if resume.education or resume.experience:
        score += 0.15
    if source == "llm":
        score += 0.1
    if not resume.phone:
        score -= 0.05
    return float(max(0.0, min(1.0, score)))


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in doc]
    return "\n".join(pages).strip()


def extract_resume_from_text(text: str) -> Resume:
    lines = [_clean_line(line) for line in text.splitlines() if _clean_line(line)]
    email = _find_email(text) or "unknown@example.com"
    phone = _find_phone(text)
    name = _find_name(lines, email, phone)
    skills = _guess_skills(lines)
    education = _extract_section(
        lines,
        ["education", "education:", "education history", "degrees", "study"],
    )
    experience = _extract_section(
        lines,
        [
            "experience",
            "experience:",
            "work experience",
            "working experience",
            "short resume",
            "short resumé",
        ],
    )
    return Resume(
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        education=education,
        experience=experience,
        raw_text=text,
    )


def extract_resume(pdf_path: str, model: str = OPENAI_MODEL) -> ExtractionResult:
    source_file = Path(pdf_path).name
    warnings: List[str] = []
    errors: List[str] = []

    try:
        text = extract_text(pdf_path)
    except Exception as exc:
        errors.append(f"PDF extraction failed: {exc}")
        logger.exception("PDF text extraction failed")
        return ExtractionResult(source_file=source_file, warnings=warnings, errors=errors)

    if not text:
        errors.append("PDF contains no extractable text.")
        return ExtractionResult(source_file=source_file, warnings=warnings, errors=errors)

    try:
        prompt = f"""
{BASE_PROMPT}

Resume content:\n{text}
"""
        response = _openai_client().chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": BASE_PROMPT},
                {"role": "user", "content": f"Resume content:\n{text}"},
            ],
        )
        data = _parse_openai_response(response)
        resume = Resume(**data, raw_text=text)
        source = "llm"
    except ValueError as exc:
        warnings.append("OPENAI_API_KEY is missing; using heuristic fallback.")
        logger.debug("OpenAI configuration failed: %s", exc)
        resume = extract_resume_from_text(text)
        source = "heuristic"
    except Exception as exc:
        warnings.append(f"OpenAI request failed for model {model}; using heuristic fallback.")
        logger.debug("OpenAI extraction failed: %s", exc)
        resume = extract_resume_from_text(text)
        source = "heuristic"

    resume.confidence = _estimate_confidence(resume, source)
    return ExtractionResult(
        source_file=source_file,
        resume=resume,
        confidence=resume.confidence,
        warnings=warnings,
        errors=errors,
    )
