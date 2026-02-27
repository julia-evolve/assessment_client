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



class Statement(BaseModel):
    question: str = Field(
        ..., description="Statement or question text shown to the participant"
    )
    eval_type: str = Field(
        ..., description="Question polarity or type (e.g. 'Прямая', 'Обратная')"
    )
    competencies: List[str] = Field(..., description="Competencies this statement belongs to")
    indicators: List[str] = Field(default_factory=list, description="Indicators related to the competencies")
    answer: str = Field(..., description="Raw participant answer text")


class Dilemma(BaseModel):
    dilemma: str = Field(
        ..., description="Dilemma question text shown to the participant"
    )
    competencies: List[str] = Field(
        ..., description="Competency this dilemma belongs to"
    )
    indicators: List[str] = Field(
        ..., description="Indicators related to the competencies"
    )
    answer: str = Field(
        ..., description="Participant's answer including their choice and explanation"
    )


class MiniCase(BaseModel):
    mini_case: str = Field(..., description="Текст мини-кейса с описанием ситуации")
    competencies: List[str] = Field(
        ..., description="Список компетенций, которые оценивает мини-кейс"
    )
    indicators: List[str] = Field(
        ..., description="Индикаторы, связанные с данными компетенциями"
    )
    answer: str = Field(default="", description="Ответ участника на мини-кейс")


class BigCase(BaseModel):
    big_case: str = Field(
        ..., description="Текст большого кейса с описанием комплексной ситуации"
    )
    competencies: List[str] = Field(
        ..., description="Список компетенций, которые оценивает большой кейс"
    )
    indicators: List[str] = Field(
        ..., description="Индикаторы, связанные с данными компетенциями"
    )
    answer: str = Field(default="", description="Ответ участника на большой кейс")


class OpenAssessmentQuestion(BaseModel):
    """Open question for assessment evaluation"""

    question: str = Field(..., description="Assessment question")
    answer: str = Field(..., description="Assessment answer")
    competencies: List[str] = Field(..., description="Associated competencies")
    indicators: Optional[List[str]] = Field(
        default=[], description="Indicators related to the competencies"
    )

class EvalAssessmentRequest(BaseModel):
    """Combined request for all assessment types"""

    # Participant info
    user_email: str = Field(..., description="User email")
    user_name: str = Field(..., description="User name")

    # Assessment metadata
    position_title: str = Field(default="", description="Position title")
    assessment_info: str = Field(default="", description="Assessment info")

    # Common assessment fields
    competency_matrix: List[Competency] = Field(
        ..., description="Competency matrix for evaluation"
    )
    assessment_type: str = Field(
        default="external", description="One of: 'external', 'internal', 'development'"
    )

    # Optional assessment data - include only what needs to be evaluated
    open_questions: Optional[List[OpenAssessmentQuestion]] = Field(
        default=None, description="List of open assessment questions (optional)"
    )
    statements: Optional[List[Statement]] = Field(
        default=None, description="List of statements to evaluate (optional)"
    )
    dilemmas: Optional[List[Dilemma]] = Field(
        default=None, description="List of dilemmas to evaluate (optional)"
    )
    mini_cases: Optional[List[MiniCase]] = Field(
        default=None, description="List of mini cases to evaluate (optional)"
    )
    big_cases: Optional[List[BigCase]] = Field(
        default=None, description="List of big cases to evaluate (optional)"
    )

    # Webhook for final results
    webhook_url: str = Field(..., description="Webhook URL to send combined results")
