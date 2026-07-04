"""The v2 checkers: website, news & fact check, product listing."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import optional_user
from ..models import NewsCheckRequest, ProductCheckRequest, UrlCheckRequest
from ..services import (article, guidance, news_checker, product_checker,
                        safe_fetch, url_checker)
from ..limiter import limiter
from .scan import save_check

router = APIRouter(prefix="/api/check", tags=["checks"])


@router.post("/url")
@limiter.limit("10/minute")
def check_url(request: Request, body: UrlCheckRequest,
              user: Annotated[dict | None, Depends(optional_user)]):
    """Analyze a website address for phishing risk (guests welcome)."""
    try:
        tips = guidance.retrieve(f"phishing website fake link {body.url}")
        result = url_checker.check(body.url, body.language, guidance=tips)
    except safe_fetch.UnsafeUrl as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    result["guidance"] = tips
    return save_check("url", result["normalized_url"], result, user)


@router.post("/news")
@limiter.limit("6/minute")
def check_news(request: Request, body: NewsCheckRequest,
               user: Annotated[dict | None, Depends(optional_user)]):
    """Credibility-check an article, headline, or claim (text or URL)."""
    if not body.text and not body.url:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Provide either text or a url to check.")
    title, text = "", body.text or ""
    if body.url and not text:
        try:
            title, text = article.extract_from_url(body.url)
        except safe_fetch.UnsafeUrl as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
        except safe_fetch.FetchFailed as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    tips = guidance.retrieve(f"fake news misinformation fact check {text[:200]}")
    result = news_checker.check(text, body.language, source_title=title,
                                guidance=tips)
    result["guidance"] = tips
    if title:
        result["title"] = title
    label = title or text[:200]
    return save_check("news", label, result, user)


@router.post("/product")
@limiter.limit("10/minute")
def check_product(request: Request, body: ProductCheckRequest,
                  user: Annotated[dict | None, Depends(optional_user)]):
    """Assess an online product listing for fraud/counterfeit risk."""
    tips = guidance.retrieve(
        f"fake product counterfeit online shopping scam {body.title}")
    result = product_checker.check(
        title=body.title, description=body.description, price=body.price,
        platform=body.platform, seller_info=body.seller_info,
        reviews_text=body.reviews_text, image_b64=body.image_b64,
        image_mime=body.image_mime, language=body.language, guidance=tips)
    result["guidance"] = tips
    return save_check("product", body.title[:200], result, user)
