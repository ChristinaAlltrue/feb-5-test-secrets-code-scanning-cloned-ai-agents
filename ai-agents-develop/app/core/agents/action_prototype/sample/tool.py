from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import RunContext

from app.core.graph.deps.action_deps import ActionDeps


async def sample(ctx: RunContext[ActionDeps], input: int) -> int:
    """
    This is a sample tool that adds 1 to the input

    Args:
        input (int): The input to add 1 to

    Returns:
        int: The input + 1
    """
    before_log = [
        PlainTextLog(data="Temporary log message: before action"),
        ObjectLog(data={"current_val": input}),
    ]
    await ctx.deps.add_log(before_log)

    # ==== logic ====

    res = input + 1

    # ==== end logic ====

    after_log = [
        PlainTextLog(data="Temporary log message: after action"),
        ObjectLog(data={"current_val": res}),
    ]
    await ctx.deps.add_log(after_log)

    return res
