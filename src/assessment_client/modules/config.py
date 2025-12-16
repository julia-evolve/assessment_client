REQUIRED_COMPETENCY_COLUMNS = ["name", "description", "level_0", "level_1", "level_2", "level_3"]
REQUIRED_QA_COLUMNS = ["Email", "Name", "Позиция", "Вопрос", "Ответ участника", "Компетенции"]
EVAL_TYPE_KEYS = ["external", "internal", "development"]

LANGUAGE_OPTIONS = ["ru", "en"]

from enum import Enum


class AssessmentGoal(str, Enum):
    IPR_UPDATE = "Срез уровня сотрудников для обновления ИПР"
    POTENTIAL_REVIEW = "Оценка потенциала для пересмотра роли или ЗП"
    CANDIDATE_SELECTION = "Отбор кандидата на должность"


# Backwards-compatible list of (key, label) tuples used by the UI
ASSESSMENT_GOALS = [goal.value for goal in AssessmentGoal]

class AssessmentFrequency(str, Enum):
    ONE_TIME = "Единоразово"
    QUARTERLY = "1 раз в квартал"
    HALF_YEAR = "1 раз в полгода"
    YEARLY = "1 раз в год"


# Backwards-compatible list of (key, label) tuples for the UI
ASSESSMENT_FREQUENCIES = [freq.value for freq in AssessmentFrequency]

DEFAULT_MATRIX_REQUEST_URL = "https://evolveaiserver-production.up.railway.app/competencies_matrix"
