import asyncio
import io
import json
import os.path
from typing import Any, Dict, List, Optional

import logfire
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from mcp.server.fastmcp import FastMCP

logfire.configure(
    send_to_logfire="if-token-present",
    service_name="google-drive-mcp-server",
)
server = FastMCP("Google Drive MCP Server")


def get_google_service(service_name: str):
    """Get authenticated Google API service (Drive v3)."""
    logfire.info(f"Getting {service_name} service")
    creds = None

    token_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    if not token_json_str:
        logfire.error("No valid credentials available")
        raise ConnectionRefusedError("No valid credentials available")

    try:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data)
        logfire.info(f"{service_name} service loaded successfully")
    except Exception as e:
        logfire.error(f"Error loading credentials from token: {e}")
        raise RuntimeError(f"Error loading credentials from token: {e}") from e

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
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

    logfire.info(f"{service_name} service created successfully")
    version = "v3" if service_name == "drive" else "v4"
    return build(service_name, version, credentials=creds)


def _get_working_dir() -> str:
    """Return working directory from env WORKING_DIR, ensure it exists."""
    workdir = os.environ.get("WORKING_DIR", "UserData/GoogleDriveMCP")
    os.makedirs(workdir, exist_ok=True)
    return workdir


def _mime_export_for_doc(target_format: str) -> Optional[str]:
    mapping = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "odt": "application/vnd.oasis.opendocument.text",
        "txt": "text/plain",
        "rtf": "application/rtf",
        "md": "text/markdown",
    }
    return mapping.get(target_format.lower())


def _mime_export_for_sheet(target_format: str) -> Optional[str]:
    mapping = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "tsv": "text/tab-separated-values",
    }
    return mapping.get(target_format.lower())


def _download_to_bytes(request) -> bytes:
    file_buf = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return file_buf.getvalue()


def _download_to_file(request, output_path: str) -> int:
    with open(output_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return os.path.getsize(output_path)


def _sanitize_filename(name: str) -> str:
    # Prevent path traversal and invalid filenames across platforms
    safe = name.replace(os.path.sep, "_")
    if os.path.altsep:
        safe = safe.replace(os.path.altsep, "_")
    # Collapse parent references and strip problematic leading/trailing chars
    while ".." in safe:
        safe = safe.replace("..", "_")
    safe = safe.strip().strip(" .")
    return safe or "file"


@server.tool()
async def list_files(
    query: str = "mimeType='application/vnd.google-apps.document'",
    spaces: str = "drive",
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    List files by Drive query.

    Args:
        query: Drive files.list q parameter.
        spaces: Search spaces (default: "drive").
        page_size: Page size limit (1-1000, default 50).

    Returns: List of files with id, name, mimeType, modifiedTime, owners, size.
    """
    logfire.info(f"listing files with query: {query}, spaces: {spaces}, page_size: {page_size}")
    try:
        page_size = max(1, min(page_size, 1000))
        drive = get_google_service("drive")
        files: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        fields = (
            "nextPageToken, files(id, name, mimeType, modifiedTime, createdTime, size,"
            " owners(displayName,emailAddress))"
        )
        while True:
            req = drive.files().list(
                q=query,
                spaces=spaces,
                fields=fields,
                pageToken=page_token,
                pageSize=page_size,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            resp = await asyncio.to_thread(lambda: req.execute(num_retries=3))
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        # Normalize owners list into display names
        result: List[Dict[str, Any]] = []
        for f in files:
            result.append(
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "mime_type": f.get("mimeType"),
                    "created_time": f.get("createdTime"),
                    "modified_time": f.get("modifiedTime"),
                    "owners": [o.get("displayName") for o in f.get("owners", [])],
                    "size": f.get("size"),
                }
            )

        return result
    except HttpError as error:
        import traceback
        logfire.error(f"An error occurred while listing files: {traceback.format_exc()}")
        return []


@server.tool()
async def download_file(file_id: str) -> Dict[str, Any]:
    """
    Download a file by id and save to WORKING_DIR.

    Returns metadata and local file path.
    """
    logfire.info(f"downloading file with id: {file_id}")
    try:
        drive = get_google_service("drive")

        meta_req = drive.files().get(
            fileId=file_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        )
        meta = await asyncio.to_thread(lambda: meta_req.execute(num_retries=3))

        mime = meta.get("mimeType") or ""
        if mime.startswith("application/vnd.google-apps."):
            return {
                "error": "Use export_document/export_spreadsheet for Google Workspace files.",
                "file_id": file_id,
                "mime_type": mime,
            }

        name = meta.get("name") or file_id
        name = _sanitize_filename(name)
        workdir = _get_working_dir()
        output_path = os.path.join(workdir, name)
        req = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
        size_bytes = await asyncio.to_thread(
            lambda: _download_to_file(req, output_path)
        )

        return {
            "file_id": file_id,
            "name": name,
            "mime_type": mime,
            "size_bytes": size_bytes,
            "saved_path": output_path,
        }
    except HttpError as error:
        logfire.error(f"An error occurred while downloading file: {error}")
        return {"error": str(error), "file_id": file_id}


@server.tool()
async def export_document(file_id: str, format: str = "pdf") -> Dict[str, Any]:
    """
    Export a Google Docs document to a given format and save to local.

    Supported formats: pdf, docx, odt, txt, rtf, md
    """
    logfire.info(f"exporting document with id: {file_id}, format: {format}")
    try:
        mime = _mime_export_for_doc(format)
        if not mime:
            return {"error": f"Unsupported format: {format}"}

        drive = get_google_service("drive")
        meta_req = drive.files().get(
            fileId=file_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        )
        meta = await asyncio.to_thread(lambda: meta_req.execute(num_retries=3))
        mime_type = meta.get("mimeType", "")
        if mime_type != "application/vnd.google-apps.document":
            return {
                "error": "Not a Google Docs file. Use export_spreadsheet for Sheets.",
                "file_id": file_id,
            }

        base_name = meta.get("name") or file_id
        base_name = _sanitize_filename(base_name)
        ext = f".{format.lower()}"
        filename = base_name if base_name.endswith(ext) else base_name + ext
        workdir = _get_working_dir()
        output_path = os.path.join(workdir, filename)
        req = drive.files().export_media(fileId=file_id, mimeType=mime)
        size_bytes = await asyncio.to_thread(
            lambda: _download_to_file(req, output_path)
        )

        return {
            "file_id": file_id,
            "name": filename,
            "export_format": format,
            "mime_type": mime,
            "size_bytes": size_bytes,
            "saved_path": output_path,
        }
    except HttpError as error:
        logfire.error(f"An error occurred while exporting document: {error}")
        return {"error": str(error), "file_id": file_id, "format": format}


@server.tool()
async def export_spreadsheet(file_id: str, format: str = "xlsx") -> Dict[str, Any]:
    """
    Export a Google Sheets file to a given format and save to local.

    Note: CSV/TSV export returns only the first sheet.

    Supported formats: xlsx, pdf, csv, ods, tsv
    """
    logfire.info(f"exporting spreadsheet with id: {file_id}, format: {format}")
    try:
        mime = _mime_export_for_sheet(format)
        if not mime:
            return {"error": f"Unsupported format: {format}"}

        drive = get_google_service("drive")
        meta_req = drive.files().get(
            fileId=file_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        )
        meta = await asyncio.to_thread(lambda: meta_req.execute(num_retries=3))
        mime_type = meta.get("mimeType", "")
        if mime_type != "application/vnd.google-apps.spreadsheet":
            return {
                "error": "Not a Google Sheets file. Use export_document for Docs.",
                "file_id": file_id,
            }

        base_name = meta.get("name") or file_id
        base_name = _sanitize_filename(base_name)
        ext = f".{format.lower()}"
        filename = base_name if base_name.endswith(ext) else base_name + ext
        workdir = _get_working_dir()
        output_path = os.path.join(workdir, filename)
        req = drive.files().export_media(fileId=file_id, mimeType=mime)
        size_bytes = await asyncio.to_thread(
            lambda: _download_to_file(req, output_path)
        )

        return {
            "file_id": file_id,
            "name": filename,
            "export_format": format,
            "mime_type": mime,
            "size_bytes": size_bytes,
            "saved_path": output_path,
        }
    except HttpError as error:
        logfire.error(f"An error occurred while exporting spreadsheet: {error}")
        return {"error": str(error), "file_id": file_id, "format": format}


@server.tool()
async def read_document(file_id: str) -> str:
    """
    Read a Google Docs document as plain text and return the content string.

    This exports the document to text/plain in-memory and returns the UTF-8 string.
    """
    logfire.info(f"reading document as text with id: {file_id}")
    try:
        drive = get_google_service("drive")

        # Confirm the file is a Google Docs document
        meta_req = drive.files().get(
            fileId=file_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        )
        meta = await asyncio.to_thread(lambda: meta_req.execute(num_retries=3))
        mime_type = meta.get("mimeType", "")
        if mime_type != "application/vnd.google-apps.document":
            return (
                "Not a Google Docs file. Use export_spreadsheet for Sheets or "
                "download_file for non-Google formats."
            )

        # Export to plain text and return content
        req = drive.files().export_media(fileId=file_id, mimeType="text/plain")
        content_bytes = await asyncio.to_thread(lambda: _download_to_bytes(req))
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return content_bytes.decode("utf-8", errors="replace")
    except HttpError as error:
        logfire.error(f"An error occurred while reading document: {error}")
        return f"Error reading document: {error}"


@server.tool()
async def upload_markdown_file(
    file_name: str,
    markdown_content: str,
) -> Dict[str, Any]:
    """
    Upload a string of markdown content as a new file to Google Drive.

    Args:
        file_name: The desired name for the file on Drive (e.g., "my_notes.md").
        markdown_content: The raw markdown string content.

    Returns: Metadata of the newly created file.
    """
    logfire.info(f"uploading markdown file with name: {file_name}")
    try:
        drive = get_google_service("drive")

        # Sanitize filename to prevent issues
        file_name = _sanitize_filename(file_name)
        file_metadata = {
            "name": file_name,
            "mimeType": "text/markdown",
        }

        content_bytes = markdown_content.encode("utf-8")
        
        content_stream = io.BytesIO(content_bytes)

        media = MediaIoBaseUpload(
            fd=content_stream,
            mimetype="text/markdown",
            chunksize=1024 * 1024, # 1MB chunk
            resumable=True
        )

        req = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, mimeType, webViewLink, modifiedTime",
            supportsAllDrives=True,
        )

        file_meta = await asyncio.to_thread(lambda: req.execute(num_retries=3))

        return {
            "id": file_meta.get("id"),
            "name": file_meta.get("name"),
            "mime_type": file_meta.get("mimeType"),
            "modified_time": file_meta.get("modifiedTime"),
            "file_link": file_meta.get("webViewLink"),
        }
    except HttpError as error:
        logfire.error(f"An error occurred while uploading markdown file: {error}")
        return {"error": str(error), "file_name": file_name}
    except Exception as e:
        logfire.error(f"An unexpected error occurred: {e}")
        return {"error": str(e), "file_name": file_name}

@server.tool()
async def delete_file(file_id: str) -> Dict[str, Any]:
    """
    Permanently delete a file by its ID.
    This bypasses the trash.

    Args:
        file_id: The ID of the file to delete.

    Returns: A confirmation dictionary.
    """
    logfire.info(f"deleting file with id: {file_id}")
    try:
        drive = get_google_service("drive")

        req = drive.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        )

        await asyncio.to_thread(lambda: req.execute(num_retries=3))

        return {
            "status": "success",
            "file_id": file_id,
            "message": "File permanently deleted."
        }
    except HttpError as error:
        logfire.error(f"An error occurred while deleting file: {error}")
        if error.resp.status == 404:
             return {"error": "File not found.", "file_id": file_id}
        return {"error": str(error), "file_id": file_id}

if __name__ == "__main__":
    print("Starting the Google Drive MCP Server")
    server.run()
