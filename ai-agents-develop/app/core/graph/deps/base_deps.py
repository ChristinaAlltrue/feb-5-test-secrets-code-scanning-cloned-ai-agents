from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import logfire
from browser_use import Browser
from pydantic import BaseModel

from app.core.models.models import ActionExecution, ControlExecution
from app.core.storage_dependencies.repositories.base import BaseRepository
from config import BROWSER_HEADLESS


class ControlInfo(BaseModel):
    customer_id: UUID
    control_id: UUID
    control_execution_id: UUID
    entity_id: UUID
    compliance_instruction: str = (
        ""  # TODO: currently give it a default value to avoid breaking changes, remove it in the future
    )


@dataclass
class BrowserDeps:
    browser_session: Optional[Browser] = None  # By Default it is None
    # control space is the place that the files are shared across all executions of the same control
    control_space_path: Path = Path("")
    entity_space_path: Path = Path("")
    # execution space is the place that the files are only used in the current execution
    execution_space_path: Path = Path("")

    download_path: Path = Path("")

    def init_browser_instance(
        self, control_info: "ControlInfo", allowed_domains: Optional[List[str]] = None
    ):
        # TODO: The cookie file may have to be stored in database or somewhere in the future
        # TODO: The download file may have to be stored in NFS or some shared volume in the future let it cross different servers

        # ==control space==
        self.control_space_path = Path(f"./UserData/{control_info.control_id}")
        self.control_space_path.mkdir(parents=True, exist_ok=True)

        # ==entity space==
        self.entity_space_path = Path(
            self.control_space_path / f"{control_info.entity_id}"
        )
        self.entity_space_path.mkdir(parents=True, exist_ok=True)

        # ==execution space==
        self.execution_space_path = Path(
            self.entity_space_path / f"{control_info.control_execution_id}"
        )
        self.execution_space_path.mkdir(parents=True, exist_ok=True)

        # ==download path==
        self.download_path = self.execution_space_path / "downloads"
        self.download_path.mkdir(parents=True, exist_ok=True)

        self.browser_session = Browser(
            keep_alive=True,
            headless=BROWSER_HEADLESS,
            downloads_path=self.download_path,
            user_data_dir=None,
            storage_state=self.entity_space_path / "storage_state.json",
            wait_for_network_idle_page_load_time=5,
            minimum_wait_page_load_time=2,
            allowed_domains=(allowed_domains or []),
        )

    async def dispose(self):
        if self.browser_session:
            logfire.info("Killing browser session")
            await self.browser_session.kill()  # Force stop even keep_alive is True


class BaseDeps(BaseModel):
    """Base state with common functionality for all state types"""

    model_config = {"arbitrary_types_allowed": True}

    control_info: ControlInfo
    working_dir: Optional[str] = None

    action_repo: BaseRepository[ActionExecution]
    control_repo: BaseRepository[ControlExecution]

    browser_deps: Optional[BrowserDeps] = None

    def model_post_init(self, __context):
        if self.working_dir is None:
            self.working_dir = str(
                Path(
                    f"./UserData/{self.control_info.control_id}/{self.control_info.entity_id}/{self.control_info.control_execution_id}"
                ).resolve()
            )
            Path(self.working_dir).mkdir(parents=True, exist_ok=True)

    def get_browser_deps(self) -> Optional[BrowserDeps]:
        return self.browser_deps

    def init_browser_deps(self, allowed_domains: Optional[List[str]] = None):
        if self.browser_deps is None:
            self.browser_deps = BrowserDeps()
            self.browser_deps.init_browser_instance(self.control_info, allowed_domains)
        else:
            logfire.info("Skipping browser deps initialization, already initialized")

    async def dispose(self):
        if self.browser_deps:
            await self.browser_deps.dispose()
