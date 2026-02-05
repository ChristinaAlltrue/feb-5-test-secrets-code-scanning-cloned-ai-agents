import asyncio
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import logfire
from alltrue.local.file_storage.file_storage import FileStorage
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from app.core.llm.model_registry import ModelRegistry

# ==============================================================================
# 1. Configuration & Domain Models
# ==============================================================================


# Define Output Models
class KeywordOutput(BaseModel):
    keywords: List[str] = Field(
        ...,
        description="List of 1-3 specific keywords in human language for grep, for example: 'evidence', 'report' ",
    )


class JudgmentOutput(BaseModel):
    decision: str = Field(
        ...,
        description="Either 'RETRY' (if results are bad) or 'PROCEED' (if results look promising)",
    )
    files_to_read: List[str] = Field(
        default_factory=list,
        description="List of relative file paths to read if Proceeding",
    )
    reasoning: str = Field(..., description="Why you made this decision")


@dataclass
class AgentDeps:
    storage: FileStorage
    customer_id: str
    cache_dir: Path
    model_name: Optional[str] = None


@dataclass
class SearchState:
    """Shared state passed between graph nodes."""

    user_query: str
    tried_keywords: List[str] = field(default_factory=list)
    grep_results_log: List[str] = field(default_factory=list)
    final_file_contents: str = ""


# --- Helper Functions ---
def _get_cached_file_path(cache_dir: Path, object_key: str) -> Path:
    safe_key = object_key.replace("/", "_").replace("\\", "_")
    safe_key = "".join(c for c in safe_key if c.isalnum() or c in ("_", "-", "."))
    return cache_dir / safe_key


def _ensure_file_cached(storage: FileStorage, cache_dir: Path, object_key: str) -> Path:
    cache_path = _get_cached_file_path(cache_dir, object_key)
    if cache_path.exists():
        return cache_path
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        content = storage.download_text(context={}, object_name=object_key)
        cache_path.write_text(content, encoding="utf-8")
        return cache_path
    except Exception as e:
        # Log warning but don't crash entire process
        logfire.warning(f"Failed to cache {object_key}: {e}")
        return cache_path


# ==============================================================================
# 2. Agents (The Brains)
# ==============================================================================


def _get_keyword_agent(model_name: Optional[str] = None) -> Agent:
    """Create keyword generator agent with specified model."""
    model = ModelRegistry.get_pydantic_ai_llm(
        model_name=model_name or "Gemini 2.5 Flash"
    )
    return Agent(
        model,
        output_type=KeywordOutput,
        system_prompt=(
            "You are a search expert. Your goal is to generate natural language keywords "
            "for grep to find information in documents/text files based on a user query.\n\n"
            "Generate keywords as they would appear in natural written text:\n"
            "- Single words: 'evidence', 'request', 'report'\n"
            "- Short phrases: 'get evidence', 'request evidence', 'submit report'\n\n"
            "DO NOT generate technical identifiers like camelCase (requestEvidence) or variable names.\n"
            "Use lowercase, natural language terms that would appear in regular text documents."
        ),
    )


def _get_judge_agent(model_name: Optional[str] = None) -> Agent:
    """Create judge agent with specified model."""
    model = ModelRegistry.get_pydantic_ai_llm(
        model_name=model_name or "Gemini 2.5 Flash"
    )
    return Agent(
        model,
        output_type=JudgmentOutput,
        system_prompt=(
            "You are a critical evaluator. You review the output of a 'grep' command. "
            "Determine if the grep results contain enough information to answer the user's request, "
            "or if we need to read the specific files found to get more context.\n"
            "If the grep result is empty or irrelevant, you must request a retry with new keywords."
        ),
    )


def _get_writer_agent(model_name: Optional[str] = None) -> Agent:
    """Create writer agent with specified model."""
    model = ModelRegistry.get_pydantic_ai_llm(
        model_name=model_name or "Gemini 2.5 Flash"
    )
    return Agent(
        model,
        system_prompt="You are a helpful assistant. Answer the user's question based strictly on the provided file contents.",
    )


# ==============================================================================
# 3. Graph Nodes
# ==============================================================================


# --- Node A: Choose Keywords ---
@dataclass
class GenerateKeywords(BaseNode[SearchState, None, AgentDeps]):
    feedback: str = ""

    async def run(self, ctx: GraphRunContext[SearchState]) -> "RunGrep":
        history_str = ", ".join(ctx.state.tried_keywords)
        prompt = (
            f"User Query: {ctx.state.user_query}\n"
            f"Already Tried Keywords: {history_str}\n"
            f"Feedback from previous attempt: {self.feedback}\n\n"
            "Generate 1 to 5 new keywords for grep. Use natural language words or short phrases "
            "as they would appear in text documents (e.g., 'evidence', 'request', 'get evidence'). "
            "Do NOT use technical identifiers or camelCase variable names."
        )

        keyword_agent = _get_keyword_agent(ctx.deps.model_name)
        result = await keyword_agent.run(prompt)

        # NOTE: Access typed result via .data
        new_keywords = result.output.keywords
        ctx.state.tried_keywords.extend(new_keywords)

        return RunGrep(keywords=new_keywords)


# --- Node B: Run Grep (Deterministic) ---
@dataclass
class RunGrep(BaseNode[SearchState, None, AgentDeps]):
    keywords: List[str]

    async def run(self, ctx: GraphRunContext[SearchState]) -> "EvaluateGrep":
        prefix = f"agent-memory/{ctx.deps.customer_id}/"
        try:
            object_keys = ctx.deps.storage.list_objects_by_prefix(prefix)
            path_mapping = {}
            for obj_key in object_keys:
                if obj_key.endswith("/"):
                    continue
                try:
                    c_path = _ensure_file_cached(
                        ctx.deps.storage, ctx.deps.cache_dir, obj_key
                    )
                    rel_path = (
                        obj_key[len(prefix) :]
                        if obj_key.startswith(prefix)
                        else obj_key
                    )
                    path_mapping[str(c_path)] = rel_path
                except Exception:
                    continue
        except Exception as e:
            return EvaluateGrep(grep_output=f"Error listing/caching files: {e}")

        combined_output = []
        for kw in self.keywords:
            try:
                proc = subprocess.run(
                    ["grep", "-i", "-R", kw, str(ctx.deps.cache_dir)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if proc.returncode == 0 and proc.stdout:
                    lines = proc.stdout.strip().split("\n")
                    for line in lines:
                        if ":" in line:
                            fpath, content = line.split(":", 1)
                            clean_name = path_mapping.get(fpath, Path(fpath).name)
                            combined_output.append(
                                f"File: {clean_name} | Match: {content.strip()}"
                            )
            except Exception as e:
                combined_output.append(f"Error grepping {kw}: {e}")

        unique_output = list(set(combined_output))
        final_output_str = (
            "\n".join(unique_output) if unique_output else "No matches found."
        )
        ctx.state.grep_results_log.append(
            f"Keywords {self.keywords}:\n{final_output_str}"
        )

        return EvaluateGrep(grep_output=final_output_str)


# --- Node C: Judge (Evaluate Result) ---
@dataclass
class EvaluateGrep(BaseNode[SearchState, None, AgentDeps]):
    grep_output: str

    async def run(
        self, ctx: GraphRunContext[SearchState]
    ) -> Union[GenerateKeywords, "ReadFiles"]:

        if len(ctx.state.tried_keywords) > 8:
            return ReadFiles(files_to_read=[])

        prompt = (
            f"User Query: {ctx.state.user_query}\n"
            f"Grep Results:\n{self.grep_output}\n\n"
            "Analyze these results.\n"
            "1. If they point to specific relevant files, select 'PROCEED' and list the file paths.\n"
            "2. If the results are empty or irrelevant, select 'RETRY' and explain why."
        )

        judge_agent = _get_judge_agent(ctx.deps.model_name)
        result = await judge_agent.run(prompt)

        # NOTE: Access typed result via .data
        decision = result.output

        if decision.decision.upper() == "RETRY":
            return GenerateKeywords(feedback=decision.reasoning)
        else:
            return ReadFiles(files_to_read=decision.files_to_read)


# --- Node D: Read Files (Deterministic) ---
@dataclass
class ReadFiles(BaseNode[SearchState, None, AgentDeps]):
    files_to_read: List[str]

    async def run(self, ctx: GraphRunContext[SearchState]) -> "GenerateAnswer":
        file_contents = []
        prefix = f"agent-memory/{ctx.deps.customer_id}"
        if not self.files_to_read:
            file_contents.append(
                "No specific files identified. Relying on grep snippets."
            )
            file_contents.extend(ctx.state.grep_results_log)
        else:
            for rel_path in self.files_to_read:
                rel_path = rel_path.strip()
                object_name = f"{prefix}/{rel_path}"
                try:
                    cache_path = _ensure_file_cached(
                        ctx.deps.storage, ctx.deps.cache_dir, object_name
                    )
                    content = cache_path.read_text(encoding="utf-8")
                    file_contents.append(
                        f"--- START FILE: {rel_path} ---\n{content}\n--- END FILE ---\n"
                    )
                except Exception as e:
                    file_contents.append(f"Error reading {rel_path}: {e}")

        ctx.state.final_file_contents = "\n".join(file_contents)
        return GenerateAnswer()


# --- Node E: Evaluate Result (Generate Answer) ---
@dataclass
class GenerateAnswer(BaseNode[SearchState, None, AgentDeps]):
    async def run(self, ctx: GraphRunContext[SearchState]) -> End[str]:
        prompt = (
            f"User Query: {ctx.state.user_query}\n\n"
            "Reference Documents:\n"
            f"{ctx.state.final_file_contents}\n\n"
            "Please answer the user's question accurately based on the documents above. "
            "If the documents don't contain the answer, admit it."
        )
        writer_agent = _get_writer_agent(ctx.deps.model_name)
        result = await writer_agent.run(prompt)
        # Standard string agents usually return the string in .data or .output.
        # For simple Agents without result_type, .data is usually the string.
        return End(result.output)


# ==============================================================================
# 5. Main Execution
# ==============================================================================
async def main():

    import dotenv

    dotenv.load_dotenv()
    import os

    from logfire import ConsoleOptions

    from app.utils.file_storage_manager import get_file_storage
    from app.utils.logfire import set_logfire_token_env_variables

    set_logfire_token_env_variables()

    logfire.configure(
        send_to_logfire="if-token-present",
        scrubbing=False,
        console=ConsoleOptions() if os.getenv("LOCAL_ACCESS") else None,
    )
    logfire.instrument_pydantic_ai()
    customer_id = "42072582-95f4-46ef-be06-bb7aa2cdcff8"
    bucket_name = "alltrue-test-evidence-storage"
    storage = get_file_storage(bucket_name=bucket_name)
    cache_dir = Path(tempfile.mkdtemp(prefix="pydantic_graph_qa_"))
    deps = AgentDeps(storage=storage, customer_id=customer_id, cache_dir=cache_dir)

    qa_graph = Graph(
        nodes=[GenerateKeywords, RunGrep, EvaluateGrep, ReadFiles, GenerateAnswer]
    )

    try:
        while True:
            user_input = input("\nUser (type 'exit' to quit): ")
            if user_input.strip().lower() in {"exit", "quit"}:
                break
            initial_state = SearchState(user_query=user_input)

            # FIX: Do NOT unpack. run() returns a single GraphRunResult object.
            run_result = await qa_graph.run(
                GenerateKeywords(), deps=deps, state=initial_state
            )
            print(run_result.output)
            # Access the final result via .output
    finally:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
