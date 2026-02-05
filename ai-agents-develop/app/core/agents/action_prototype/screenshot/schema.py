from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# TODO: we will remove this after merged iter 4
class S3ScreenshotUploadResult(BaseModel):
    type: Literal["s3"] = "s3"
    key: str
    bucket_name: str


class LocalScreenshotUploadResult(BaseModel):
    type: Literal["local"] = "local"
    file_name: str
    file_path: str


ScreenshotUploadResult = Annotated[
    Union[S3ScreenshotUploadResult, LocalScreenshotUploadResult],
    Field(discriminator="type"),
]


class ScreenshotDeps(BaseModel):
    target_information: str = Field(
        ...,
        description="User prompt for the agent",
    )
    target_url: str = Field(
        ...,
        description="The URL to navigate to for taking screenshots",
    )


class ScreenshotOutput(BaseModel):
    img_list: list[ScreenshotUploadResult] = Field(default_factory=list)
    target_url: str = Field(
        ..., description="The URL for the target page to take screenshots of"
    )
