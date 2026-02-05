from test_suite_v2.test_module.supervisor_agent.sample_two_action import (
    get_sample_two_action,
)
from test_suite_v2.test_module.supervisor_agent.sample_two_action_pause import (
    get_sample_two_action_pause,
)


def get_test_settings():
    """Factory function that generates fresh UUIDs each time it's called."""
    return {
        **get_sample_two_action(),
        **get_sample_two_action_pause(),
    }


# For backward compatibility, also expose as a dict (but it will be regenerated on each access)
TEST_SETTINGS = get_test_settings()
