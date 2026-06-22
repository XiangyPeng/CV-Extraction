from pathlib import Path
from typing import Iterable

from .database import save_resume, save_resume_json
from .extractor import extract_resume
from .models import ExtractionResult


def process_document(pdf_path: str | Path, save_db: bool = False, save_json: bool = False) -> ExtractionResult:
    result = extract_resume(str(pdf_path))
    if result.resume:
        if save_db:
            save_resume(result.resume)
        if save_json:
            save_resume_json(result.resume)
    return result


def process_documents(paths: Iterable[str | Path], save_db: bool = False, save_json: bool = False) -> list[ExtractionResult]:
    return [process_document(path, save_db=save_db, save_json=save_json) for path in paths]
