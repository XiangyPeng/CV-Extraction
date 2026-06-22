
from src.models import Resume


def test_resume_basic_validation():
    r = Resume(name="Alice Zhang", email="alice@example.com", phone="+86 138 0013 8000")
    assert r.name == "Alice Zhang"
    assert r.email == "alice@example.com"
    assert r.phone == "+8613800138000"
    assert isinstance(r.skills, list)


def test_resume_list_fields_normalized():
    r = Resume(
        name="Bob",
        email="bob@example.com",
        skills="Python, SQL; Data Analysis",
        education="BSc Computer Science\nMSc AI",
        experience=["Data Engineer", "Product Analyst"],
    )
    assert r.skills == ["Python", "SQL", "Data Analysis"]
    assert r.education == ["BSc Computer Science", "MSc AI"]
    assert r.experience == ["Data Engineer", "Product Analyst"]
