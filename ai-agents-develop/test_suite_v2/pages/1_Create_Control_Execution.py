import json  # Import json for better display of request preview/response
import os
import sys
from pathlib import Path
from runpy import run_path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import streamlit as st
from alltrue.agents.schema.control_execution import (
    PostControlExecutionRequest,
    ResetControlExecutionHeadToIndexRequest,
    ResumeControlExecutionRequest,
    RunControlExecutionRequest,
)
from alltrue.client.client import Client
from alltrue.client.client_config import Client_Config

st.set_page_config(page_title="Create Control Execution", page_icon="🎯", layout="wide")


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
TEST_MODULE_ROOT = BASE_DIR / "test_module"

# Ensure project root is on sys.path so absolute package imports work in run_path'ed files
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_module_from_path(module_name: str, file_path: Path):
    try:
        # Ensure PROJECT_ROOT is on the path for imports like test_suite.credential
        # (test_suite is a package under PROJECT_ROOT)
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        globals_dict = run_path(str(file_path), run_name=module_name)
        return SimpleNamespace(**globals_dict)
    except Exception as e:
        # Log the error for debugging (Streamlit will show this in the UI)
        import traceback

        st.error(f"Error loading module {module_name} from {file_path}: {e}")
        st.code(traceback.format_exc())
        return None


def discover_modules(root: Path) -> List[Tuple[str, Path]]:
    """
    Return a list of (display_name, settings_module_path) for each test submodule
    that exposes MODULE_CONFIG with keys 'name' and 'test_settings_module'.
    """
    modules: List[Tuple[str, Path]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        config_py = child / "config.py"
        if not config_py.exists():
            continue
        try:
            cfg = _load_module_from_path(
                module_name=f"tsv2.{child.name}.config", file_path=config_py
            )
            module_config = getattr(cfg, "MODULE_CONFIG", None) if cfg else None
            if not isinstance(module_config, dict):
                continue
            display_name = module_config.get("name") or child.name
            modules.append((str(display_name), child))
        except Exception:
            continue
        except BaseException:  # Catch broader exceptions during loading
            continue
    return modules


def load_test_cases(module_dir: Path) -> Tuple[Dict[str, Any], bool]:
    """
    Load test cases from a module directory.
    Returns: (test_cases_dict, uses_factory_function)
    """
    try:
        settings_py = module_dir / "settings.py"
        if not settings_py.exists():
            return {}, False
        mod = _load_module_from_path(
            module_name=f"tsv2.{module_dir.name}.settings", file_path=settings_py
        )
        if mod is None:
            return {}, False

        # Check if there's a factory function first (preferred for fresh UUIDs)
        get_test_settings = getattr(mod, "get_test_settings", None)
        if callable(get_test_settings):
            tests = get_test_settings()
            return (tests if isinstance(tests, dict) else {}), True

        # Fall back to TEST_SETTINGS dict (for backward compatibility)
        tests = getattr(mod, "TEST_SETTINGS", {}) if mod else {}
        return (tests if isinstance(tests, dict) else {}), False
    except Exception as e:
        import traceback

        st.error(f"Error loading test cases from {module_dir}: {e}")
        st.code(traceback.format_exc())
        return {}, False


def coerce_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(value)
    except Exception:
        return None


def to_jsonable(obj: Any) -> Any:
    """Convert pydantic/dataclass-like objects to JSON-serializable recursively."""
    # Pydantic v1/v2 compat: most objects have .model_dump or .dict
    if hasattr(obj, "model_dump"):
        try:
            return to_jsonable(obj.model_dump())
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return to_jsonable(obj.dict())
        except Exception:
            pass
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj


def get_agents_client(api_base_url: str) -> Optional[Any]:
    """
    Initialize and return an AiAgentsClient instance configured for the given API base URL.
    Returns None if initialization fails.
    """
    try:
        # Extract host and port from API base URL
        # Expected format: http://localhost:8001 or https://example.com
        from urllib.parse import urlparse

        parsed = urlparse(api_base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (8001 if parsed.scheme == "http" else 443)
        scheme = parsed.scheme or "http"

        # Get access token from environment or use empty string for localhost
        access_token = os.environ.get("ACCESS_TOKEN", "")

        client = Client(access_token=access_token)
        client._client_config = Client_Config(
            api_endpoint=host,
            endpoint_port=port,
            schema=scheme,
            access_token=access_token,
        )
        return client.agents()
    except Exception as e:
        st.error(f"Error initializing SDK client: {e}")
        return None


st.title("Create Control Execution")
st.caption("Select a module and test case, choose a Control Execution ID, then create.")

with st.sidebar:
    st.page_link("Home.py", label="⬅ Back to Home")
    # Shared API base URL control (persists via session_state)
    default_api = os.environ.get("API_BASE_URL", "http://localhost:8001")
    st.text_input(
        "API Base URL",
        value=st.session_state.get("api_base_url", default_api),
        key="api_base_url",
    )


# Discover modules once and store in session
if "modules" not in st.session_state:
    st.session_state.modules = discover_modules(TEST_MODULE_ROOT)
if "test_cases_cache" not in st.session_state:
    # Cache per-module to avoid regenerating uuid4() objects on rerun
    st.session_state.test_cases_cache = {}
if "last_test_case_selection" not in st.session_state:
    # Track last test case selection to detect when it changes
    st.session_state.last_test_case_selection = None
if "control_exec_id_manually_set" not in st.session_state:
    # Track if control_execution_id was manually set (to preserve action IDs)
    st.session_state.control_exec_id_manually_set = False

modules: List[Tuple[str, Path]] = st.session_state.modules
module_names = [m[0] for m in modules] if modules else []

# --- Layout Restructure: First row (Setup + Preview) ---

# First row: Setup Args (Modules/Test Case/UUID/Actions) and Request Preview
col_setup_args, col_preview_request = st.columns([1, 1], gap="large")


# Define build_request_payload here so it's available for the actions
def build_request_payload() -> Optional[Dict[str, Any]]:
    # Need to access selected_test_case_name and test_cases from the surrounding scope
    if not selected_test_case_name:
        return None
    obj = test_cases.get(selected_test_case_name)
    if obj is None:
        return None
    payload = to_jsonable(obj)
    # Override control_execution_id if provided (from textbox/session)
    user_uuid = coerce_uuid(st.session_state.get("control_execution_id", ""))
    if user_uuid and isinstance(payload, dict):
        payload["control_execution_id"] = str(user_uuid)
    return payload if isinstance(payload, dict) else None


# Prepare necessary variables for the actions section
default_api = os.environ.get("API_BASE_URL", "http://localhost:8001")
api_base_url = st.session_state.get("api_base_url", default_api)
# Note: selected_module_name and selected_test_case_name are defined in the next block

with col_setup_args:
    st.header("Choose module and test case")

    # Row 1: Select Module & Select Test Case
    module_col, test_case_col = st.columns([1, 1])

    def _on_module_change():
        # Clear dependent selection so the test case options refresh correctly
        if "selected_test_case_name" in st.session_state:
            del st.session_state["selected_test_case_name"]

    with module_col:
        selected_module_name = st.selectbox(
            "Test Module",
            options=module_names,
            index=0 if module_names else None,
            placeholder="Select a test module",
            key="selected_module_name",
            on_change=_on_module_change,
        )

    # Load test cases based on selected module
    selected_module_dir: Optional[Path] = None
    if selected_module_name:
        for display_name, module_dir in modules:
            if display_name == selected_module_name:
                selected_module_dir = module_dir
                break

    cache_key = str(selected_module_dir) if selected_module_dir else None
    test_cases: Dict[str, Any]

    # Get current test case selection from session state (before selectbox renders)
    previous_test_case = st.session_state.get("selected_test_case_name")

    # Check if we have cached test cases for this module
    cached_test_cases = None
    cached_uses_factory = False
    if cache_key and cache_key in st.session_state.test_cases_cache:
        cached_entry = st.session_state.test_cases_cache[cache_key]
        if isinstance(cached_entry, tuple):
            cached_test_cases, cached_uses_factory = cached_entry
        else:
            cached_test_cases = cached_entry

    # Load test cases to get the list for the selectbox (only if not cached)
    if cached_test_cases:
        test_case_names = list(cached_test_cases.keys())
    else:
        initial_test_cases, _ = (
            load_test_cases(selected_module_dir) if selected_module_dir else ({}, False)
        )
        test_case_names = list(initial_test_cases.keys())

    with test_case_col:
        selected_test_case_name = st.selectbox(
            "Test Case",
            options=test_case_names,
            index=0 if test_case_names else None,
            placeholder="Select a test case",
            key="selected_test_case_name",
        )

    # Check if test case selection changed (need to regenerate UUIDs)
    current_selection = (
        f"{selected_module_name}:{selected_test_case_name}"
        if (selected_module_name and selected_test_case_name)
        else None
    )
    test_case_changed = (
        current_selection != st.session_state.last_test_case_selection
        or (previous_test_case != selected_test_case_name and selected_test_case_name)
    )

    # If test case changed, clear the manual flag and regenerate UUIDs
    if test_case_changed and current_selection:
        st.session_state.control_exec_id_manually_set = False
        st.session_state.last_test_case_selection = current_selection
        # Regenerate test cases with fresh UUIDs
        test_cases, uses_factory = (
            load_test_cases(selected_module_dir) if selected_module_dir else ({}, False)
        )
        # Cache them (always cache to preserve UUIDs on subsequent reruns)
        if cache_key:
            st.session_state.test_cases_cache[cache_key] = test_cases
    elif cache_key and cache_key in st.session_state.test_cases_cache:
        # Use cached test cases if available (preserve UUIDs on button clicks)
        cached_entry = st.session_state.test_cases_cache[cache_key]
        if isinstance(cached_entry, tuple):
            test_cases, uses_factory = cached_entry
        else:
            test_cases = cached_entry
            uses_factory = False
    else:
        # First load or no cache - regenerate
        test_cases, uses_factory = (
            load_test_cases(selected_module_dir) if selected_module_dir else ({}, False)
        )
        # Always cache to preserve UUIDs on subsequent reruns
        if cache_key:
            st.session_state.test_cases_cache[cache_key] = test_cases

    # Row 2: Control Execution ID and Generate Button
    st.markdown("### Control Execution ID")
    uuid_input_col, uuid_button_col = st.columns([3, 1])

    # Track previous value to detect manual changes
    previous_control_exec_id = st.session_state.get("control_execution_id", "")

    with uuid_input_col:
        control_exec_id_str = st.text_input(
            "ID (UUID)",
            value=previous_control_exec_id,
            placeholder="Enter a UUID or generate one",
            label_visibility="collapsed",
            key="control_execution_id_input",
        )
    with uuid_button_col:
        # st.markdown("<br>", unsafe_allow_html=True) # Vertical alignment trick
        if st.button("Generate UUID4", use_container_width=True):
            new_uuid = str(uuid4())
            st.session_state.control_execution_id = new_uuid
            # Mark as manually set to preserve action IDs
            st.session_state.control_exec_id_manually_set = True
            # Cache current test cases to preserve action IDs (use already loaded test_cases)
            if cache_key and selected_test_case_name:
                st.session_state.test_cases_cache[cache_key] = test_cases
            st.rerun()

    # Detect manual changes to the input field
    # Check if the value in the input differs from session state (user typed something)
    if control_exec_id_str != previous_control_exec_id and control_exec_id_str:
        st.session_state.control_execution_id = control_exec_id_str
        # Mark as manually set to preserve action IDs
        st.session_state.control_exec_id_manually_set = True
        # Cache current test cases to preserve action IDs (use already loaded test_cases)
        if cache_key and selected_test_case_name:
            st.session_state.test_cases_cache[cache_key] = test_cases

    # --- START OF MOVED ACTION COLUMN CONTENT ---

    st.divider()
    st.markdown("### Actions")

    action_feedback_placeholder = st.empty()

    create_tab, run_tab, resume_tab, reset_tab, create_run_old_tab = st.tabs(
        [
            "Create Control",
            "Run Control",
            "Resume Control",
            "Reset Head",
            "create-run(old)",
        ]
    )

    create_disabled = not (
        selected_module_name and selected_test_case_name and api_base_url
    )
    run_resume_disabled = not (
        api_base_url and coerce_uuid(st.session_state.get("control_execution_id", ""))
    )

    with create_tab:
        st.caption("Create or update a control execution without triggering a run.")
        st.write("This will persist the selected test case configuration.")
        if st.button(
            "Create Control",
            type="primary",
            use_container_width=True,
            disabled=create_disabled,
            key="create_control_button",
        ):
            payload = build_request_payload()
            if payload and "control_execution_id" in payload:
                st.session_state.control_execution_id = payload["control_execution_id"]
            if not payload:
                action_feedback_placeholder.error("Invalid test case payload.")
            else:
                try:
                    client = get_agents_client(api_base_url)
                    if not client:
                        action_feedback_placeholder.error(
                            "Failed to initialize SDK client."
                        )
                    else:
                        request = PostControlExecutionRequest(**payload)
                        response = client.create_control_only(request)
                        action_feedback_placeholder.success(
                            "Control Execution created or updated successfully."
                        )
                        st.session_state.response_json = to_jsonable(response)
                except Exception as e:
                    action_feedback_placeholder.error(f"Error calling API: {e}")
                    st.session_state.response_json = {}

    with run_tab:
        st.caption("Run an existing control execution.")
        st.info(
            "Provide a Control Execution ID above, then choose whether to run step by step."
        )
        run_step_by_step = st.checkbox(
            "Run step by step",
            key="run_step_by_step_flag",
            help="Queue the graph run in step-by-step mode.",
        )
        if st.button(
            "Queue Run",
            use_container_width=True,
            disabled=run_resume_disabled,
            key="run_control_button",
        ):
            control_execution_id = st.session_state.get("control_execution_id", "")
            if not coerce_uuid(control_execution_id):
                action_feedback_placeholder.error(
                    "Please provide a valid Control Execution ID before running."
                )
            else:
                try:
                    client = get_agents_client(api_base_url)
                    if not client:
                        action_feedback_placeholder.error(
                            "Failed to initialize SDK client."
                        )
                    else:
                        request = RunControlExecutionRequest(
                            control_execution_id=UUID(str(control_execution_id)),
                            run_step_by_step=bool(run_step_by_step),
                        )
                        response = client.run_control_only(request)
                        action_feedback_placeholder.success(
                            "Control Execution run queued successfully."
                        )
                        st.session_state.response_json = to_jsonable(response)
                except Exception as e:
                    action_feedback_placeholder.error(f"Error calling API: {e}")
                    st.session_state.response_json = {}

    with resume_tab:
        st.caption("Resume a control execution with optional extra instructions.")
        st.write("Use this to provide additional context before resuming the graph.")
        resume_step_by_step = st.checkbox(
            "Resume step by step",
            key="resume_step_by_step_flag",
            help="Resume execution in step-by-step mode.",
        )
        extra_instructions = st.text_area(
            "Extra instructions",
            key="resume_extra_instructions_input",
            placeholder="Add any additional guidance for the agent...",
            height=150,
        )

        if st.button(
            "Queue Resume",
            use_container_width=True,
            disabled=run_resume_disabled,
            key="resume_control_button",
        ):
            control_execution_id = st.session_state.get("control_execution_id", "")
            if not coerce_uuid(control_execution_id):
                action_feedback_placeholder.error(
                    "Please provide a valid Control Execution ID before resuming."
                )
            else:
                try:
                    client = get_agents_client(api_base_url)
                    if not client:
                        action_feedback_placeholder.error(
                            "Failed to initialize SDK client."
                        )
                    else:
                        request = ResumeControlExecutionRequest(
                            control_execution_id=UUID(str(control_execution_id)),
                            extra_instructions=extra_instructions or "",
                            resume_step_by_step=bool(resume_step_by_step),
                        )
                        response = client.resume_control_execution(request)
                        action_feedback_placeholder.success(
                            "Control Execution resume queued successfully."
                        )
                        st.session_state.response_json = to_jsonable(response)
                except Exception as e:
                    action_feedback_placeholder.error(f"Error calling resume API: {e}")
                    st.session_state.response_json = {}

    with reset_tab:
        st.caption("Reset the head index for the current control execution.")
        st.warning(
            "This will truncate action history after the selected index. "
            "Make sure you understand the impact before resetting."
        )
        reset_index = st.number_input(
            "New head index",
            min_value=0,
            step=1,
            key="reset_head_index_input",
        )
        if st.button(
            "Confirm Reset",
            type="secondary",
            use_container_width=True,
            disabled=run_resume_disabled,
            key="reset_head_button",
        ):
            control_execution_id = st.session_state.get("control_execution_id")

            if not coerce_uuid(str(control_execution_id or "")):
                action_feedback_placeholder.error(
                    "Please provide a valid Control Execution ID before resetting."
                )
            else:
                try:
                    client = get_agents_client(api_base_url)
                    if not client:
                        action_feedback_placeholder.error(
                            "Failed to initialize SDK client."
                        )
                    else:
                        request = ResetControlExecutionHeadToIndexRequest(
                            control_execution_id=UUID(str(control_execution_id)),
                            reset_to=int(reset_index),
                        )
                        response = client.reset_control_execution_head_to_index(request)
                        action_feedback_placeholder.success(
                            "Control Execution head reset successfully."
                        )
                        st.session_state.response_json = to_jsonable(response)
                except Exception as e:
                    action_feedback_placeholder.error(
                        f"Error calling Reset Head API: {e}"
                    )
                    st.session_state.response_json = {}

    with create_run_old_tab:
        st.caption("Create and run a control execution in one step (legacy method).")
        st.write(
            "This will create the control execution and immediately queue it for execution."
        )
        if st.button(
            "Create & Run Control",
            type="primary",
            use_container_width=True,
            disabled=create_disabled,
            key="create_run_old_button",
        ):
            payload = build_request_payload()
            if payload and "control_execution_id" in payload:
                st.session_state.control_execution_id = payload["control_execution_id"]
            if not payload:
                action_feedback_placeholder.error("Invalid test case payload.")
            else:
                try:
                    client = get_agents_client(api_base_url)
                    if not client:
                        action_feedback_placeholder.error(
                            "Failed to initialize SDK client."
                        )
                    else:
                        request = PostControlExecutionRequest(**payload)
                        response = client.run_control_execution(request)
                        action_feedback_placeholder.success(
                            "Control Execution created and run queued successfully."
                        )
                        st.session_state.response_json = to_jsonable(response)
                except Exception as e:
                    action_feedback_placeholder.error(f"Error calling API: {e}")
                    st.session_state.response_json = {}


# The build_request_payload function must be defined before its use in this block
# (It was moved earlier in the file to handle this)

with col_preview_request:
    st.header("Request Preview")
    preview = build_request_payload()

    with st.container(height=400, border=True):
        if preview is None:
            st.caption("Select a module and test case to preview the payload.")
        else:
            st.json(preview, expanded=True)


st.divider()

# --- Layout Restructure: Second row (now just Response View) ---
# Removed the column split for buttons/response

st.header("API Response")

# Add a button to fetch current control execution status (KEEP THIS AS IS)
status_message_placeholder = st.empty()
disabled_status_btn = not coerce_uuid(st.session_state.get("control_execution_id", ""))
if st.button("Get Control Execution Status", disabled=disabled_status_btn):
    control_id = st.session_state.get("control_execution_id", "")
    if not coerce_uuid(control_id):
        status_message_placeholder.error(
            "Please enter a valid Control Execution ID (UUID)."
        )
    else:
        try:
            client = get_agents_client(api_base_url)
            if not client:
                status_message_placeholder.error("Failed to initialize SDK client.")
            else:
                response = client.get_control_execution_status(UUID(str(control_id)))
                status_message_placeholder.success("Fetched control execution status.")
                st.session_state.response_json = to_jsonable(response)
        except Exception as e:
            status_message_placeholder.error(f"Error calling API: {e}")
            st.session_state.response_json = {}

# --- START OF NEW TWO-COLUMN LAYOUT ---

# 1. Get the response data safely
response_data = st.session_state.get("response_json", {})
action_ids = response_data.get("action_exec_history_ids")
is_valid_action_ids = isinstance(action_ids, list) and action_ids

# 2. Create the two columns (adjust ratio if needed, e.g., [1, 2] for more right space)
col_full_response, col_action_id_selector = st.columns([1, 1], gap="large")

# --- Left Column: Full JSON Response ---
with col_full_response:
    st.markdown("### Control Execution Response")
    with st.container(height=400, border=True):
        if response_data:
            st.json(response_data, expanded=True)
        else:
            st.caption("Response will appear here after a successful API call.")

# --- Right Column: Action ID Selector ---
with col_action_id_selector:
    st.markdown("### Select Action ID for Detail View")

    # Placeholder for messages related to fetching action details
    action_status_message_placeholder = st.empty()
    selected_action_if_placeholder = st.empty()
    if is_valid_action_ids:
        # 1. Action ID Radio Button
        selected_action_id = st.radio(
            "Action Execution ID",
            options=action_ids,
            index=0,
            key="selected_action_execution_id",
            label_visibility="collapsed",
        )

        selected_action_if_placeholder.info(f"Selected ID: **{selected_action_id}**")

        # 2. Action Detail Fetch Button
        def fetch_action_details(action_id: str):
            """Function to call the specific action execution API."""
            try:
                client = get_agents_client(api_base_url)
                if not client:
                    action_status_message_placeholder.error(
                        "Failed to initialize SDK client."
                    )
                else:
                    response = client.get_action_execution(UUID(str(action_id)))
                    action_status_message_placeholder.success(
                        f"Fetched details for action: {action_id}"
                    )
                    st.session_state.action_detail_json = to_jsonable(response)
            except Exception as e:
                action_status_message_placeholder.error(f"Error calling API: {e}")
                st.session_state.action_detail_json = {}

        if st.button(
            "Fetch Action Details",
            key="fetch_action_details_btn",
            use_container_width=True,
        ):
            # The selected ID is in the session state from the radio button
            fetch_action_details(st.session_state.selected_action_execution_id)

        st.markdown("### Action Detail Response")

        # 3. New JSON View for Action Details
        with st.container(height=250, border=True):
            action_detail_data = st.session_state.get("action_detail_json")
            if action_detail_data:
                st.json(action_detail_data, expanded=True)
            else:
                st.caption("Press 'Fetch Action Details' to load the response.")

    elif response_data:
        st.caption("No `action_exec_history_ids` found in the response.")
    else:
        st.caption("Awaiting API response containing action execution history.")
