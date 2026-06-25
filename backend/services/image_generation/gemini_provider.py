"""Gemini native image generation provider."""

import logging
from typing import Any

from google.genai import types
from google.genai.errors import APIError

from backend.config.settings import GEMINI_API_KEY
from backend.services import gemini_service
from backend.services.image_generation.base import (
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageProvider,
)

logger = logging.getLogger(__name__)

GEMINI_IMAGE_MODELS = (
    "gemini-2.0-flash-preview-image-generation",
    "gemini-2.5-flash-image",
)


class GeminiProvider(ImageProvider):
    name = "gemini"

    def is_available(self) -> bool:
        return bool(GEMINI_API_KEY)

    def unavailability_reason(self) -> str:
        return "no API key"

    def _extract_image_bytes(self, response: Any) -> bytes | None:
        for part in getattr(response, "parts", None) or []:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and inline_data.data:
                return inline_data.data
        return None

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                provider=self.name,
                error="Gemini API key is not configured.",
            )

        client = gemini_service.initialize_gemini()
        parts: list[Any] = []

        if request.reference_image_bytes and request.reference_image_mime:
            parts.append(
                types.Part.from_bytes(
                    data=request.reference_image_bytes,
                    mime_type=request.reference_image_mime,
                )
            )

        parts.append(types.Part.from_text(text=request.prompt))

        last_error = "Gemini image generation failed for all configured models."
        for model_name in GEMINI_IMAGE_MODELS:
            try:
                logger.info("Gemini image generation using model: %s", model_name)
                response = client.models.generate_content(
                    model=model_name,
                    contents=parts,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"]
                    ),
                )
                image_bytes = self._extract_image_bytes(response)
                if image_bytes:
                    mime_type = "image/png"
                    for part in getattr(response, "parts", None) or []:
                        inline_data = getattr(part, "inline_data", None)
                        if inline_data and inline_data.mime_type:
                            mime_type = inline_data.mime_type
                            break
                    return ImageGenerationResult(
                        success=True,
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                        provider=self.name,
                    )
                last_error = f"model {model_name} returned no image data"
                logger.warning("Gemini model %s returned no image data", model_name)
            except (APIError, ValueError, AttributeError) as exc:
                last_error = str(exc)
                logger.exception(
                    "Gemini model %s failed: %s",
                    model_name,
                    exc,
                )

        return ImageGenerationResult(
            success=False,
            provider=self.name,
            error=last_error,
        )
