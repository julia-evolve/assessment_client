import tempfile
from pathlib import Path

import pandas as pd

from assessment_client.modules.config import REQUIRED_COMPETENCY_COLUMNS, REQUIRED_QA_COLUMNS
from assessment_client.modules.validation import drop_rows_with_nan, normalize_spaces, validate_competency_data
from assessment_client.modules.data_models import StatementRequest


def process_excel_files(file1, file2, evaluation_type: str, assessment_info: str | None = None):
    """
    Process two Excel files and create JSON payloads for each email.

    Args:
        file1: First Excel file (competency matrix)
        file2: Second Excel file (questions and answers)
        evaluation_type: Selected evaluator key that should be forwarded to the API
        assessment_info: Optional free-text assessment context to send alongside payload

    Returns:
        List of tuples containing (email, json_payload)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        file1_path = Path(temp_dir) / file1.name
        with open(file1_path, 'wb') as f:
            f.write(file1.getbuffer())

        file2_path = Path(temp_dir) / file2.name
        with open(file2_path, 'wb') as f:
            f.write(file2.getbuffer())

        df_competency = pd.read_excel(file1_path)
        df_qa = pd.read_excel(file2_path)

        df_competency = drop_rows_with_nan(df_competency, REQUIRED_COMPETENCY_COLUMNS, "Матрица компетенций")
        df_qa = drop_rows_with_nan(df_qa, REQUIRED_QA_COLUMNS, "Таблица ответов")

        validate_competency_data(df_competency, df_qa)

        results = []
        competency_matrix = []

        level_columns = [col for col in df_competency.columns if col.startswith('level_')]

        for _, row in df_competency.iterrows():
            normalized_name = normalize_spaces(row['name']) if 'name' in row else ''
            competency = {
                "name": normalized_name,
                "description": str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                "levels": []
            }

            for level_col in level_columns:
                if level_col in row and pd.notna(row[level_col]) and str(row[level_col]).strip():
                    competency["levels"].append({
                        "name": level_col,
                        "description": str(row[level_col]).strip()
                    })

            competency_matrix.append(competency)

        if 'Email' in df_qa.columns:
            emails = df_qa['Email'].unique()

            for email in emails:
                one_student = df_qa[df_qa['Email'] == email]

                json_payload = {
                    "competency_matrix": competency_matrix,
                    "questions_and_answers": [],
                    "webhook_url": "https://ntfy.sh/assessment",
                    "evaluation_type": evaluation_type,
                    "assessment_info": assessment_info or "",
                    "user_email": email,
                    "user_name": one_student['Name'].iloc[0] if 'Name' in one_student.columns else email,
                    "position_title": one_student['Позиция'].iloc[0] if 'Позиция' in one_student.columns else "",
                }

                for _, row in one_student.iterrows():
                    qa_entry = {}
                    if 'Вопрос' in row:
                        qa_entry['question'] = str(row['Вопрос'])
                    if 'Ответ участника' in row:
                        qa_entry['answer'] = str(row['Ответ участника'])
                    if 'Компетенции' in row:
                        competencies_value = normalize_spaces(row['Компетенции'])
                        qa_entry['competencies'] = [part.strip() for part in competencies_value.split(',') if part.strip()]

                    if qa_entry:
                        json_payload["questions_and_answers"].append(qa_entry)

                results.append((email, json_payload))

        return results


def process_statement_inputs(file1):
    """
    Process a single Excel file containing statements.

    Args:
        file1: Excel file with statements

    Returns:
        List of statements
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        file1_path = Path(temp_dir) / file1.name
        with open(file1_path, 'wb') as f:
            f.write(file1.getbuffer())

        df_statements = pd.read_excel(file1_path)

    emails = df_statements["Email"].unique()
    payloads = []
    for email in emails:
        statements = []
        one_student = df_statements[df_statements["Email"] == email]
        for row, col in one_student.iterrows():
            statement_request = dict(
                question_number = col["№"],
                email=col["Email"],
                question=col["Вопрос"],
                question_type=col["П\О"],
                competency=col["Компетенции"],
                participant_answer=col["Ответ участника"],
            )
            statements.append(statement_request)
        payloads.append({"statements": statements, "webhook_url": "https://ntfy.sh/assessment"})
    return payloads
