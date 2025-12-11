import streamlit as st
from pathlib import Path

from modules.api_client import send_to_assessment_api
from modules.config import EVAL_TYPE_KEYS
from modules.processing import process_excel_files

st.set_page_config(
    page_title="Assessment Client",
    layout="wide"
)

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

    evaluation_type = st.selectbox(
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
        st.write("[Email, Name, Позиция, Вопрос, Ответ участника, Компетенции]")
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
                    results = process_excel_files(file1, file2, evaluation_type, assessment_info)
                    
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
    st.markdown("""
### 1. **Подготовьте Excel файлы:**.  
    - Файл 1 (Матрица компетенций): Должен содержать столбцы `name`, `description`, `level_0`, `level_1`, `level_2`, `level_3`
    - В колонке `name` **нельзя** использовать запятые, лишние пробелы и текст в круглых скобках
    - Дополнительные колонки игнорируются
    - Вся информация на первом листе Excel с первой строки
---
    - Файл 2 (Вопросы и ответы): Должен содержать столбцы `Email`, `Name`, `Позиция`, `Вопрос`, `Ответ участника`, `Компетенции`
    - В колонке `Компетенции` запрещён текст в скобках, значения перечисляются через `", "`
    - Информация на первом листе Excel
    - Наименование колонок строго, без пустых строк и объединённых ячеек

### 2. Получение результата:
       - [https://ntfy.sh/assessment](https://ntfy.sh/assessment)
    """)


if __name__ == "__main__":
    main()
