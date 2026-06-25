"""Marketing Studio service — orchestrates AI and business intelligence layers."""

from __future__ import annotations

import base64
import json
import logging
import random
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db
from backend.config.settings import POSTER_STORAGE_DIR
from backend.services import (
    analytics_service,
    finance_service,
    gemini_service,
    inventory_service,
)
from backend.services.image_generation.base import ImageGenerationRequest
from backend.services.image_generation_service import (
    ImageGenerationService,
    USER_FRIENDLY_FAILURE_MESSAGE,
)

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
POSTERS_COLLECTION = "posters"

LAYOUT_STYLES = (
    "bold split layout with product hero on the right",
    "minimal centered product focus with wide headline band",
    "diagonal promotional ribbon across the corner",
    "grid-based retail flyer with offer badge",
    "vertical story-style poster with stacked text blocks",
)
COLOR_PALETTES = (
    "warm sunset palette with coral and gold accents",
    "fresh green and cream natural tones",
    "high-contrast monochrome with one accent color",
    "festive jewel tones with rich contrast",
    "modern pastel retail palette with soft gradients",
)
COMPOSITIONS = (
    "large product spotlight with supporting icons",
    "offer badge overlay with clean whitespace",
    "lifestyle-inspired background with product cutout",
    "typography-first composition with subtle texture",
    "corner CTA panel with balanced negative space",
)
ACCENT_ELEMENTS = (
    "starburst discount badge",
    "rounded offer sticker",
    "ribbon corner tag",
    "floating price callout",
    "limited-time banner strip",
)

_image_generation_service = ImageGenerationService()
_generation_lock_registry: dict[str, threading.Lock] = {}
_generation_registry_lock = threading.Lock()


class MarketingValidationError(Exception):
    """Raised when marketing input validation fails."""


class MarketingAIError(Exception):
    """Raised when Gemini generation fails."""


class GenerationInProgressError(Exception):
    """Raised when an identical poster generation is already running."""


class PosterNotFoundError(Exception):
    """Raised when a poster record does not exist."""


class CalendarType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    FESTIVAL = "festival"
    SEASONAL = "seasonal"


@dataclass
class PosterDesignSpec:
    poster_headline: str
    promotional_text: str
    call_to_action: str
    design_style: str
    color_suggestions: list[str]
    font_suggestions: list[str]
    layout_suggestions: list[str]
    image_generation_prompt: str


@dataclass
class PosterResult:
    success: bool
    poster_id: str
    poster_headline: str
    promotional_text: str
    call_to_action: str
    design_style: str
    design_summary: str
    poster_image: str | None = None
    download_url: str | None = None
    design_details: PosterDesignSpec | None = None
    error: str | None = None


@dataclass
class PosterRecord:
    poster_id: str
    session_id: str | None
    product_name: str
    generation_timestamp: datetime
    image_location: str
    download_url: str
    prompt: str
    provider: str
    generation_status: str
    poster_headline: str
    promotional_text: str
    call_to_action: str
    design_style: str
    design_summary: str
    keywords: list[str]
    offer: str
    theme: str
    target_audience: str
    image_mime: str


@dataclass
class CaptionResult:
    success: bool
    instagram: str
    facebook: str
    linkedin: str
    whatsapp_business: str
    error: str | None = None


@dataclass
class HashtagResult:
    success: bool
    hashtags: list[str]
    error: str | None = None


@dataclass
class OfferSuggestion:
    title: str
    description: str
    rationale: str
    offer_type: str


@dataclass
class OffersResult:
    success: bool
    offers: list[OfferSuggestion]
    business_context_used: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class MarketingRecommendation:
    product_to_promote: str
    reason: str
    expected_business_impact: str
    suggested_duration: str
    suggested_offer: str


@dataclass
class RecommendationResult:
    success: bool
    recommendation: MarketingRecommendation | None = None
    business_context_used: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class CampaignResult:
    success: bool
    campaign_title: str
    slogan: str
    objective: str
    target_audience: str
    promotional_message: str
    campaign_description: str
    error: str | None = None


@dataclass
class CalendarIdea:
    title: str
    description: str
    suggested_channels: list[str]
    call_to_action: str


@dataclass
class CalendarResult:
    success: bool
    calendar_type: str
    ideas: list[CalendarIdea]
    error: str | None = None


@dataclass
class PublishContent:
    """Content prepared for future social publishing adapters."""

    text: str
    media_base64: str | None = None
    hashtags: list[str] | None = None
    platform_overrides: dict[str, str] = field(default_factory=dict)


@dataclass
class PublishResult:
    success: bool
    platform: str
    message: str
    post_id: str | None = None


class SocialPublisher(ABC):
    """Base interface for future social media publishing integrations."""

    platform: str

    @abstractmethod
    def publish(self, content: PublishContent) -> PublishResult:
        """Publish content to the target social platform."""


class InstagramPublisher(SocialPublisher):
    platform = "instagram"

    def publish(self, content: PublishContent) -> PublishResult:
        logger.info("Instagram publish requested — integration not yet implemented")
        return PublishResult(
            success=False,
            platform=self.platform,
            message="Instagram publishing will be available in a future release.",
        )


class FacebookPublisher(SocialPublisher):
    platform = "facebook"

    def publish(self, content: PublishContent) -> PublishResult:
        logger.info("Facebook publish requested — integration not yet implemented")
        return PublishResult(
            success=False,
            platform=self.platform,
            message="Facebook publishing will be available in a future release.",
        )


class LinkedInPublisher(SocialPublisher):
    platform = "linkedin"

    def publish(self, content: PublishContent) -> PublishResult:
        logger.info("LinkedIn publish requested — integration not yet implemented")
        return PublishResult(
            success=False,
            platform=self.platform,
            message="LinkedIn publishing will be available in a future release.",
        )


class TwitterPublisher(SocialPublisher):
    platform = "x"

    def publish(self, content: PublishContent) -> PublishResult:
        logger.info("X (Twitter) publish requested — integration not yet implemented")
        return PublishResult(
            success=False,
            platform=self.platform,
            message="X (Twitter) publishing will be available in a future release.",
        )


class SocialPublisherRegistry:
    """Registry for modular social publishing adapters."""

    _publishers: dict[str, SocialPublisher] = {}

    @classmethod
    def register(cls, publisher: SocialPublisher) -> None:
        cls._publishers[publisher.platform] = publisher

    @classmethod
    def get(cls, platform: str) -> SocialPublisher | None:
        return cls._publishers.get(platform.lower())

    @classmethod
    def supported_platforms(cls) -> list[str]:
        return sorted(cls._publishers.keys())


def _register_default_publishers() -> None:
    for publisher in (
        InstagramPublisher(),
        FacebookPublisher(),
        LinkedInPublisher(),
        TwitterPublisher(),
    ):
        SocialPublisherRegistry.register(publisher)


_register_default_publishers()


def validate_keywords(keywords: list[str]) -> list[str]:
    """Validate and normalize marketing keywords."""
    if not keywords:
        raise MarketingValidationError("At least one keyword is required.")

    cleaned = [keyword.strip() for keyword in keywords if keyword and keyword.strip()]
    if not cleaned:
        raise MarketingValidationError("Keywords cannot be empty.")

    if len(cleaned) > 20:
        raise MarketingValidationError("A maximum of 20 keywords is allowed.")

    return cleaned


def validate_product_image(
    image_bytes: bytes | None,
    content_type: str | None,
) -> tuple[bytes | None, str | None]:
    """Validate optional uploaded product image."""
    if image_bytes is None:
        return None, None

    if not content_type or content_type not in ALLOWED_IMAGE_TYPES:
        raise MarketingValidationError(
            "Invalid image type. Allowed types: JPEG, PNG, WEBP."
        )

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise MarketingValidationError("Image size must not exceed 5 MB.")

    if len(image_bytes) == 0:
        raise MarketingValidationError("Uploaded image file is empty.")

    return image_bytes, content_type


def _parse_gemini_json(content: str) -> dict[str, Any]:
    """Parse JSON returned by Gemini, stripping optional markdown fences."""
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise MarketingAIError("Gemini returned invalid JSON.") from exc


def _request_gemini_json(prompt: str) -> dict[str, Any]:
    """Send a prompt to Gemini and parse the JSON response."""
    result = gemini_service.generate_response(prompt)
    if not result.success or not result.content:
        raise MarketingAIError(result.error or "Gemini generation failed.")
    return _parse_gemini_json(result.content)


def _build_design_summary(spec: PosterDesignSpec) -> str:
    colors = ", ".join(spec.color_suggestions)
    fonts = ", ".join(spec.font_suggestions)
    layouts = "; ".join(spec.layout_suggestions)
    return (
        f"{spec.design_style}. Headline-driven poster using {colors} with {fonts} typography. "
        f"Layout: {layouts}. CTA: {spec.call_to_action}"
    )


def _build_prompt_variation() -> dict[str, str]:
    """Introduce unique variation for every poster generation request."""
    return {
        "variation_id": str(uuid4()),
        "layout_style": random.choice(LAYOUT_STYLES),
        "color_palette": random.choice(COLOR_PALETTES),
        "composition": random.choice(COMPOSITIONS),
        "accent_element": random.choice(ACCENT_ELEMENTS),
    }


def _image_bytes_to_data_url(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _mime_to_extension(mime_type: str) -> str:
    if "jpeg" in mime_type or "jpg" in mime_type:
        return "jpg"
    if "webp" in mime_type:
        return "webp"
    return "png"


def _get_posters_collection() -> Collection:
    return db[POSTERS_COLLECTION]


def _poster_download_path(poster_id: str) -> str:
    return f"/marketing/posters/{poster_id}/download"


def _save_poster_image_file(poster_id: str, image_bytes: bytes, mime_type: str) -> Path:
    POSTER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = POSTER_STORAGE_DIR / f"{poster_id}.{_mime_to_extension(mime_type)}"
    file_path.write_bytes(image_bytes)
    return file_path


def _document_to_poster_record(document: dict) -> PosterRecord:
    poster_id = document["poster_id"]
    return PosterRecord(
        poster_id=poster_id,
        session_id=document.get("session_id"),
        product_name=document["product_name"],
        generation_timestamp=document["generation_timestamp"],
        image_location=document["image_location"],
        download_url=_poster_download_path(poster_id),
        prompt=document["prompt"],
        provider=document.get("provider", ""),
        generation_status=document["generation_status"],
        poster_headline=document["poster_headline"],
        promotional_text=document["promotional_text"],
        call_to_action=document["call_to_action"],
        design_style=document["design_style"],
        design_summary=document["design_summary"],
        keywords=document.get("keywords", []),
        offer=document["offer"],
        theme=document["theme"],
        target_audience=document["target_audience"],
        image_mime=document.get("image_mime", "image/png"),
    )


def _acquire_generation_lock(lock_key: str) -> threading.Lock:
    with _generation_registry_lock:
        lock = _generation_lock_registry.setdefault(lock_key, threading.Lock())
    if not lock.acquire(blocking=False):
        raise GenerationInProgressError(
            "A poster is already being generated for this product. Please wait a moment."
        )
    return lock


def list_posters(session_id: str | None = None) -> list[PosterRecord]:
    """Return stored poster history, optionally filtered by session."""
    query: dict[str, Any] = {}
    if session_id:
        query["session_id"] = session_id

    try:
        documents = list(
            _get_posters_collection().find(query, {"_id": 0}).sort("generation_timestamp", -1)
        )
    except PyMongoError as exc:
        logger.error("Failed to list posters: %s", exc)
        raise

    return [_document_to_poster_record(document) for document in documents]


def get_poster_by_id(poster_id: str) -> PosterRecord:
    """Fetch a single poster record by ID."""
    try:
        document = _get_posters_collection().find_one({"poster_id": poster_id}, {"_id": 0})
    except PyMongoError as exc:
        logger.error("Failed to fetch poster %s: %s", poster_id, exc)
        raise

    if document is None:
        raise PosterNotFoundError(f"Poster '{poster_id}' not found")

    return _document_to_poster_record(document)


def get_poster_image_file(poster_id: str) -> tuple[Path, str]:
    """Return the stored poster image path and MIME type."""
    record = get_poster_by_id(poster_id)
    image_path = Path(record.image_location)
    if not image_path.is_file():
        raise PosterNotFoundError(f"Poster image for '{poster_id}' was not found on disk.")
    return image_path, record.image_mime


def delete_poster(poster_id: str) -> str:
    """Delete a poster record and its stored image file."""
    record = get_poster_by_id(poster_id)
    image_path = Path(record.image_location)

    try:
        result = _get_posters_collection().delete_one({"poster_id": poster_id})
    except PyMongoError as exc:
        logger.error("Failed to delete poster %s: %s", poster_id, exc)
        raise

    if result.deleted_count == 0:
        raise PosterNotFoundError(f"Poster '{poster_id}' not found")

    if image_path.is_file():
        image_path.unlink(missing_ok=True)

    logger.info("Deleted poster: %s", poster_id)
    return poster_id


def collect_business_context() -> dict[str, Any]:
    """Aggregate finance, analytics, and inventory data for marketing decisions."""
    try:
        finance = finance_service.get_finance_summary()
        analytics = analytics_service.get_analytics_summary()
        inventory_health = inventory_service.get_inventory_health()
        low_stock = inventory_service.get_low_stock_products()
        out_of_stock = inventory_service.get_out_of_stock_products()
        top_products = analytics_service.get_top_products()
        category_performance = analytics_service.get_category_performance()
        sales_trend = analytics_service.get_sales_trend()
    except PyMongoError as exc:
        logger.error("Failed to collect business context: %s", exc)
        raise

    return {
        "finance": asdict(finance),
        "analytics": asdict(analytics),
        "inventory_health": asdict(inventory_health),
        "low_stock_products": [product.model_dump() for product in low_stock[:10]],
        "out_of_stock_products": [product.model_dump() for product in out_of_stock[:10]],
        "top_products": [asdict(product) for product in top_products[:10]],
        "category_performance": [asdict(row) for row in category_performance[:10]],
        "sales_trend": [asdict(point) for point in sales_trend[-14:]],
    }


def generate_poster(
    product_name: str,
    keywords: list[str],
    offer: str,
    theme: str,
    target_audience: str,
    product_image_bytes: bytes | None = None,
    product_image_mime: str | None = None,
    session_id: str | None = None,
) -> PosterResult:
    """Generate a unique AI poster with automatic image-provider fallback."""
    if not product_name or not product_name.strip():
        raise MarketingValidationError("Product name is required.")
    if not offer or not offer.strip():
        raise MarketingValidationError("Offer is required.")
    if not theme or not theme.strip():
        raise MarketingValidationError("Theme is required.")
    if not target_audience or not target_audience.strip():
        raise MarketingValidationError("Target audience is required.")

    validated_keywords = validate_keywords(keywords)
    image_bytes, image_mime = validate_product_image(product_image_bytes, product_image_mime)

    lock_key = f"{session_id or 'anonymous'}:{product_name.strip().lower()}"
    generation_lock = _acquire_generation_lock(lock_key)
    poster_id = str(uuid4())

    try:
        variation = _build_prompt_variation()
        keyword_text = ", ".join(validated_keywords)
        design_prompt = (
            "You are an expert retail poster designer for local shops.\n"
            "Return ONLY valid JSON with these exact keys:\n"
            "poster_headline, promotional_text, call_to_action, design_style, "
            "color_suggestions, font_suggestions, layout_suggestions, "
            "image_generation_prompt\n\n"
            "Lists must contain 2-4 concise items.\n"
            "Create a UNIQUE design that differs from previous posters while keeping the "
            "same marketing intent.\n"
            f"Variation ID: {variation['variation_id']}\n"
            f"Suggested layout style: {variation['layout_style']}\n"
            f"Suggested color palette: {variation['color_palette']}\n"
            f"Suggested composition: {variation['composition']}\n"
            f"Suggested accent: {variation['accent_element']}\n"
            f"Product: {product_name.strip()}\n"
            f"Keywords: {keyword_text}\n"
            f"Offer: {offer.strip()}\n"
            f"Theme: {theme.strip()}\n"
            f"Target audience: {target_audience.strip()}\n"
            f"Has product photo: {'yes' if image_bytes else 'no'}\n"
        )

        design_data = _request_gemini_json(design_prompt)
        spec = PosterDesignSpec(
            poster_headline=str(design_data["poster_headline"]),
            promotional_text=str(design_data["promotional_text"]),
            call_to_action=str(design_data["call_to_action"]),
            design_style=str(design_data.get("design_style", variation["layout_style"])),
            color_suggestions=[str(item) for item in design_data["color_suggestions"]],
            font_suggestions=[str(item) for item in design_data["font_suggestions"]],
            layout_suggestions=[str(item) for item in design_data["layout_suggestions"]],
            image_generation_prompt=str(design_data["image_generation_prompt"]),
        )
        design_summary = _build_design_summary(spec)

        image_prompt = (
            f"{spec.image_generation_prompt}\n"
            f"Create a professional retail promotional poster for a local shop.\n"
            f"Headline: {spec.poster_headline}\n"
            f"Promotional copy: {spec.promotional_text}\n"
            f"Offer: {offer.strip()}\n"
            f"Theme: {theme.strip()}\n"
            f"Target audience: {target_audience.strip()}\n"
            f"Design style: {spec.design_style}\n"
            f"Variation ID: {variation['variation_id']}\n"
            f"Layout: {variation['layout_style']}\n"
            f"Palette: {variation['color_palette']}\n"
            f"Composition: {variation['composition']}\n"
            f"Accent: {variation['accent_element']}\n"
            "Use bold typography, clear product focus, and polished retail composition."
        )

        image_result = _image_generation_service.generate_image(
            ImageGenerationRequest(
                prompt=image_prompt,
                reference_image_bytes=image_bytes,
                reference_image_mime=image_mime,
                variation_seed=variation["variation_id"],
            )
        )

        if not image_result.success or not image_result.image_bytes:
            _save_failed_poster_record(
                poster_id=poster_id,
                session_id=session_id,
                product_name=product_name.strip(),
                prompt=image_prompt,
                keywords=validated_keywords,
                offer=offer.strip(),
                theme=theme.strip(),
                target_audience=target_audience.strip(),
                spec=spec,
                design_summary=design_summary,
                error_message=image_result.error or USER_FRIENDLY_FAILURE_MESSAGE,
            )
            return PosterResult(
                success=False,
                poster_id=poster_id,
                poster_headline=spec.poster_headline,
                promotional_text=spec.promotional_text,
                call_to_action=spec.call_to_action,
                design_style=spec.design_style,
                design_summary=design_summary,
                design_details=spec,
                error=image_result.error or USER_FRIENDLY_FAILURE_MESSAGE,
            )

        image_path = _save_poster_image_file(
            poster_id,
            image_result.image_bytes,
            image_result.mime_type,
        )
        download_url = _poster_download_path(poster_id)
        poster_image = _image_bytes_to_data_url(image_result.image_bytes, image_result.mime_type)

        poster_document = {
            "poster_id": poster_id,
            "session_id": session_id,
            "product_name": product_name.strip(),
            "generation_timestamp": datetime.now(UTC),
            "image_location": str(image_path),
            "prompt": image_prompt,
            "provider": image_result.provider,
            "generation_status": "completed",
            "poster_headline": spec.poster_headline,
            "promotional_text": spec.promotional_text,
            "call_to_action": spec.call_to_action,
            "design_style": spec.design_style,
            "design_summary": design_summary,
            "keywords": validated_keywords,
            "offer": offer.strip(),
            "theme": theme.strip(),
            "target_audience": target_audience.strip(),
            "image_mime": image_result.mime_type,
        }
        _get_posters_collection().insert_one(poster_document)

        logger.info("Poster %s generated for product: %s", poster_id, product_name.strip())
        return PosterResult(
            success=True,
            poster_id=poster_id,
            poster_headline=spec.poster_headline,
            promotional_text=spec.promotional_text,
            call_to_action=spec.call_to_action,
            design_style=spec.design_style,
            design_summary=design_summary,
            poster_image=poster_image,
            download_url=download_url,
            design_details=spec,
        )
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Poster copy generation failed for %s: %s", product_name, exc)
        return PosterResult(
            success=False,
            poster_id=poster_id,
            poster_headline="",
            promotional_text="",
            call_to_action="",
            design_style="",
            design_summary="",
            error=USER_FRIENDLY_FAILURE_MESSAGE,
        )
    except PyMongoError as exc:
        logger.error("Failed to persist poster %s: %s", poster_id, exc)
        raise
    finally:
        generation_lock.release()


def _save_failed_poster_record(
    poster_id: str,
    session_id: str | None,
    product_name: str,
    prompt: str,
    keywords: list[str],
    offer: str,
    theme: str,
    target_audience: str,
    spec: PosterDesignSpec,
    design_summary: str,
    error_message: str,
) -> None:
    """Persist a failed poster attempt for auditing without storing an image."""
    poster_document = {
        "poster_id": poster_id,
        "session_id": session_id,
        "product_name": product_name,
        "generation_timestamp": datetime.now(UTC),
        "image_location": "",
        "prompt": prompt,
        "provider": "",
        "generation_status": "failed",
        "poster_headline": spec.poster_headline,
        "promotional_text": spec.promotional_text,
        "call_to_action": spec.call_to_action,
        "design_style": spec.design_style,
        "design_summary": design_summary,
        "keywords": keywords,
        "offer": offer,
        "theme": theme,
        "target_audience": target_audience,
        "image_mime": "",
        "error_message": error_message,
    }
    _get_posters_collection().insert_one(poster_document)


def generate_captions(
    product_name: str,
    offer: str,
    target_audience: str | None = None,
) -> CaptionResult:
    """Generate platform-specific social captions."""
    if not product_name or not product_name.strip():
        raise MarketingValidationError("Product name is required.")
    if not offer or not offer.strip():
        raise MarketingValidationError("Offer is required.")

    audience = target_audience.strip() if target_audience else "local shoppers"
    prompt = (
        "You are a social media copywriter for a local retail shop.\n"
        "Return ONLY valid JSON with these exact keys:\n"
        "instagram, facebook, linkedin, whatsapp_business\n\n"
        f"Product: {product_name.strip()}\n"
        f"Offer: {offer.strip()}\n"
        f"Target audience: {audience}\n\n"
        "Tailor tone and length for each platform. "
        "Instagram should be visual and hashtag-friendly. "
        "Facebook should be conversational. "
        "LinkedIn should be professional. "
        "WhatsApp Business should be concise and direct."
    )

    try:
        data = _request_gemini_json(prompt)
        return CaptionResult(
            success=True,
            instagram=str(data["instagram"]),
            facebook=str(data["facebook"]),
            linkedin=str(data["linkedin"]),
            whatsapp_business=str(data["whatsapp_business"]),
        )
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Caption generation failed: %s", exc)
        return CaptionResult(
            success=False,
            instagram="",
            facebook="",
            linkedin="",
            whatsapp_business="",
            error=str(exc),
        )


def generate_hashtags(product_name: str, keywords: list[str]) -> HashtagResult:
    """Generate at least 10 relevant marketing hashtags."""
    validated_keywords = validate_keywords(keywords)
    if not product_name or not product_name.strip():
        raise MarketingValidationError("Product name is required.")

    prompt = (
        "You are a social media strategist for local retail.\n"
        "Return ONLY valid JSON with one key: hashtags (array of at least 10 strings).\n"
        "Each hashtag must start with # and be relevant to local retail marketing.\n"
        f"Product: {product_name.strip()}\n"
        f"Keywords: {', '.join(validated_keywords)}"
    )

    try:
        data = _request_gemini_json(prompt)
        hashtags = [str(tag) if str(tag).startswith("#") else f"#{tag}" for tag in data["hashtags"]]
        if len(hashtags) < 10:
            raise MarketingAIError("Gemini returned fewer than 10 hashtags.")
        return HashtagResult(success=True, hashtags=hashtags)
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Hashtag generation failed: %s", exc)
        return HashtagResult(success=False, hashtags=[], error=str(exc))


def generate_intelligent_offers() -> OffersResult:
    """Generate data-driven promotional offers using inventory, analytics, and finance."""
    try:
        context = collect_business_context()
    except PyMongoError as exc:
        raise MarketingAIError("Unable to load business data for offer generation.") from exc

    prompt = (
        "You are a retail promotions strategist for a local shop.\n"
        "Analyze the business context and return ONLY valid JSON with key 'offers' "
        "containing exactly 5 objects.\n"
        "Each object must include: title, description, rationale, offer_type.\n"
        "Choose offer types from: Buy 2 Get 1, Weekend Combo, Festival Discount, "
        "Flash Sale, Clearance Sale, Bundle Deal, Loyalty Offer.\n"
        "Base recommendations on low stock, out-of-stock items, top products, "
        "profit margin, and sales trends — not random suggestions.\n\n"
        f"Business context:\n{json.dumps(context, indent=2, default=str)}"
    )

    try:
        data = _request_gemini_json(prompt)
        offers = [
            OfferSuggestion(
                title=str(item["title"]),
                description=str(item["description"]),
                rationale=str(item["rationale"]),
                offer_type=str(item["offer_type"]),
            )
            for item in data["offers"]
        ]
        return OffersResult(success=True, offers=offers, business_context_used=context)
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Offer generation failed: %s", exc)
        return OffersResult(success=False, offers=[], error=str(exc))


def generate_marketing_recommendation() -> RecommendationResult:
    """Recommend which product to promote based on business intelligence."""
    try:
        context = collect_business_context()
    except PyMongoError as exc:
        raise MarketingAIError(
            "Unable to load business data for marketing recommendation."
        ) from exc

    prompt = (
        "You are a local retail marketing advisor.\n"
        "Analyze the business context and return ONLY valid JSON with keys:\n"
        "product_to_promote, reason, expected_business_impact, "
        "suggested_duration, suggested_offer\n\n"
        f"Business context:\n{json.dumps(context, indent=2, default=str)}"
    )

    try:
        data = _request_gemini_json(prompt)
        recommendation = MarketingRecommendation(
            product_to_promote=str(data["product_to_promote"]),
            reason=str(data["reason"]),
            expected_business_impact=str(data["expected_business_impact"]),
            suggested_duration=str(data["suggested_duration"]),
            suggested_offer=str(data["suggested_offer"]),
        )
        return RecommendationResult(
            success=True,
            recommendation=recommendation,
            business_context_used=context,
        )
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Marketing recommendation failed: %s", exc)
        return RecommendationResult(success=False, error=str(exc))


def generate_campaign(
    product_name: str,
    offer: str,
    target_audience: str,
    theme: str | None = None,
) -> CampaignResult:
    """Generate a complete marketing campaign package."""
    if not product_name or not product_name.strip():
        raise MarketingValidationError("Product name is required.")
    if not offer or not offer.strip():
        raise MarketingValidationError("Offer is required.")
    if not target_audience or not target_audience.strip():
        raise MarketingValidationError("Target audience is required.")

    theme_text = theme.strip() if theme else "local retail promotion"
    prompt = (
        "You are a campaign strategist for local retail shops.\n"
        "Return ONLY valid JSON with keys:\n"
        "campaign_title, slogan, objective, target_audience, "
        "promotional_message, campaign_description\n\n"
        f"Product: {product_name.strip()}\n"
        f"Offer: {offer.strip()}\n"
        f"Target audience: {target_audience.strip()}\n"
        f"Theme: {theme_text}"
    )

    try:
        data = _request_gemini_json(prompt)
        return CampaignResult(
            success=True,
            campaign_title=str(data["campaign_title"]),
            slogan=str(data["slogan"]),
            objective=str(data["objective"]),
            target_audience=str(data["target_audience"]),
            promotional_message=str(data["promotional_message"]),
            campaign_description=str(data["campaign_description"]),
        )
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Campaign generation failed: %s", exc)
        return CampaignResult(
            success=False,
            campaign_title="",
            slogan="",
            objective="",
            target_audience="",
            promotional_message="",
            campaign_description="",
            error=str(exc),
        )


def generate_campaign_calendar(
    calendar_type: CalendarType,
    shop_name: str | None = None,
    focus_product: str | None = None,
) -> CalendarResult:
    """Generate campaign ideas for a specific calendar horizon."""
    shop = shop_name.strip() if shop_name else "Local Shop"
    product = focus_product.strip() if focus_product else "top-selling products"

    type_guidance = {
        CalendarType.DAILY: "Generate 3 daily campaign ideas for today and tomorrow.",
        CalendarType.WEEKLY: "Generate 4 weekly campaign ideas for the coming week.",
        CalendarType.MONTHLY: "Generate 5 monthly campaign ideas for the coming month.",
        CalendarType.FESTIVAL: "Generate 5 festival-themed campaign ideas relevant to local retail.",
        CalendarType.SEASONAL: "Generate 5 seasonal campaign ideas based on the current season.",
    }

    try:
        context = collect_business_context()
    except PyMongoError:
        context = {}

    prompt = (
        "You are a campaign planner for local retail shops.\n"
        f"{type_guidance[calendar_type]}\n"
        "Return ONLY valid JSON with key 'ideas' as a list of objects containing:\n"
        "title, description, suggested_channels, call_to_action\n"
        "suggested_channels must be a list using values from: "
        "instagram, facebook, linkedin, whatsapp, in-store\n\n"
        f"Shop name: {shop}\n"
        f"Focus product: {product}\n"
        f"Business context:\n{json.dumps(context, indent=2, default=str)}"
    )

    try:
        data = _request_gemini_json(prompt)
        ideas = [
            CalendarIdea(
                title=str(item["title"]),
                description=str(item["description"]),
                suggested_channels=[str(channel) for channel in item["suggested_channels"]],
                call_to_action=str(item["call_to_action"]),
            )
            for item in data["ideas"]
        ]
        return CalendarResult(
            success=True,
            calendar_type=calendar_type.value,
            ideas=ideas,
        )
    except (MarketingAIError, gemini_service.GeminiConfigurationError) as exc:
        logger.error("Campaign calendar generation failed: %s", exc)
        return CalendarResult(
            success=False,
            calendar_type=calendar_type.value,
            ideas=[],
            error=str(exc),
        )


def prepare_publish_content(
    captions: CaptionResult,
    hashtags: list[str] | None = None,
    media_base64: str | None = None,
) -> dict[str, PublishContent]:
    """Prepare publish-ready content for each supported social platform."""
    tags = " ".join(hashtags) if hashtags else ""
    return {
        "instagram": PublishContent(
            text=f"{captions.instagram}\n\n{tags}".strip(),
            media_base64=media_base64,
            hashtags=hashtags,
        ),
        "facebook": PublishContent(
            text=captions.facebook,
            media_base64=media_base64,
        ),
        "linkedin": PublishContent(
            text=captions.linkedin,
            media_base64=media_base64,
        ),
        "x": PublishContent(
            text=captions.instagram[:280],
            media_base64=media_base64,
            hashtags=hashtags,
        ),
    }
