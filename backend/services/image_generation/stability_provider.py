"""Stability AI image generation provider."""

import base64
import logging

import requests

from backend.config.settings import STABILITY_API_KEY
from backend.services.image_generation.base import (
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageProvider,
)

logger = logging.getLogger(__name__)

STABILITY_IMAGE_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"


class StabilityProvider(ImageProvider):
    name = "stability"

    def is_available(self) -> bool:
        return bool(STABILITY_API_KEY)

    def unavailability_reason(self) -> str:
        return "no API key"

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                provider=self.name,
                error="Stability API key is not configured.",
            )

        try:
            logger.info("Stability image generation requested")
            headers = {
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json",
            }
            files = {
                "prompt": (None, request.prompt),
                "output_format": (None, "png"),
            }

            if request.reference_image_bytes and request.reference_image_mime:
                files["image"] = (
                    "reference.png",
                    request.reference_image_bytes,
                    request.reference_image_mime,
                )

            response = requests.post(
                STABILITY_IMAGE_URL,
                headers=headers,
                files=files,
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            image_base64 = payload.get("image")
            if not image_base64:
                raise ValueError("Stability response did not include image data.")

            image_bytes = base64.b64decode(image_base64)
            return ImageGenerationResult(
                success=True,
                image_bytes=image_bytes,
                mime_type="image/png",
                provider=self.name,
            )
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.exception("Stability image generation failed: %s", exc)
            return ImageGenerationResult(
                success=False,
                provider=self.name,
                error=str(exc),
            )
