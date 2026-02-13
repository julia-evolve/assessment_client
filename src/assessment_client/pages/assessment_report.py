import streamlit as st
import pandas as pd
from pathlib import Path
from assessment_client.modules.api_client import send_to_assessment_api
from assessment_client.modules.config import EVAL_TYPE_KEYS
from assessment_client.modules.processing import process_all_inputs
from assessment_client.modules.utils import download_example_button
import asyncio


async def render():
    st.title("Assessment Report")
    st.write("Звгрузите два Excel файла для обработки и отправки данных на API оценки.")
    
    # Configuration section
    st.sidebar.header("Configuration")
    api_url = st.sidebar.selectbox(
        "Assessment API URL",
        options=[
            "https://evolveaiserver-production.up.railway.app/evaluate_assessment",
            "http://host.docker.internal:8000/evaluate_assessment",
            "Custom"
        ],
        index=0,
        help="Select the API endpoint URL"
    )
    if api_url == "Custom":
        api_url = st.sidebar.text_input(
            "Custom API URL",
            value="https://evolveaiserver-production.up.railway.app/evaluate_assessment",
            help="Enter the API endpoint URL"
        )

    assessment_type = st.selectbox(
        "Тип оценки",
        options=EVAL_TYPE_KEYS,
        index=0,
        help="Выберите тип оценивания, соответствующий доступным evaluators"
    )

    assessment_info = st.text_area(
        "Общие данные про ассессмент",
        placeholder="Добавьте вводные, контекст, ссылки...",
        height=200
    )

    # File upload section
    st.header("Загрузка файлов")
    
    col1, col2 = st.columns(2)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Таблица c вопросами и ответами")
        download_example_button(
            "src/assessment_client/examples/answers.xlsx",
            file_name="answers.xlsx"
        )
        answers_file = st.file_uploader(
            "Выберите Excel файл с утверждениями для проверки",
            type=['xlsx'],
            key="answers_file"
        )
    with col2:
        st.write("Таблица с расшифровкой компетенций")
        download_example_button(
            "src/assessment_client/examples/logic.xlsx",
            file_name="logic.xlsx"
        )
        tasks_file = st.file_uploader(
            "Выберите Excel файл с расшифровкой компетенций",
            type=['xlsx'],
            key="tasks_file"
        )
    st.subheader("Матрица компетенций")
    st.caption("🚫 В колонке competency нельзя использовать запятые или текст в скобках.")
    
    download_example_button(
            "src/assessment_client/examples/matrix.xlsx",
            file_name="competency_matrix.xlsx"
        )
    competency_file = st.file_uploader(
            "Выберите Excel файл с матрицей компетенций",
            type=['xlsx'],
            key="competency_file"
        )
    # Upload button
    if st.button("Отправить", type="primary"):
        if answers_file is None or tasks_file is None or competency_file is None:
            st.error("Пожалуйста, загрузите все три файла перед отправкой.")
        else:
            with st.spinner("Обработка файлов..."):
                try:
                    # Process the Excel files
                    results = await process_all_inputs(
                        participants_results_file=answers_file,
                        tasks_file=tasks_file,
                        competency_file=competency_file,
                        assessment_info=assessment_info,
                        assessment_type=assessment_type
                    )
                    
                    if not results:
                        st.warning("No data found to process. Please check that your Excel files have an 'email' column.")
                    else:
                        st.success(f"Found {len(results)} email(s) to process")
                        
                        # Send each payload to the API
                        progress_bar = st.progress(0)
                        status_container = st.container()
                        
                        for idx, (email, payload) in enumerate(results.items()):
                            with status_container:
                                st.write(f"Processing email: {email}")
                                
                                # Show JSON payload in expander
                                with st.expander(f"View JSON for {email}"):
                                    st.json(payload)
                                
                                # Send to API
                                response = send_to_assessment_api(payload, api_url)
                                
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

    def load_columns_info(path: str) -> str:
        df = pd.read_excel(path)
        columns = df.columns.tolist()
        columns_to_code = list(map(lambda x: f"`{x}`", columns))
        columns_to_string = ", ".join(columns_to_code)
        return columns_to_string

    matrix_columns = load_columns_info("src/assessment_client/examples/matrix.xlsx")
    answers_columns = load_columns_info("src/assessment_client/examples/answers.xlsx")
    st.markdown(f"""
### 1. **Подготовьте Excel файлы:**
    - Файл 1 (Матрица компетенций): Должен содержать столбцы {matrix_columns}
    - В колонке `competency` **нельзя** использовать запятые, лишние пробелы и текст в круглых скобках
    - Несколько строк с одним и тем же `competency` группируются как индикаторы одной компетенции
    - Вся информация на первом листе Excel с первой строки
---
    - Файл 2 (Вопросы и ответы): Должен содержать столбцы {answers_columns}
    - В колонке `Компетенции` запрещён текст в скобках, значения перечисляются через `", "`
    - Информация на первом листе Excel
    - Наименование колонок строго, без пустых строк и объединённых ячеек

### 2. Получение результата:
[https://ntfy.sh/assessment](https://ntfy.sh/assessment)
""")


if __name__ == "__main__":
    # When Streamlit runs this file directly from the pages menu, render the page.
    asyncio.run(render())
