from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class IndicatorLevel(BaseModel):
    level_0: str = Field(..., description="Level 0 description")
    level_1: str = Field(..., description="Level 1 description")
    level_2: str = Field(..., description="Level 2 description")
    level_3: str = Field(..., description="Level 3 description")

class Indicator(BaseModel):
    name: str = Field(..., description="Indicator name")
    description: str = Field(..., description="Indicator description")
    levels: IndicatorLevel = Field(..., description="Indicator levels")

class Competency(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="competency", description="Competency name")
    description: str = Field(..., alias="competency_description", description="Description of the competency")
    weight: float = Field(
        default=50.0,
        description="Weight of the competency (as a fraction, e.g., 50.0 for 50%)"
    )
    indicators: List[Indicator] = Field(
        default_factory=list, description="List of indicators for the competency"
    )

class CreateAssessmentRequest(BaseModel):
    assessment_time: Optional[int] = Field(
        default=60, description="Time allocated for the assessment in minutes"
    )
    description: str = Field(..., description="Description of the assessment")
    competency_matrix: List[Competency] = Field(
        ..., description="Competency matrix for the assessment"
    )
    num_statements: Optional[int] = Field(
        default=10, description="Number of statements to create"
    )
    webhook_url: Optional[str] = Field(
        default="https://ntfy.sh/assessment",
        description="Webhook URL to send created assessment",
    )
    num_dilemmas: Optional[int] = Field(
        default=2, description="Number of dilemmas to create"
    )
    num_mini_cases: Optional[int] = Field(
        default=2, description="Number of mini cases to create"
    )
    num_big_cases: Optional[int] = Field(
        default=1, description="Number of big cases to create"
    )
    num_open_questions: Optional[int] = Field(
        default=2, description="Number of open questions to create"
    )

class AssessmentGoal(str, Enum):
    LEVEL_ASSESSMENT_FOR_IDP_UPDATE = "level_assessment_for_idp_update"
    EMPLOYEE_POTENTIAL_FOR_ROLE_SALARY_REVIEW = "employee_potential_for_role_salary_review"
    CANDIDATE_SELECTION_FOR_POSITION = "candidate_selection_for_position"


class AssessmentFrequency(str, Enum):
    ONCE_A_YEAR = "once_a_year"
    EVERY_SIX_MONTHS = "every_six_months"
    ONCE_A_QUARTER = "once_a_quarter"
    ONE_TIME = "one_time"


class MatrixRequest(BaseModel):
    language: str = Field(
        ..., description="Language of the report (e.g. ru, en)"
    )
    target_audience: str = Field(
        ..., description="Target audience: who are we evaluating"
    )
    assessment_goal: AssessmentGoal = Field(
        ..., description="Goal of the assessment center"
    )
    frequency: AssessmentFrequency = Field(
        ..., description="Frequency of the assessment center"
    )
    company_name: str = Field(
        ..., description="Company name (may come from LMS)"
    )
    competencies: List[Competency] = Field(
        ..., description="List of competencies with weights"
    )
    assessment_length_minutes: Optional[int] = Field(
        default=60,
        description="Planned length of the assessment in minutes (30, 60, 90, 120)",
    )
    typical_cases: Optional[List[str]] = Field(
        default=None,
        min_items=1,
        max_items=5,
        description="Typical cases (1–5), reflecting real work situations",
    )
    audience_description: Optional[str] = Field(
        default=None, description="Requirements for the candidate / employee"
    )
    company_values_and_tone: Optional[str] = Field(
        default=None,
        description="Company values, corporate style and communication tone",
    )
    customer_pain_points: Optional[str] = Field(
        default=None,
        description="What difficulties does the customer face and why they need an assessment",
    )
    webhook_url: Optional[str] = Field(
        default="https://ntfy.sh/assessment", description="Webhook URL"
    )
