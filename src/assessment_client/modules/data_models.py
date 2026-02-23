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
