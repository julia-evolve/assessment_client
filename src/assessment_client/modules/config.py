REQUIRED_COMPETENCY_COLUMNS = [
    "competency", "competency_description", "weight",
    "indicator_name", "indicator_description",
    "level_0", "level_1", "level_2", "level_3",
]
REQUIRED_QA_COLUMNS = ["Email", "Name", "Позиция", "Вопрос", "Ответ участника", "Компетенции"]
EVAL_TYPE_KEYS = ["external", "development"]

LANGUAGE_OPTIONS = [
    "ar", "az", "da", "de", "en", "es", "fi", "fr",
    "hy", "it", "ka", "kk", "nb", "pl", "pt", "pt-BR",
    "ru", "sv", "tg", "tr", "uz", "uz-Cyrl"]


DEFAULT_MATRIX_REQUEST_URL = "https://evolveaiserver-production.up.railway.app/competencies_matrix"
