"""Pydantic models for API request validation."""

from pydantic import BaseModel, constr
from typing import Optional


class MessageRequest(BaseModel):
    """Request model for /api/message endpoint."""
    text: constr(min_length=1, max_length=10000)


class CreateCrabRequest(BaseModel):
    """Request model for /api/crabs POST endpoint."""
    name: constr(min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_\- ]+$")


class FocusModeRequest(BaseModel):
    """Request model for /api/focus-mode endpoint."""
    enabled: bool


class SnapshotRequest(BaseModel):
    """Request model for /api/snapshot endpoint."""
    image: constr(min_length=1)
