<h1 align="center">
📖Streamlit Toy Chatbot📖
</h1>

**Toy chatbot applications to test LLM Gateway**

Select an LLM Provider and experiment with LLM Gateway rules.

## Installation

Follow the instructions below to run the Streamlit server locally.

### Pre-requisites

Make sure you have Python ≥3.10 installed.

### Steps

1. Install dependencies with Virtual Environment

```bash
source .venv/bin/activate  # or whatever command you use to activate your virtual environment

uv sync --active
```

3. Add `.env` file to top level.

See `.env.example` for how the file should look like.

4. Run the Streamlit server

```bash
PYTHONPATH=. uv run streamlit run app/main.py
```
