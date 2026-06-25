"""OpenAI Images provider."""

import base64
import logging

import requests

from backend.config.settings import OPENAI_API_KEY
from backend.services.image_generation.base import (
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageProvider,
)

logger = logging.getLogger(__name__)

OPENAI_IMAGE_URL = "https://api.openai.com/v1/images/generations"


class OpenAIProvider(ImageProvider):
    name = "openai"

    def is_available(self) -> bool:
        return bool(OPENAI_API_KEY)

    def unavailability_reason(self) -> str:
        return "no API key"

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                provider=self.name,
                error="OpenAI API key is not configured.",
            )

        try:
            logger.info("OpenAI image generation requested")
            response = requests.post(
                OPENAI_IMAGE_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": request.prompt,
                    "size": "1024x1024",
                    "response_format": "b64_json",
                    "n": 1,
                },
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            image_data = payload["data"][0]["b64_json"]
            image_bytes = base64.b64decode(image_data)
            return ImageGenerationResult(
                success=True,
                image_bytes=image_bytes,
                mime_type="image/png",
                provider=self.name,
            )
        except (requests.RequestException, KeyError, ValueError, IndexError) as exc:
            logger.exception("OpenAI image generation failed: %s", exc)
            return ImageGenerationResult(
                success=False,
                provider=self.name,
                error=str(exc),
            )
