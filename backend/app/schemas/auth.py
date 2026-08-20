"""Pydantic schemas for authentication."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    id: str
    username: str
    email: str
    role: Literal["analyst", "domain_expert", "admin"]


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Literal["analyst", "domain_expert", "admin"] = "analyst"
