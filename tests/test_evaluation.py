"""
Test evaluation module integration.
Validates that extracted resume data can be compared against ground truth.
"""
from pathlib import Path

from src.evaluation import evaluate_extraction, load_ground_truth, score_field
from src.pipeline import process_document


def test_load_ground_truth():
    """Test loading ground truth JSON file."""
    truth_path = Path("tests/ground_truth/CV1_ground_truth.json")
    truth = load_ground_truth(truth_path)

    assert truth["name"] == "Sample Candidate"
    assert truth["email"] == "candidate@example.com"
    assert truth["phone"] == "5550100"  # Phone format: cleaned digits only
    assert isinstance(truth["skills"], list)
    assert len(truth["skills"]) > 0


def test_score_field_exact_match():
    """Test exact string matching."""
    score = score_field("John Doe", "John Doe")
    assert score == 1.0


def test_score_field_no_match():
    """Test complete mismatch."""
    score = score_field("Jane Doe", "John Doe")
    assert score == 0.0


def test_score_field_list_partial_match():
    """Test partial list matching."""
    predicted = ["Python", "JavaScript", "Go"]
    truth = ["Python", "JavaScript"]
    score = score_field(predicted, truth)
    assert score == 1.0  # Both skills in predicted

    predicted = ["Python"]
    truth = ["Python", "JavaScript"]
    score = score_field(predicted, truth)
    assert score == 0.5  # Only 1 of 2 skills matched


def test_evaluate_extraction_against_ground_truth():
    """Test full evaluation workflow: extract CV and compare against ground truth."""
    sample_cv = Path("sample_data/CV1.pdf")
    truth_path = Path("tests/ground_truth/CV1_ground_truth.json")

    # Extract resume from sample CV
    result = process_document(sample_cv, save_db=False, save_json=False)
    assert result.resume is not None

    # Load ground truth
    truth = load_ground_truth(truth_path)

    # Evaluate extracted data against ground truth
    metrics = evaluate_extraction(result, truth)

    # Validate metrics structure and ranges
    assert "overall" in metrics
    assert all(key in metrics for key in ["name", "email", "phone", "skills", "education", "experience"])
    assert all(0.0 <= score <= 1.0 for score in metrics.values())

    # Overall score should exist and be reasonable
    assert metrics["overall"] >= 0.0
    assert metrics["overall"] <= 1.0


def test_evaluation_with_perfect_extraction():
    """Test evaluation when extraction perfectly matches ground truth."""
    from src.models import Resume, ExtractionResult

    # Create a resume that exactly matches ground truth
    extracted_resume = Resume(
        name="Sample Candidate",
        email="candidate@example.com",
        phone="5550100",
        skills=["Python", "Machine Learning", "Data Analysis"],
        education=["Bachelor of Science in Computer Science"],
        experience=["Senior Software Engineer", "Data Scientist"],
        raw_text="sample text",
        confidence=0.95,
    )

    result = ExtractionResult(
        resume=extracted_resume,
        source_file="test.pdf",
        confidence=0.95,
        warnings=[],
        errors=[],
    )

    truth_path = Path("tests/ground_truth/CV1_ground_truth.json")
    truth = load_ground_truth(truth_path)

    metrics = evaluate_extraction(result, truth)

    # Verify high accuracy on all fields when perfectly matched
    assert metrics["overall"] > 0.8  # Overall score should be high
    assert metrics["name"] == 1.0
    assert metrics["email"] == 1.0
    assert metrics["phone"] == 1.0
    assert metrics["skills"] == 1.0  # All skills match
    assert metrics["education"] == 1.0
    assert metrics["experience"] == 1.0
