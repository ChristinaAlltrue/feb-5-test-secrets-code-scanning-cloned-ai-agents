import asyncio
import base64
import json
import os.path
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import logfire
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

logfire.configure(
    send_to_logfire="if-token-present",
    service_name="gmail-mcp-server",
)

server = FastMCP("Gmail MCP Server")


def get_gmail_service():
    """Get authenticated Gmail service."""
    logfire.info("Getting Gmail service")
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    # this is from stdio client, not from the token.json file
    token_json_str = os.environ.get("GOOGLE_CREDENTIALS")

    if not token_json_str:
        logfire.error("No valid credentials available")
        raise ConnectionRefusedError("No valid credentials available")

    try:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data)
        logfire.info("Gmail service loaded successfully")
    except Exception as e:
        logfire.error(f"Error loading credentials from token: {e}")
        raise RuntimeError(f"Error loading credentials from token: {e}") from e

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # TODO: we may need to save the refreshed token to somewhere to avoid refreshing every time
            logfire.warning("Access token expired, refreshing...")
            try:
                creds.refresh(Request())
            except RefreshError as e:
                logfire.error(f"Error refreshing credentials: {e}")
                raise ConnectionRefusedError(
                    f"Error refreshing credentials: {e}"
                ) from e
        else:
            logfire.error("No valid credentials available")
            raise ConnectionRefusedError("No valid credentials available")

    logfire.info("Gmail service created successfully")
    return build("gmail", "v1", credentials=creds)


@server.tool()
async def get_current_date(tz: str = "UTC") -> str:
    """
    Get the current date in the format YYYY/MM/DD for the given IANA timezone (default: UTC).
    """
    try:
        now = datetime.now(ZoneInfo(tz))
    except Exception as e:
        logfire.error(f"Invalid timezone '{tz}': {e}")
        return f"Error: Invalid timezone '{tz}'"
    return now.strftime("%Y/%m/%d")


@server.tool()
async def list_mails(
    max_results: int = 10, query: str = "is:inbox"
) -> List[Dict[str, Any]]:
    """
    List Gmail messages with optional filtering.

    For the query, you can use:
    - is:unread — List unread emails
    - subject:your_subject — Filter by subject
    - from:someone@example.com — Filter by sender
    - to:someone@example.com — Filter by recipient
    - before:2025/01/01 — Emails before a date
    - after:2025/01/01 — Emails after a date
    - older_than:2d — Emails older/newer than a time period (d=day, m=month, y=year)
    - has:attachment — Emails with attachments

    You can combine multiple terms with spaces (AND) or use OR.
    Examples: `subject:evidence from:someone@example.com` or
    `subject:evidence OR subject:report`.

    Args:
        max_results: Max messages to return (default: 10)
        query: Gmail search query (default: "is:inbox")

    Returns:
        List of message summaries with id, subject, sender, and snippet.
    """
    try:
        service = get_gmail_service()
        max_results = max(1, min(max_results, 500))
        # Call the Gmail API
        logfire.info(
            f"listing messages with query: {query}, max_results: {max_results}"
        )
        req = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
        )
        results = await asyncio.to_thread(lambda: req.execute(num_retries=3))
        messages = results.get("messages", [])
        msg_count = len(messages)
        logfire.info(f"listed {msg_count} messages")

        if not messages:
            return []

        # Get message details for each message
        message_list = []
        for message in messages:
            try:
                req = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message["id"],
                        format="metadata",
                        metadataHeaders=["Subject", "From", "To", "Date", "Snippet"],
                    )
                )
                msg = await asyncio.to_thread(lambda: req.execute(num_retries=3))
                logfire.info(f"message: {msg}")

                headers = msg.get("payload", {}).get("headers", [])
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                sender = next(
                    (h["value"] for h in headers if h["name"] == "From"),
                    "Unknown Sender",
                )
                to = next(
                    (h["value"] for h in headers if h["name"] == "To"),
                    "Unknown Recipient",
                )
                date = next(
                    (h["value"] for h in headers if h["name"] == "Date"), "Unknown Date"
                )

                message_list.append(
                    {
                        "id": message["id"],
                        "subject": subject,
                        "sender": sender,
                        "to": to,
                        "date": date,
                        "snippet": msg.get("snippet", "No preview available"),
                        "thread_id": msg.get("threadId"),
                    }
                )
            except HttpError as error:
                logfire.error(f"Error getting message {message['id']}: {error}")
                continue

        return message_list

    except HttpError as error:
        logfire.error(f"An error occurred: {error}")
        return []


@server.tool()
async def get_email_content(message_id: str) -> Dict[str, Any]:
    """
    Get the full content of a specific email by message ID.

    Args:
        message_id: The Gmail message ID to retrieve

    Returns:
        Dictionary containing email details including body, headers, and metadata
    """
    logfire.info(f"getting email content with id: {message_id}")
    try:
        service = get_gmail_service()

        # Get the full message
        req = service.users().messages().get(userId="me", id=message_id, format="full")
        msg = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        headers = msg.get("payload", {}).get("headers", [])
        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"), "No Subject"
        )
        sender = next(
            (h["value"] for h in headers if h["name"] == "From"), "Unknown Sender"
        )
        to_recipient = next(
            (h["value"] for h in headers if h["name"] == "To"), "Unknown Recipient"
        )
        date = next(
            (h["value"] for h in headers if h["name"] == "Date"), "Unknown Date"
        )

        # Extract email body
        body = ""
        payload = msg.get("payload", {})

        if payload.get("body", {}).get("data"):
            # Simple text email
            data = payload["body"]["data"]
            padded = data + "=" * (-len(data) % 4)
            body = base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
        elif payload.get("parts"):
            # Multipart email
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get(
                    "data"
                ):
                    data = part["body"]["data"]
                    padded = data + "=" * (-len(data) % 4)
                    body = base64.urlsafe_b64decode(padded).decode(
                        "utf-8", errors="replace"
                    )
                    break

        return {
            "id": message_id,
            "subject": subject,
            "sender": sender,
            "to": to_recipient,
            "date": date,
            "body": body,
            "snippet": msg.get("snippet", "No preview available"),
            "internal_date": msg.get("internalDate"),
            "thread_id": msg.get("threadId"),
            "labels": msg.get("labelIds", []),
        }

    except HttpError as error:
        logfire.error(f"An error occurred: {error}")
        return {"status": "error", "error": str(error)}


@server.tool()
async def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Sends a new email to a specified recipient.

    Args:
        to: The recipient's email address.
        subject: The subject of the email.
        body: The plain text content of the email.

    Returns:
        A dictionary containing the ID and thread ID of the sent message.
    """
    try:
        service = get_gmail_service()

        # Create the email message object using Python's email library
        message = MIMEText(body, _subtype="plain", _charset="utf-8")
        message["to"] = to
        message["subject"] = subject
        # Omit From; Gmail sets it to the authenticated account automatically.

        # Encode the message in a URL-safe base64 format
        encoded_message = (
            base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
        )

        create_message = {"raw": encoded_message}

        # Call the Gmail API's send method
        logfire.info(f"Sending email to: {to} with subject: {subject}")
        send_request = service.users().messages().send(userId="me", body=create_message)
        sent_message = await asyncio.to_thread(
            lambda: send_request.execute(num_retries=3)
        )

        logfire.info(f"Email sent successfully. Message ID: {sent_message['id']}")
        return {
            "id": sent_message.get("id"),
            "thread_id": sent_message.get("threadId"),
            "status": "success",
        }

    except HttpError as error:
        logfire.error(f"An error occurred while sending email: {error}")
        return {"status": "error", "error": str(error)}


@server.tool()
async def reply_to_email(message_id: str, body: str) -> Dict[str, Any]:
    """
    Replies to a specific email, ensuring it stays in the same conversation thread.

    Args:
        message_id: The ID of the email to reply to.
        body: The plain text content of the reply.

    Returns:
        A dictionary containing the ID and thread ID of the sent reply.
    """
    logfire.info(f"replying to email with id: {message_id} with body: {body}")
    try:
        service = get_gmail_service()

        # 1. Get the original message to extract headers
        logfire.info(f"Fetching original email with ID: {message_id} to prepare reply.")
        get_request = service.users().messages().get(userId="me", id=message_id)
        original_message = await asyncio.to_thread(
            lambda: get_request.execute(num_retries=3)
        )

        original_headers = original_message.get("payload", {}).get("headers", [])

        # 2. Extract necessary headers for a proper reply
        def get_header(headers: List[Dict], name: str) -> str:
            return next(
                (h["value"] for h in headers if h["name"].lower() == name.lower()), ""
            )

        original_subject = get_header(original_headers, "Subject")
        original_sender = get_header(original_headers, "From")
        original_message_id_header = get_header(original_headers, "Message-ID")
        original_references = get_header(original_headers, "References")
        thread_id = original_message.get("threadId")
        if thread_id is None:
            logfire.warning(
                "Original message missing threadId; sending reply without threadId"
            )
            return {
                "status": "error",
                "error": "Original message missing threadId",
            }

        # 3. Construct the reply subject
        reply_subject = original_subject
        if not reply_subject.lower().startswith("re:"):
            reply_subject = f"Re: {original_subject}"

        # 4. Create the reply message object
        reply = MIMEText(body, _subtype="plain", _charset="utf-8")
        reply["to"] = original_sender
        reply["subject"] = reply_subject
        # Omit From; Gmail sets it to the authenticated account automatically.

        # Set In-Reply-To/References only when original Message-ID is present
        if original_message_id_header:
            reply["In-Reply-To"] = original_message_id_header
            reply["References"] = (
                f"{original_references} {original_message_id_header}"
                if original_references
                else original_message_id_header
            )
        else:
            logfire.warning(
                "Original message missing Message-ID; sending reply without In-Reply-To/References"
            )

        # 5. Encode and send the reply
        encoded_message = (
            base64.urlsafe_b64encode(reply.as_bytes()).decode().rstrip("=")
        )

        # IMPORTANT: Include the threadId in the request body to keep it in the same conversation
        create_reply_request = {"raw": encoded_message, "threadId": thread_id}

        logfire.info(f"Sending reply to: {original_sender}")
        send_request = (
            service.users().messages().send(userId="me", body=create_reply_request)
        )
        sent_reply = await asyncio.to_thread(
            lambda: send_request.execute(num_retries=3)
        )

        logfire.info(f"Reply sent successfully. Message ID: {sent_reply['id']}")
        return {
            "id": sent_reply.get("id"),
            "thread_id": sent_reply.get("threadId"),
            "status": "success",
        }

    except HttpError as error:
        logfire.error(f"An error occurred while replying to email: {error}")
        return {"status": "error", "error": str(error)}


if __name__ == "__main__":
    print("Starting the Gmail MCP Server")
    server.run()
