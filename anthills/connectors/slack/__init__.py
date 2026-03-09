"""
Slack Connector: Post messages and read channels via Slack API.

Requires: pip install anthills[slack]
         (installs slack-sdk)
"""

from __future__ import annotations

from typing import Any

from ..base import Connector, ConnectorConfig


class SlackConnector(Connector):
    """
    Connector for Slack API.
    
    Provides methods to:
    - Post messages to channels
    - List channels
    - Get channel history
    - React to messages
    
    Example:
        slack = await registry.resolve("slack")
        await slack.post_message("#general", "Hello from Anthills!")
    """
    
    connector_type = "slack"
    display_name = "Slack"
    description = "Post messages and read channels in your Slack workspace"
    required_scopes = [
        "chat:write",
        "channels:read",
        "channels:history",
    ]
    
    async def connect(self) -> None:
        """Initialize Slack API client with bot token."""
        try:
            from slack_sdk.web.async_client import AsyncWebClient
        except ImportError:
            raise ImportError(
                "SlackConnector requires the slack-sdk package. "
                "Install it with: pip install anthills[slack]"
            )
        
        bot_token = self.config.credentials.get("bot_token")
        if not bot_token:
            raise ValueError("Slack credentials must include 'bot_token'")
        
        self._client = AsyncWebClient(token=bot_token)
    
    async def health_check(self) -> bool:
        """Verify Slack connection by testing auth."""
        if not self._client:
            return False
        try:
            response = await self._client.auth_test()
            return response.get("ok", False)
        except Exception:
            return False
    
    async def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """
        Post a message to a channel.
        
        Args:
            channel: Channel ID or name (e.g. "#general" or "C01234567")
            text: Message text
            thread_ts: Optional thread timestamp to reply in
            
        Returns:
            Slack API response
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        kwargs: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        
        return await self._client.chat_postMessage(**kwargs)
    
    async def list_channels(self, types: str = "public_channel") -> list[dict[str, Any]]:
        """
        List channels in the workspace.
        
        Args:
            types: Channel types to include (comma-separated)
            
        Returns:
            List of channel objects
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        response = await self._client.conversations_list(types=types)
        return response.get("channels", [])
    
    async def get_channel_history(
        self,
        channel: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get recent messages from a channel.
        
        Args:
            channel: Channel ID
            limit: Maximum number of messages to return
            
        Returns:
            List of message objects
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        response = await self._client.conversations_history(
            channel=channel,
            limit=limit,
        )
        return response.get("messages", [])
    
    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str,
    ) -> dict[str, Any]:
        """
        Add a reaction to a message.
        
        Args:
            channel: Channel ID
            timestamp: Message timestamp
            name: Reaction emoji name (without colons)
            
        Returns:
            Slack API response
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        return await self._client.reactions_add(
            channel=channel,
            timestamp=timestamp,
            name=name,
        )
    
    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """
        Get information about a user.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            User profile data
        """
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")
        
        response = await self._client.users_info(user=user_id)
        return response.get("user", {})
