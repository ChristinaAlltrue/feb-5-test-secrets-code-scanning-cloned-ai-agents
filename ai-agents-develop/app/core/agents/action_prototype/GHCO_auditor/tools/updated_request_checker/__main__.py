import asyncio

from pydantic import SecretStr

from app.core.agents.action_prototype.GHCO_auditor.tools.updated_request_checker.check_request_update import (
    check_request_update,
)
from test_suite.credential import GOOGLE_CREDENTIALS

if __name__ == "__main__":
    check_request_ids = ["REQ-3114054", "REQ-3114055", "REQ-3114056"]
    result = asyncio.run(
        check_request_update(check_request_ids, SecretStr(GOOGLE_CREDENTIALS))
    )
    print(result)
