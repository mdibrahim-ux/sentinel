from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class AnalysisRequest(BaseModel):
    repository_url: str = Field(min_length=1, max_length=500)
    branch: str = Field(default="main", min_length=1, max_length=120)
    project_label: str = Field(default="", max_length=120)
    include_security: bool = True
    include_quality: bool = True
    include_architecture: bool = True
    audience: Literal["mentor", "developer"] = "developer"

    @field_validator("branch")
    @classmethod
    def branch_is_reasonable(cls, value: str) -> str:
        if value.startswith("-") or ".." in value or "\\" in value or "\x00" in value:
            raise ValueError("Branch contains unsupported characters.")
        return value


class FindingStatusUpdate(BaseModel):
    status: Literal["open", "accepted", "fixed", "ignored", "investigate"]
    note: str = Field(default="", max_length=1000)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=800)


class AskSentinalRequest(BaseModel):
    question: str = Field(min_length=2, max_length=600)
    selected_path: str | None = Field(default=None, max_length=500)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)


class ProfilePayload(BaseModel):
    full_name: str = Field(default="", max_length=120)
    username: str = Field(default="", max_length=80)
    headline: str = Field(default="", max_length=160)
    bio: str = Field(default="", max_length=1200)
    location: str = Field(default="", max_length=120)
    website: str = Field(default="", max_length=500)
    email: str = Field(default="", max_length=254)
    email_public: bool = False
    github_username: str = Field(default="", max_length=80)
    github_url: str = Field(default="", max_length=500)
    preferred_languages: list[str] = Field(default_factory=list, max_length=30)
    technical_skills: list[str] = Field(default_factory=list, max_length=60)
    interests: list[str] = Field(default_factory=list, max_length=30)
    role: str = Field(default="", max_length=120)
    avatar_data_url: str = Field(default="", max_length=350000)
    default_dashboard: str = Field(default="Home", max_length=40)
    notifications_enabled: bool = True
    privacy_profile_public: bool = False

    @field_validator("username")
    @classmethod
    def validate_profile_username(cls, value: str) -> str:
        value = value.strip()
        if value and not __import__("re").fullmatch(r"[A-Za-z0-9._-]{1,80}", value):
            raise ValueError("Username may contain letters, numbers, dots, underscores, and hyphens.")
        return value

    @field_validator("github_username")
    @classmethod
    def validate_github_username(cls, value: str) -> str:
        value = value.strip().lstrip("@")
        if value and not __import__("re").fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", value):
            raise ValueError("Enter a valid GitHub username.")
        return value

    @field_validator("website", "github_url")
    @classmethod
    def validate_optional_url(cls, value: str) -> str:
        value = value.strip()
        if value and not value.lower().startswith(("https://", "http://")):
            raise ValueError("URLs must start with https:// or http://.")
        return value

    @field_validator("avatar_data_url")
    @classmethod
    def validate_avatar(cls, value: str) -> str:
        if value and not value.startswith(("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")):
            raise ValueError("Profile images must be PNG, JPEG, or WebP.")
        return value
