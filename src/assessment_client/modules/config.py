REQUIRED_COMPETENCY_COLUMNS = ["name", "description", "level_0", "level_1", "level_2", "level_3"]
REQUIRED_QA_COLUMNS = ["Email", "Name", "Позиция", "Вопрос", "Ответ участника", "Компетенции"]
EVAL_TYPE_KEYS = ["external", "internal", "development"]

LANGUAGE_OPTIONS = ["ru", "en"]

from enum import Enum


class AssessmentGoal(str, Enum):
    LEVEL_ASSESSMENT_FOR_IDP_UPDATE = "level_assessment_for_idp_update"
    EMPLOYEE_POTENTIAL_FOR_ROLE_SALARY_REVIEW = "employee_potential_for_role_salary_review"
    CANDIDATE_SELECTION_FOR_POSITION = "candidate_selection_for_position"

# Backwards-compatible list of (key, label) tuples used by the UI
ASSESSMENT_GOALS = [goal.value for goal in AssessmentGoal]

class AssessmentFrequency(str, Enum):
    ONCE_A_YEAR = "once_a_year"
    EVERY_SIX_MONTHS = "every_six_months"
    ONCE_A_QUARTER = "once_a_quarter"
    ONE_TIME = "one_time"


# Backwards-compatible list of (key, label) tuples for the UI
ASSESSMENT_FREQUENCIES = [freq.value for freq in AssessmentFrequency]

DEFAULT_MATRIX_REQUEST_URL = "https://evolveaiserver-production.up.railway.app/competencies_matrix"
