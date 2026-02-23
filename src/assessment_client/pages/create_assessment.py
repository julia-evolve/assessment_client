import json
from pathlib import Path
import streamlit as st

from assessment_client.modules import data_models as dm
import asyncio


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


async def render():
    st.title("Создание ассессмента")
    st.sidebar.header("Configuration")
    api_url = st.sidebar.selectbox(
        "Assessment API URL",
        options=[
            "https://evolveaiserver-production.up.railway.app/create_assessment",
            "http://host.docker.internal:8000/create_assessment",
            "Custom"
        ],
        index=0,
        help="Select the API endpoint URL"
    )
    if api_url == "Custom":
        api_url = st.sidebar.text_input(
            "Custom API URL",
            value="https://evolveaiserver-production.up.railway.app/create_assessment",
            help="Enter the API endpoint URL"
        )

    webhook_url = st.text_input(
        "Webhook URL для отправки созданного ассессмента",
        value="https://ntfy.sh/assessment",
        help="Введите URL, на который будет отправляться созданный ассессмент в формате JSON"
    )

    assessment_time = st.number_input(
        "Время на прохождение ассессмента (в минутах)",
        min_value=30,
        max_value=120,
        step=30,
        value=60
    )
    description = st.text_area(
        "Описание ассессмента",
        placeholder="Добавьте вводные, контекст, ссылки...",
        height=200
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        num_statements = st.number_input(
            "Количество утверждений",
            min_value=0,
            max_value=100,
            step=1,
            value=10
        )
        num_dilemmas = st.number_input(
            "Количество дилемм",
            min_value=0,
            max_value=100,
            step=1,
            value=2
        )
    with col2:
        num_mini_cases = st.number_input(
            "Количество мини-кейсов",
            min_value=0,
            max_value=100,
            step=1,
            value=2
        )
        num_big_cases = st.number_input(
            "Количество больших кейсов",
            min_value=0,
            max_value=100,
            step=1,
            value=1
        )
    with col3:
        num_open_questions = st.number_input(
            "Количество открытых вопросов",
            min_value=0,
            max_value=100,
            step=1,
            value=2
        )
    
    # --- Default competency matrix in session state ---
    if "competencies" not in st.session_state:
        with open(EXAMPLES_DIR / "default_competencies.json", "r", encoding="utf-8") as f:
            st.session_state["competencies"] = json.load(f)

    competencies = st.session_state["competencies"]

    # --- Competency matrix UI ---
    st.header("Компетенции и индикаторы")
    st.caption("Добавьте компетенции и соответствующие им индикаторы, которые будут использоваться для оценки. Убедитесь, что вес компетенций в сумме составляет 100%.")

    # --- Weight summary ---
    total_weight = sum(c["weight"] for c in competencies)
    if abs(total_weight - 100.0) > 0.01:
        st.warning(f"Сумма весов: **{total_weight:.1f}%** (должно быть 100%)")
    else:
        st.success(f"Сумма весов: **{total_weight:.1f}%**")

    for comp_idx, comp in enumerate(competencies):
        with st.expander(f"Компетенция {comp_idx + 1}: {comp['name'] or '—'}", expanded=True):
            left, right = st.columns([1, 2])

            with left:
                st.subheader("Компетенция")
                comp["name"] = st.text_input(
                    "Название",
                    value=comp["name"],
                    key=f"comp_name_{comp_idx}",
                )
                comp["description"] = st.text_area(
                    "Описание",
                    value=comp["description"],
                    key=f"comp_desc_{comp_idx}",
                    height=100,
                )
                comp["weight"] = st.number_input(
                    "Вес (%)",
                    min_value=0.0,
                    max_value=100.0,
                    step=5.0,
                    value=comp["weight"],
                    key=f"comp_weight_{comp_idx}",
                )

                if st.button("Удалить компетенцию", key=f"del_comp_{comp_idx}", type="secondary"):
                    competencies.pop(comp_idx)
                    st.rerun()

            with right:
                st.subheader("Индикаторы")
                for ind_idx, ind in enumerate(comp["indicators"]):
                    st.markdown(f"**Индикатор {ind_idx + 1}**")
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        ind["name"] = st.text_input(
                            "Название индикатора",
                            value=ind["name"],
                            key=f"ind_name_{comp_idx}_{ind_idx}",
                        )
                    with c2:
                        if st.button("✕", key=f"del_ind_{comp_idx}_{ind_idx}", help="Удалить индикатор"):
                            comp["indicators"].pop(ind_idx)
                            st.rerun()

                    ind["description"] = st.text_input(
                        "Описание индикатора",
                        value=ind["description"],
                        key=f"ind_desc_{comp_idx}_{ind_idx}",
                    )

                    lv0, lv1, lv2, lv3 = st.columns(4)
                    with lv0:
                        ind["level_0"] = st.text_area(
                            "Уровень 0",
                            value=ind["level_0"],
                            key=f"lv0_{comp_idx}_{ind_idx}",
                            height=80,
                        )
                    with lv1:
                        ind["level_1"] = st.text_area(
                            "Уровень 1",
                            value=ind["level_1"],
                            key=f"lv1_{comp_idx}_{ind_idx}",
                            height=80,
                        )
                    with lv2:
                        ind["level_2"] = st.text_area(
                            "Уровень 2",
                            value=ind["level_2"],
                            key=f"lv2_{comp_idx}_{ind_idx}",
                            height=80,
                        )
                    with lv3:
                        ind["level_3"] = st.text_area(
                            "Уровень 3",
                            value=ind["level_3"],
                            key=f"lv3_{comp_idx}_{ind_idx}",
                            height=80,
                        )
                    st.divider()

                if st.button("➕ Добавить индикатор", key=f"add_ind_{comp_idx}"):
                    comp["indicators"].append({
                        "name": "",
                        "description": "",
                        "level_0": "",
                        "level_1": "",
                        "level_2": "",
                        "level_3": "",
                    })
                    st.rerun()

    if st.button("➕ Добавить компетенцию"):
        competencies.append({
            "name": "",
            "description": "",
            "weight": 0.0,
            "indicators": [
                {
                    "name": "",
                    "description": "",
                    "level_0": "",
                    "level_1": "",
                    "level_2": "",
                    "level_3": "",
                }
            ],
        })
        st.rerun()
    
    # build CreateAssessmentRequest from form data
    # Nest flat level_* fields into IndicatorLevel for Pydantic validation
    structured_competencies = []
    for comp in competencies:
        structured_indicators = []
        for ind in comp["indicators"]:
            structured_indicators.append({
                "name": ind["name"],
                "description": ind["description"],
                "levels": {
                    "level_0": ind["level_0"],
                    "level_1": ind["level_1"],
                    "level_2": ind["level_2"],
                    "level_3": ind["level_3"],
                },
            })
        structured_competencies.append({
            "competency": comp["name"],
            "competency_description": comp["description"],
            "weight": comp["weight"],
            "indicators": structured_indicators,
        })

    request_data = dm.CreateAssessmentRequest(
        assessment_time=assessment_time,
        description=description,
        competency_matrix=structured_competencies,
        num_statements=num_statements,
        num_dilemmas=num_dilemmas,
        num_mini_cases=num_mini_cases,
        num_big_cases=num_big_cases,
        num_open_questions=num_open_questions,
        webhook_url=webhook_url,
    )

    st.subheader("JSON запроса для API")
    st.json(request_data.model_dump())

    # send request to API endpoint
    if st.button("Отправить запрос на создание ассессмента"):
        try:
            import requests
            with st.spinner("Отправляем запрос..."):
                response = requests.post(api_url, json=request_data.model_dump(), timeout=120)
                response.raise_for_status()
                st.success("Ассессмент успешно создан!")
                st.json(response.json())
        except Exception as e:
            st.error(f"Ошибка при отправке запроса: {e}")



if __name__ == "__main__":
    # When Streamlit runs this file directly from the pages menu, render the page.
    asyncio.run(render())
