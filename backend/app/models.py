"""Pydantic request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="senior", pattern="^(senior|caregiver)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class ScanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    channel: str = Field(default="sms", pattern="^(sms|email|call|chat|other)$")
    language: str = Field(default="en", pattern="^(en|bn)$")


class ImageScanRequest(BaseModel):
    image_b64: str = Field(min_length=1, max_length=8_000_000)  # ~6 MB binary
    mime_type: str = Field(pattern="^image/(png|jpeg|jpg|webp)$")
    channel: str = Field(default="sms", pattern="^(sms|email|call|chat|other)$")
    language: str = Field(default="en", pattern="^(en|bn)$")


class LinkRedeemRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class UrlCheckRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2000)
    language: str = Field(default="en", pattern="^(en|bn)$")


class NewsCheckRequest(BaseModel):
    text: str | None = Field(default=None, min_length=10, max_length=20000)
    url: str | None = Field(default=None, min_length=4, max_length=2000)
    language: str = Field(default="en", pattern="^(en|bn)$")


class ProductCheckRequest(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(default="", max_length=10000)
    price: str = Field(default="", max_length=50)
    platform: str = Field(default="", max_length=100)
    seller_info: str = Field(default="", max_length=1000)
    reviews_text: str = Field(default="", max_length=10000)
    image_b64: str = Field(default="", max_length=8_000_000)
    image_mime: str = Field(default="image/png",
                            pattern="^image/(png|jpeg|jpg|webp)$")
    language: str = Field(default="en", pattern="^(en|bn)$")
