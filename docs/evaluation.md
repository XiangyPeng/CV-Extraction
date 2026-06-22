# Extraction Evaluation and Quality Validation

## Purpose

Evaluate extraction accuracy and data quality, establishing systematic acceptance criteria.

## Evaluation Module

The project implements `src/evaluation.py`, which can be used to:

- load ground truth JSON
- compute field-level accuracy
- summarize batch metrics

## Metrics

- `name`: name match
- `email`: email match
- `phone`: phone match
- `skills`: skill list matching ratio
- `education`: education matching ratio
- `experience`: experience matching ratio
- `overall`: average field accuracy

## Data Quality Checks

If results are missing required fields or confidence is low, the data quality should be considered unacceptable and routed for manual review.

## Example Usage

```python
from pathlib import Path
from src.evaluation import load_ground_truth, evaluate_extraction

truth = load_ground_truth(Path("ground_truth/CV1.json"))
result = ...
metrics = evaluate_extraction(result, truth)
print(metrics)
```

## Ground Truth Format

Recommended ground truth JSON structure:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+49 170 1234567",
  "skills": ["Python", "SQL", "Machine Learning"],
  "education": ["MSc Computer Science"],
  "experience": ["Data Scientist at ExampleCorp"]
}
```

## Result Interpretation

- `overall` > 0.8: high-quality extraction
- `overall` 0.5-0.8: moderate quality, needs review
- `overall` < 0.5: low quality, consider improving rules or manual correction
