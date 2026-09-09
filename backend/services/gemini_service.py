"""Reusable Gemini AI service for BizMate business assistant features."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai.errors import APIError

from backend.config.settings import GEMINI_API_KEY

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"

_client: genai.Client | None = None
_model_name: str = DEFAULT_MODEL


class GeminiConfigurationError(Exception):
    """Raised when the Gemini client cannot be configured."""


@dataclass
class GeminiResult:
    """Structured response returned by all Gemini service functions."""

    success: bool
    content: str | None = None
    error: str | None = None


def initialize_gemini(model_name: str = DEFAULT_MODEL) -> genai.Client:
    """Configure and return a reusable Gemini client.

    Reads ``GEMINI_API_KEY`` from application settings. The client is cached
    at module level so subsequent calls reuse the same instance.

    Args:
        model_name: Gemini model identifier to use for generation.

    Returns:
        A configured ``genai.Client`` instance.

    Raises:
        GeminiConfigurationError: If the API key is missing or empty.
    """
    global _client, _model_name

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured")
        raise GeminiConfigurationError(
            "GEMINI_API_KEY is not configured. Set it in your environment or .env file."
        )

    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        _model_name = model_name
        logger.info("Gemini client initialized with model: %s", model_name)

    return _client


def _extract_response_text(response: Any) -> str:
    """Extract text content from a Gemini API response."""
    text = getattr(response, "text", None)
    if text is None:
        raise ValueError("Gemini returned no usable text content.")

    if not text.strip():
        raise ValueError("Gemini returned an empty response.")

    return text.strip()


def _execute_prompt(prompt: str) -> GeminiResult:
    """Send a prompt to Gemini and return a structured result."""
    try:
        client = initialize_gemini()
        logger.info("Sending prompt to Gemini (%d characters)", len(prompt))
        response = client.models.generate_content(
            model=_model_name,
            contents=prompt,
        )
        content = _extract_response_text(response)
        logger.info("Gemini response received (%d characters)", len(content))
        return GeminiResult(success=True, content=content)

    except GeminiConfigurationError as exc:
        logger.error("Gemini configuration error: %s", exc)
        return GeminiResult(success=False, error=str(exc))

    except (APIError, ValueError) as exc:
        logger.error("Gemini API error: %s", exc)
        return GeminiResult(success=False, error=str(exc))

    except Exception as exc:
        logger.exception("Unexpected Gemini error: %s", exc)
        return GeminiResult(
            success=False,
            error="An unexpected error occurred while contacting Gemini.",
        )


def generate_response(prompt: str) -> GeminiResult:
    """Generate a general-purpose AI response for the given prompt.

    Args:
        prompt: The user or system prompt to send to Gemini.

    Returns:
        ``GeminiResult`` with generated text on success, or an error message
        on failure.
    """
    if not prompt or not prompt.strip():
        logger.warning("generate_response called with empty prompt")
        return GeminiResult(success=False, error="Prompt cannot be empty.")

    return _execute_prompt(prompt.strip())


def generate_marketing_content(product_name: str, keywords: str | list[str]) -> GeminiResult:
    """Generate marketing copy for a local retail product.

    Args:
        product_name: Name of the product to promote.
        keywords: Target keywords as a string or list of strings.

    Returns:
        ``GeminiResult`` containing marketing content tailored to the product.
    """
    if not product_name or not product_name.strip():
        return GeminiResult(success=False, error="Product name cannot be empty.")

    keyword_text = ", ".join(keywords) if isinstance(keywords, list) else keywords.strip()
    if not keyword_text:
        return GeminiResult(success=False, error="At least one keyword is required.")

    prompt = (
        "You are a marketing assistant for a local retail shop.\n"
        f"Product: {product_name.strip()}\n"
        f"Keywords: {keyword_text}\n\n"
        "Write concise, persuasive marketing content suitable for in-store "
        "posters, flyers, or product descriptions. Highlight local appeal and "
        "customer benefits. Keep the tone friendly and professional."
    )
    return _execute_prompt(prompt)


def generate_business_advice(business_data: dict[str, Any]) -> GeminiResult:
    """Generate actionable business advice from shop performance data.

    Args:
        business_data: Dictionary of business metrics and context such as
            revenue, profit, inventory health, or sales trends.

    Returns:
        ``GeminiResult`` containing practical recommendations for the shop owner.
    """
    if not business_data:
        return GeminiResult(
            success=False,
            error="Business data cannot be empty.",
        )

    serialized_data = json.dumps(business_data, indent=2, default=str)
    prompt = (
        "You are a business advisor for a local retail shop owner.\n"
        "Analyze the following business data and provide clear, actionable advice:\n\n"
        f"{serialized_data}\n\n"
        "Focus on inventory, sales, profitability, and customer growth. "
        "Use short paragraphs and bullet points where helpful."
    )
    return _execute_prompt(prompt)


def generate_social_caption(product_name: str, offer: str) -> GeminiResult:
    """Generate a social media caption for a product promotion.

    Args:
        product_name: Name of the product being promoted.
        offer: Offer details such as discount, bundle, or limited-time deal.

    Returns:
        ``GeminiResult`` containing a ready-to-post social media caption.
    """
    if not product_name or not product_name.strip():
        return GeminiResult(success=False, error="Product name cannot be empty.")

    if not offer or not offer.strip():
        return GeminiResult(success=False, error="Offer details cannot be empty.")

    prompt = (
        "You are a social media assistant for a local retail shop.\n"
        f"Product: {product_name.strip()}\n"
        f"Offer: {offer.strip()}\n\n"
        "Write one engaging social media caption for Instagram or Facebook. "
        "Include a call to action, keep it concise, and add 3-5 relevant hashtags "
        "at the end."
    )
    return _execute_prompt(prompt)


def generate_offer_suggestions(product_data: dict[str, Any]) -> GeminiResult:
    """Generate promotional offer ideas based on product information.

    Args:
        product_data: Dictionary describing the product, such as name, category,
            stock level, cost price, and selling price.

    Returns:
        ``GeminiResult`` containing suggested offers to boost sales.
    """
    if not product_data:
        return GeminiResult(
            success=False,
            error="Product data cannot be empty.",
        )

    serialized_data = json.dumps(product_data, indent=2, default=str)
    prompt = (
        "You are a retail promotions strategist for a local shop.\n"
        "Based on the product data below, suggest 3 practical promotional offers "
        "that can increase sales without hurting profitability:\n\n"
        f"{serialized_data}\n\n"
        "For each offer, include a short title and a one-sentence explanation. "
        "Consider stock levels, pricing, and local customer appeal."
    )
    return _execute_prompt(prompt)
