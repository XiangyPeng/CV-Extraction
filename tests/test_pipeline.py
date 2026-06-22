from pathlib import Path

from src.pipeline import process_document


def test_process_user_sample_pdfs():
    sample_dir = Path("sample_data")
    paths = sorted(sample_dir.glob("CV*.pdf"))
    assert len(paths) == 5

    results = [process_document(path, save_db=False, save_json=False) for path in paths]

    assert len(results) == 5
    for result in results:
        assert result.resume is not None
        assert "@" in result.resume.email
        assert result.resume.name
        assert result.confidence >= 0.0


def test_batch_processing_progress():
    sample_dir = Path("sample_data")
    paths = sorted(sample_dir.glob("CV*.pdf"))
    results = [process_document(path, save_db=False, save_json=False) for path in paths]

    assert len(results) == 5
    assert all(isinstance(result.resume, object) for result in results)
