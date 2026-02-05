# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an AI agent orchestration system that executes compliance controls through a graph-based workflow engine. It uses browser automation, LLM agents, and various integrations to automate auditing and compliance tasks.

## Development Commands

### Environment Setup
```bash
# Install dependencies for development (includes client, service, and dev extras)
make sync-dev

# Or use specific extras:
uv sync --extra service    # Service dependencies only
uv sync --extra client     # Client dependencies only
```

### Running the Service
```bash
# Run FastAPI server with hot reload
make run

# Or directly:
uv run --active uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Testing
```bash
# Run all tests
make test

# Run tests with coverage report (opens browser on port 8099)
make cov-report

# Run test database
make run-test-db
uv run python cli.py init-test-db

# Stop test database
make stop-test-db

# Run local GitHub Actions tests (requires act and docker)
make local-action-test
```

### Code Quality
```bash
# Run pre-commit hooks
make pc
```

### Running Scripts
Scripts in `scripts/` directory must be run from the project root:
```bash
python scripts/test_entity_creation.py
python scripts/test_simple_multi_action.py
```

### Running Test Suites
```bash
# Interactive test suite CLI
python -m test_suite
```

## Architecture

### Core Components

**Graph Execution Engine** (`app/core/graph/`)
- **`graph.py`**: Creates and executes pydantic-graph based workflows from action nodes
- **`state/`**: Manages shared state across graph execution
- **`deps/`**: Dependency injection for graph nodes

**Action Prototype System** (`app/core/agents/action_prototype/`)
- Each action is a self-contained module with:
  - `register.py`: Registers the action with the registry
  - `action.py`: Implements the BaseNode logic
  - `schema.py`: Defines input dependencies and output models
  - `tool.py`: Optional custom tools for the action

**Registry Pattern** (`app/core/registry.py`)
- `PROTOTYPE_REGISTRY`: Maps action names to ActionPrototypeBundle
- `GRAPH_NODE_REGISTRY`: Maps action names to BaseNode implementations
- `TOOLS_REGISTRY`: Maps tool IDs to ToolBundle
- All actions must be imported in `app/core/prototype_loader.py` to be registered

**Storage Layer** (`app/core/storage_dependencies/`)
- Supports multiple backends: SQLite (default), PostgreSQL, Redis
- `storage_dependencies.py`: Factory pattern for storage providers
- `repositories/`: Repository pattern for data access
- Models: `ControlExecution`, `ActionExecution`

**API Layer** (`app/api/`)
- FastAPI application entry point: `app/api/main.py`
- Routes in `app/api/routes/`: action_execution, control_execution, framework, tools, etc.
- Services in `app/api/services/`: Event handlers and update services

### Key Concepts

**Action Prototype Bundle**
Each action is packaged as an `ActionPrototypeBundle` containing:
- `prototype`: Metadata (name, type, category, schemas)
- `deps_model`: Pydantic model for input dependencies
- `output_model`: Pydantic model for output
- `logic_cls`: BaseNode implementation

**Control Execution Flow**
1. Control execution created with actions
2. Graph built from action nodes
3. State persistence initialized
4. Graph executed with dependency injection
5. Compliance agent evaluates results

**Browser Automation**
- Uses `browser-use` library with Playwright
- Supports authentication state persistence in `playwright/.auth/`
- MCP (Model Context Protocol) server integration for browser control
- Configure with `BROWSER_HEADLESS` env var

**LLM Integration**
- Supports OpenAI, Anthropic (via pydantic-ai)
- Logfire instrumentation for tracing
- Model configuration in `app/core/llm/`

## Creating New Actions

1. Create new directory under `app/core/agents/action_prototype/{action_name}/`
2. Implement required files:
   - `schema.py`: Define `{ActionName}Deps` and `{ActionName}Output` models
   - `action.py`: Implement `{ActionName}(BaseNode)` class
   - `register.py`: Create and register `ActionPrototypeBundle`
3. Import register module in `app/core/prototype_loader.py`
4. Action automatically available in registry

## Environment Variables

Key environment variables (see README for full list):
- `LOCAL_ACCESS=true`: Enable local mode
- `STORAGE_BACKEND`: sqlite, postgres, or redis
- `BROWSER_HEADLESS`: Browser automation headless mode
- `CONTROL_PLANE_EVENT_HANDLER_ENABLED`: Enable/disable event handlers
- `CONFIG_OPENAI_API_KEY`: OpenAI API key
- `CONFIG_LOGFIRE_TOKEN`: Logfire telemetry token

## Dependencies

This project uses `uv` for package management with optional dependency groups:
- Main: Schema definitions (minimal)
- `service`: FastAPI, browser-use, pydantic-ai, storage backends
- `client`: AllTrue API client
- `dev`: Testing and pre-commit tools

Add packages with:
```bash
uv add <package> --service    # For service dependencies
uv add <package> --dev        # For dev dependencies
```

## External Browser MCP Server (Development)

For debugging browser interactions:
```bash
# Create auth session first
python scripts/create_auth_session.py

# Run external MCP server
npx @playwright/mcp@0.0.40 --storage-state playwright/.auth/user.json --isolated --output-dir playwright/files --viewport-size 1280,900 --port 8931

# Debug with MCP Inspector
npm install -g @modelcontextprotocol/inspector
mcp-inspector npx -y @playwright/mcp-server
```

## Important Notes

- Zero Trust must be disabled when running tests
- SSH private key required in `.secrets` for GitHub Actions local testing
- Scripts must be executed from project root for correct import paths
- Storage backend defaults to SQLite with `database.db`
- Browser automation requires: `apt-get install -y libzbar0` and Playwright chromium
