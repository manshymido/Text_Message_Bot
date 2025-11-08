"""Google OAuth2 authentication helper."""

import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from utils.config import settings
from utils.logger import logger

# Scopes required for Calendar and Tasks
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]


def get_google_credentials() -> Optional[Credentials]:
    """
    Get or refresh Google OAuth2 credentials.

    Returns:
        Credentials object or None if authentication fails
    """
    creds = None
    # Use data directory for token if credentials is read-only (Docker)
    token_path = Path(settings.google_token_file)
    if not token_path.parent.exists() or not os.access(token_path.parent, os.W_OK):
        # Fallback to data directory
        data_dir = Path("data/credentials")
        data_dir.mkdir(parents=True, exist_ok=True)
        token_path = data_dir / "token.json"
        logger.info(f"Using data directory for token: {token_path}")
    
    creds_path = Path(settings.google_credentials_file)

    # Check if credentials file exists
    if not creds_path.exists():
        logger.error(
            f"Credentials file not found: {creds_path}. "
            "Please download OAuth2 credentials from Google Cloud Console."
        )
        return None

    # Load existing token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_path), SCOPES
            )
        except Exception as e:
            logger.warning(f"Failed to load existing token: {e}")

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed Google credentials")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                creds = None

        if not creds:

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Obtained new Google credentials")
            except Exception as e:
                logger.error(f"Failed to obtain credentials: {e}")
                return None

        # Save credentials for next run
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        logger.info(f"Saved credentials to {token_path}")

    return creds


def get_calendar_service():
    """
    Get Google Calendar service instance.

    Returns:
        Calendar service object or None
    """
    creds = get_google_credentials()
    if not creds:
        return None

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build Calendar service: {e}")
        return None


def get_tasks_service():
    """
    Get Google Tasks service instance.

    Returns:
        Tasks service object or None
    """
    creds = get_google_credentials()
    if not creds:
        return None

    try:
        service = build("tasks", "v1", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build Tasks service: {e}")
        return None

