from typing import List, Literal

from pydantic import BaseModel, Field


class ScreenshotInformation(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the target page to take a screenshot of",
        json_schema_extra={"example": "https://example.com/target-page"},
    )
    stored_images: list[str] = Field(
        ...,
        description="List of stored images from the screenshot action",
        json_schema_extra={"example": ["image1.png", "image2.png"]},
    )
    target_info: str = Field(
        "",
        description="The target information of the screenshot",
    )


class AuditInformation(BaseModel):
    url: str = Field(
        ...,
        description="The URL of the page that was audited",
        json_schema_extra={"example": "https://example.com/target-page"},
    )
    pass_or_not: Literal["yes", "no"] = Field(
        ...,
        description="Indicates whether the audit check passed or not",
        json_schema_extra={"example": "yes"},
    )
    reason: str = Field(
        ...,
        description="Reason for the pass or fail status of the audit check",
        json_schema_extra={"example": "The file is uploaded on <timestamp>."},
    )


class BrowserInfo:
    def __init__(self):
        self.screenshot_info: List[ScreenshotInformation] = []
        self.check_info: List[AuditInformation] = []

    def add_screenshot_info(self, url: str, stored_images: list, target_info: str = ""):
        self.screenshot_info.append(
            ScreenshotInformation(
                url=url, stored_images=stored_images, target_info=target_info
            )
        )

    def add_check_info(self, url: str, pass_or_not: Literal["yes", "no"], reason: str):
        self.check_info.append(
            AuditInformation(url=url, pass_or_not=pass_or_not, reason=reason)
        )
