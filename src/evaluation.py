import json
from pathlib import Path
from typing import Any

from .models import ExtractionResult


def load_ground_truth(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def score_field(predicted: Any, truth: Any) -> float:
    if predicted == truth:
        return 1.0
    if isinstance(predicted, list) and isinstance(truth, list):
        matched = sum(1 for item in truth if item in predicted)
        return matched / max(len(truth), 1)
    return 0.0


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
