from pydantic import BaseModel, Field


class SampleGenericActionDeps(BaseModel):
    goal: str = Field(
        ...,
        description="Input number to increment",
        json_schema_extra={"example": "Increment the input number by 1"},
    )


class SampleGenericActionOutput(BaseModel):
    output: int = Field(
        ...,
        description="Output of the incremented input number",
        json_schema_extra={"example": 2},
    )
