import streamlit as st
import pandas as pd
import tempfile
import requests
import re
from pathlib import Path

st.set_page_config(
    page_title="Assessment Client",
    layout="wide"
)

REQUIRED_COMPETENCY_COLUMNS = ["name", "description", "level_0", "level_1", "level_2", "level_3"]
REQUIRED_QA_COLUMNS = ["Email", "Вопрос", "Ответ участника", "Компетенции"]


def normalize_spaces(text: str) -> str:
    if text is None:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def drop_rows_with_nan(df: pd.DataFrame, required_cols, dataset_name: str) -> pd.DataFrame:
    missing_columns = [col for col in required_cols if col not in df.columns]
    if missing_columns:
        raise ValueError(f"{dataset_name}: отсутствуют обязательные колонки: {', '.join(missing_columns)}")

    rows_to_drop = []
    for idx, row in df.iterrows():
        nan_columns = [col for col in required_cols if pd.isna(row[col])]
        if nan_columns:
            rows_to_drop.append((idx, nan_columns))

    if not rows_to_drop:
        return df

    for idx, nan_columns in rows_to_drop:
        excel_row_number = idx + 2  # +2 to account for header row in Excel export
        st.warning(
            f"{dataset_name}: строка {excel_row_number} удалена из-за NaN в колонках: "
            + ", ".join(nan_columns)
        )

    cleaned_df = df.drop(index=[idx for idx, _ in rows_to_drop]).reset_index(drop=True)
    return cleaned_df


def validate_competency_data(df_competency: pd.DataFrame, df_qa: pd.DataFrame):
    errors = []

    if 'name' not in df_competency.columns:
        errors.append("В матрице компетенций отсутствует колонка 'name'.")
        matrix_names = pd.Series(dtype=str)
    else:
        matrix_names = df_competency['name'].fillna('').astype(str).map(normalize_spaces)

        comma_mask = matrix_names.str.contains(',', regex=False)
        if comma_mask.any():
            offending = matrix_names[comma_mask].unique().tolist()
            errors.append(
                "В матрице компетенций запрещены запятые в названии. Исправьте: "
                + ", ".join(offending[:5])
                + (" ..." if len(offending) > 5 else "")
            )

        parentheses_mask = matrix_names.str.contains(r'[()]', regex=True)
        if parentheses_mask.any():
            offending = matrix_names[parentheses_mask].unique().tolist()
            errors.append(
                "В матрице компетенций уберите текст в скобках из 'name'. Найдены: "
                + ", ".join(offending[:5])
                + (" ..." if len(offending) > 5 else "")
            )

        empty_mask = matrix_names.eq('')
        if empty_mask.any():
            errors.append("В матрице компетенций найдены пустые значения в колонке 'name'.")

    if 'Компетенции' not in df_qa.columns:
        errors.append("В таблице ответов отсутствует колонка 'Компетенции'.")
        qa_competencies_series = pd.Series(dtype=str)
    else:
        qa_competencies_series = df_qa['Компетенции'].fillna('').astype(str).map(normalize_spaces)

        qa_parentheses_mask = qa_competencies_series.str.contains(r'[()]', regex=True)
        if qa_parentheses_mask.any():
            offending_rows = df_qa.loc[qa_parentheses_mask, ['Email', 'Компетенции']]
            details = "; ".join(
                f"Email {row.get('Email', 'N/A')}: {row['Компетенции']}" for _, row in offending_rows.head(5).iterrows()
            )
            if len(offending_rows) > 5:
                details += " ..."
            errors.append(
                "Уберите текст в скобках в колонке 'Компетенции' таблицы ответов. Примеры: " + details
            )

    qa_competency_names = set()
    for value in qa_competencies_series:
        if not value:
            continue
        parts = [part.strip() for part in value.split(',') if part.strip()]
        qa_competency_names.update(parts)

    matrix_name_set = set(matrix_names[matrix_names != ''])

    missing_in_matrix = sorted(qa_competency_names - matrix_name_set)
    missing_in_qa = sorted(matrix_name_set - qa_competency_names)

    if missing_in_matrix:
        errors.append(
            "В таблице ответов найдены компетенции без соответствий в матрице: "
            + ", ".join(missing_in_matrix)
        )
    if missing_in_qa:
        errors.append(
            "В матрице компетенций есть названия, которых нет в таблице ответов: "
            + ", ".join(missing_in_qa)
        )

    if errors:
        raise ValueError("\n".join(errors))




def process_excel_files(file1, file2):
    """
    Process two Excel files and create JSON payloads for each email.
    
    Args:
        file1: First Excel file (competency matrix)
        file2: Second Excel file (questions and answers)
    
    Returns:
        List of tuples containing (email, json_payload)
    """
    # Save uploaded files to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save first file (competency matrix)
        file1_path = Path(temp_dir) / file1.name
        with open(file1_path, 'wb') as f:
            f.write(file1.getbuffer())
        
        # Save second file (questions and answers)
        file2_path = Path(temp_dir) / file2.name
        with open(file2_path, 'wb') as f:
            f.write(file2.getbuffer())
        
        # Read Excel files
        df_competency = pd.read_excel(file1_path)
        df_qa = pd.read_excel(file2_path)

        # Drop rows with NaN in required columns and inform the user
        df_competency = drop_rows_with_nan(df_competency, REQUIRED_COMPETENCY_COLUMNS, "Матрица компетенций")
        df_qa = drop_rows_with_nan(df_qa, REQUIRED_QA_COLUMNS, "Таблица ответов")

        validate_competency_data(df_competency, df_qa)

        # Group data by email
        results = []
        competency_matrix = []

        level_columns = [col for col in df_competency.columns if col.startswith('level_')]

        for _, row in df_competency.iterrows():
            normalized_name = normalize_spaces(row['name']) if 'name' in row else ''
            # Create competency with levels
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
  
                # Build JSON structure
                json_payload = {
                    "competency_matrix": competency_matrix,
                    "questions_and_answers": [],
                    "webhook_url": "https://ntfy.sh/assessment",
                    "user_email": email,
                    "user_name": email
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


def send_to_assessment_api(email, payload, api_url):
    """
    Send JSON payload to the assessment API.
    
    Args:
        email: Email address
        payload: JSON payload to send
        api_url: API endpoint URL
    
    Returns:
        Response object or error message
    """
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        return str(e)


def main():
    st.title("Assessment Client")
    st.write("Звгрузите два Excel файла для обработки и отправки данных на API оценки.")
    
    # Configuration section
    st.sidebar.header("Configuration")
    api_url = st.sidebar.selectbox(
        "Assessment API URL",
        options=[
            "https://evolveaiserver-production.up.railway.app/evaluate_open_assessments",
            "http://localhost:8000/evaluate_open_assessments",
            "Custom"
        ],
        index=0,
        help="Select the API endpoint URL"
    )
    if api_url == "Custom":
        api_url = st.sidebar.text_input(
            "Custom API URL",
            value="https://evolveaiserver-production.up.railway.app/evaluate_open_assessments",
            help="Enter the API endpoint URL"
        )
        
    # File upload section
    st.header("Загрузка файлов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Матрица компетенций")
        st.write("Ожидаемые столбцы:")
        st.write("[name, description, level_0, level_1, level_2, level_3]")
        st.caption("🚫 В колонке name нельзя использовать запятые или текст в скобках.")
        
        # Download example button
        example_file_path = Path("examples/matrix_example.xlsx")
        if not example_file_path.exists():
            example_file_path = Path("/app/examples/matrix_example.xlsx")
        if example_file_path.exists():
            with open(example_file_path, "rb") as f:
                st.download_button(
                    label="📥 Скачать пример",
                    data=f,
                    file_name="matrix_example.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        file1 = st.file_uploader(
            "Выберите Excel файл матрицы компетенций",
            type=['xlsx', 'xls'],
            key="file1"
        )
    
    with col2:
        st.subheader("Вопросы и ответы")
        st.write("Ожидаемые столбцы:")
        st.write("[Email, Вопрос, Ответ участника, Компетенции]")
        st.caption("🚫 В колонке 'Компетенции' не допускается текст в скобках.")
        
        # Download example button
        example_file_path = Path("examples/qa_example.xlsx")
        if not example_file_path.exists():
            example_file_path = Path("/app/examples/qa_example.xlsx")
        if example_file_path.exists():
            with open(example_file_path, "rb") as f:
                st.download_button(
                    label="📥 Скачать пример",
                    data=f,
                    file_name="qa_example.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        file2 = st.file_uploader(
            "Выберите Excel файл с вопросами и ответами",
            type=['xlsx', 'xls'],
            key="file2"
        )
    
    # Upload button
    if st.button("Отправить", type="primary"):
        if file1 is None or file2 is None:
            st.error("Пожалуйста, загрузите оба файла перед отправкой.")
        else:
            with st.spinner("Обработка файлов..."):
                try:
                    # Process the Excel files
                    results = process_excel_files(file1, file2)
                    
                    if not results:
                        st.warning("No data found to process. Please check that your Excel files have an 'email' column.")
                    else:
                        st.success(f"Found {len(results)} email(s) to process")
                        
                        # Send each payload to the API
                        progress_bar = st.progress(0)
                        status_container = st.container()
                        
                        for idx, (email, payload) in enumerate(results):
                            with status_container:
                                st.write(f"Processing email: {email}")
                                
                                # Show JSON payload in expander
                                with st.expander(f"View JSON for {email}"):
                                    st.json(payload)
                                
                                # Send to API
                                response = send_to_assessment_api(email, payload, api_url)
                                
                                if isinstance(response, str):
                                    # Error occurred
                                    st.error(f"Error for {email}: {response}")
                                else:
                                    # Check response status
                                    if response.status_code == 200:
                                        st.success(f"✅ Successfully sent data for {email}")
                                    else:
                                        st.warning(f"⚠️ API returned status {response.status_code} for {email}: {response.text}")
                            
                            # Update progress
                            progress_bar.progress((idx + 1) / len(results))
                        
                        st.balloons()
                        st.success("All emails processed!")
                
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")
                    st.exception(e)
    
    # Information section
    st.divider()
    st.header("How to Use")
    st.markdown("""
### 1. **Подготовьте Excel файлы:**.  
    - Файл 1 (Матрица компетенций): Должен содержать столбцы `name`, `description`, `level_0`, `level_1`, `level_2`, `level_3`
    - В колонке `name` **нельзя** использовать запятые, лишние пробелы и текст в круглых скобках
    - Дополнительные колонки игнорируются
    - Вся информация на первом листе Excel с первой строки
---
    - Файл 2 (Вопросы и ответы): Должен содержать столбцы `Email`, `Вопрос`, `Ответ участника`, `Компетенции`
    - В колонке `Компетенции` запрещён текст в скобках, значения перечисляются через `", "`
    - Информация на первом листе Excel
    - Наименование колонок строго, без пустых строк и объединённых ячеек

### 2. Получение результата:
       - [https://ntfy.sh/assessment](https://ntfy.sh/assessment)
    """)


if __name__ == "__main__":
    main()
