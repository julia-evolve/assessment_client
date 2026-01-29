# Copilot Instructions for Assessment Client

## Project Overview
Streamlit-based web client for employee competency assessments. Uploads Excel files containing competency matrices and Q&A data, transforms them into JSON payloads, and sends to an external assessment API (`evolveaiserver`).

## Architecture

```
src/assessment_client/
├── app.py              # Main Streamlit entry point, page routing
├── pages/              # Streamlit page components (UI + orchestration)
│   ├── matrix_competencies.py  # Form to request competency matrix generation
│   └── assessment_report.py    # Upload Excel files → process → send to API
├── modules/            # Shared business logic (import from pages)
│   ├── api_client.py   # HTTP requests to assessment API
│   ├── config.py       # Constants, enums (REQUIRED_*_COLUMNS, EVAL_TYPE_KEYS)
│   ├── processing.py   # Excel→DataFrame→JSON transformation
│   ├── validation.py   # Data validation, normalize_spaces(), cross-file checks
│   └── utils.py        # UI helpers (download_example_button)
└── examples/           # Sample Excel files for users to download
```

## Key Conventions

### Streamlit Pages Pattern
- Each page in `pages/` exports a `render()` function (can be `async`)
- Pages handle UI and orchestration; delegate logic to `modules/`
- Use `st.session_state` for form state persistence
- Sidebar for API configuration, main area for forms/uploads

### Data Flow
1. User uploads Excel files → `process_*` functions in `processing.py`
2. Validation via `validation.py` (normalize text, check required columns)
3. Transform to JSON payload matching API contract
4. Send via `send_to_assessment_api()` in `api_client.py`

### Text Normalization (Critical)
Always use `normalize_spaces()` from `validation.py` on user input:
```python
from assessment_client.modules.validation import normalize_spaces
normalized = normalize_spaces(text)  # Collapses whitespace, strips edges
```

### Required Excel Columns (from config.py)
- **Competency Matrix**: `name`, `description`, `level_0`, `level_1`, `level_2`, `level_3`
- **Q&A File**: `Email`, `Name`, `Позиция`, `Вопрос`, `Ответ участника`, `Компетенции`
- Naming restrictions: No commas or parentheses in competency names

## Development Commands

```bash
# Run locally
streamlit run src/assessment_client/app.py

# Run with Docker
docker-compose up --build        # Development with volume mount
docker build -t assessment-client . && docker run -p 8501:8501 assessment-client

# Run tests
pytest tests/
```

## API Integration
- Default endpoint: `https://evolveaiserver-production.up.railway.app/`
- Two main endpoints: `/competencies_matrix`, `/evaluate_assessment`
- Timeout: 120 seconds (long-running AI processing)
- Notification webhook: `https://ntfy.sh/assessment`

## Language
- UI text is in **Russian**
- Code (variables, functions, comments) in **English**
- Keep this convention when adding features

## Testing
- Tests import from `src.assessment_client.*` (note the `src` prefix)
- Test fixtures use Excel files from `tests/examples/`
- Validation tests check parentheses/comma restrictions in competency names
