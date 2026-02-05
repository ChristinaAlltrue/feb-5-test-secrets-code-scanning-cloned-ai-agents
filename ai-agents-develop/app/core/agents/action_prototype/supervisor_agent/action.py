from typing import Callable, List

import logfire
from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog, SubagentNode
from pydantic import Field
from pydantic.dataclasses import (  # IMPORTANT: this fix the init problem with dataclasses
    dataclass,
)
from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import CallToolsNode, ModelRequestNode
from pydantic_ai.messages import ToolReturnPart
from pydantic_graph import BaseNode, GraphRunContext
from pydantic_graph.nodes import End

# from app.core.agents.action_prototype.supervisor_agent.schema import (
#     ToolConfiguration,
# )
from app.core.agents.action_prototype.bundles import ToolBundle
from app.core.agents.action_prototype.supervisor_agent.prompt import (
    SUPERVISOR_SYSTEM_PROMPT,
)
from app.core.agents.action_prototype.supervisor_agent.schema import (
    SupervisorAgentDeps,
    SupervisorOutput,
    ToolConfiguration,
)
from app.core.agents.action_prototype.supervisor_agent.subagent import (
    build_agent_from_node,
)
from app.core.agents.action_prototype.supervisor_agent.tools import (
    list_working_directory_files_tool,
)
from app.core.agents.base_node.base_node import AgentBaseNode
from app.core.agents.utils.action_lifecycle.pausable_action_lifecycle import (
    PausableActionLifecycleManager,
)
from app.core.agents.utils.tool_wrapper import create_validated_tool_callable
from app.core.graph.deps.action_deps import ActionDeps
from app.core.graph.deps.graph_deps import GraphDeps, patched_action_deps
from app.core.graph.state.state import State
from app.core.llm.model_registry import ModelRegistry
from app.core.registry import TOOLS_REGISTRY


async def handle_iter_log(ctx: RunContext[ActionDeps], node: BaseNode):
    def prettify_tool_name(tool_name: str) -> str:
        return tool_name.replace("_", " ").capitalize()

    def scrub_sensitive_info(args: dict) -> dict:
        if isinstance(args, str):
            return args
        res = {}
        for k, v in args.items():
            if "token" in k:
                res[k] = "<token>"
            elif "password" in k:
                res[k] = "<password>"
            else:
                res[k] = v
        return res

    if isinstance(node, CallToolsNode):
        for part in node.model_response.parts:
            tool_name = part.tool_name
            if tool_name == "final_result":
                return
            args = part.args
            if isinstance(args, str):
                args = {"args": args}
            await ctx.deps.add_log(
                [
                    PlainTextLog(
                        data=f"Delegating to sub agent: {prettify_tool_name(tool_name)}"
                    ),
                    ObjectLog(data=scrub_sensitive_info(args)),
                ]
            )
    elif isinstance(node, ModelRequestNode):
        for part in node.request.parts:
            if isinstance(part, ToolReturnPart):
                tool_name = part.tool_name
                result = part.content
                await ctx.deps.add_log(
                    [
                        PlainTextLog(
                            data=f"Sub agent {prettify_tool_name(tool_name)}: {result}"
                        ),
                    ]
                )
    elif isinstance(node, End):
        result = node.data.output
        await ctx.deps.add_log(
            [PlainTextLog(data="Task completed"), ObjectLog(data=result.model_dump())]
        )


@dataclass
class Supervisor(AgentBaseNode):
    lifecycle: PausableActionLifecycleManager[SupervisorAgentDeps, SupervisorOutput] = (
        Field(
            default_factory=lambda: PausableActionLifecycleManager(
                deps_type=SupervisorAgentDeps,
                action_name="Supervisor",
                # pre_execution_hook=self._pre_execution_hook,
            ),
            exclude=True,
        )
    )

    async def _pre_execution_hook(
        self,
        ctx: GraphRunContext[State, GraphDeps],
        deps: SupervisorAgentDeps,
    ):
        pass

    async def run(self, ctx: GraphRunContext[State, GraphDeps]) -> BaseNode:
        return await self.lifecycle.execute(ctx, self._execute_business_logic)

    async def get_subagents(
        self,
        action_deps: ActionDeps,
        vanilla_tool_registry: dict[str, "ToolBundle"],
    ) -> List[Callable]:
        "Top level function to get subagent tools"
        action_orm_object = await action_deps.action_repo.get(action_deps.action_id)
        if not action_orm_object:
            raise ValueError(f"Action with ID '{action_deps.action_id}' not found.")

        subagents = action_orm_object.subagents
        subagent_tools = []
        for subagent in subagents:
            subagent_tool_node = SubagentNode.model_validate(subagent)
            subagent_tools.append(
                build_agent_from_node(
                    subagent_tool_node,
                    vanilla_tool_registry,
                )
            )
        return subagent_tools

    async def _execute_business_logic(
        self,
        ctx: GraphRunContext[State, GraphDeps],
        current_deps: SupervisorAgentDeps,
    ) -> BaseNode:
        resume_prompt = "You are not resuming from a pause state."
        if self.resume:
            resume_prompt = "You are now resuming from a pause state."
            ctx.deps.node_ind = ctx.state.node_ind
        else:
            ctx.state.node_ind = ctx.deps.node_ind

        action_deps = ctx.deps.get_action_deps()
        # Always include the longterm memory search tool
        tools = [
            create_validated_tool_callable(
                TOOLS_REGISTRY["longterm_memory_search_tool"],
                tool_config_from_deps=ToolConfiguration(
                    tool_id="longterm_memory_search_tool",
                    selected_model="Gemini 2.5 Flash",
                ),
            )
        ]
        for tool_config in current_deps.tools:
            logfire.info(f"Processing tool config: {tool_config}")
            # TODO: handle tools without LLM needed
            # tool_config = ToolConfiguration(
            #     tool_id=tool_config, selected_model="GPT-4.1"
            # )  # Testing line
            if tool_config.tool_id not in TOOLS_REGISTRY:
                logfire.error(f"Tool id '{tool_config.tool_id}' not found in registry")
                raise ValueError(
                    f"Tool id '{tool_config.tool_id}' not found in registry"
                )
            tool_bundle = TOOLS_REGISTRY[tool_config.tool_id]
            tools.append(
                create_validated_tool_callable(
                    tool_bundle, tool_config_from_deps=tool_config
                )
            )

        tools.append(list_working_directory_files_tool)
        subagent_tools = await self.get_subagents(action_deps, TOOLS_REGISTRY)
        # Determine the model name for the Supervisor Agent itself
        # TODO: remove this else branch when new model selection is used by frontend
        selected_model = current_deps.selected_model or "GPT-4.1"

        # Create an Agent with dynamic tools
        supervisor_tools = tools + subagent_tools
        logfire.info(f"Supervisor tools (limit 10): {supervisor_tools[:10]}")
        SUPERVISOR_AGENT = Agent(
            model=ModelRegistry.get_pydantic_ai_llm(
                selected_model,
            ),
            deps_type=SupervisorAgentDeps,
            output_type=SupervisorOutput,
            system_prompt=AgentBaseNode.complete_system_prompt(
                SUPERVISOR_SYSTEM_PROMPT
            ),
            tools=supervisor_tools,
        )

        user_prompt = (
            f"Here is the state to help you making pause decision: {resume_prompt}\n"
            f"Goal: {current_deps.task_description}\n"
            f"{current_deps.additional_description}\n"
            f"Previous Output: {ctx.state.output}\n"
            f"Available credentials: {[key for key in action_deps.credentials.keys()]}\n"
            "Based on current goal and previous goal, you need to decide if you need request the Pause.\n"
            "**DO NOT REPEAT** any steps you performed before pause. You must continue from where you left off.\n"
        )
        async with patched_action_deps(ctx, action_deps) as new_ctx:
            # new_ctx.deps.credentials = current_deps.credentials
            async with SUPERVISOR_AGENT.iter(
                AgentBaseNode.complete_user_prompt(
                    user_prompt, self.extra_instructions
                ),
                deps=new_ctx.deps,
                message_history=ctx.state.agent_messages,
            ) as agent_run:
                async for node in agent_run:
                    try:
                        await handle_iter_log(new_ctx, node)
                    except Exception as e:
                        logfire.error(f"Error in Supervisor action: {e}")
                        # don't raise the error for logging, just continue

            result = agent_run.result
            new_messages = result.new_messages()
            ctx.state.store_agent_messages(new_messages)

        return result.output
