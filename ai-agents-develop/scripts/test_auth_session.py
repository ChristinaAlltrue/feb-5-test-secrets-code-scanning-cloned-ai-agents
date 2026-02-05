#!/usr/bin/env python3
"""
Test script for create_authenticated_session_with_agents function
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

# Set up logfire
import logfire
from logfire import ConsoleOptions

from app.core.agents.action_prototype.auth_agents.authentication_agent import (
    create_authenticated_session_with_agents,
)
from test_suite.credential import GHCO_PASSWORD, GHCO_USERNAME

# Configure logfire for standalone testing
logfire.configure(
    send_to_logfire=False,  # Don't send to cloud for testing
    scrubbing=False,
    console=ConsoleOptions(),  # Enable console output
)


async def test_auth_session():
    """Test the authentication session creation"""

    print("Testing create_authenticated_session_with_agents...")

    # Configuration
    login_url = "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
    test_url = "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
    username = GHCO_USERNAME
    password = GHCO_PASSWORD
    storage_state_path = Path("temp_storage/ghco_session.json")

    print(f"Login URL: {login_url}")
    print(f"Test URL: {test_url}")
    print(f"Username: {username}")
    print(f"Storage path: {storage_state_path}")
    try:
        # Test authentication
        auth_result = await create_authenticated_session_with_agents(
            login_url=login_url,
            test_url=test_url,
            username=username,
            password=password,
            storage_state_path=storage_state_path,
            headless=True,
        )

        if auth_result.is_authenticated == "yes":
            print("✅ Authentication successful!")
            print(f"Session state saved to: {storage_state_path}")
            print(f"Feedback: {auth_result.feedback}")

            # Check if file was created
            if storage_state_path.exists():
                print(
                    f"✅ Session file exists (size: {storage_state_path.stat().st_size} bytes)"
                )
            else:
                print("❌ Session file was not created")

        else:
            print("❌ Authentication failed!")
            print(f"Feedback: {auth_result.feedback}")
            if auth_result.redirect_url:
                print(f"Redirected to: {auth_result.redirect_url}")

    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        import traceback

        traceback.print_exc()


async def test_concurrent_auth():
    """Test concurrent authentication sessions"""

    print("\nTesting concurrent authentication sessions...")

    # Configuration
    login_url = "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
    test_url = "https://ghco-dev.archerirm.us/apps/ArcherApp/Home.aspx"
    username = GHCO_USERNAME
    password = GHCO_PASSWORD
    storage_state_path = Path("temp_storage/ghco_concurrent_session.json")

    async def auth_task(task_id: int):
        print(f"Task {task_id}: Starting authentication...")
        auth_result = await create_authenticated_session_with_agents(
            login_url=login_url,
            test_url=test_url,
            username=username,
            password=password,
            storage_state_path=storage_state_path,
            headless=True,
        )
        success = auth_result.is_authenticated == "yes"
        result = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"Task {task_id}: {result}")
        if not success:
            print(f"Task {task_id}: Feedback - {auth_result.feedback}")
        return success

    # Run 3 concurrent authentication tasks
    tasks = [auth_task(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Summary
    successful = sum(1 for r in results if r is True)
    print(f"\nConcurrent test summary: {successful}/{len(results)} tasks succeeded")

    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"Task {i}: Exception - {result}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test GHCO authentication session")
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Test concurrent authentication sessions",
    )

    args = parser.parse_args()

    if args.concurrent:
        asyncio.run(test_concurrent_auth())
    else:
        asyncio.run(test_auth_session())


if __name__ == "__main__":
    main()
