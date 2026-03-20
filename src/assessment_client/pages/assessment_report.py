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
    st.write("Загрузите два Excel файла для обработки и отправки данных на API оценки.")
    
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

    if assessment_type == "external":
        st.info(
            "Допустимые ответы: Полностью согласен, Скорее согласен, "
            "Затрудняюсь ответить, Скорее не согласен, Полностью не согласен"
        )
    elif assessment_type == "development":
        st.info(
            "Допустимые ответы: Всегда, Часто, Иногда, Редко, Никогда, "
            "Никогда или очень редко, Всегда или почти всегда, "
            "Никогда или очень редко (менее 10% подходящих ситуаций), "
            "Редко (примерно в 30% ситуаций), "
            "Иногда (примерно в половине ситуаций), "
            "Часто (в большинстве ситуаций), "
            "Всегда или почти всегда (более 90% ситуаций)"
        )

    assessment_info = st.text_area(
        "Общие данные про ассессмент",
        placeholder="Добавьте вводные, контекст, ссылки...",
        height=200
    )

    # File upload section
    st.header("Загрузка файлов")
    st.caption("Инструкция по заполнению файлов находится на главной странице. Пожалуйста, внимательно ознакомьтесь с требованиями к структуре данных в файлах, чтобы обеспечить корректную работу системы.")
    
    examples_subdir = "external" if assessment_type == "external" else "ipr"
    examples_base = f"src/assessment_client/examples/{examples_subdir}"

    col1, col2 = st.columns(2)
    with col1:
        st.write("Таблица c вопросами и ответами")
        download_example_button(
            f"{examples_base}/answers.xlsx",
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
            f"{examples_base}/logic.xlsx",
            file_name="logic.xlsx"
        )
        tasks_file = st.file_uploader(
            "Выберите Excel файл с расшифровкой компетенций",
            type=['xlsx'],
            key="tasks_file"
        )
    st.subheader("Матрица компетенций")
    
    download_example_button(
            f"{examples_base}/matrix.xlsx",
            file_name="competency_matrix.xlsx"
        )
    competency_file = st.file_uploader(
            "Выберите Excel файл с матрицей компетенций",
            type=['xlsx'],
            key="competency_file"
        )
    # Auto-preview: process files and show JSON when all files are uploaded
    if answers_file is not None and tasks_file is not None and competency_file is not None:
        try:
            results = await process_all_inputs(
                participants_results_file=answers_file,
                tasks_file=tasks_file,
                competency_file=competency_file,
                assessment_info=assessment_info,
                assessment_type=assessment_type
            )
            if results:
                st.session_state["preview_results"] = results
                for email, payload in results.items():
                    with st.expander(f"JSON запрос для {email}"):
                        st.json(payload)
            else:
                st.session_state.pop("preview_results", None)
        except Exception as e:
            st.error(f"Ошибка обработки файлов: {str(e)}")
            st.session_state.pop("preview_results", None)

    # Send button
    if st.button("Отправить", type="primary"):
        if answers_file is None or tasks_file is None or competency_file is None:
            st.error("Пожалуйста, загрузите все три файла перед отправкой.")
        elif "preview_results" not in st.session_state or not st.session_state["preview_results"]:
            st.error("Не удалось сформировать данные. Проверьте загруженные файлы.")
        else:
            results = st.session_state["preview_results"]
            st.success(f"Отправка {len(results)} email(ов)...")

            progress_bar = st.progress(0)
            status_container = st.container()

            for idx, (email, payload) in enumerate(results.items()):
                with status_container:
                    st.write(f"Processing email: {email}")

                    response = send_to_assessment_api(payload, api_url)

                    if isinstance(response, str):
                        st.error(f"Error for {email}: {response}")
                    else:
                        if response.status_code == 200:
                            st.success(f"✅ Successfully sent data for {email}")
                        else:
                            st.warning(f"⚠️ API returned status {response.status_code} for {email}: {response.text}")

                progress_bar.progress((idx + 1) / len(results))

            st.balloons()
            st.success("All emails processed!")
    
    # Information section
    st.divider()

    _examples_dir = Path(__file__).resolve().parent.parent / "examples" / examples_subdir

    @st.cache_data
    def load_columns_info(path: str) -> str:
        df = pd.read_excel(path)
        columns = df.columns.tolist()
        columns_to_code = list(map(lambda x: f"`{x}`", columns))
        columns_to_string = ", ".join(columns_to_code)
        return columns_to_string

    matrix_columns = load_columns_info(str(_examples_dir / "matrix.xlsx"))
    answers_columns = load_columns_info(str(_examples_dir / "answers.xlsx"))
    st.markdown(f"""
## Получение результата:
[https://ntfy.sh/assessment](https://ntfy.sh/assessment)
""")


if __name__ == "__main__":
    # When Streamlit runs this file directly from the pages menu, render the page.
    asyncio.run(render())
