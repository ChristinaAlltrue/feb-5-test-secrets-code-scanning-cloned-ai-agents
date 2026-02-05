#!/usr/bin/env python3
"""
Google OAuth Token Generator CLI Tool

This tool generates a token.json file from a credentials.json file using Google OAuth flow.
Usage: python google_auth_token_generator.py --credentials path/to/credentials.json
"""

import argparse
import os
import sys

# Google OAuth imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def validate_credentials_file(credentials_path: str) -> bool:
    """Validate that the credentials file exists and is readable."""
    if not os.path.exists(credentials_path):
        print(f"Error: Credentials file not found: {credentials_path}")
        return False

    if not os.path.isfile(credentials_path):
        print(f"Error: Path is not a file: {credentials_path}")
        return False

    if not os.access(credentials_path, os.R_OK):
        print(f"Error: Cannot read credentials file: {credentials_path}")
        return False

    return True


def generate_token(credentials_path: str, output_path: str = "token.json") -> bool:
    """
    Generate a token.json file from credentials.json using Google OAuth flow.

    Args:
        credentials_path: Path to the credentials.json file
        output_path: Path where token.json should be saved

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        creds = None

        # Check if token.json already exists
        if os.path.exists(output_path):
            print(f"Found existing token file: {output_path}")
            try:
                creds = Credentials.from_authorized_user_file(output_path, SCOPES)
                print("Loaded existing credentials from token file")
                # If requested scopes are not covered by the existing token, re-consent
                existing_scopes = set(getattr(creds, "scopes", []) or [])
                requested_scopes = set(SCOPES or [])
                if requested_scopes - existing_scopes:
                    print(
                        "Existing token lacks some requested scopes; re-running OAuth flow..."
                    )
                    creds = None
            except Exception as e:
                print(f"Warning: Could not load existing token file: {e}")
                creds = None

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                    print("Credentials refreshed successfully")
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None

            if not creds:
                print("Starting OAuth flow...")
                print(f"Using credentials file: {credentials_path}")
                print("A browser window will open for authentication...")

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    print("OAuth flow completed successfully")
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return False

        # Save the credentials for the next run
        print(f"Saving credentials to: {output_path}")
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as token:
            token.write(creds.to_json())

        print("Token file generated successfully!")
        return True

    except Exception as e:
        print(f"Error generating token: {e}")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate Google OAuth token.json from credentials.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python google_auth_token_generator.py --credentials ./credentials.json
  python google_auth_token_generator.py -c ./credentials.json -o ./my_token.json
        """,
    )

    parser.add_argument(
        "-c", "--credentials", required=False, help="Path to the credentials.json file"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="token.json",
        help="Output path for token.json (default: token.json)",
    )

    parser.add_argument(
        "--scopes", nargs="+", help="Custom OAuth scopes (overrides default scopes)"
    )

    args = parser.parse_args()

    # Update scopes if custom ones are provided
    global SCOPES
    if args.scopes:
        SCOPES = args.scopes
        print(f"Using custom scopes: {SCOPES}")

    # Get credentials path interactively if not provided
    credentials_path = args.credentials
    if not credentials_path:
        print("Welcome to Google OAuth Token Generator!")
        print("=" * 50)

        # Check for common credentials file locations
        common_paths = [
            "./credentials.json",
            "credentials.json",
            "~/credentials.json",
            "~/Downloads/credentials.json",
        ]

        existing_files = []
        for path in common_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                existing_files.append((path, expanded_path))

        if existing_files:
            print("\nFound existing credentials files:")
            for i, (display_path, full_path) in enumerate(existing_files, 1):
                print(f"  {i}. {display_path}")
            print(f"  {len(existing_files) + 1}. Enter custom path")

            while True:
                try:
                    choice = input(
                        f"\nSelect a file (1-{len(existing_files) + 1}): "
                    ).strip()
                    choice_num = int(choice)

                    if 1 <= choice_num <= len(existing_files):
                        credentials_path = existing_files[choice_num - 1][1]
                        print(f"Selected: {credentials_path}")
                        break
                    elif choice_num == len(existing_files) + 1:
                        credentials_path = input(
                            "Enter path to credentials.json: "
                        ).strip()
                        break
                    else:
                        print(
                            f"Please enter a number between 1 and {len(existing_files) + 1}"
                        )
                except ValueError:
                    print("Please enter a valid number")
        else:
            print("\nNo credentials files found in common locations.")
            credentials_path = input("Enter path to credentials.json: ").strip()

        # Expand user path if needed
        credentials_path = os.path.expanduser(credentials_path)

        if not credentials_path:
            print("❌ No credentials path provided. Exiting.")
            sys.exit(1)

    # Validate credentials file
    if not validate_credentials_file(credentials_path):
        sys.exit(1)

    # Generate token
    if generate_token(credentials_path, args.output):
        print(f"\n✅ Success! Token file created at: {args.output}")
        sys.exit(0)
    else:
        print("\n❌ Failed to generate token file")
        sys.exit(1)


if __name__ == "__main__":
    main()
