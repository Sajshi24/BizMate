"""Google Imagen provider via the google-genai SDK."""

import logging

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

IMAGEN_MODELS = (
    "imagen-3.0-generate-002",
    "imagen-4.0-generate-001",
)


class ImagenProvider(ImageProvider):
    name = "imagen"

    def is_available(self) -> bool:
        return bool(GEMINI_API_KEY)

    def unavailability_reason(self) -> str:
        return "no API key"

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                provider=self.name,
                error="Gemini API key is not configured for Imagen.",
            )

        client = gemini_service.initialize_gemini()
        last_error = "Imagen image generation failed for all configured models."

        for model_name in IMAGEN_MODELS:
            try:
                logger.info("Imagen generation using model: %s", model_name)
                response = client.models.generate_images(
                    model=model_name,
                    prompt=request.prompt,
                    config=types.GenerateImagesConfig(number_of_images=1),
                )

                generated_images = getattr(response, "generated_images", None) or []
                if not generated_images:
                    last_error = f"model {model_name} returned no images"
                    logger.warning("Imagen model %s returned no images", model_name)
                    continue

                image = generated_images[0]
                image_bytes = getattr(image.image, "image_bytes", None)
                if image_bytes:
                    return ImageGenerationResult(
                        success=True,
                        image_bytes=image_bytes,
                        mime_type="image/png",
                        provider=self.name,
                    )
                last_error = f"model {model_name} returned empty image bytes"
            except (APIError, ValueError, AttributeError, TypeError) as exc:
                last_error = str(exc)
                logger.exception("Imagen model %s failed: %s", model_name, exc)

        return ImageGenerationResult(
            success=False,
            provider=self.name,
            error=last_error,
        )
