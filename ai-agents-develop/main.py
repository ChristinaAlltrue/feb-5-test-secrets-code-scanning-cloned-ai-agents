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
import re

import logfire
from logfire import ConsoleOptions

from app.utils.logfire import set_logfire_token_env_variables

set_logfire_token_env_variables()

logfire.configure(
    send_to_logfire="if-token-present",
    scrubbing=False,
    console=ConsoleOptions() if os.getenv("LOCAL_ACCESS") else None,
)
logfire.instrument_requests(
    excluded_urls="https://search-*"  # exclude opensearch requests from tracing
)
logfire.instrument_httpx(
    excluded_urls="https://search-*"  # exclude opensearch requests from tracing
)
logfire.instrument_pydantic_ai()


# Which methods to auto-trace
def should_trace(module: logfire.AutoTraceModule) -> bool:
    """'
    add all services to be auto-traced. For example:

    ```python
    if re.match(r"app\.api\.v1\..services\..*", module.name) is not None:
        return True
    ```
    """
    if re.match(r"app\.api\.v1\..*service.*", module.name) is not None:
        return True
    return False


logfire.install_auto_tracing(should_trace, min_duration=0)

from app.api.main import app  # type: ignore
