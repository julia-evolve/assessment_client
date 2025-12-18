from pydantic import BaseModel, Field


class StatementRequest(BaseModel):
    question_number: int = Field(
        ...,
        description="Question number"
    )
    email: str = Field(
        ...,
        description="Participant email"
    )
    question: str = Field(
        ...,
        description="Statement or question text shown to the participant"
    )
    question_type: str = Field(
        ...,
        description="Question polarity or type (e.g. 'Прямая', 'Обратная')"
    )
    competency: str = Field(
        ...,
        description="Competency this statement belongs to"
    )
    participant_answer: str = Field(
        ...,
        description="Raw participant answer text"
    )
