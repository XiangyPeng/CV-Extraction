from src.extractor import extract_resume_from_text


def test_extract_resume_from_sample_text():
    sample = """
John Doe
john@example.com
Python, Machine Learning, SQL

Experience:
Data Scientist

Education:
MSc Computer Science
"""
    resume = extract_resume_from_text(sample)

    assert resume.name == "John Doe"
    assert resume.email == "john@example.com"
    assert resume.skills == ["Python", "Machine Learning", "SQL"]
    assert resume.experience == ["Data Scientist"]
    assert resume.education == ["MSc Computer Science"]
