"""
Gmail Connector: Read and send emails via Gmail API.

Requires: pip install anthills[gmail]
         (installs google-api-python-client, google-auth)
"""

from __future__ import annotations

from typing import Any

from ..base import Connector, ConnectorConfig


class GmailConnector(Connector):
    """
    Connector for Gmail API.
    
    Provides methods to:
    - List unread emails
    - Get email threads
    - Send replies
    - Search messages
    
    Example:
        gmail = await registry.resolve("gmail")
        unread = await gmail.list_unread(max_results=10)
        for msg in unread:
            thread = await gmail.get_thread(msg["threadId"])
            ...
    """
    
    connector_type = "gmail"
    display_name = "Gmail"
    description = "Read and send emails from your Gmail account"
    required_scopes = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]
    
    async def connect(self) -> None:
        """Initialize Gmail API client with OAuth credentials."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "GmailConnector requires the google-api-python-client package. "
                "Install it with: pip install anthills[gmail]"
            )
        
        creds = Credentials(
            token=self.config.credentials.get("access_token"),
            refresh_token=self.config.credentials.get("refresh_token"),
            client_id=self.config.credentials.get("client_id"),
            client_secret=self.config.credentials.get("client_secret"),
            token_uri="https://oauth2.googleapis.com/token",
        )
        self._client = build("gmail", "v1", credentials=creds)
    
    async def health_check(self) -> bool:
        """Verify Gmail connection by fetching user profile."""
        if not self._client:
            return False
        try:
            self._client.users().getProfile(userId="me").execute()
            return True
        except Exception:
            return False
    
    async def list_unread(self, max_results: int = 10) -> list[dict[str, Any]]:
        """
        List unread messages.
        
        Args:
            max_results: Maximum number of messages to return
            
        Returns:
            List of message metadata dicts with 'id' and 'threadId'
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        result = self._client.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
        ).execute()
        return result.get("messages", [])
    
    async def get_message(self, message_id: str) -> dict[str, Any]:
        """
        Get a single message by ID.
        
        Args:
            message_id: The message ID
            
        Returns:
            Full message data
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        return self._client.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()
    
    async def get_thread(self, thread_id: str) -> dict[str, Any]:
        """
        Get an email thread by ID.
        
        Args:
            thread_id: The thread ID
            
        Returns:
            Thread data including all messages
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        return self._client.users().threads().get(
            userId="me",
            id=thread_id,
        ).execute()
    
    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """
        Search messages with a Gmail query.
        
        Args:
            query: Gmail search query (e.g. "from:someone@example.com")
            max_results: Maximum number of results
            
        Returns:
            List of matching message metadata
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        result = self._client.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()
        return result.get("messages", [])
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            thread_id: Optional thread ID to reply in
            
        Returns:
            Sent message metadata
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        body_data: dict[str, Any] = {"raw": raw}
        if thread_id:
            body_data["threadId"] = thread_id
        
        return self._client.users().messages().send(
            userId="me",
            body=body_data,
        ).execute()
    
    async def send_reply(
        self,
        thread_id: str,
        body: str,
        to: str,
    ) -> dict[str, Any]:
        """
        Send a reply to an existing thread.
        
        Args:
            thread_id: Thread to reply to
            body: Reply body (plain text)
            to: Recipient email address
            
        Returns:
            Sent message metadata
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(body)
        message["to"] = to
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        return self._client.users().messages().send(
            userId="me",
            body={"raw": raw, "threadId": thread_id},
        ).execute()
