"""Image generation orchestration with automatic provider fallback."""

from __future__ import annotations

import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Sequence

from backend.services.image_generation.base import (
    ImageGenerationRequest,
    ImageGenerationResult,
    ImageProvider,
)
from backend.services.image_generation.gemini_provider import GeminiProvider
from backend.services.image_generation.imagen_provider import ImagenProvider
from backend.services.image_generation.openai_provider import OpenAIProvider
from backend.services.image_generation.stability_provider import StabilityProvider

logger = logging.getLogger(__name__)

USER_FRIENDLY_FAILURE_MESSAGE = (
    "We're unable to generate your poster right now. Please try again in a moment."
)
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 60

PROVIDER_DISPLAY_NAMES = {
    "gemini": "GeminiProvider",
    "imagen": "ImagenProvider",
    "openai": "OpenAIProvider",
    "stability": "StabilityProvider",
}


@dataclass
class _ProviderAttemptRecord:
    """Internal diagnostic record for a single provider attempt."""

    provider_key: str
    display_name: str
    started: bool = False
    succeeded: bool = False
    skipped: bool = False
    skip_reason: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None


class ImageGenerationService:
    """Automatically selects the first available image generation provider."""

    def __init__(
        self,
        providers: Sequence[ImageProvider] | None = None,
        provider_timeout_seconds: int = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    ):
        self._providers = list(providers or self._default_providers())
        self._provider_timeout_seconds = provider_timeout_seconds
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="image-generation",
        )

    @staticmethod
    def _default_providers() -> list[ImageProvider]:
        return [
            GeminiProvider(),
            ImagenProvider(),
            OpenAIProvider(),
            StabilityProvider(),
        ]

    @staticmethod
    def _display_name(provider: ImageProvider) -> str:
        return PROVIDER_DISPLAY_NAMES.get(provider.name, provider.name)

    def _log_attempt_started(self, display_name: str) -> None:
        logger.info("[image-gen] provider=%s | started=yes", display_name)

    def _log_attempt_skipped(self, display_name: str, reason: str) -> None:
        logger.info(
            "[image-gen] provider=%s | started=no | skipped=yes | reason=%s",
            display_name,
            reason,
        )

    def _log_attempt_succeeded(self, display_name: str) -> None:
        logger.info("[image-gen] provider=%s | succeeded=yes", display_name)

    def _log_attempt_failed(
        self,
        display_name: str,
        error_message: str,
        stack_trace: str | None = None,
    ) -> None:
        logger.error(
            "[image-gen] provider=%s | succeeded=no | error=%s",
            display_name,
            error_message,
        )
        if stack_trace:
            logger.error(
                "[image-gen] provider=%s | stack_trace:\n%s",
                display_name,
                stack_trace,
            )

    def _print_failure_summary(self, attempts: list[_ProviderAttemptRecord]) -> None:
        """Print a developer-facing summary when every provider fails or is skipped."""
        lines = ["", "=== Image Generation Failure Summary ==="]
        for attempt in attempts:
            if attempt.skipped:
                lines.append(
                    f"{attempt.display_name} -> skipped ({attempt.skip_reason})"
                )
            elif attempt.succeeded:
                lines.append(f"{attempt.display_name} -> succeeded")
            else:
                detail = attempt.error_message or "unknown error"
                lines.append(f"{attempt.display_name} -> failed -> {detail}")
        lines.append("=== End Image Generation Failure Summary ===")
        lines.append("")

        summary = "\n".join(lines)
        logger.error(summary)
        print(summary)

    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Try providers in order until one succeeds."""
        attempts: list[_ProviderAttemptRecord] = []

        for provider in self._providers:
            display_name = self._display_name(provider)
            record = _ProviderAttemptRecord(
                provider_key=provider.name,
                display_name=display_name,
            )
            attempts.append(record)

            if not provider.is_available():
                record.skipped = True
                record.skip_reason = provider.unavailability_reason()
                self._log_attempt_skipped(display_name, record.skip_reason)
                continue

            record.started = True
            self._log_attempt_started(display_name)

            try:
                future = self._executor.submit(provider.generate, request)
                result = future.result(timeout=self._provider_timeout_seconds)
            except FuturesTimeoutError as exc:
                record.error_message = (
                    f"timed out after {self._provider_timeout_seconds} seconds"
                )
                record.stack_trace = traceback.format_exc()
                self._log_attempt_failed(
                    display_name,
                    record.error_message,
                    record.stack_trace,
                )
                continue
            except Exception as exc:
                record.error_message = str(exc)
                record.stack_trace = traceback.format_exc()
                self._log_attempt_failed(
                    display_name,
                    record.error_message,
                    record.stack_trace,
                )
                continue

            if result.success and result.image_bytes:
                record.succeeded = True
                self._log_attempt_succeeded(display_name)
                return result

            record.error_message = result.error or "provider returned no image bytes"
            self._log_attempt_failed(display_name, record.error_message)

        self._print_failure_summary(attempts)
        return ImageGenerationResult(
            success=False,
            error=USER_FRIENDLY_FAILURE_MESSAGE,
        )
