
import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from .config import DATABASE_URL, JSON_OUTPUT_DIR

engine = create_engine(DATABASE_URL, future=True)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")[:50]


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS resumes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            skills TEXT,
            education TEXT,
            experience TEXT,
            confidence REAL,
            raw_json TEXT NOT NULL,
            raw_text TEXT,
            created_at TEXT NOT NULL
        )
        """
            )
        )


def save_resume(resume) -> None:
    payload = json.dumps(resume.model_dump(), ensure_ascii=False)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
            INSERT INTO resumes(name,email,phone,skills,education,experience,confidence,raw_json,raw_text,created_at)
            VALUES(:name,:email,:phone,:skills,:education,:experience,:confidence,:raw_json,:raw_text,:created_at)
            """
            ),
            {
                "name": resume.name,
                "email": str(resume.email),
                "phone": resume.phone,
                "skills": json.dumps(resume.skills, ensure_ascii=False),
                "education": json.dumps(resume.education, ensure_ascii=False),
                "experience": json.dumps(resume.experience, ensure_ascii=False),
                "confidence": resume.confidence,
                "raw_json": payload,
                "raw_text": resume.raw_text,
                "created_at": datetime.utcnow().isoformat(),
            },
        )


def save_resume_json(resume, output_dir: str | Path = JSON_OUTPUT_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    name_slug = _slugify(resume.name or "resume")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = output_dir / f"{name_slug}_{timestamp}.json"
    with path.open("w", encoding="utf-8") as fp:
        json.dump(resume.model_dump(), fp, ensure_ascii=False, indent=2)
    return path


def list_resumes() -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT id, name, email, phone, skills, education, experience, confidence, created_at "
                "FROM resumes ORDER BY created_at DESC"
            )
        )
        rows = result.mappings().all()
    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "skills": json.loads(row["skills"]) if row["skills"] else [],
                "education": json.loads(row["education"]) if row["education"] else [],
                "experience": json.loads(row["experience"]) if row["experience"] else [],
                "confidence": row["confidence"],
                "created_at": row["created_at"],
            }
        )
    return items
