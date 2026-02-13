import tempfile
from pathlib import Path
import asyncio
from typing import Dict, List

import pandas as pd
import json
import numpy as np

from assessment_client.modules.config import REQUIRED_COMPETENCY_COLUMNS, REQUIRED_QA_COLUMNS
from assessment_client.modules.validation import drop_rows_with_nan, normalize_spaces, clean_text


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


def process_competency_file(competency_file):
    """
    Process a competency matrix Excel file and return a list of Competency dicts.

    Each row in the spreadsheet represents one *indicator* that belongs to a
    competency.  Rows sharing the same ``competency`` value are grouped into a
    single Competency object whose ``indicators`` list contains all of them.

    Expected columns:
        competency, competency_description, weight,
        indicator_name, indicator_description,
        level_0, level_1, level_2, level_3

    Returns:
        List[dict] – one dict per unique competency, matching the
        ``Competency`` Pydantic model on the server.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        competency_path = Path(temp_dir) / competency_file.name
        with open(competency_path, 'wb') as f:
            f.write(competency_file.getbuffer())

        df_competency = pd.read_excel(competency_path)

    df_competency = drop_rows_with_nan(
        df_competency, REQUIRED_COMPETENCY_COLUMNS, "Матрица компетенций"
    )

    # Normalise key text columns
    df_competency["competency"] = (
        df_competency["competency"].fillna("").astype(str).map(normalize_spaces)
    )
    df_competency["competency_description"] = (
        df_competency["competency_description"].fillna("").astype(str).map(normalize_spaces)
    )

    level_columns = ["level_0", "level_1", "level_2", "level_3"]

    # Group rows by competency name to build nested structure
    competency_matrix = []
    seen_competencies: dict = {}  # name -> index in competency_matrix

    for _, row in df_competency.iterrows():
        comp_name = row["competency"]
        if not comp_name:
            continue

        # Build indicator entry
        indicator = {
            "name": normalize_spaces(str(row.get("indicator_name", ""))),
            "description": normalize_spaces(str(row.get("indicator_description", ""))),
            "levels": {
                lvl: str(row[lvl]).strip() if pd.notna(row.get(lvl)) else ""
                for lvl in level_columns
            },
        }

        if comp_name in seen_competencies:
            idx = seen_competencies[comp_name]
            competency_matrix[idx]["indicators"].append(indicator)
        else:
            weight_val = row.get("weight", 50.0)
            try:
                weight_val = float(weight_val)
            except (ValueError, TypeError):
                weight_val = 50.0

            competency = {
                "competency": comp_name,
                "competency_description": row["competency_description"],
                "weight": weight_val,
                "indicators": [indicator],
            }
            seen_competencies[comp_name] = len(competency_matrix)
            competency_matrix.append(competency)

    return competency_matrix


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
        'ФИО',
        'Email',
        'Название главы',
        'Название задания',
        'Дата отправки',
        'Ответ участника',
    ]
    df_answers_filtered = df1[cols_answers]

    cols_tasks = [
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


async def process_statement_inputs(df_statements_one_email) -> List[Dict]:
    """
    Process statements for a single email.
    
    Args:
        df_statements_one_email: DataFrame filtered for one email and 'Быстрая самооценка' chapter
    
    Returns:
        List of dicts matching StatementsData contract
    """
    statements = []
    for _, col in df_statements_one_email.iterrows():
        statement_request = dict(
            question=safe_value(col["Вопрос"], ""),
            eval_type=safe_value(col["Тип оценки"], ""),
            competency=safe_value(col["Компетенции"], ""),
            answer=safe_value(col["Ответ участника"], ""),
        )
        statements.append(statement_request)
    return statements

async def process_mini_case_inputs(df_mini_cases_one_email) -> List[Dict]:
    """
    Process mini cases for a single email.
    Args:
        df_mini_cases_one_email: DataFrame filtered for one email and 'Мини кейсы' chapter
    Returns:
        List of dicts matching MiniCase contract
    """
    mini_cases = []
    for _, col in df_mini_cases_one_email.iterrows():
        competencies_value = safe_value(col["Компетенции"], "")
        competencies_list = [c.strip() for c in str(competencies_value).split(',') if c.strip()] if competencies_value else []
        indicators_value = safe_value(col["Индикаторы"], "")
        indicators_list = [i.strip() for i in str(indicators_value).split(';\n') if i.strip()] if indicators_value else []

        mini_case = dict(
            mini_case=safe_value(col["Вопрос"], ""),
            competencies=competencies_list,
            indicators=indicators_list,
            answer=safe_value(col["Ответ участника"], ""),
        )
        mini_cases.append(mini_case)
    return mini_cases

async def process_big_case_inputs(df_big_cases_one_email) -> List[Dict]:
    """
    Process big cases for a single email.
    Args:
        df_big_cases_one_email: DataFrame filtered for one email and 'Большие кейсы' chapter
    Returns:
        List of dicts matching BigCase contract
    """
    big_cases = []
    for _, col in df_big_cases_one_email.iterrows():
        competencies_value = safe_value(col["Компетенции"], "")
        competencies_list = [c.strip() for c in str(competencies_value).split(',') if c.strip()] if competencies_value else []
        indicators_value = safe_value(col["Индикаторы"], "")
        indicators_list = [i.strip() for i in str(indicators_value).split(';\n') if i.strip()] if indicators_value else []

        big_case = dict(
            big_case=safe_value(col["Вопрос"], ""),
            competencies=competencies_list,
            indicators=indicators_list,
            answer=safe_value(col["Ответ участника"], ""),
        )
        big_cases.append(big_case)
    return big_cases

async def process_dilemma_inputs(df_dilemma_one_email) -> List[Dict]:
    """
    Process dilemmas for a single email.
    
    Args:
        df_dilemma_one_email: DataFrame filtered for one email and 'Дилеммы' chapter
    
    Returns:
        List of dicts matching DilemmasData contract
    """
    dilemmas = []
    for _, col in df_dilemma_one_email.iterrows():
        competencies_value = safe_value(col["Компетенции"], "")
        competencies_list = [c.strip() for c in str(competencies_value).split(',') if c.strip()] if competencies_value else []
        indicators_value = safe_value(col["Индикаторы"], "")
        indicators_list = [i.strip() for i in str(indicators_value).split(';\n') if i.strip()] if indicators_value else []

        dilemma_request = dict(
            dilemma=safe_value(col["Вопрос"], ""),
            competencies=competencies_list,
            indicators=indicators_list,
            answer=safe_value(col["Ответ участника"], ""),
        )
        dilemmas.append(dilemma_request)
    return dilemmas

async def process_open_question_inputs(df_open_one_email) -> List[Dict]:
    """
    Process open questions for a single email.
    Args:
        df_open_one_email: DataFrame filtered for one email and 'Открытые вопросы' chapter    
    Returns:
        List of dicts matching OpenQuestionsData contract
    """
    questions_and_answers = []
    for _, col in df_open_one_email.iterrows():
        competencies_value = safe_value(col["Компетенции"], "")
        competencies_list = [c.strip() for c in str(competencies_value).split(',') if c.strip()] if competencies_value else []
        indicators_value = safe_value(col["Индикаторы"], "")
        indicators_list = [i.strip() for i in str(indicators_value).split(';\n') if i.strip()] if indicators_value else []

        qa_entry = dict(
            question=safe_value(col["Вопрос"], ""),
            answer=safe_value(col["Ответ участника"], ""),
            competencies=competencies_list,
            indicators=indicators_list,
        )
        questions_and_answers.append(qa_entry)
    
    return questions_and_answers

async def process_all_inputs(participants_results_file, tasks_file, competency_file=None, assessment_info="", assessment_type="external") -> Dict[str, Dict]:
    """
    Process uploaded files and return CombinedAssessmentRequest payloads per email.
    
    Args:
        participants_results_file: Uploaded Excel file with raw data (sheet: "Результаты участников")
        tasks_file: Uploaded Excel file with task definitions
        competency_file: Optional uploaded Excel file with competency matrix
        assessment_info: Optional assessment context info
    
    Returns:
        Dict mapping email -> CombinedAssessmentRequest payload
    """
    # Merge dataframes from uploaded files
    df_merged = await df_from_files(participants_results_file, tasks_file)
    
    # Process competency file if provided
    competency_matrix = None
    if competency_file is not None:
        competency_matrix = process_competency_file(competency_file)
    
    # Split by email at the top level
    emails = df_merged["Email"].unique()
    all_payloads = {}
    
    for email in emails:
        # Filter data for this specific email
        df_one_email = df_merged[df_merged["Email"] == email]
        
        # Get user info from first row
        first_row = df_one_email.iloc[0]
        user_name = safe_value(first_row.get("ФИО"), email)
        position_title = safe_value(first_row.get("Позиция"), "")
        df_one_email["Название главы"] = df_one_email["Название главы"].fillna('').astype(str).map(normalize_spaces)
        df_one_email["Ответ участника"] = df_one_email["Ответ участника"].fillna('').astype(str).map(clean_text)
        
        # Prepare filtered dataframes for each task type
        df_statements = df_one_email[df_one_email['Название главы'] == 'Быстрая самооценка']
        df_open_questions = df_one_email[df_one_email['Название главы'] == 'Открытые вопросы']
        df_dilemmas = df_one_email[df_one_email['Название главы'] == 'Дилеммы']
        df_mini_cases = df_one_email[df_one_email['Название главы'] == 'Мини кейсы']
        df_big_cases = df_one_email[df_one_email['Название главы'] == 'Большие кейсы']

        # Build CombinedAssessmentRequest structure
        combined_request = {
            "user_email": email,
            "user_name": user_name,
            "position_title": position_title,
            "assessment_info": assessment_info,
            "webhook_url": "https://ntfy.sh/assessment",
            "competency_matrix": competency_matrix,
            "assessment_type": assessment_type,
            "open_questions": None,
            "statements": None,
            "dilemmas": None,
            "mini_cases": None,
            "big_cases": None,
        }
        
        # Process each task type
        if not df_statements.empty:
            statements_data = await process_statement_inputs(df_statements)
            combined_request["statements"] = statements_data
        
        if not df_dilemmas.empty:
            dilemmas_data = await process_dilemma_inputs(df_dilemmas)
            combined_request["dilemmas"] = dilemmas_data

        if not df_open_questions.empty:
            open_data = await process_open_question_inputs(df_open_questions)
            combined_request["open_questions"] = open_data

        if not df_mini_cases.empty:
            mini_cases_data = await process_mini_case_inputs(df_mini_cases)
            combined_request["mini_cases"] = mini_cases_data
        
        if not df_big_cases.empty:
            big_cases_data = await process_big_case_inputs(df_big_cases)
            combined_request["big_cases"] = big_cases_data
        
        all_payloads[email] = combined_request
        # break
    
    return all_payloads
