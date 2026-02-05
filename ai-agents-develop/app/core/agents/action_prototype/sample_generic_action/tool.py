from alltrue.agents.schema.action_execution import ObjectLog, PlainTextLog
from pydantic_ai import RunContext

from app.core.graph.deps.action_deps import ActionDeps


async def sample_increment(
    ctx: RunContext[ActionDeps], input: int, increment: int
) -> int:
    """
    This is a sample tool that adds a number to the input

    Args:
        input (int): The input to add 1 to
        increment (int): The number to add to the input
    Returns:
        int: The input + increment
    """
    before_log = [
        PlainTextLog(data="Temporary log message: before action"),
        ObjectLog(data={"current_val": input, "increment": increment}),
    ]
    await ctx.deps.add_log(before_log)

    # ==== logic ====

    res = input + increment

    # ==== end logic ====

    after_log = [
        PlainTextLog(data="Temporary log message: after action"),
        ObjectLog(data={"current_val": res, "increment": increment}),
    ]
    await ctx.deps.add_log(after_log)

    return res
