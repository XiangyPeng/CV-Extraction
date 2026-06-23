import ast
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .models import ExtractionResult

KEY_ALIASES = {
    "duration": "years",
    "responsibilities": "description",
}


def load_ground_truth(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _normalize_text(value: str) -> str:
    # NFKC helps unify visually similar unicode forms, e.g. ligatures in PDFs.
    normalized = unicodedata.normalize("NFKC", value).lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _parse_structured_string(value: str) -> Any:
    text = value.strip()
    if not text:
        return text
    if not ((text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]"))):
        return value
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return value


def _normalize_key(key: str) -> str:
    key = _normalize_text(key)
    return KEY_ALIASES.get(key, key)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        parsed = _parse_structured_string(value)
        if parsed is not value:
            return _canonicalize(parsed)
        return _normalize_text(value)

    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            normalized[_normalize_key(str(key))] = _canonicalize(item)
        return normalized

    if isinstance(value, list):
        return [_canonicalize(item) for item in value]

    if value is None:
        return None

    if isinstance(value, (int, float, bool)):
        return value

    return _normalize_text(str(value))


def _flatten_tokens(value: Any) -> set[str]:
    if value is None:
        return set()

    if isinstance(value, str):
        return set(re.findall(r"[a-z0-9]+", value))

    if isinstance(value, dict):
        tokens: set[str] = set()
        for key, item in value.items():
            tokens.update(_flatten_tokens(str(key)))
            tokens.update(_flatten_tokens(item))
        return tokens

    if isinstance(value, list):
        tokens: set[str] = set()
        for item in value:
            tokens.update(_flatten_tokens(item))
        return tokens

    return _flatten_tokens(str(value))


def _token_overlap_score(predicted: Any, truth: Any) -> float:
    truth_tokens = _flatten_tokens(truth)
    if not truth_tokens:
        return 1.0
    predicted_tokens = _flatten_tokens(predicted)
    return len(predicted_tokens & truth_tokens) / len(truth_tokens)


def _value_similarity(predicted: Any, truth: Any) -> float:
    if predicted == truth:
        return 1.0

    if isinstance(predicted, dict) and isinstance(truth, dict):
        keys = set(predicted.keys()) | set(truth.keys())
        if not keys:
            return 1.0
        scores = []
        for key in keys:
            if key not in predicted or key not in truth:
                scores.append(0.0)
            else:
                scores.append(_value_similarity(predicted[key], truth[key]))
        return sum(scores) / len(scores)

    if isinstance(predicted, list) and isinstance(truth, list):
        return _list_similarity(predicted, truth)

    if isinstance(predicted, str) and isinstance(truth, str):
        ratio = SequenceMatcher(None, predicted, truth).ratio()
        return ratio if ratio >= 0.85 else 0.0

    if isinstance(predicted, (dict, list)) or isinstance(truth, (dict, list)):
        return _token_overlap_score(predicted, truth)

    return 0.0


def _list_similarity(predicted: list[Any], truth: list[Any]) -> float:
    if not truth:
        return 1.0
    if not predicted:
        return 0.0

    used_predicted: set[int] = set()
    matched_scores: list[float] = []

    for truth_item in truth:
        best_index = -1
        best_score = 0.0
        for index, predicted_item in enumerate(predicted):
            if index in used_predicted:
                continue
            score = _value_similarity(predicted_item, truth_item)
            if score > best_score:
                best_score = score
                best_index = index

        if best_index >= 0:
            used_predicted.add(best_index)
            matched_scores.append(best_score)
        else:
            matched_scores.append(0.0)

    return sum(matched_scores) / len(truth)


def score_field(predicted: Any, truth: Any) -> float:
    predicted_normalized = _canonicalize(predicted)
    truth_normalized = _canonicalize(truth)
    return _value_similarity(predicted_normalized, truth_normalized)


def evaluate_extraction(result: ExtractionResult, truth: dict[str, Any]) -> dict[str, float]:
    if result.resume is None:
        return {"overall": 0.0, "name": 0.0, "email": 0.0, "phone": 0.0, "skills": 0.0, "education": 0.0, "experience": 0.0}

    resume = result.resume
    name_score = score_field(resume.name, truth.get("name"))
    email_score = score_field(str(resume.email), truth.get("email"))
    phone_score = score_field(resume.phone or "", truth.get("phone"))
    skills_score = score_field(resume.skills, truth.get("skills", []))
    education_score = score_field(resume.education, truth.get("education", []))
    experience_score = score_field(resume.experience, truth.get("experience", []))
    overall = (name_score + email_score + phone_score + skills_score + education_score + experience_score) / 6.0
    return {
        "overall": overall,
        "name": name_score,
        "email": email_score,
        "phone": phone_score,
        "skills": skills_score,
        "education": education_score,
        "experience": experience_score,
    }


def summarize_metrics(metrics_list: list[dict[str, float]]) -> dict[str, float]:
    if not metrics_list:
        return {}
    keys = metrics_list[0].keys()
    summary = {key: sum(m[key] for m in metrics_list) / len(metrics_list) for key in keys}
    return summary
