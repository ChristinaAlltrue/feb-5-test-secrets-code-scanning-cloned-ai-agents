"""
Authentication agents for dynamic login element detection and authentication status checking.
"""

import json
from pathlib import Path
from typing import Literal, Optional

import logfire
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm

AUTHENTICATION_MODEL_NAME = "gpt-4o-mini-2024-07-18"


class LoginElementsResult(BaseModel):
    """Result model for login element detection"""

    username_selector: str = Field(description="CSS selector for username field")
    password_selector: str = Field(description="CSS selector for password field")
    login_button_selector: str = Field(description="CSS selector for login button")
    success: Literal["yes", "no"] = Field(
        description="Whether elements were found successfully"
    )
    feedback: str = Field(description="Additional feedback about the detection process")


class AuthStatusResult(BaseModel):
    """Result model for authentication status check"""

    is_authenticated: Literal["yes", "no"] = Field(
        description="Whether user is authenticated"
    )
    redirect_url: Optional[str] = Field(
        default=None, description="URL redirected to if not authenticated"
    )
    feedback: str = Field(description="Details about the authentication check")


async def create_login_element_detection_agent(
    login_url: str, headless: bool = True
) -> LoginElementsResult:
    """
    Create an agent that dynamically finds login form elements on a webpage.

    Args:
        login_url: The URL of the login page
        headless: Whether to run browser in headless mode

    Returns:
        LoginElementsResult with selectors for username, password, and login button
    """

    logfire.info(f"Creating login element detection agent for {login_url}")

    # Create the element detection agent
    agent = Agent(
        model=get_pydanticai_openai_llm(model_name=AUTHENTICATION_MODEL_NAME),
        output_type=LoginElementsResult,
        system_prompt="""You are a web element detection agent. Your task is to analyze a login page
        and identify the CSS selectors for:
        1. Username/email input field
        2. Password input field
        3. Login/submit button

        You will be provided with the page HTML content. Analyze the structure and return the most
        reliable CSS selectors for each element. Look for:
        - Input fields with type="text", type="email", or similar for username
        - Input fields with type="password" for password
        - Buttons or inputs with type="submit" or containing "login", "sign in" text

        Return specific, unique selectors that will reliably target these elements.
        If you cannot find clear login elements, set success to "no" and explain why.""",
    )

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to login page
            await page.goto(login_url)
            await page.wait_for_load_state("networkidle")

            # Get page content for analysis
            page_content = await page.content()

            # Run the agent to detect elements
            async with agent:
                result = await agent.run(
                    f"Analyze this login page HTML and find selectors for username, password, and login button:\n\n{page_content[:10000]}..."
                )

            await browser.close()
            return result.output

    except Exception as e:
        logfire.error(f"Error in login element detection: {e}")
        return LoginElementsResult(
            username_selector="",
            password_selector="",
            login_button_selector="",
            success="no",
            feedback=f"Failed to detect login elements: {str(e)}",
        )


async def create_auth_status_agent(
    test_url: str, storage_state_path: Optional[Path] = None, headless: bool = True
) -> AuthStatusResult:
    """
    Create an agent that checks if a user session is authenticated.

    Args:
        test_url: URL of a protected page to test authentication
        storage_state_path: Path to stored browser session state
        headless: Whether to run browser in headless mode

    Returns:
        AuthStatusResult indicating authentication status
    """

    logfire.info(f"Creating authentication status agent for {test_url}")

    # Create the authentication check agent
    agent = Agent(
        model=get_pydanticai_openai_llm(model_name=AUTHENTICATION_MODEL_NAME),
        output_type=AuthStatusResult,
        system_prompt="""You are an authentication status detection agent. Your task is to determine
        if a user is authenticated on a website by analyzing the page content.

        Signs that indicate NOT authenticated:
        - Page contains login forms, "sign in" buttons, username/password fields
        - Page shows "Please log in", "Access denied", or similar messages
        - Redirected to a different domain or login page

        Signs that indicate authenticated:
        - Page shows user-specific content, dashboards, navigation menus
        - Page shows logout buttons, user profiles, or personalized content
        - No login forms present on the page

        Analyze the provided page content to determine authentication status.""",
    )

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)

            # Create context with storage state if provided
            context_options = {}
            if storage_state_path and storage_state_path.exists():
                with open(storage_state_path, "r") as f:
                    context_options["storage_state"] = json.load(f)

            context = await browser.new_context(**context_options)
            page = await context.new_page()

            # Navigate to test page
            await page.goto(test_url)
            await page.wait_for_load_state("networkidle")

            # wait for any dynamic content to load
            await asyncio.sleep(2)

            # Get current URL and page content
            current_url = page.url
            page_content = await page.content()

            # Run the agent to check authentication
            async with agent:
                result = await agent.run(
                    f"Check if user is authenticated based on this page:\n\n"
                    f"Original URL: {test_url}\n"
                    f"Current URL: {current_url}\n"
                    f"Page content: {page_content[:10000]}..."
                )

            await browser.close()

            # Add redirect URL if different from test URL
            auth_result = result.output
            if current_url != test_url:
                auth_result.redirect_url = current_url

            return auth_result

    except Exception as e:
        logfire.error(f"Error in authentication status check: {e}")
        return AuthStatusResult(
            is_authenticated="no",
            feedback=f"Failed to check authentication status: {str(e)}",
        )


async def _is_lock_stale(lock_file_path: Path, max_age_seconds: int = 300) -> bool:
    """
    Check if a lock file is stale (indicating potential deadlock).

    Args:
        lock_file_path: Path to the lock file
        max_age_seconds: Maximum age in seconds before considering lock stale

    Returns:
        True if lock is stale, False otherwise
    """
    import psutil

    try:
        if not lock_file_path.exists():
            return False

        # Check lock file age
        lock_age = time.time() - lock_file_path.stat().st_mtime
        if lock_age > max_age_seconds:
            logfire.warning(
                f"Lock file is {lock_age:.1f} seconds old (max: {max_age_seconds})"
            )
            return True

        # Try to read lock info to check if process is still alive
        try:
            with open(lock_file_path, "r") as f:
                lock_info = json.load(f)
                lock_pid = lock_info.get("pid")

                if lock_pid:
                    # Check if process is still running
                    if not psutil.pid_exists(lock_pid):
                        logfire.warning(f"Lock held by dead process PID {lock_pid}")
                        return True

                    # Check if process is in zombie state
                    try:
                        proc = psutil.Process(lock_pid)
                        if proc.status() == psutil.STATUS_ZOMBIE:
                            logfire.warning(
                                f"Lock held by zombie process PID {lock_pid}"
                            )
                            return True
                    except psutil.NoSuchProcess:
                        logfire.warning(
                            f"Lock held by non-existent process PID {lock_pid}"
                        )
                        return True

        except (json.JSONDecodeError, KeyError, ValueError):
            # If we can't read lock info, consider it potentially stale
            logfire.warning("Could not parse lock file info")
            return lock_age > 60  # Conservative timeout if we can't check process

        return False

    except Exception as e:
        logfire.warning(f"Error checking lock staleness: {e}")
        return False


import asyncio
import fcntl
import os
import time


async def create_authenticated_session_with_agents(
    login_url: str,
    test_url: str,
    username: str,
    password: str,
    storage_state_path: Path,
    headless: bool = True,
    by_pass_login: bool = False,
) -> AuthStatusResult:
    """
    Create an authenticated session using agents to dynamically detect login elements.
    The session state is shared between different clients for concurrent access.

    Args:
        login_url: URL of the login page
        test_url: URL to test authentication status
        username: Username for login
        password: Password for login
        storage_state_path: Path to save shared session state
        headless: Whether to run browser in headless mode
        by_pass_login: For local testing - bypass authentication and create minimal session state

    Returns:
        AuthStatusResult with authentication status and details
    """

    # Early exit for bypass mode - avoid all locking and browser overhead for local testing
    if by_pass_login:
        logfire.info(
            "Bypass mode enabled for local testing - creating minimal session state"
        )
        storage_state_path.parent.mkdir(parents=True, exist_ok=True)

        # Write minimal valid storage state directly (no browser needed)
        minimal_state: dict = {"cookies": [], "origins": []}
        with open(storage_state_path, "w") as f:
            json.dump(minimal_state, f)

        logfire.info(
            f"Minimal session state created at {storage_state_path} for local testing"
        )
        return AuthStatusResult(
            is_authenticated="yes",
            feedback="Bypassed login for local testing (no actual authentication performed)",
        )

    logfire.info(
        "Creating authenticated session with shared state for concurrent access"
    )

    # Use file locking to prevent race conditions when multiple clients authenticate simultaneously
    lock_file_path = storage_state_path.parent / f"{storage_state_path.stem}.lock"

    try:
        # Create lock file directory if it doesn't exist
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Acquire file lock for authentication process with deadlock prevention
        with open(lock_file_path, "w") as lock_file:
            # Write process ID and timestamp to lock file for debugging
            lock_info = {
                "pid": os.getpid(),
                "timestamp": time.time(),
                "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
            }
            lock_file.write(json.dumps(lock_info))
            lock_file.flush()

            try:
                # Try to acquire exclusive lock (non-blocking)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logfire.info(
                    f"Acquired authentication lock (PID: {os.getpid()}), proceeding with login"
                )

                # Check if we already have a valid session
                if storage_state_path.exists():
                    # Test existing session first
                    auth_status = await create_auth_status_agent(
                        test_url, storage_state_path, headless
                    )
                    if auth_status.is_authenticated == "yes":
                        logfire.info(
                            "Existing session is still valid, reusing shared state"
                        )
                        return auth_status
                    else:
                        logfire.info("Existing session expired, creating new one")

                # Step 1: Detect login elements
                login_elements = await create_login_element_detection_agent(
                    login_url, headless
                )

                if login_elements.success == "no":
                    logfire.error(
                        f"Failed to detect login elements: {login_elements.feedback}"
                    )
                    return AuthStatusResult(
                        is_authenticated="no",
                        feedback=f"Failed to detect login elements: {login_elements.feedback}",
                    )

                logfire.info(
                    f"Detected login elements: username={login_elements.username_selector}, "
                    f"password={login_elements.password_selector}, button={login_elements.login_button_selector}"
                )

                # Step 2: Perform login using detected elements
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch(headless=headless)
                    try:
                        # Create browser context for authentication
                        context = await browser.new_context(
                            # Add user agent and viewport to avoid detection
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            viewport={"width": 1920, "height": 1080},
                        )

                        page = await context.new_page()

                        # Navigate to login page
                        await page.goto(login_url)
                        await page.wait_for_load_state("networkidle")

                        # Fill credentials using detected selectors
                        await page.fill(login_elements.username_selector, username)
                        await page.fill(login_elements.password_selector, password)

                        # Click login button
                        await page.click(login_elements.login_button_selector)
                        await page.wait_for_load_state("networkidle")

                        # wait for loading and processing
                        await asyncio.sleep(3)

                        # Save shared session state
                        storage_state_path.parent.mkdir(parents=True, exist_ok=True)
                        await context.storage_state(path=str(storage_state_path))

                        # # save the page screenshot for debugging
                        # screenshot_path = storage_state_path.parent / "login_result.png"
                        # await page.screenshot(path=str(screenshot_path))

                        logfire.info(
                            f"Shared session state saved to {storage_state_path}"
                        )

                    finally:
                        # Ensure browser is always closed
                        await browser.close()

                # Step 3: Verify authentication
                auth_status = await create_auth_status_agent(
                    test_url, storage_state_path, headless
                )

                if auth_status.is_authenticated == "yes":
                    logfire.info(
                        "Authentication successful, shared session ready for all clients"
                    )
                    return auth_status
                else:
                    logfire.error(f"Authentication failed: {auth_status.feedback}")
                    return auth_status

            except BlockingIOError:
                # Another process is already authenticating, implement deadlock detection
                logfire.info(
                    "Another client is authenticating, checking for deadlock..."
                )

                # Check if the lock is stale (deadlock detection)
                if await _is_lock_stale(lock_file_path):
                    logfire.warning("Detected stale lock, attempting recovery")
                    try:
                        # Force remove stale lock file
                        lock_file_path.unlink()
                        logfire.info("Removed stale lock file, retrying authentication")
                        # Recursive retry (but only once to avoid infinite recursion)
                        return await create_authenticated_session_with_agents(
                            login_url,
                            test_url,
                            username,
                            password,
                            storage_state_path,
                            headless,
                            by_pass_login,
                        )
                    except Exception as e:
                        logfire.error(f"Failed to recover from stale lock: {e}")
                        return AuthStatusResult(
                            is_authenticated="no",
                            feedback=f"Failed to recover from stale lock: {str(e)}",
                        )

                # Wait for other process to complete authentication (with timeout)
                max_wait_time = 60  # 60 seconds timeout
                start_time = time.time()

                while time.time() - start_time < max_wait_time:
                    await asyncio.sleep(2)  # Check every 2 seconds

                    # Check again if lock became stale during waiting
                    if await _is_lock_stale(lock_file_path):
                        logfire.warning("Lock became stale during wait, breaking out")
                        break

                    if storage_state_path.exists():
                        # Test if the session created by other process is valid
                        auth_status = await create_auth_status_agent(
                            test_url, storage_state_path, headless
                        )
                        if auth_status.is_authenticated == "yes":
                            logfire.info(
                                "Using shared session created by another client"
                            )
                            return auth_status

                logfire.error("Timeout waiting for shared authentication session")
                return AuthStatusResult(
                    is_authenticated="no",
                    feedback="Timeout waiting for shared authentication session",
                )

    except Exception as e:
        logfire.error(f"Error creating shared authenticated session: {e}")
        return AuthStatusResult(
            is_authenticated="no",
            feedback=f"Error creating shared authenticated session: {str(e)}",
        )
    finally:
        # Clean up lock file
        try:
            if lock_file_path.exists():
                lock_file_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors
