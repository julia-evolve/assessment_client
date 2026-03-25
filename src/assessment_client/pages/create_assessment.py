import json
from pathlib import Path
import streamlit as st

from assessment_client.modules import config, data_models as dm
from assessment_client.modules.api_client import send_to_assessment_api
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

    language = st.selectbox(
            "Язык ассессмента",
            config.LANGUAGE_OPTIONS,
            index=config.LANGUAGE_OPTIONS.index("ru"),
            key='language',
        )
    assessment_type = st.selectbox(
            "Тип ассессмента",
            config.EVAL_TYPE_KEYS,
            index=0,
            key='assessment_type',
            format_func=lambda x: {"external": "Внешний", "development": "Развитие"}.get(x, x),
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

    # Migrate old-format indicators (level_0..level_3) → new format (levels list)
    for comp in competencies:
        for ind in comp.get("indicators", []):
            if "levels" not in ind:
                ind["levels"] = [
                    {"level": i, "description": ind.pop(f"level_{i}", "")}
                    for i in range(4)
                ]

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

                    lv_cols = st.columns(len(ind["levels"]))
                    for lv_idx, lv in enumerate(ind["levels"]):
                        with lv_cols[lv_idx]:
                            lv["description"] = st.text_area(
                                f"Уровень {lv['level']}",
                                value=lv["description"],
                                key=f"lv{lv_idx}_{comp_idx}_{ind_idx}",
                                height=80,
                            )
                    st.divider()

                if st.button("➕ Добавить индикатор", key=f"add_ind_{comp_idx}"):
                    comp["indicators"].append({
                        "name": "",
                        "description": "",
                        "levels": [
                            {"level": 0, "description": ""},
                            {"level": 1, "description": ""},
                            {"level": 2, "description": ""},
                            {"level": 3, "description": ""},
                        ],
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
                    "levels": [
                        {"level": 0, "description": ""},
                        {"level": 1, "description": ""},
                        {"level": 2, "description": ""},
                        {"level": 3, "description": ""},
                    ],
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
                "levels": ind["levels"],
            })
        structured_competencies.append({
            "competency": comp["name"],
            "competency_description": comp["description"],
            "weight": comp["weight"],
            "indicators": structured_indicators,
        })

    # Build request payload (used for preview and sending)
    request_payload = {
        "language": language,
        "assessment_time": assessment_time,
        "assessment_type": assessment_type,
        "description": description,
        "competency_matrix": structured_competencies,
        "num_statements": num_statements,
        "num_dilemmas": num_dilemmas,
        "num_mini_cases": num_mini_cases,
        "num_big_cases": num_big_cases,
        "num_open_questions": num_open_questions,
        "webhook_url": webhook_url,
    }

    with st.expander("JSON запроса для API", expanded=False):
        st.json(request_payload)

    # send request to API endpoint
    if st.button("Отправить запрос на создание ассессмента"):
        try:
            request_data = dm.CreateAssessmentRequest(**request_payload)
            with st.spinner("Отправляем запрос..."):
                response = send_to_assessment_api(request_data.model_dump(by_alias=True), api_url)
                response.raise_for_status()
                st.success("Ассессмент успешно создан!")

        except Exception as e:
            st.error(f"Ошибка при отправке запроса: {e}")



if __name__ == "__main__":
    # When Streamlit runs this file directly from the pages menu, render the page.
    asyncio.run(render())
