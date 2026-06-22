
```mermaid
flowchart LR
A[Resume PDF] --> B[PyMuPDF]
B --> C[OpenAI API]
C --> D[Pydantic Validation]
D --> E[SQLite]
D --> F[JSON]
F --> G[Streamlit UI]
```
