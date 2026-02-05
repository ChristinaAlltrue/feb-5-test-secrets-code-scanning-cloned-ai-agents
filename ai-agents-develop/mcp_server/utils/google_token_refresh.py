import json

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


def get_refreshed_credentials_json(token_json_str: str) -> str:
    """
    Refreshes the credentials if necessary and returns the FULL credential
    object serialized as a JSON string for persistent storage.

    Args:
        token_json_str: A JSON string containing credential information.

    Returns:
        A JSON string containing the updated credentials (including the new access token).

    Raises:
        ValueError/RuntimeError: Propagated from internal credential loading/refresh logic.
    """
    # This logic is almost identical to get_refreshed_access_token but returns the full JSON.
    if not token_json_str:
        raise ValueError("Input token string is empty.")

    try:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in token string: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading credentials from token data: {e}") from e

    # Check validity and refresh if expired
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print("Access token expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                print("Token refreshed successfully.")
            except RefreshError as e:
                raise RuntimeError(
                    f"Failed to refresh token using the provided refresh_token: {e}"
                ) from e
        else:
            raise ValueError(
                "Credentials are not valid and cannot be refreshed (missing refresh token or other fundamental issue)."
            )
    else:
        print("Access token is currently valid.")

    # Return the full credential object as a JSON string
    return creds.to_json()


# --- Example Usage (Requires installing google-auth and google-auth-oauthlib) ---
if __name__ == "__main__":
    from test_suite.credential import GOOGLE_CREDENTIALS

    print("--- Simulating Token Refresh Attempt ---")
    print(
        "If this were a real expired token, the output below would be the new access token."
    )

    try:
        new_credentials_json = get_refreshed_credentials_json(GOOGLE_CREDENTIALS)

        # If successful (in a real environment):
        print(f"\nNew Credentials JSON: {new_credentials_json}")
        # print(f"\nReady to build service with: build('gmail', 'v1', credentials=Credentials.from_authorized_user_info(json.loads(new_credentials_json)))")

    except (ValueError, RuntimeError) as e:
        print(f"\n!!! Caught Expected Error in Example: {e}")
        print(
            "This error is expected because the placeholder uses fake client IDs/secrets."
        )
        print(
            "In a live environment with valid credentials, this would return the new access token."
        )
