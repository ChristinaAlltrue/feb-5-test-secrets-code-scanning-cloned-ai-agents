#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.
from typing import List, Literal

from pydantic import BaseModel
from pydantic_ai import Agent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class AuditToolException(Exception):
    """Custom exception raised for errors in processing audit tool."""


class AuditResult(BaseModel):
    has_info: Literal["yes", "no"]
    pass_audit: Literal["yes", "no"]
    issue_link: str
    reason: str
    evidence: List[str]


async def audit_page(page_content: str, instructions: str) -> AuditResult:
    agent_system_prompt = f"""
        You are an AI agent. Your job is to analyze the page and determine if the page fits the audit requirements.

        When making a decision, please provide clear and obvious evidence (could be a text or an element) to support your choice. The evidence should be in this format: "Scroll to <evidence_location>, it shows <evidence>". So that it can be easily located by scrolling up and down and easy to understand what should be checked. Ensure that the evidence_location is on the page.

        Guidelines:
        1. Read the page clearly and thoroughly, then check if the information in the page fits the instructions.
        2. If the page fits what the instructions require, set the `pass_audit` field to "yes" and return it.
        3. If the page does not fit what the instructions require, set the `pass_audit` field to "no" and return it.
        4. If the page does not contain any information the instructions claim it should have, set the `has_info` field to "no" and return it. Otherwise, `has_info` should always be "yes".
        5. In the `reason` field, provide a brief explanation of why the issue was detected or not detected. For example, "The pull request is related to issue #13" or "No issue was found in the pull request", respectively.
        """
    agent = Agent(
        model=get_pydanticai_openai_llm(),
        system_prompt=agent_system_prompt,
        output_type=AuditResult,
    )
    user_prompt = f"""
        The HTML Source of the page:
        {page_content}
        Instructions:
        {instructions}
        """
    result = await agent.run(user_prompt)
    output = AuditResult.model_validate(result.output)
    return output
