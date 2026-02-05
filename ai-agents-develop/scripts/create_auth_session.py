"""
Authentication Session Creator for MCP Server

This script opens a browser window for manual authentication and saves the session state
to the location that the MCP server expects (playwright/.auth/user.json).

Usage:
    python scripts/create_auth_session.py

After authentication:
    1. The session state will be saved to playwright/.auth/user.json
    2. Run the MCP server with: npx @playwright/mcp@0.0.40 --storage-state playwright/.auth/user.json --isolated --output-dir playwright/files --viewport-size 1280,900 --port 8931
"""

import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_authenticated_session():
    """
    Create authenticated session by opening a browser window for manual login.
    Saves the session state to playwright/.auth/user.json for MCP server use.
    """
    print("🚀 Starting authentication session creator...")
    print("📋 This will open a browser window for you to manually log in")

    # Create auth directory if it doesn't exist
    auth_dir = Path("playwright/.auth")
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "user.json"

    print(f"💾 Session will be saved to: {auth_file.absolute()}")

    async with async_playwright() as playwright:
        # Launch browser in non-headless mode for manual authentication
        browser = await playwright.chromium.launch(
            headless=False,
            args=["--no-sandbox"],  # Add no-sandbox for better compatibility
        )

        # Create context with reasonable viewport size
        context = await browser.new_context(viewport={"width": 1280, "height": 900})

        page = await context.new_page()

        # Enable console logging for debugging
        page.on("console", lambda msg: logger.info(f"BROWSER: {msg.text}"))

        try:
            # Navigate to the login page (you can modify this URL as needed)
            login_url = "https://ghco-dev.archerirm.us/Default.aspx"
            print(f"🌐 Navigating to: {login_url}")

            await page.goto(login_url)

            print("\n" + "=" * 60)
            print("🔐 MANUAL AUTHENTICATION REQUIRED")
            print("=" * 60)
            print("1. Please log in manually in the browser window that opened")
            print("2. Navigate through the application as needed")
            print("3. When you're done, press Enter in this terminal")
            print("4. The session state will be automatically saved")
            print("=" * 60)

            # Wait for user to complete authentication manually
            input("\nPress Enter after you have completed authentication...")

            # Save authentication state
            await context.storage_state(path=str(auth_file))

            print(f"✅ Authentication state saved to: {auth_file.absolute()}")
            print(f"📁 File size: {auth_file.stat().st_size} bytes")

            return str(auth_file)

        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
        finally:
            print("🔄 Closing browser...")
            await browser.close()


def print_next_steps(auth_file: str):
    """Print instructions for using the saved authentication state"""
    print("\n" + "🎉" + "=" * 58 + "🎉")
    print("SUCCESS! Authentication session created")
    print("=" * 60)
    print("\n📋 NEXT STEPS:")
    print("1. Start the MCP server with the saved authentication state:")
    print(f"   npx @playwright/mcp@0.0.40 \\")
    print(f"     --storage-state {auth_file} \\")
    print(f"     --isolated \\")
    print(f"     --output-dir playwright/files \\")
    print(f"     --viewport-size 1280,900 \\")
    print(f"     --port 8931")
    print("\n2. The MCP server will use your saved authentication state")
    print("3. Your browser agent can now access authenticated pages")
    print("\n💡 TIP: If authentication expires, run this script again")
    print("=" * 60)


async def main():
    """Main function to create authentication session"""
    try:
        auth_file = await create_authenticated_session()
        print_next_steps(auth_file)

    except KeyboardInterrupt:
        print("\n⚠️  Authentication cancelled by user")
    except Exception as e:
        logger.error(f"❌ Error creating authentication session: {e}")
        print("\n💡 Troubleshooting tips:")
        print("- Make sure Playwright is installed: uv run playwright install")
        print("- Check network connectivity")
        print("- Verify the login URL is accessible")


if __name__ == "__main__":
    asyncio.run(main())
