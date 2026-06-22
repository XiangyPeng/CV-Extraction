
# CV-Extraction

This repository implements a local end-to-end resume parsing solution for a take-home case study. It covers text extraction, validation, transformation, and structured storage.

## Features

- Extract text from PDF resumes
- Use OpenAI API to generate structured JSON
- Fall back to local heuristics when OpenAI is unavailable
- Support rule-based fallback for diverse document layouts
- Validate fields and formats with Pydantic models
- Persist data locally in SQLite and export JSON files
- Provide a Streamlit demo UI for interactive preview

## Installation and Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

Create a `.env` file in the project root with your OpenAI credentials:

```env
OPENAI_API_KEY=sk-proj-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
DATABASE_URL=sqlite:///cv_extraction.db
JSON_OUTPUT_DIR=output
LOG_LEVEL=INFO
```

To get your API key:
1. Visit [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Create a new secret key
3. Copy and paste it into the `OPENAI_API_KEY` field

### 3. Run the Application

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## Docker

Make sure `.env` is configured first, then:

```bash
docker-compose up --build
```

## Project Structure

- `streamlit_app.py`: upload, parse, display, and save resumes
- `src/config.py`: environment and configuration
- `src/extractor.py`: PDF text extraction and AI parsing
- `src/models.py`: data models and field validation
- `src/database.py`: SQLite storage and JSON export
- `src/pipeline.py`: document processing pipeline
- `src/evaluation.py`: extraction accuracy and evaluation metrics
- `tests/`: automated tests
- `docs/`: architecture and usage documentation
- `sample_data/`: demo resumes using CV1-5

## Documentation

- Case study: `docs/case_study.md`
- Architecture: `docs/architecture.md`
- Prompt engineering: `docs/prompt_engineering.md`
- Evaluation guide: `docs/evaluation.md`

## Azure Mapping

| Local Component | Azure Production Equivalent |
|---|---|
| PDF files | Azure Blob Storage |
| OpenAI API | Azure OpenAI / Azure Cognitive Services |
| SQLite | Azure SQL Database / Azure Cosmos DB |
| JSON files | Azure Data Lake Storage |
| Streamlit | Azure App Service |

## Testing

```bash
python -m pytest -q
```
