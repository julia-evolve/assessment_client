REQUIRED_COMPETENCY_COLUMNS = ["name", "description", "level_0", "level_1", "level_2", "level_3"]
REQUIRED_QA_COLUMNS = ["Email", "Name", "Позиция", "Вопрос", "Ответ участника", "Компетенции"]
EVAL_TYPE_KEYS = ["external", "internal", "development"]

LANGUAGE_OPTIONS = ["ru", "en"]
ASSESSMENT_GOALS = [
    ("hiring", "Найм / подбор"),
    ("development", "Развитие сотрудников"),
    ("certification", "Аттестация / подтверждение уровня"),
]
ASSESSMENT_FREQUENCIES = [
    ("one_time", "Разово"),
    ("quarterly", "Ежеквартально"),
    ("annual", "Ежегодно"),
]
DEFAULT_MATRIX_REQUEST_URL = "https://evolveaiserver-production.up.railway.app/competencies_matrix"
