import os

import streamlit as st

st.set_page_config(
    page_title="Test Suite v2",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "_redirected_default_page" not in st.session_state:
    st.session_state["_redirected_default_page"] = True
    try:
        st.switch_page("pages/1_Create_Control_Execution.py")
    except Exception:
        pass

st.title("Test Suite v2")
st.caption("Streamlit UI for running test modules")

with st.sidebar:
    st.header("Modules")
    # Shared API base URL input for all pages
    default_api = os.environ.get("API_BASE_URL", "http://localhost:8001")
    st.text_input(
        "API Base URL",
        value=st.session_state.get("api_base_url", default_api),
        key="api_base_url",
    )
    st.page_link(
        "pages/1_Create_Control_Execution.py",
        label="Create Control Execution",
        icon="🎯",
    )

st.success("Use the left sidebar to choose a module.")
