import tempfile
from pathlib import Path
import asyncio

import pandas as pd
import json
import numpy as np

from assessment_client.modules.config import REQUIRED_COMPETENCY_COLUMNS, REQUIRED_QA_COLUMNS
from assessment_client.modules.validation import drop_rows_with_nan, normalize_spaces, validate_competency_data


def safe_value(value, default=None):
    """
    Convert pandas/numpy values to JSON-safe values.
    Replaces NaN, inf, -inf with default value (None or empty string).
    
    Args:
        value: Value from pandas DataFrame
        default: Default value to return if value is NaN/inf
    
    Returns:
        JSON-safe value
    """
    if pd.isna(value):
        return default
    if isinstance(value, (float, np.floating)):
        if np.isinf(value):
            return default
    if isinstance(value, str) and value.strip() == '':
        return default if default is not None else ''
    return value


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

async def df_from_files(file1, file2):
    with tempfile.TemporaryDirectory() as temp_dir:
        file1_path = Path(temp_dir) / file1.name
        with open(file1_path, 'wb') as f:
            f.write(file1.getbuffer())

        df1 = pd.read_excel(file1_path, sheet_name="Результаты участников")

        file2_path = Path(temp_dir) / file2.name
        with open(file2_path, 'wb') as f:
            f.write(file2.getbuffer())

        df2 = pd.read_excel(file2_path)

    cols_answers = [
        'Имя',
        'Email',
        'Название главы',
        'Название задания',
        'Дата отправки',
        'Ответ участника',
    ]
    df_answers_filtered = df1[cols_answers]

    cols_tasks = [
        '№',
        'Название задания',
        'Вопрос',
        'Тип оценки',
        'Компетенции',
        'Индикаторы',
    ]

    missing_task_cols = [col for col in cols_tasks if col not in df2.columns]
    if missing_task_cols:
        raise ValueError(
            "The tasks Excel file is missing required column(s): "
            + ", ".join(missing_task_cols)
        )
    df_tasks_filtered = df2[cols_tasks]
    df_tasks_filtered.dropna(subset=["Название задания"], inplace=True)

    merged_df = pd.merge(df_answers_filtered, df_tasks_filtered, on="Название задания", how="inner")
    if merged_df.empty:
        raise ValueError(
            'Не удалось сопоставить задания между файлами: ни одно значение в столбце '
            '"Название задания" из листа "Результаты участников" не совпало со значениями '
            'в файле с заданиями. Проверьте, что названия заданий совпадают (учитывая пробелы, '
            'опечатки и регистр букв) в обоих файлах.'
        )
    return merged_df

async def process_statement_inputs(df_statements_one_email):
    """
    Process statements for a single email.
    
    Args:
        df_statements_one_email: DataFrame filtered for one email and 'Быстрая самооценка' chapter
    
    Returns:
        Dict with 'statements' list and 'webhook_url'
    """
    statements = []
    for _, col in df_statements_one_email.iterrows():
        statement_request = dict(
            question_number=safe_value(col["№"]),
            email=safe_value(col["Email"], ""),
            question=safe_value(col["Вопрос"], ""),
            question_type=safe_value(col["Тип оценки"], ""),
            competency=safe_value(col["Компетенции"], ""),
            participant_answer=safe_value(col["Ответ участника"], ""),
        )
        statements.append(statement_request)
    return {"statements": statements, "webhook_url": "https://ntfy.sh/assessment"}

async def process_dilemma_inputs(df_dilemma_one_email):
    """
    Process dilemmas for a single email.
    
    Args:
        df_dilemma_one_email: DataFrame filtered for one email and 'Дилеммы' chapter
    
    Returns:
        Dict with 'dilemmas' list and 'webhook_url'
    """
    dilemmas = []
    for _, col in df_dilemma_one_email.iterrows():
        dilemma_request = dict(
            question_number=str(safe_value(col["№"], "")),
            email=safe_value(col["Email"], ""),
            situation=safe_value(col["Название главы"], ""),
            question=safe_value(col["Название задания"], ""),
            competency=safe_value(col["Компетенции"], ""),
            indicators=safe_value(col["Индикаторы"], ""),
            participant_answer=safe_value(col["Ответ участника"], ""),
        )
        dilemmas.append(dilemma_request)
    return {"dilemmas": dilemmas, "webhook_url": "https://ntfy.sh/assessment"}

async def process_situation_inputs(df_situation_one_email):
    """
    Process situational cases for a single email.
    
    Args:
        df_situation_one_email: DataFrame filtered for one email and 'Ситуационные кейсы' chapter
    
    Returns:
        Dict with 'situations' list and 'webhook_url'
    """
    situations = []
    for _, col in df_situation_one_email.iterrows():
        situation_request = dict(
            question_number=str(safe_value(col["№"], "")),
            email=safe_value(col["Email"], ""),
            situation=safe_value(col["Название главы"], ""),
            question=safe_value(col["Название задания"], ""),
            competency=safe_value(col["Компетенции"], ""),
            indicators=safe_value(col["Индикаторы"], ""),
            participant_answer=safe_value(col["Ответ участника"], ""),
        )
        situations.append(situation_request)
    return {"situations": situations, "webhook_url": "https://ntfy.sh/assessment"}

async def process_open_question_inputs(df_open_one_email):
    """
    Process open questions for a single email.
    
    Args:
        df_open_one_email: DataFrame filtered for one email and 'Открытые вопросы' chapter
    
    Returns:
        Dict with 'open_questions' list and 'webhook_url'
    """
    open_questions = []
    for _, col in df_open_one_email.iterrows():
        open_question_request = dict(
            question_number=str(safe_value(col["№"], "")),
            email=safe_value(col["Email"], ""),
            situation=safe_value(col["Название главы"], ""),
            question=safe_value(col["Название задания"], ""),
            competency=safe_value(col["Компетенции"], ""),
            indicators=safe_value(col["Индикаторы"], ""),
            participant_answer=safe_value(col["Ответ участника"], ""),
        )
        open_questions.append(open_question_request)
    return {"open_questions": open_questions, "webhook_url": "https://ntfy.sh/assessment"}

async def process_all_inputs(file1, file2):
    """
    Process uploaded files and return combined payloads for all task types per email.
    
    Args:
        file1: Uploaded Excel file with raw data (sheet: "Результаты участников")
        file2: Uploaded Excel file with task definitions
    
    Returns:
        List of payload dicts ready to send to API (one payload per email per task type)
    """
    # Merge dataframes from uploaded files
    df_merged = await df_from_files(file1, file2)
    
    # Split by email at the top level
    emails = df_merged["Email"].unique()
    all_payloads = {}
    
    for email in emails:
        # Filter data for this specific email
        df_one_email = df_merged[df_merged["Email"] == email]
        
        # Prepare filtered dataframes for each task type
        df_statements = df_one_email[df_one_email['Название главы'] == 'Быстрая самооценка']
        df_dilemmas = df_one_email[df_one_email['Название главы'] == 'Дилеммы']
        df_situations = df_one_email[df_one_email['Название главы'] == 'Ситуационные кейсы']
        df_open = df_one_email[df_one_email['Название главы'] == 'Открытые вопросы']
        
        # Process each task type concurrently for this email
        tasks = []
        if not df_statements.empty:
            tasks.append(process_statement_inputs(df_statements))
        if not df_dilemmas.empty:
            tasks.append(process_dilemma_inputs(df_dilemmas))
        if not df_situations.empty:
            tasks.append(process_situation_inputs(df_situations))
        if not df_open.empty:
            tasks.append(process_open_question_inputs(df_open))
        
        # Gather results for this email
        if tasks:
            email_payloads = await asyncio.gather(*tasks)
            all_payloads[email] = email_payloads
    
    return all_payloads
