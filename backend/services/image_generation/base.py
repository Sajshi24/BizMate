"""Shared types and provider interface for image generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageGenerationRequest:
    """Input payload for poster image generation."""

    prompt: str
    reference_image_bytes: bytes | None = None
    reference_image_mime: str | None = None
    variation_seed: str = ""


@dataclass
class ImageGenerationResult:
    """Output from a single image generation provider attempt."""

    success: bool
    image_bytes: bytes | None = None
    mime_type: str = "image/png"
    provider: str = ""
    error: str | None = None


class ImageProvider(ABC):
    """Provider interface for modular image generation backends."""

    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the provider is configured and ready."""

    def unavailability_reason(self) -> str:
        """Human-readable reason when ``is_available()`` is False."""
        return "not configured"

    @abstractmethod
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate an image for the given request."""
