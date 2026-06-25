import json
import logging

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from backend.services import marketing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketing", tags=["Marketing Studio"])


class CaptionRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    offer: str = Field(..., min_length=1, max_length=500)
    target_audience: str | None = Field(default=None, max_length=200)


class HashtagRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    keywords: list[str] = Field(..., min_length=1, max_length=20)


class CampaignRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    offer: str = Field(..., min_length=1, max_length=500)
    target_audience: str = Field(..., min_length=1, max_length=200)
    theme: str | None = Field(default=None, max_length=200)


class CalendarRequest(BaseModel):
    calendar_type: marketing_service.CalendarType
    shop_name: str | None = Field(default=None, max_length=200)
    focus_product: str | None = Field(default=None, max_length=200)


class PosterDesignDetailsResponse(BaseModel):
    poster_headline: str
    promotional_text: str
    call_to_action: str
    design_style: str
    color_suggestions: list[str]
    font_suggestions: list[str]
    layout_suggestions: list[str]
    image_generation_prompt: str


class PosterResponse(BaseModel):
    success: bool
    poster_id: str
    poster_headline: str
    promotional_text: str
    call_to_action: str
    design_style: str
    design_summary: str
    poster_image: str | None = None
    download_url: str | None = None
    design_details: PosterDesignDetailsResponse | None = None
    error: str | None = None


class PosterRecordResponse(BaseModel):
    poster_id: str
    session_id: str | None = None
    product_name: str
    generation_timestamp: str
    image_location: str
    download_url: str
    prompt: str
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


class CaptionResponse(BaseModel):
    success: bool
    instagram: str
    facebook: str
    linkedin: str
    whatsapp_business: str
    error: str | None = None


class HashtagResponse(BaseModel):
    success: bool
    hashtags: list[str]
    error: str | None = None


class OfferSuggestionResponse(BaseModel):
    title: str
    description: str
    rationale: str
    offer_type: str


class OffersResponse(BaseModel):
    success: bool
    offers: list[OfferSuggestionResponse]
    business_context_used: dict
    error: str | None = None


class RecommendationDetailsResponse(BaseModel):
    product_to_promote: str
    reason: str
    expected_business_impact: str
    suggested_duration: str
    suggested_offer: str


class RecommendationResponse(BaseModel):
    success: bool
    recommendation: RecommendationDetailsResponse | None = None
    business_context_used: dict
    error: str | None = None


class CampaignResponse(BaseModel):
    success: bool
    campaign_title: str
    slogan: str
    objective: str
    target_audience: str
    promotional_message: str
    campaign_description: str
    error: str | None = None


class CalendarIdeaResponse(BaseModel):
    title: str
    description: str
    suggested_channels: list[str]
    call_to_action: str


class CalendarResponse(BaseModel):
    success: bool
    calendar_type: str
    ideas: list[CalendarIdeaResponse]
    error: str | None = None


class SocialPlatformResponse(BaseModel):
    platform: str
    status: str


class SocialPublishingInfoResponse(BaseModel):
    supported_platforms: list[str]
    note: str
    platforms: list[SocialPlatformResponse]


def _parse_keywords(raw_keywords: str) -> list[str]:
    """Parse keywords submitted as JSON array or comma-separated text."""
    raw_keywords = raw_keywords.strip()
    if not raw_keywords:
        raise marketing_service.MarketingValidationError("Keywords are required.")

    if raw_keywords.startswith("["):
        try:
            parsed = json.loads(raw_keywords)
        except json.JSONDecodeError as exc:
            raise marketing_service.MarketingValidationError(
                "Keywords JSON must be a valid array of strings."
            ) from exc
        if not isinstance(parsed, list):
            raise marketing_service.MarketingValidationError(
                "Keywords JSON must be a valid array of strings."
            )
        return [str(keyword) for keyword in parsed]

    return [keyword.strip() for keyword in raw_keywords.split(",") if keyword.strip()]


@router.post(
    "/poster",
    response_model=PosterResponse,
    summary="Generate an AI promotional poster",
)
async def create_poster(
    product_name: str = Form(...),
    keywords: str = Form(...),
    offer: str = Form(...),
    theme: str = Form(...),
    target_audience: str = Form(...),
    session_id: str | None = Form(default=None),
    product_image: UploadFile | None = File(default=None),
) -> PosterResponse:
    try:
        parsed_keywords = _parse_keywords(keywords)
        image_bytes = None
        image_mime = None

        if product_image is not None and product_image.filename:
            image_bytes = await product_image.read()
            image_mime = product_image.content_type

        result = marketing_service.generate_poster(
            product_name=product_name,
            keywords=parsed_keywords,
            offer=offer,
            theme=theme,
            target_audience=target_audience,
            product_image_bytes=image_bytes,
            product_image_mime=image_mime,
            session_id=session_id,
        )

        design_details = None
        if result.design_details:
            design_details = PosterDesignDetailsResponse(
                poster_headline=result.design_details.poster_headline,
                promotional_text=result.design_details.promotional_text,
                call_to_action=result.design_details.call_to_action,
                design_style=result.design_details.design_style,
                color_suggestions=result.design_details.color_suggestions,
                font_suggestions=result.design_details.font_suggestions,
                layout_suggestions=result.design_details.layout_suggestions,
                image_generation_prompt=result.design_details.image_generation_prompt,
            )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result.error or "Poster generation failed.",
            )

        return PosterResponse(
            success=result.success,
            poster_id=result.poster_id,
            poster_headline=result.poster_headline,
            promotional_text=result.promotional_text,
            call_to_action=result.call_to_action,
            design_style=result.design_style,
            design_summary=result.design_summary,
            poster_image=result.poster_image,
            download_url=result.download_url,
            design_details=design_details,
        )
    except marketing_service.GenerationInProgressError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except marketing_service.MarketingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PyMongoError as exc:
        logger.error("Database error during poster generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/posters",
    response_model=list[PosterRecordResponse],
    summary="List generated poster history",
)
def list_posters(session_id: str | None = None) -> list[PosterRecordResponse]:
    try:
        posters = marketing_service.list_posters(session_id=session_id)
        return [
            PosterRecordResponse(
                poster_id=poster.poster_id,
                session_id=poster.session_id,
                product_name=poster.product_name,
                generation_timestamp=poster.generation_timestamp.isoformat(),
                image_location=poster.image_location,
                download_url=poster.download_url,
                prompt=poster.prompt,
                generation_status=poster.generation_status,
                poster_headline=poster.poster_headline,
                promotional_text=poster.promotional_text,
                call_to_action=poster.call_to_action,
                design_style=poster.design_style,
                design_summary=poster.design_summary,
                keywords=poster.keywords,
                offer=poster.offer,
                theme=poster.theme,
                target_audience=poster.target_audience,
                image_mime=poster.image_mime,
            )
            for poster in posters
        ]
    except PyMongoError as exc:
        logger.error("Database error while listing posters: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/posters/{poster_id}",
    response_model=PosterRecordResponse,
    summary="Get a generated poster record",
)
def get_poster(poster_id: str) -> PosterRecordResponse:
    try:
        poster = marketing_service.get_poster_by_id(poster_id)
        return PosterRecordResponse(
            poster_id=poster.poster_id,
            session_id=poster.session_id,
            product_name=poster.product_name,
            generation_timestamp=poster.generation_timestamp.isoformat(),
            image_location=poster.image_location,
            download_url=poster.download_url,
            prompt=poster.prompt,
            generation_status=poster.generation_status,
            poster_headline=poster.poster_headline,
            promotional_text=poster.promotional_text,
            call_to_action=poster.call_to_action,
            design_style=poster.design_style,
            design_summary=poster.design_summary,
            keywords=poster.keywords,
            offer=poster.offer,
            theme=poster.theme,
            target_audience=poster.target_audience,
            image_mime=poster.image_mime,
        )
    except marketing_service.PosterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PyMongoError as exc:
        logger.error("Database error while fetching poster %s: %s", poster_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/posters/{poster_id}/download",
    summary="Download a generated poster image",
)
def download_poster(poster_id: str) -> FileResponse:
    try:
        image_path, mime_type = marketing_service.get_poster_image_file(poster_id)
        filename = Path(image_path).name
        return FileResponse(
            path=image_path,
            media_type=mime_type,
            filename=filename,
        )
    except marketing_service.PosterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PyMongoError as exc:
        logger.error("Database error while downloading poster %s: %s", poster_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.delete(
    "/posters/{poster_id}",
    summary="Delete a generated poster",
)
def delete_poster(poster_id: str) -> dict[str, str]:
    try:
        deleted_id = marketing_service.delete_poster(poster_id)
        return {
            "success": True,
            "message": "Poster deleted successfully",
            "poster_id": deleted_id,
        }
    except marketing_service.PosterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PyMongoError as exc:
        logger.error("Database error while deleting poster %s: %s", poster_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.post(
    "/caption",
    response_model=CaptionResponse,
    summary="Generate platform-specific captions",
)
def create_captions(payload: CaptionRequest) -> CaptionResponse:
    try:
        result = marketing_service.generate_captions(
            product_name=payload.product_name,
            offer=payload.offer,
            target_audience=payload.target_audience,
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.error or "Caption generation failed.",
            )
        return CaptionResponse(
            success=result.success,
            instagram=result.instagram,
            facebook=result.facebook,
            linkedin=result.linkedin,
            whatsapp_business=result.whatsapp_business,
        )
    except marketing_service.MarketingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/hashtags",
    response_model=HashtagResponse,
    summary="Generate marketing hashtags",
)
def create_hashtags(payload: HashtagRequest) -> HashtagResponse:
    try:
        result = marketing_service.generate_hashtags(
            product_name=payload.product_name,
            keywords=payload.keywords,
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.error or "Hashtag generation failed.",
            )
        return HashtagResponse(success=result.success, hashtags=result.hashtags)
    except marketing_service.MarketingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/offers",
    response_model=OffersResponse,
    summary="Generate intelligent promotional offers",
)
def create_offers() -> OffersResponse:
    try:
        result = marketing_service.generate_intelligent_offers()
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.error or "Offer generation failed.",
            )
        return OffersResponse(
            success=result.success,
            offers=[
                OfferSuggestionResponse(
                    title=offer.title,
                    description=offer.description,
                    rationale=offer.rationale,
                    offer_type=offer.offer_type,
                )
                for offer in result.offers
            ],
            business_context_used=result.business_context_used,
        )
    except marketing_service.MarketingAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error during offer generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.post(
    "/recommendation",
    response_model=RecommendationResponse,
    summary="Generate a data-driven marketing recommendation",
)
def create_recommendation() -> RecommendationResponse:
    try:
        result = marketing_service.generate_marketing_recommendation()
        if not result.success or result.recommendation is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.error or "Recommendation generation failed.",
            )
        return RecommendationResponse(
            success=result.success,
            recommendation=RecommendationDetailsResponse(
                product_to_promote=result.recommendation.product_to_promote,
                reason=result.recommendation.reason,
                expected_business_impact=result.recommendation.expected_business_impact,
                suggested_duration=result.recommendation.suggested_duration,
                suggested_offer=result.recommendation.suggested_offer,
            ),
            business_context_used=result.business_context_used,
        )
    except marketing_service.MarketingAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error during recommendation generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.post(
    "/campaign",
    response_model=CampaignResponse,
    summary="Generate a marketing campaign",
)
def create_campaign(payload: CampaignRequest) -> CampaignResponse:
    try:
        result = marketing_service.generate_campaign(
            product_name=payload.product_name,
            offer=payload.offer,
            target_audience=payload.target_audience,
            theme=payload.theme,
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.error or "Campaign generation failed.",
            )
        return CampaignResponse(
            success=result.success,
            campaign_title=result.campaign_title,
            slogan=result.slogan,
            objective=result.objective,
            target_audience=result.target_audience,
            promotional_message=result.promotional_message,
            campaign_description=result.campaign_description,
        )
    except marketing_service.MarketingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/calendar",
    response_model=CalendarResponse,
    summary="Generate campaign calendar ideas",
)
def create_campaign_calendar(payload: CalendarRequest) -> CalendarResponse:
    try:
        result = marketing_service.generate_campaign_calendar(
            calendar_type=payload.calendar_type,
            shop_name=payload.shop_name,
            focus_product=payload.focus_product,
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result.error or "Campaign calendar generation failed.",
            )
        return CalendarResponse(
            success=result.success,
            calendar_type=result.calendar_type,
            ideas=[
                CalendarIdeaResponse(
                    title=idea.title,
                    description=idea.description,
                    suggested_channels=idea.suggested_channels,
                    call_to_action=idea.call_to_action,
                )
                for idea in result.ideas
            ],
        )
    except marketing_service.MarketingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PyMongoError as exc:
        logger.error("Database error during calendar generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/platforms",
    response_model=SocialPublishingInfoResponse,
    summary="List future social publishing platforms",
)
def list_social_platforms() -> SocialPublishingInfoResponse:
    platforms = marketing_service.SocialPublisherRegistry.supported_platforms()
    return SocialPublishingInfoResponse(
        supported_platforms=platforms,
        note=(
            "Publishing adapters are modular and reserved for future integrations. "
            "Marketing Studio currently generates publish-ready content only."
        ),
        platforms=[
            SocialPlatformResponse(platform=platform, status="planned")
            for platform in platforms
        ],
    )
