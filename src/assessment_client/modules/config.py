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

IPR_REPORT_PARTS = [
    "strong_competencies",
    "growth_zones",
    "risk_zones",
    "strong_indicators",
    "growth_indicators",
    "risk_indicators",
    "contradictions",
    "recommendations",
    "ai_usage",
    "strong_summary",
    "main_recommendation",
]
