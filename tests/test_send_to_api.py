import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.assessment_client.modules.api_client import send_to_assessment_api


def test_send_to_assessment_api():
    # Payload based on the MatrixRequest example
    payload = {
        "competencies": [
            {
                "name": "Стрессоустойчивость",
                "description": "Сохраняет спокойствие и принимает решения под давлением",
            }
        ],
        "language": "ru",
        "target_audience": "Команда поддержки клиентов",
        "assessment_goal": "Срез уровня сотрудников для обновления ИПР",
        "frequency": "1 раз в квартал",
        "company_name": "ООО Пример",
        "typical_cases": ["Работа с жалобами в пиковые часы"],
        "audience_description": "Сотрудники первой линии поддержки",
        "company_values_and_tone": "Доброжелательность и оперативность",
        "customer_pain_points": "Длительное время ответа и эмоциональные клиенты",
        "webhook_url": "https://ntfy.sh/assessment",
    }

    # Using httpbin.org for testing POST requests
    api_url = "http://localhost:8000/competencies_matrix"

    response = send_to_assessment_api(payload, api_url)

    # Check that we received a response object
    assert response is not None
    assert response.status_code == 200

