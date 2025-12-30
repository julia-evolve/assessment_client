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


async def df_from_files(participants_results_file, tasks_file):
    with tempfile.TemporaryDirectory() as temp_dir:
        participants_path = Path(temp_dir) / participants_results_file.name
        with open(participants_path, 'wb') as f:
            f.write(participants_results_file.getbuffer())

        df1 = pd.read_excel(participants_path, sheet_name="Результаты участников")

        tasks_path = Path(temp_dir) / tasks_file.name
        with open(tasks_path, 'wb') as f:
            f.write(tasks_file.getbuffer())

        df2 = pd.read_excel(tasks_path)

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
    df_tasks_filtered = df2[cols_tasks].copy()
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
        Dict with 'statements' list matching StatementsData contract
    """
    statements = []
    for _, col in df_statements_one_email.iterrows():
        statement_request = dict(
            id=safe_value(col["№"]),
            email=safe_value(col["Email"], ""),
            question=safe_value(col["Вопрос"], ""),
            eval_type=safe_value(col["Тип оценки"], ""),
            competency=safe_value(col["Компетенции"], ""),
            answer=safe_value(col["Ответ участника"], ""),
        )
        statements.append(statement_request)
    return {"statements": statements}

async def process_dilemma_inputs(df_dilemma_one_email):
    """
    Process dilemmas for a single email.
    
    Args:
        df_dilemma_one_email: DataFrame filtered for one email and 'Дилеммы' chapter
    
    Returns:
        Dict with 'dilemmas' list matching DilemmasData contract
    """
    dilemmas = []
    for _, col in df_dilemma_one_email.iterrows():
        dilemma_request = dict(
            id=str(safe_value(col["№"], "")),
            email=safe_value(col["Email"], ""),
            question=safe_value(col["Вопрос"], ""),
            competency=safe_value(col["Компетенции"], ""),
            indicators=safe_value(col["Индикаторы"], ""),
            answer=safe_value(col["Ответ участника"], ""),
        )
        dilemmas.append(dilemma_request)
    return {"dilemmas": dilemmas}

async def process_situation_inputs(df_situation_one_email):
    """
    Process situational cases for a single email.
    
    Args:
        df_situation_one_email: DataFrame filtered for one email and 'Ситуационные кейсы' chapter
    
    Returns:
        Dict with 'situations' list matching contract
    """
    situations = []
    for _, col in df_situation_one_email.iterrows():
        situation_request = dict(
            id=str(safe_value(col["№"], "")),
            email=safe_value(col["Email"], ""),
            question=safe_value(col["Вопрос"], ""),
            competency=safe_value(col["Компетенции"], ""),
            indicators=safe_value(col["Индикаторы"], ""),
            answer=safe_value(col["Ответ участника"], ""),
        )
        situations.append(situation_request)
    return {"situations": situations}

async def process_open_question_inputs(df_open_one_email, competency_matrix=None, assessment_type="external"):
    """
    Process open questions for a single email.
    
    Args:
        df_open_one_email: DataFrame filtered for one email and 'Открытые вопросы' chapter
        competency_matrix: List of competency dicts (optional)
        assessment_type: Type of assessment (default: "external")
    
    Returns:
        Dict with 'competency_matrix', 'questions_and_answers', 'assessment_type' matching OpenQuestionsData contract
    """
    questions_and_answers = []
    for _, col in df_open_one_email.iterrows():
        competencies_value = safe_value(col["Компетенции"], "")
        # Parse competencies as comma-separated list
        competencies_list = [c.strip() for c in str(competencies_value).split(',') if c.strip()] if competencies_value else []
        
        qa_entry = dict(
            question=safe_value(col["Вопрос"], ""),
            answer=safe_value(col["Ответ участника"], ""),
            competencies=competencies_list,
        )
        questions_and_answers.append(qa_entry)
    
    return {
        "competency_matrix": competency_matrix or [],
        "questions_and_answers": questions_and_answers,
        "assessment_type": assessment_type
    }

async def process_all_inputs(participants_results_file, tasks_file, competency_matrix=None, assessment_info=""):
    """
    Process uploaded files and return CombinedAssessmentRequest payloads per email.
    
    Args:
        participants_results_file: Uploaded Excel file with raw data (sheet: "Результаты участников")
        tasks_file: Uploaded Excel file with task definitions
        competency_matrix: Optional list of competency dicts for open questions
        assessment_info: Optional assessment context info
    
    Returns:
        Dict mapping email -> CombinedAssessmentRequest payload
    """
    # Merge dataframes from uploaded files
    df_merged = await df_from_files(participants_results_file, tasks_file)
    
    # Split by email at the top level
    emails = df_merged["Email"].unique()
    all_payloads = {}
    
    for email in emails:
        # Filter data for this specific email
        df_one_email = df_merged[df_merged["Email"] == email]
        
        # Get user info from first row
        first_row = df_one_email.iloc[0]
        user_name = safe_value(first_row.get("Имя"), email)
        position_title = safe_value(first_row.get("Позиция"), "")
        
        # Prepare filtered dataframes for each task type
        df_statements = df_one_email[df_one_email['Название главы'] == 'Быстрая самооценка']
        df_dilemmas = df_one_email[df_one_email['Название главы'] == 'Дилеммы']
        df_situations = df_one_email[df_one_email['Название главы'] == 'Ситуационные кейсы']
        df_open = df_one_email[df_one_email['Название главы'] == 'Открытые вопросы']
        
        # Build CombinedAssessmentRequest structure
        combined_request = {
            "user_email": email,
            "user_name": user_name,
            "position_title": position_title,
            "assessment_info": assessment_info,
            "webhook_url": "https://ntfy.sh/assessment",
            "open_questions": None,
            "statements": None,
            "dilemmas": None,
        }
        
        # Process each task type
        if not df_statements.empty:
            statements_data = await process_statement_inputs(df_statements)
            combined_request["statements"] = statements_data
        
        if not df_dilemmas.empty:
            dilemmas_data = await process_dilemma_inputs(df_dilemmas)
            combined_request["dilemmas"] = dilemmas_data
        
        if not df_situations.empty:
            situations_data = await process_situation_inputs(df_situations)
            # Situational cases can be treated as dilemmas or separate
            if combined_request["dilemmas"] is None:
                combined_request["dilemmas"] = {"dilemmas": []}
            combined_request["dilemmas"]["dilemmas"].extend(situations_data.get("situations", []))
        
        if not df_open.empty:
            open_data = await process_open_question_inputs(df_open, competency_matrix)
            combined_request["open_questions"] = open_data
        
        all_payloads[email] = combined_request
    
    return all_payloads
