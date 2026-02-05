import logfire
from pydantic_ai import Agent, RunContext

from app.core.agents.action_prototype.GHCO_auditor.schema import GHCOAuditorOutput
from app.core.agents.action_prototype.GHCO_auditor.tools.audit_analysis_agent import (
    audit_analysis_agent_tool,
)
from app.core.agents.action_prototype.GHCO_auditor.tools.ghco_browser_agent import (
    ghco_browser_agent_tool,
)
from app.core.agents.action_prototype.GHCO_auditor.tools.ghco_login import (
    ghco_login_tool,
)
from app.core.graph.deps.action_deps import ActionDeps
from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


async def GHCO_auditor(
    ctx: RunContext[ActionDeps],
    target_business_unit: str,
    login_url: str,
    navigation_instruction: str,
    username: str,
    password: str,
) -> GHCOAuditorOutput:

    # attach the credentials to the action deps to avoid passing them by LLM
    ctx.deps.model_extra.update(
        {
            "username": username,
            "password": password,
        }
    )

    try:
        agent = Agent(
            model=get_pydanticai_openai_llm(),
            tools=[
                ghco_browser_agent_tool,
                ghco_login_tool,
                audit_analysis_agent_tool,
            ],
            system_prompt="""
            you are a GHCO auditor.
            Your first step is to call the ghco_login tool to login to the GHCO.
            Your second step is to call the AuditAnalysisBrowserAgent tool to navigate and download the files related to the targets.
            Your third step is to call the audit_analysis_agent tool to process downloaded files and generate comprehensive audit reports.
            """,
        )
        result = await agent.run(
            f"""
            check the GHCO business units: {target_business_unit}.
            login url: {login_url}
            navigation instruction: {navigation_instruction}
        """,
            output_type=GHCOAuditorOutput,
            deps=ctx.deps,
        )

        logfire.info(f"GHCOAuditorOutput: {result.output}")

        return result.output

    except Exception as e:
        logfire.error(f"GHCOAuditor failed: {e}")
        raise
