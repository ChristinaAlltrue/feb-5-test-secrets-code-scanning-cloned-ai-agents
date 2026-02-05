import shutil
import tempfile
from pathlib import Path

import logfire
from pydantic_ai import RunContext

from app.core.graph.deps.action_deps import ToolActionDeps
from app.core.longterm_memory.longterm_memory_search import (
    AgentDeps,
    EvaluateGrep,
    GenerateAnswer,
    GenerateKeywords,
    Graph,
    ReadFiles,
    RunGrep,
    SearchState,
)
from app.utils.file_storage_manager import get_file_storage
from config import AGENTS_EVIDENCE_STORAGE_BUCKET


async def longterm_memory_search_tool(
    ctx: RunContext[ToolActionDeps],
    question: str,
) -> str:
    """
    Query the longterm memory to get the answer to a question based on stored documents.

    Args:
        ctx: The run context with action dependencies
        question: The question to ask the longterm memory system
    """
    try:
        logfire.info("Starting longterm memory search", question=question)

        # Get storage instance
        storage = get_file_storage(bucket_name=AGENTS_EVIDENCE_STORAGE_BUCKET)

        # Use entity_id as customer_id
        customer_id = str(ctx.deps.control_info.customer_id)

        # Create temporary cache directory
        cache_dir = Path(tempfile.mkdtemp(prefix=f"longterm_memory_{customer_id}"))

        try:
            # Create agent deps with selected model from context
            agent_deps = AgentDeps(
                storage=storage,
                customer_id=customer_id,
                cache_dir=cache_dir,
                model_name=ctx.deps.selected_model,
            )

            # Create the graph with all necessary nodes
            qa_graph = Graph(
                nodes=[
                    GenerateKeywords,
                    RunGrep,
                    EvaluateGrep,
                    ReadFiles,
                    GenerateAnswer,
                ]
            )

            # Create initial state
            initial_state = SearchState(user_query=question)

            # Run the graph
            logfire.info("Running longterm memory graph", customer_id=customer_id)
            run_result = await qa_graph.run(
                GenerateKeywords(), deps=agent_deps, state=initial_state
            )

            # Get the result
            result = run_result.output
            logfire.info("Longterm memory agent completed", result_length=len(result))

            return result

        finally:
            # Clean up cache directory
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                except Exception as e:
                    logfire.warning(f"Failed to clean up cache directory: {e}")

    except Exception as e:
        logfire.error(f"longterm_memory_agent_tool failed: {e}")
        raise
