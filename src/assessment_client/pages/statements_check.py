import streamlit as st
import pandas as pd
from pathlib import Path
from assessment_client.modules.api_client import send_to_assessment_api
from assessment_client.modules.config import EVAL_TYPE_KEYS
from assessment_client.modules.processing import process_statement_inputs


def transform_and_send(file1):
    with st.spinner("Обработка файлов..."):
        payloads = process_statement_inputs(
            file1=file1,
        )
        for data in payloads:
            response = send_to_assessment_api(
                api_url=st.session_state.get(
                    'api_url',
                    "https://evolveaiserver-production.up.railway.app/evaluate_statements_batch"
                ),
                payload=data
            )
        st.success("Данные успешно отправлены на API оценки.")


def render():
    st.title("Statements Check")
    st.write("Звгрузите Excel с вопросами и ответами")

    # Configuration section
    st.sidebar.header("Configuration")
    api_url = st.sidebar.selectbox(
        "Assessment API URL",
        options=[
            "https://evolveaiserver-production.up.railway.app/evaluate_statements_batch",
            "http://host.docker.internal:8000/evaluate_statements_batch",
            "Custom"
        ],
        index=0,
        help="Select the API endpoint URL"
    )
    if api_url == "Custom":
        api_url = st.sidebar.text_input(
            "Custom API URL",
            value="https://evolveaiserver-production.up.railway.app/statements_check",
            help="Enter the API endpoint URL"
        )
    
    # File upload section
    st.header("Загрузка файлов")
    st.subheader("Проверка утверждений")
    st.write("Ожидаемые столбцы:")
    st.write("[name, description, level_0, level_1, level_2, level_3]")
    st.caption("🚫 1 лист в эксель!")
    df = pd.read_excel("src/assessment_client/examples/statements_example.xlsx")
    st.dataframe(df.head(1))
    
    # Download example button
    example_file_path = Path("src/assessment_client/examples/statements_example.xlsx")
    if example_file_path.exists():
        with open(example_file_path, "rb") as f:
            st.download_button(
                label="📥 Скачать пример",
                data=f,
                file_name="statements_example.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    file1 = st.file_uploader(
        "Выберите Excel файл с утверждениями для проверки",
        type=['xlsx'],
        key="file1"
    )

    # Upload button
    if st.button("Отправить", type="primary"):
        if file1 is None:
            st.error("Пожалуйста, загрузите файл перед отправкой.")
        else:
            transform_and_send(file1=file1)

if __name__ == "__main__":
    render()
