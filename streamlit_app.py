
import tempfile
from pathlib import Path

import streamlit as st

from src.config import JSON_OUTPUT_DIR
from src.evaluation import evaluate_extraction, load_ground_truth, summarize_metrics
from src.database import init_db, list_resumes, save_resume, save_resume_json
from src.pipeline import process_document

st.set_page_config(page_title="CV-Extraction", layout="wide")
st.title("CV-Extraction")

init_db()

files = st.file_uploader(
    "Upload one or more PDF resumes",
    type=["pdf"],
    accept_multiple_files=True,
)

results = []
if files:
    progress = st.progress(0)
    for idx, file in enumerate(files, start=1):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            temp_path = tmp.name
        result = process_document(temp_path, save_db=False, save_json=False)
        result.source_file = file.name
        results.append(result)
        progress.progress(int(idx / len(files) * 100))


def _ground_truth_path_for(result_source_file: str) -> Path:
    sample_stem = Path(result_source_file).stem
    return Path("tests/ground_truth") / f"{sample_stem}_ground_truth.json"

if results:
    st.subheader("Parsing Results")
    summary_rows = []
    for result in results:
        if result.resume:
            summary_rows.append(
                {
                    "File": result.source_file,
                    "Name": result.resume.name,
                    "Email": result.resume.email,
                    "Phone": result.resume.phone,
                    "Confidence": f"{result.confidence:.2f}",
                    "Warnings": "; ".join(result.warnings) if result.warnings else "None",
                    "Errors": "; ".join(result.errors) if result.errors else "None",
                }
            )
        else:
            summary_rows.append(
                {
                    "File": result.source_file,
                    "Name": "Parse failed",
                    "Email": "Parse failed",
                    "Phone": "Parse failed",
                    "Confidence": "0.00",
                    "Warnings": "; ".join(result.warnings) if result.warnings else "None",
                    "Errors": "; ".join(result.errors) if result.errors else "Unknown error",
                }
            )
    st.table(summary_rows)

    evaluation_rows = []
    for result in results:
        truth_path = _ground_truth_path_for(result.source_file)
        if result.resume and truth_path.exists():
            truth = load_ground_truth(truth_path)
            metrics = evaluate_extraction(result, truth)
            evaluation_rows.append(
                {
                    "File": result.source_file,
                    "Overall": f"{metrics['overall']:.2f}",
                    "Name": f"{metrics['name']:.2f}",
                    "Email": f"{metrics['email']:.2f}",
                    "Phone": f"{metrics['phone']:.2f}",
                    "Skills": f"{metrics['skills']:.2f}",
                    "Education": f"{metrics['education']:.2f}",
                    "Experience": f"{metrics['experience']:.2f}",
                }
            )

    if evaluation_rows:
        st.subheader("Evaluation Against Ground Truth")
        st.caption("The page shows evaluation scores when a matching JSON file exists in tests/ground_truth.")
        st.dataframe(evaluation_rows, use_container_width=True)
        summary_metrics = summarize_metrics(
            [
                {
                    "overall": float(row["Overall"]),
                    "name": float(row["Name"]),
                    "email": float(row["Email"]),
                    "phone": float(row["Phone"]),
                    "skills": float(row["Skills"]),
                    "education": float(row["Education"]),
                    "experience": float(row["Experience"]),
                }
                for row in evaluation_rows
            ]
        )
        st.metric("Average Overall Score", f"{summary_metrics.get('overall', 0.0):.2f}")
    else:
        st.info(
            "No ground truth JSON found for the uploaded files. To see evaluation scores, add a matching file under tests/ground_truth/ like CV1_ground_truth.json."
        )

    with st.expander("View detailed JSON results"):
        for result in results:
            st.markdown(f"**{result.source_file}**")
            if result.resume:
                st.json(result.resume.model_dump())
            else:
                st.error("This document could not be parsed. Please make sure the PDF contains extractable text.")

    if st.button("Save all parsed results"):
        output_paths = []
        for result in results:
            if result.resume:
                save_resume(result.resume)
                path = save_resume_json(result.resume)
                output_paths.append(path)
        if output_paths:
            st.success(f"Saved {len(output_paths)} results. JSON output folder: {JSON_OUTPUT_DIR}")
        else:
            st.warning("No results available to save.")

st.markdown("---")

with st.expander("View saved resumes"):
    saved = list_resumes()
    if saved:
        st.dataframe(saved)
    else:
        st.info("No saved resumes yet.")

st.markdown(
    "This system uses `.env` configuration. Customize settings with `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`, `DATABASE_URL`, and `JSON_OUTPUT_DIR`."
)

st.markdown("---")

if Path("sample_data").exists():
    sample_files = list(Path("sample_data").glob("*.pdf"))
    if sample_files:
        st.info("The sample_data directory contains example PDF resumes for quick testing.")
    else:
        st.info("The sample_data directory currently has no example PDFs.")
else:
    st.info("The sample_data directory was not found.")
