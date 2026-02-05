from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.agents.compliance_agent.models import EvidenceItem


class GenericAuditorAgentDeps(BaseModel):
    user_prompt: str = Field(
        ...,
        description="User prompt for the agent",
        json_schema_extra={"example": "Please log in to the application."},
    )
    login_url: str = Field(
        ...,
        description="Starting URL for login",
        json_schema_extra={"example": "https://example.com"},
    )  # override the initial_url in the base schema
    username: str = Field(
        ...,
        description="Username to log in",
        json_schema_extra={"example": "user@example.com"},
    )
    password: str = Field(..., description="Password for the account")
    login_instructions: str = Field(..., description="Login flow instructions")
    mfa_secret: Optional[str] = Field("", description="TOTP MFA key")
    screenshot_target_information: Optional[str] = Field(
        None,
        description="Information to search for on the pages visited",
        json_schema_extra={"example": "Find the latest news on the homepage."},
    )
    page_audit_check_information: Optional[str] = Field(
        None,
        description="Information to check on the pages visited",
        json_schema_extra={"example": "Check if the latest news is displayed."},
    )


class GenericAuditorAgentOutput(BaseModel):
    evidence: List[EvidenceItem] = Field(
        default_factory=list, description="List of evidence items"
    )

    class Config:
        extra = "allow"  # Allow additional fields not explicitly defined
