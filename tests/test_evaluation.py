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

    assert truth["name"] == "John Snow"
    assert truth["email"] == "me@myself.me"
    assert truth["phone"] == "+0123456789"
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


def test_score_field_structured_aliases_not_zero():
    """Structured strings with key aliases should receive non-zero score."""
    predicted = [
        "{'title': 'Intern', 'duration': '2020', 'responsibilities': ['Built APIs']}"
    ]
    truth = [
        "{'title': 'Intern', 'years': '2020', 'description': ['Built APIs']}"
    ]

    score = score_field(predicted, truth)
    assert score > 0.0


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
        name="John Snow",
        email="me@myself.me",
        phone="+0123456789",
        skills=[
            "Pizza",
            "Chocolate",
            "Spacecrafts",
            "Star wars",
            "Narcos",
            "Team work",
            "Hard work",
            "Any softskill",
            "Programming lang",
        ],
        education=[
            "{'degree': 'M.Sc. Snack Science', 'institution': 'University of Nowhere', 'years': '2019 – 2021 (expected)', 'details': ['Curriculum Cocoa and derivatives', 'Current GPA: 3.5']}",
            "{'degree': 'B.Sc. Snack Science', 'institution': 'University of Nowhere', 'years': '2016 – 2019', 'details': ['Final grade: the highest!', 'GPA: 3', \"Thesis: 'Pizza is the best: a comparative analysis'\"]}"
        ],
        experience=[
            "{'title': 'Another Summer Internship', 'company': 'Yet another best place in the world', 'years': 'Jul – Sep 2019 (10 weeks)', 'location': 'Kangaroo island, Australia', 'description': ['Saw many many animals', 'Increased by animal knowledge by 100% by getting to know the best jumping animals in the whole world.']}",
            "{'title': 'Summer Internship', 'company': 'The best place in the world', 'years': 'Jul – Sep 2019 (10 weeks)', 'location': 'Pisa, Italy', 'description': ['Studied how leaned is the leaning tower', 'Increased tower leaning by 0.00001% by climbing on it using my climbing skills (I have proﬁciency).', 'IRL, this section should be bigger but I’m out of fantasy']}"
        ],
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
