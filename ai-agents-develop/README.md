# ai-agents

## Required
* `apt-get install -y libzbar0`
* `uv pip install browser-use`
* `playwright install chromium --with-deps --no-shell`
* `uv run playwright install`


## Usage
### Setup Environment
* Only Use Schema
    *  `uv sync`
* Run the client
    * `uv sync --extra client`
* Run the service
    * `uv sync --extra service`
* Develop
    * `uv sync --extra client --extra service --extra dev`
    * shortcut: `make sync-dev`

### Run the fastapi app service
Check more command in `Makefile`
```
make run
```
### Run the test with coverage report
```
make cov-report
```
### Run pre-commit hooks
```
make pc
```
## uv commands
### Add packages
* Add packages in the main dependencies
    * We don't add package here usually, since the main pakage is only schema
    * `uv add <package_name>`
* for client dependencies
    * `uv add <package_name> --client`
* for service dependencies
    * `uv add <package_name> --service`
* for development dependencies
    * `uv add <package_name> --dev`

### uninstall packages:
`uv remove <package_name> --{dependency group}`

### upgrade package:
`uv lock --upgrade-package <package name>`
* For example: `uv lock --upgrade-package alltrue`

Then `make sync-dev` again.

## External MCP Server (Development Only)

For development purposes, you can run the MCP server separately using external mode. This requires running the MCP server manually:

```bash
npx @playwright/mcp@0.0.40 --storage-state playwright/.auth/user.json --isolated --output-dir playwright/files --viewport-size 1280,900 --port 8931
```

### Debug element interaction issue

Some elements don't work well with playwright mcp, I used MCP Inspector to interact with page using the same interface for debugging.

```bash
# Install the inspector
npm install -g @modelcontextprotocol/inspector

# Run it with the playwright server
mcp-inspector npx -y @playwright/mcp-server
```

**Important**: Ensure the `external_downloads_path` parameter matches the `--output-dir` value (default: `playwright/files`).

### Creating Authentication Session

Before running the external MCP server, you need to create an authenticated session:

```bash
python scripts/create_auth_session.py
```

This script will:
1. Open a browser window for manual authentication
2. Save the session state to `playwright/.auth/user.json`
3. Display the complete MCP server command to run with the saved authentication state

The saved session state will be automatically used by the MCP server when you run the command above.



## Project Structure

The project is organized as follows:
```
├── app/                        # Main application package
│   ├── api/                   # API endpoints and routes
│   │   ├── core/              # Core API functionality
│   │   ├── routes/            # API route definitions
│   │   ├── services/          # API service layer
│   │   └── main.py            # API main entry point
│   ├── core/                  # Core application logic
│   │   ├── agents/            # Agent-related functionality
│   │   │   ├── action_prototype/        # Action prototype implementations
│   │   │   ├── base_action_schema/      # Base schemas for actions
│   │   │   ├── condition_resolve_agent/ # Condition resolution logic
│   │   │   ├── supervisor_agent/        # Supervisor agent implementations
│   │   │   └── utils/         # Agent utility functions
│   │   ├── graph/             # Graph-related functionality
│   │   │   ├── deps/          # Graph dependencies
│   │   │   ├── state/         # Graph state management
│   │   │   └── graph.py       # Graph implementation
│   │   ├── llm/               # Large Language Model integrations
│   │   │   ├── langchain/     # LangChain specific implementations
│   │   │   └── pydanticai/    # Pydantic AI integrations
│   │   ├── models/            # Data models and types
│   │   │   ├── models.py      # Database models
│   │   │   └── types.py       # Type definitions
│   │   ├── storage_dependencies/  # Storage layer dependencies
│   │   │   ├── repositories/  # Data repositories
│   │   │   ├── storage_dependencies.py  # Storage configuration
│   │   │   └── __main__.py    # Storage initialization
│   │   ├── prototype_loader.py  # Prototype loading utilities
│   │   └── registry.py        # Component registry
│   ├── exceptions/            # Custom exception definitions
│   ├── predefined_framework/  # Predefined framework configurations
│   │   ├── activate/          # Framework activation logic
│   │   └── deactivate/        # Framework deactivation logic
│   └── utils/                 # Utility functions and helpers
│       ├── chatgpt/           # ChatGPT specific utilities
│       │   └── openai_secret_key.py  # OpenAI key management
│       ├── cookie_contextmanager/    # Cookie management utilities
│       ├── deps_validation/   # Dependency validation utilities
│       ├── gmail/             # Gmail integration utilities
│       ├── mcp_server/        # MCP server utilities
│       ├── parameter_manager/ # Parameter management utilities
│       ├── secret_manager/    # Secret management utilities
│       ├── yaml_loader/       # YAML loading utilities
│       └── logfire.py         # Logging utilities
├── ai_agents/                 # AI Agents package
│   ├── alltrue_client.py      # AllTrue client implementation
│   └── schema/                # Schema-related files
│       ├── action_execution.py    # Action execution logic
│       ├── action_prototype.py    # Action prototype definitions
│       ├── control_execution.py   # Control flow execution
│       ├── entity.py             # Entity definitions
│       └── predefined.py         # Predefined schemas
├── tests/                     # Test suite
├── scripts/                   # Standalone test and utility scripts
├── cli.py                     # Command line interface
├── config.py                  # Configuration settings
├── main.py                    # Main application entry point
├── Makefile                   # Build and development commands
├── pyproject.toml             # Project configuration
└── README.md                  # Project documentation
```

The `PoC/` folder is excluded from this structure as it is not part of the main project.


## Run Testing
**Make sure you turn off the Zero Trust temporarily**

### Run pytest
```
# start test db:
make run-test-db
uv run python cli.py init-test-db
# run pytest
make test

# stop and clean test db
make stop-test-db
```

### Local Github Action Test

This is the same as the github action test we trigger in the github action workflow, but you can run it locally, which is faster.
#### pre-requisites
- act (https://github.com/nektos/act)
    - [Installation](https://nektosact.com/installation/index.html)
- docker

Also, there are some libraries that we need from private repositories, so you need to add your own GitHub ssh private key to the `.secrets` file.
create `.secrets` with your own GitHub ssh private key(`~/.ssh/id_rsa` or `~/.ssh/id_ed25519`):
```
SSH_PRIVATE_KEY="<your-ssh-private-key copy to here>"
```
remember to replace the new line with `\n`.
example:
```
SSH_PRIVATE_KEY="line1\nline2\nline3"
```
#### Run Local GitHub Actions Test

run github action test locally:
```
make local-action-test
```

## Running Scripts

The `scripts/` directory contains standalone test and utility scripts. These scripts should be run from the project root directory to ensure proper import paths:

```bash
# Run from the root directory
python scripts/test_entity_creation.py
python scripts/test_simple_multi_action.py
python scripts/test_audit_analysis_agent.py
```

**Note**: Scripts must be executed from the root directory as they depend on imports from `test_suite/` and other project modules.
