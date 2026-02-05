from pydantic import BaseModel, Field


class Start(BaseModel):
    number: int = Field(..., description="Starting Number")


class Output(BaseModel):
    pass
