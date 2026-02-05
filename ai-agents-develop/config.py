#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.

import os

import dotenv
from alltrue.local.parameter_manager.parameter_manager_factory import (
    get_parameter_manager,
)

dotenv.load_dotenv()

SERVICE_NAME = "ai-agents"

# root directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# path to .env file
ENV_FILE_PATH = os.path.join(PROJECT_DIR, ".env")

# source directory app/
APP_DIR = os.path.join(PROJECT_DIR, "app")

# source for API
API_DIR = os.path.join(APP_DIR, "api")

# directory for sqlalchemy models
MODELS_DIR_PATH = os.path.join(APP_DIR, "core", "db", "models")


parameter_manager = get_parameter_manager()
parameter_manager.fetch(parameter_names=["/config/agents-evidence-storage-bucket"])
AGENTS_EVIDENCE_STORAGE_BUCKET = parameter_manager.get(
    "/config/agents-evidence-storage-bucket"
)

# default is false, there are some bugs when RQ working with MCP processes
RQ_BACKGROUND_TASKS_ENABLED = (
    os.getenv("RQ_BACKGROUND_TASKS_ENABLED", "false").lower() == "true"
)


# By default it is True, will send events to Control Plane
CONTROL_PLANE_EVENT_HANDLER_ENABLED = (
    os.getenv("CONTROL_PLANE_EVENT_HANDLER_ENABLED", "true").lower() == "true"
)


STORAGE_BACKEND = "sqlite"
SQLITE_DATABASE_URL = "sqlite+aiosqlite:///./database.db"
SQLITE_DATABASE_SYNC_URL = "sqlite:///./database.db"
# this is used to determine the type of the UUID column
IS_SQLITE = STORAGE_BACKEND == "sqlite"

# Server has to be headless for the browser-use usage, by default it is False
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

# Playwright MCP server mode, by default it is DIRECT
PLAYWRIGHT_MCP_DIRECT = os.getenv("PLAYWRIGHT_MCP_DIRECT", "true").lower() == "true"

# Wrtiting to the env for browser-use usage, the package cannot be configured to use the parameter manager
os.environ["IS_IN_EVALS"] = "true"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
