from pydantic import BaseModel, Field


class SampleDeps(BaseModel):
    input: int = Field(
        ..., description="Input number to increment", json_schema_extra={"example": 1}
    )


class SampleOutput(BaseModel):
    output: int = Field(
        ..., description="Input number plus 1", json_schema_extra={"example": 2}
    )
