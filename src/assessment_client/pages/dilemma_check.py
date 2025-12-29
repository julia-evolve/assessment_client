import asyncio
import streamlit as st
import pandas as pd
from pathlib import Path
from assessment_client.modules.api_client import send_to_assessment_api
from assessment_client.modules.processing import df_from_files, process_dilemma_inputs


async def transform_and_send(file1, file2, api_url: str):
    with st.spinner("Обработка файлов..."):
        df = await df_from_files(file1, file2)
        
        # Filter for dilemmas chapter
        df_dilemmas = df[df['Название главы'] == 'Дилеммы']
        
        if df_dilemmas.empty:
            st.warning("Не найдено записей с главой 'Дилеммы'")
            return
        
        # Process each email separately
        emails = df_dilemmas["Email"].unique()
        all_payloads = []
        
        for email in emails:
            df_one_email = df_dilemmas[df_dilemmas["Email"] == email]
            payload = await process_dilemma_inputs(df_one_email)
            all_payloads.append(payload)
        
        # Send each payload to API
        for data in all_payloads:
            response = send_to_assessment_api(
                api_url=api_url,
                payload=data
            )
        st.success("Данные успешно отправлены на API оценки.")

def download_example_button(
        path: str, 
        file_name: str = "statements_example.xlsx",
        label: str = "📥 Скачать пример",
    ):
    example_file_path = Path(path)
    if example_file_path.exists():
        with open(example_file_path, "rb") as f:
            st.download_button(
                label=label,
                data=f,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


async def render():
    st.title("Dilemma Check")
    st.write("Загрузите Excel с вопросами и ответами")

    # Configuration section
    st.sidebar.header("Configuration")
    api_url = st.sidebar.selectbox(
        "Assessment API URL",
        options=[
            "https://evolveaiserver-production.up.railway.app/evaluate_dilemmas_batch",
            "http://host.docker.internal:8000/evaluate_dilemmas_batch",
            "Custom"
        ],
        index=0,
        help="Select the API endpoint URL"
    )
    if api_url == "Custom":
        api_url = st.sidebar.text_input(
            "Custom API URL",
            value="https://evolveaiserver-production.up.railway.app/evaluate_dilemmas_batch",
            help="Enter the API endpoint URL"
        )
    
    # File upload section
    st.header("Загрузка файлов")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Таблица дилеммами")
        download_example_button(
            "src/assessment_client/examples/stat_raw_example.xlsx",
            file_name="stat_raw_example.xlsx"
        )
        file1 = st.file_uploader(
            "Выберите Excel файл с утверждениями для проверки",
            type=['xlsx'],
            key="file1"
        )
    with col2:
        st.write("Таблица с расшифровкой компетенций")
        download_example_button(
            "src/assessment_client/examples/stat_logic_example.xlsx",
            file_name="stat_logic_example.xlsx"
        )
        file2 = st.file_uploader(
            "Выберите Excel файл с расшифровкой компетенций",
            type=['xlsx'],
            key="file2"
        )



    if st.button("Отправить", type="primary"):
        if file1 is None or file2 is None:
            st.error("Пожалуйста, загрузите оба файла перед отправкой.")
        else:
            await transform_and_send(file1=file1, file2=file2, api_url=api_url)

    st.markdown("---")
    st.markdown("## Инструкция по подготовке файлов")
    st.markdown("""
1. Файл с ответами должен содержать лист с названием `Результаты участников`. 
2. Файл с расшифровкой должен содержать только один лист
3. Колонки должны называться строго как в примерах (проверьте регистр и пробелы)
""")

if __name__ == "__main__":
    asyncio.run(render())