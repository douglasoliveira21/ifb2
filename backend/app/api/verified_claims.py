from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.indicator_definition import IndicatorDefinition
from app.models.verified_claim import VerifiedClaim
from app.schemas.verified_claim import VerifiedClaimOut

router = APIRouter(prefix="/verified-claims", tags=["verified-claims"])


@router.get("", response_model=list[VerifiedClaimOut])
def list_verified_claims(db: Session = Depends(get_db)) -> list[VerifiedClaimOut]:
    """Frases de campanha checadas contra indicadores reais — curadoria
    manual (ver /admin/verified-claims), sem geração automática."""
    rows = db.execute(
        select(VerifiedClaim, IndicatorDefinition.slug)
        .outerjoin(IndicatorDefinition, IndicatorDefinition.id == VerifiedClaim.indicator_id)
        .order_by(VerifiedClaim.claim_date.desc().nulls_last(), VerifiedClaim.created_at.desc())
    ).all()

    return [
        VerifiedClaimOut(
            id=claim.id,
            quote=claim.quote,
            speaker_name=claim.speaker_name,
            speaker_role=claim.speaker_role,
            claim_date=claim.claim_date,
            source_url=claim.source_url,
            indicator_slug=slug,
            verdict=claim.verdict.value,
            explanation=claim.explanation,
            created_at=claim.created_at,
        )
        for claim, slug in rows
    ]
