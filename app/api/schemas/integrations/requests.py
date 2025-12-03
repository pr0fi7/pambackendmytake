from typing import Optional

from pydantic import BaseModel, Field


class ConnectIntegrationRequest(BaseModel):
    """Request to connect an integration."""

    slug: str = Field(..., description="Integration slug (e.g., 'gmail', 'slack')")
    redirect_url: Optional[str] = Field(None, description="Optional redirect URL after OAuth completion")


class DisconnectIntegrationRequest(BaseModel):
    """Request to disconnect an integration."""

    slug: str = Field(..., description="Integration slug to disconnect")


class IntegrationCallbackRequest(BaseModel):
    """Request sent from frontend after OAuth redirect."""

    slug: str = Field(..., description="Integration slug that was connected")
