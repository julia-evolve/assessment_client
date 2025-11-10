# Assessment Client

A Streamlit-based web application for uploading Excel files containing competency matrices and questions/answers, then sending formatted JSON data to an assessment API.

## Features

- **Drag-and-drop Excel file upload** for two files:
  - Competency Matrix (columns: email, competency, description)
  - Questions & Answers (columns: email, question, answer, competency)
- **Automatic JSON generation** for each email in the dataset
- **API integration** to send assessment data to a configurable endpoint
- **Progress tracking** and status reporting for each email processed
- **Dockerized** for easy deployment

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/julia-evolve/assessment_client.git
cd assessment_client
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

### Docker Setup

1. Build the Docker image:
```bash
docker build -t assessment-client .
```

2. Run the container:
```bash
docker run -p 8501:8501 assessment-client
```

3. Open your browser to `http://localhost:8501`

## Usage

1. **Prepare Excel Files:**
   - **File 1 (Competency Matrix):** Must contain columns `email`, `competency`, `description`
   - **File 2 (Questions & Answers):** Must contain columns `email`, `question`, `answer`, `competency`

2. **Upload Files:**
   - Use the drag-and-drop interface or browse to select your Excel files
   - Both files must be uploaded before processing

3. **Configure API Endpoint** (optional):
   - Use the sidebar to modify the API URL (default: `https://example:8000/assessment`)

4. **Process and Upload:**
   - Click the "Upload and Process" button
   - The app will process each unique email from the competency matrix
   - For each email, it creates a JSON payload and sends it to the API

## JSON Format

For each email, the application generates JSON in the following format:

```json
{
  "competency_matrix": [
    {
      "competency": "Python Programming",
      "description": "Ability to write Python code"
    }
  ],
  "questions_and_answers": [
    {
      "question": "What is your experience with Python?",
      "answer": "5 years of professional experience",
      "competency": "Python Programming"
    }
  ]
}
```

## Excel File Examples

### Competency Matrix (File 1)
| email | competency | description |
|-------|------------|-------------|
| user@example.com | Python | Advanced Python skills |
| user@example.com | SQL | Database querying |

### Questions & Answers (File 2)
| email | question | answer | competency |
|-------|----------|--------|------------|
| user@example.com | Describe your Python experience | 5 years | Python |
| user@example.com | SQL knowledge? | Expert level | SQL |

## API Endpoint

The application sends POST requests to the configured API endpoint with the JSON payload. The default endpoint is `https://example:8000/assessment`.

**Request Format:**
- Method: POST
- Headers: `Content-Type: application/json`
- Body: JSON payload as described above

## Requirements

- Python 3.11+
- streamlit==1.28.1
- pandas==2.1.3
- openpyxl==3.1.2
- requests==2.31.0

## License

MIT