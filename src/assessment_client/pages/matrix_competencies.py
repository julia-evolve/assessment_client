import streamlit as st

from assessment_client.modules.api_client import send_to_assessment_api
from assessment_client.modules.validation import normalize_spaces
import assessment_client.modules.config as config


def render():
    st.title("Запрос на подготовку матрицы компетенций")
    st.write("Заполните форму, чтобы отправить запрос в сервис оценки.")

    # Configuration sidebar
    st.sidebar.header("Настройки API")
    api_url = st.sidebar.text_input(
        "Matrix request API URL",
        value=config.DEFAULT_MATRIX_REQUEST_URL,
        help="URL эндпоинта, принимающего MatrixRequest payload"
    )

    st.sidebar.divider()
    st.sidebar.markdown(
        """
        **Подсказки**
        - Весы компетенций задайте суммарно до 100 или в относительных величинах
        - Типичные кейсы описывают реальные рабочие ситуации (1-5 штук)
        - Поля можно оставить пустыми, если они необязательные
        """
    )

    with st.form("matrix_request_form"):
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox("Язык отчёта", config.LANGUAGE_OPTIONS, index=0)
            target_audience = st.text_input("Целевая аудитория", placeholder="Менеджеры по продажам")
            assessment_goal = st.selectbox(
                "Цель ассессмента",
                options=[goal[0] for goal in config.ASSESSMENT_GOALS],
                format_func=lambda key: dict(config.ASSESSMENT_GOALS)[key]
            )
        with col2:
            frequency = st.selectbox(
                "Частота ассессмента",
                options=[freq[0] for freq in config.ASSESSMENT_FREQUENCIES],
                format_func=lambda key: dict(config.ASSESSMENT_FREQUENCIES)[key]
            )
            company_name = st.text_input("Название компании", placeholder="ООО Пример")

        audience_description = st.text_area("Требования к участникам", height=100)
        company_values_and_tone = st.text_area("Ценности и тон коммуникации", height=100)
        customer_pain_points = st.text_area("Боли заказчика и причины обращения", height=120)

        st.subheader("Компетенции и веса")
        competency_count = st.number_input(
            "Количество компетенций", min_value=1, max_value=20, step=1, value=3
        )
        competency_inputs = []
        for idx in range(int(competency_count)):
            with st.expander(f"Компетенция {idx + 1}", expanded=idx < 2):
                name = st.text_input(
                    f"Название компетенции #{idx + 1}",
                    key=f"comp_name_{idx}"
                )
                weight = st.number_input(
                    f"Вес компетенции #{idx + 1}",
                    min_value=0.0,
                    max_value=100.0,
                    value=10.0,
                    key=f"comp_weight_{idx}"
                )
                description = st.text_area(
                    f"Описание компетенции #{idx + 1}",
                    height=80,
                    key=f"comp_desc_{idx}"
                )
                competency_inputs.append((name, weight, description))

        st.subheader("Типичные кейсы")
        typical_case_count = st.number_input(
            "Количество кейсов", min_value=0, max_value=5, step=1, value=1
        )
        typical_cases_inputs = []
        for idx in range(int(typical_case_count)):
            case_value = st.text_area(
                f"Кейс #{idx + 1}",
                height=80,
                key=f"case_{idx}"
            )
            typical_cases_inputs.append(case_value)

        submitted = st.form_submit_button("Отправить заявку")

    if not submitted:
        return

    errors = []
    competencies_payload = []
    for idx, (name, weight, description) in enumerate(competency_inputs, start=1):
        normalized_name = normalize_spaces(name)
        if not normalized_name:
            errors.append(f"Компетенция #{idx} должна содержать название.")
        if weight <= 0:
            errors.append(f"Компетенция #{idx} должна иметь положительный вес.")
        competencies_payload.append({
            "name": normalized_name,
            "weight": weight,
            "description": normalize_spaces(description) or None
        })

    competencies_payload = [comp for comp in competencies_payload if comp["name"]]

    typical_cases_payload = [
        normalize_spaces(case)
        for case in typical_cases_inputs
        if normalize_spaces(case)
    ]

    if typical_cases_inputs and not typical_cases_payload:
        errors.append("Добавьте текст хотя бы к одному кейсу или установите количество 0.")

        normalized_target_audience = normalize_spaces(target_audience)
        normalized_company_name = normalize_spaces(company_name)

        if not normalized_target_audience:
            errors.append("Заполните поле 'Целевая аудитория'.")
        if not normalized_company_name:
            errors.append("Заполните поле 'Название компании'.")
        if not competencies_payload:
            errors.append("Нужно указать хотя бы одну компетенцию с названием и весом.")

        if errors:
            for err in errors:
                st.error(err)
            return

    payload = {
        "language": language,
        "target_audience": normalized_target_audience,
        "assessment_goal": assessment_goal,
        "frequency": frequency,
        "company_name": normalized_company_name,
        "competencies": competencies_payload,
        "typical_cases": typical_cases_payload or None,
        "audience_description": normalize_spaces(audience_description) or None,
        "company_values_and_tone": normalize_spaces(company_values_and_tone) or None,
        "customer_pain_points": normalize_spaces(customer_pain_points) or None,
    }

    st.subheader("Предпросмотр payload")
    st.json(payload)

    response = send_to_assessment_api(payload, api_url)
    if isinstance(response, str):
        st.error(f"Ошибка при отправке запроса: {response}")
        return

    if response.status_code == 200:
        st.success("Запрос успешно отправлен")
    else:
        st.warning(
            f"API вернул статус {response.status_code}: {response.text}"
        )


if __name__ == "__main__":
    # When Streamlit runs this file directly (via the top-left pages menu),
    # execute the page rendering. When imported by `app.py` we don't
    # execute render() on import.
    render()
