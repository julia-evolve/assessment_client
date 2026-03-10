from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from assessment_client.modules.config import AssessmentGoal, AssessmentFrequency


class IndicatorLevel(BaseModel):
    level: int = Field(..., description="Indicator level number (e.g., 0-3)")
    description: str = Field(..., description="Description of the indicator level")


class IndicatorLevels(BaseModel):
    levels: List[IndicatorLevel] = Field(..., description="List of indicator levels")


class Indicator(BaseModel):
    name: str = Field(..., description="Indicator name")
    description: str = Field(..., description="Indicator description")
    levels: List[IndicatorLevel] = Field(default_factory=list, description="Indicator levels")


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
    num_indicators: Optional[int] = Field(
        default=1, description="Number of indicators for the competency"
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


class Statement(BaseModel):
    question: str = Field(..., description="Statement or question text shown to the participant")
    eval_type: str = Field(..., description="Question polarity or type (e.g. 'Прямая', 'Обратная')")
    competency: str = Field(..., description="Competency this statement belongs to")
    indicators: List[str] = Field(default_factory=list, description="Indicators related to the competency")
    answer: str = Field(..., description="Raw participant answer text")


class Dilemma(BaseModel):
    dilemma: str = Field(..., description="Dilemma question text shown to the participant")
    competencies: List[str] = Field(..., description="Competencies this dilemma belongs to")
    indicators: List[str] = Field(default_factory=list, description="Indicators related to the competencies")
    answer: str = Field(..., description="Participant's answer including their choice and explanation")


class MiniCase(BaseModel):
    mini_case: str = Field(..., description="Текст мини-кейса с описанием ситуации")
    competencies: List[str] = Field(..., description="Список компетенций, которые оценивает мини-кейс")
    indicators: List[str] = Field(default_factory=list, description="Индикаторы, связанные с данными компетенциями")
    answer: str = Field(default="", description="Ответ участника на мини-кейс")


class BigCase(BaseModel):
    big_case: str = Field(..., description="Текст большого кейса с описанием комплексной ситуации")
    competencies: List[str] = Field(..., description="Список компетенций, которые оценивает большой кейс")
    indicators: List[str] = Field(default_factory=list, description="Индикаторы, связанные с данными компетенциями")
    answer: str = Field(default="", description="Ответ участника на большой кейс")


class OpenAssessmentQuestion(BaseModel):
    question: str = Field(..., description="Assessment question")
    answer: str = Field(..., description="Assessment answer")
    competencies: List[str] = Field(..., description="Associated competencies")
    indicators: List[str] = Field(default_factory=list, description="Indicators related to the competencies")


class EvalAssessmentRequest(BaseModel):
    """Combined request for all assessment types"""

    user_email: str = Field(..., description="User email")
    user_name: str = Field(..., description="User name")
    position_title: str = Field(default="", description="Position title")
    assessment_info: str = Field(default="", description="Assessment info")
    competency_matrix: List[Competency] = Field(..., description="Competency matrix for evaluation")
    assessment_type: str = Field(default="external", description="One of: 'external', 'internal', 'development'")
    open_questions: Optional[List[OpenAssessmentQuestion]] = Field(default=None, description="List of open assessment questions")
    statements: Optional[List[Statement]] = Field(default=None, description="List of statements to evaluate")
    dilemmas: Optional[List[Dilemma]] = Field(default=None, description="List of dilemmas to evaluate")
    mini_cases: Optional[List[MiniCase]] = Field(default=None, description="List of mini cases to evaluate")
    big_cases: Optional[List[BigCase]] = Field(default=None, description="List of big cases to evaluate")
    webhook_url: str = Field(..., description="Webhook URL to send combined results")


class MatrixRequest(BaseModel):
    """Request for competency matrix generation"""

    language: str = Field(..., description="Language of the report (e.g. ru, en)")
    target_audience: str = Field(..., description="Target audience: who are we evaluating")
    assessment_goal: AssessmentGoal = Field(..., description="Goal of the assessment center")
    frequency: AssessmentFrequency = Field(..., description="Frequency of the assessment center")
    company_name: str = Field(..., description="Company name (may come from LMS)")
    competencies: List[Competency] = Field(..., description="List of competencies with weights")
    assessment_length_minutes: Optional[int] = Field(
        default=60, description="Planned length of the assessment in minutes (30, 60, 90, 120)"
    )
    typical_cases: Optional[List[str]] = Field(
        default=None, description="Typical cases (1-5), reflecting real work situations"
    )
    audience_description: Optional[str] = Field(
        default=None, description="Requirements for the candidate / employee"
    )
    company_values_and_tone: Optional[str] = Field(
        default=None, description="Company values, corporate style and communication tone"
    )
    customer_pain_points: Optional[str] = Field(
        default=None, description="What difficulties does the customer face and why they need an assessment"
    )
    webhook_url: Optional[str] = Field(
        default="https://ntfy.sh/assessment", description="Webhook URL"
    )