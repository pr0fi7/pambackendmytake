from typing import List, Optional

from pydantic import BaseModel, Field


class IntegrationItem(BaseModel):
    """Single integration item."""

    name: str = Field(..., description="Display name of the integration")
    slug: str = Field(..., description="Unique slug for the integration")
    image: str = Field(..., description="Image URL for the integration")
    is_connected: bool = Field(..., description="Whether user has connected this integration")


class ListIntegrationsResponse(BaseModel):
    """Response for listing all integrations."""

    active: List[IntegrationItem] = Field(default_factory=list, description="Connected integrations")
    inactive: List[IntegrationItem] = Field(default_factory=list, description="Available but not connected integrations")


class ConnectIntegrationResponse(BaseModel):
    """Response for connecting an integration."""

    auth_url: str = Field(..., description="OAuth authorization URL for user to visit")
    app_slug: str = Field(..., description="Integration slug")
    status: str = Field(..., description="Connection status")
    message: str = Field(..., description="User-friendly message")


class DisconnectIntegrationResponse(BaseModel):
    """Response for disconnecting an integration."""

    success: bool = Field(..., description="Whether disconnection was successful")
    app_slug: str = Field(..., description="Integration slug")
    status: str = Field(..., description="New connection status")
    note: Optional[str] = Field(None, description="Additional information about the disconnection")


class IntegrationCallbackResponse(BaseModel):
    """Response for OAuth callback notification."""

    success: bool = Field(..., description="Whether callback processing was successful")
    app_slug: str = Field(..., description="Integration slug")
    status: str = Field(..., description="Current connection status")
    message: Optional[str] = Field(None, description="Additional message if needed")
