import threading
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_admin
from app.models.data_revision import DataRevision
from app.models.indicator_definition import IndicatorDefinition
from app.models.indicator_methodology import IndicatorMethodology
from app.models.indicator_value import IndicatorValue
from app.models.location import Location
from app.models.source import Source
from app.models.sync_run import SyncRun
from app.models.verified_claim import (
    ClaimOrigin,
    ClaimStatus,
    ClaimVerdict,
    VerifiedClaim,
)
from app.schemas.admin import (
    AdminIndicatorOut,
    AdminIndicatorValueOut,
    AdminSourceOut,
    AdminSyncRunOut,
    CorrectionIn,
    CorrectionOut,
    ToggleIndicatorIn,
    VerifiedClaimIn,
)
from app.schemas.verified_claim import VerifiedClaimOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/sources", response_model=list[AdminSourceOut])
def list_admin_sources(db: Session = Depends(get_db)) -> list[AdminSourceOut]:
    sources = db.execute(select(Source).order_by(Source.name)).scalars().all()
    counts = {
        source_id: count
        for source_id, count in db.execute(
            select(IndicatorDefinition.source_id, func.count(IndicatorDefinition.id))
            .group_by(IndicatorDefinition.source_id)
        )
    }
    return [
        AdminSourceOut(
            name=s.name,
            url=s.url,
            description=s.description,
            indicators_count=counts.get(s.id, 0),
        )
        for s in sources
    ]


def _latest_methodology(db: Session, indicator_id) -> IndicatorMethodology | None:
    return db.execute(
        select(IndicatorMethodology)
        .where(IndicatorMethodology.indicator_id == indicator_id)
        .order_by(IndicatorMethodology.version.desc())
    ).scalars().first()


@router.get("/indicators", response_model=list[AdminIndicatorOut])
def list_admin_indicators(db: Session = Depends(get_db)) -> list[AdminIndicatorOut]:
    definitions = db.execute(select(IndicatorDefinition).order_by(IndicatorDefinition.name)).scalars().all()
    result = []
    for d in definitions:
        methodology = _latest_methodology(db, d.id)
        result.append(
            AdminIndicatorOut(
                slug=d.slug,
                name=d.name,
                category=d.category.value,
                unit=d.unit,
                source_name=d.source.name,
                enabled=d.enabled,
                methodology=methodology.content if methodology else None,
                methodology_version=methodology.version if methodology else None,
            )
        )
    return result


@router.patch("/indicators/{slug}", response_model=AdminIndicatorOut)
def toggle_indicator(
    slug: str, payload: ToggleIndicatorIn, db: Session = Depends(get_db)
) -> AdminIndicatorOut:
    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.slug == slug)
    ).scalar_one_or_none()
    if definition is None:
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    definition.enabled = payload.enabled
    db.commit()
    db.refresh(definition)

    db.connection().exec_driver_sql("REFRESH MATERIALIZED VIEW indicators")
    db.commit()

    methodology = _latest_methodology(db, definition.id)
    return AdminIndicatorOut(
        slug=definition.slug,
        name=definition.name,
        category=definition.category.value,
        unit=definition.unit,
        source_name=definition.source.name,
        enabled=definition.enabled,
        methodology=methodology.content if methodology else None,
        methodology_version=methodology.version if methodology else None,
    )


@router.get("/indicators/{slug}/values", response_model=list[AdminIndicatorValueOut])
def list_indicator_values(slug: str, db: Session = Depends(get_db)) -> list[AdminIndicatorValueOut]:
    """Valores vigentes (não revisados) de um indicador, em qualquer
    localização — usado para escolher qual valor corrigir manualmente."""
    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.slug == slug)
    ).scalar_one_or_none()
    if definition is None:
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    rows = db.execute(
        select(IndicatorValue, Location.code)
        .join(Location, Location.id == IndicatorValue.location_id)
        .where(
            IndicatorValue.indicator_id == definition.id,
            IndicatorValue.is_revised == False,  # noqa: E712
        )
        .order_by(Location.code, IndicatorValue.reference_date.desc())
    ).all()

    return [
        AdminIndicatorValueOut(
            id=value.id,
            location_code=code,
            reference_date=value.reference_date,
            value=float(value.value),
            is_revised=value.is_revised,
        )
        for value, code in rows
    ]


@router.get("/sync-runs", response_model=list[AdminSyncRunOut])
def list_sync_runs(db: Session = Depends(get_db)) -> list[AdminSyncRunOut]:
    rows = db.execute(
        select(SyncRun, Source.name)
        .join(Source, Source.id == SyncRun.source_id)
        .order_by(SyncRun.started_at.desc())
        .limit(100)
    ).all()

    return [
        AdminSyncRunOut(
            id=run.id,
            source_name=source_name,
            started_at=run.started_at,
            finished_at=run.finished_at,
            status=run.status.value,
            records_processed=run.records_processed,
            error_message=run.error_message,
        )
        for run, source_name in rows
    ]


_sync_lock = threading.Lock()
_sync_running = False


def _run_sync_and_release() -> None:
    global _sync_running
    try:
        from app.sync.run import (
            main as run_sync,  # import local: evita custo de import em todo request
        )

        run_sync()
    finally:
        with _sync_lock:
            _sync_running = False


@router.post("/sync", status_code=202)
def trigger_sync(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Dispara a sincronização completa em segundo plano e retorna na hora.

    Com os indicadores municipais (Fase 4), a sync completa passou a levar
    de 10 a 20 minutos — rodar isso de forma síncrona dentro da requisição
    estourava o timeout do navegador/proxy antes de terminar, fazendo o
    botão parecer travado mesmo com a sync completando corretamente no
    servidor. Acompanhe o progresso em /admin/sincronizacoes: cada fonte
    grava seu próprio `SyncRun` assim que termina, não só no final."""
    global _sync_running
    with _sync_lock:
        if _sync_running:
            raise HTTPException(status_code=409, detail="Uma sincronização já está em andamento.")
        _sync_running = True

    background_tasks.add_task(_run_sync_and_release)
    return {"status": "iniciado"}


@router.get("/corrections", response_model=list[CorrectionOut])
def list_corrections(db: Session = Depends(get_db)) -> list[CorrectionOut]:
    rows = db.execute(
        select(DataRevision, IndicatorValue, IndicatorDefinition, Location.code)
        .join(IndicatorValue, IndicatorValue.id == DataRevision.indicator_value_id)
        .join(IndicatorDefinition, IndicatorDefinition.id == IndicatorValue.indicator_id)
        .join(Location, Location.id == IndicatorValue.location_id)
        .where(DataRevision.changed_by != "sync")
        .order_by(DataRevision.changed_at.desc())
        .limit(100)
    ).all()

    return [
        CorrectionOut(
            id=revision.id,
            indicator_slug=definition.slug,
            location_code=code,
            reference_date=value.reference_date,
            previous_value=float(revision.previous_value),
            new_value=float(revision.new_value),
            reason=revision.reason,
            changed_by=revision.changed_by,
            changed_at=revision.changed_at,
        )
        for revision, value, definition, code in rows
    ]


@router.post("/corrections", response_model=CorrectionOut, status_code=201)
def create_correction(
    payload: CorrectionIn,
    db: Session = Depends(get_db),
    admin_user: str = Depends(require_admin),
) -> CorrectionOut:
    """Registra uma correção manual. Nunca sobrescreve o valor em silêncio:
    toda mudança fica em `data_revisions`, com motivo e autor obrigatórios."""
    value = db.execute(
        select(IndicatorValue).where(IndicatorValue.id == payload.indicator_value_id)
    ).scalar_one_or_none()
    if value is None:
        raise HTTPException(status_code=404, detail="Valor não encontrado")

    if not payload.reason.strip():
        raise HTTPException(status_code=422, detail="Motivo da correção é obrigatório")

    revision = DataRevision(
        indicator_value_id=value.id,
        previous_value=value.value,
        new_value=payload.new_value,
        reason=payload.reason.strip(),
        changed_by=f"admin:{admin_user}",
        changed_at=datetime.now(timezone.utc),
    )
    value.value = payload.new_value
    db.add(revision)
    db.commit()
    db.refresh(revision)

    db.connection().exec_driver_sql("REFRESH MATERIALIZED VIEW indicators")
    db.commit()

    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.id == value.indicator_id)
    ).scalar_one()
    location_code = db.execute(select(Location.code).where(Location.id == value.location_id)).scalar_one()

    return CorrectionOut(
        id=revision.id,
        indicator_slug=definition.slug,
        location_code=location_code,
        reference_date=value.reference_date,
        previous_value=float(revision.previous_value),
        new_value=float(revision.new_value),
        reason=revision.reason,
        changed_by=revision.changed_by,
        changed_at=revision.changed_at,
    )


def _resolve_indicator_id(db: Session, slug: str | None) -> UUID | None:
    if not slug:
        return None
    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.slug == slug)
    ).scalar_one_or_none()
    if definition is None:
        raise HTTPException(status_code=422, detail=f"Indicador '{slug}' não encontrado")
    return definition.id


def _verified_claim_out(db: Session, claim: VerifiedClaim) -> VerifiedClaimOut:
    slug = None
    if claim.indicator_id is not None:
        slug = db.execute(
            select(IndicatorDefinition.slug).where(IndicatorDefinition.id == claim.indicator_id)
        ).scalar_one_or_none()
    return VerifiedClaimOut(
        id=claim.id,
        quote=claim.quote,
        speaker_name=claim.speaker_name,
        speaker_role=claim.speaker_role,
        claim_date=claim.claim_date,
        source_url=claim.source_url,
        indicator_slug=slug,
        verdict=claim.verdict.value,
        explanation=claim.explanation,
        status=claim.status.value,
        origin=claim.origin.value,
        created_at=claim.created_at,
    )


@router.get("/verified-claims", response_model=list[VerifiedClaimOut])
def list_admin_verified_claims(
    status: str | None = None, db: Session = Depends(get_db)
) -> list[VerifiedClaimOut]:
    """`status=DRAFT` lista só os rascunhos pendentes de revisão (gerados
    pela varredura automática ou manualmente); sem o parâmetro, lista
    tudo, rascunho e publicado."""
    query = select(VerifiedClaim)
    if status:
        try:
            query = query.where(VerifiedClaim.status == ClaimStatus(status))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f"Status inválido: {status}") from exc
    rows = db.execute(query.order_by(VerifiedClaim.created_at.desc())).scalars().all()
    return [_verified_claim_out(db, claim) for claim in rows]


@router.post("/verified-claims", response_model=VerifiedClaimOut, status_code=201)
def create_verified_claim(payload: VerifiedClaimIn, db: Session = Depends(get_db)) -> VerifiedClaimOut:
    try:
        verdict = ClaimVerdict(payload.verdict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Veredito inválido: {payload.verdict}") from exc

    claim = VerifiedClaim(
        quote=payload.quote.strip(),
        speaker_name=payload.speaker_name.strip(),
        speaker_role=payload.speaker_role.strip() if payload.speaker_role else None,
        claim_date=payload.claim_date,
        source_url=payload.source_url.strip() if payload.source_url else None,
        indicator_id=_resolve_indicator_id(db, payload.indicator_slug),
        verdict=verdict,
        explanation=payload.explanation.strip(),
        status=ClaimStatus.PUBLISHED,
        origin=ClaimOrigin.MANUAL,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return _verified_claim_out(db, claim)


@router.put("/verified-claims/{claim_id}", response_model=VerifiedClaimOut)
def update_verified_claim(
    claim_id: UUID, payload: VerifiedClaimIn, db: Session = Depends(get_db)
) -> VerifiedClaimOut:
    """Edita o conteúdo de uma frase, publicada ou rascunho — não muda o
    status. Use POST /verified-claims/{id}/publish para aprovar um
    rascunho."""
    claim = db.execute(select(VerifiedClaim).where(VerifiedClaim.id == claim_id)).scalar_one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="Frase verificada não encontrada")

    try:
        verdict = ClaimVerdict(payload.verdict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Veredito inválido: {payload.verdict}") from exc

    claim.quote = payload.quote.strip()
    claim.speaker_name = payload.speaker_name.strip()
    claim.speaker_role = payload.speaker_role.strip() if payload.speaker_role else None
    claim.claim_date = payload.claim_date
    claim.source_url = payload.source_url.strip() if payload.source_url else None
    claim.indicator_id = _resolve_indicator_id(db, payload.indicator_slug)
    claim.verdict = verdict
    claim.explanation = payload.explanation.strip()
    db.commit()
    db.refresh(claim)
    return _verified_claim_out(db, claim)


@router.post("/verified-claims/{claim_id}/publish", response_model=VerifiedClaimOut)
def publish_verified_claim(claim_id: UUID, db: Session = Depends(get_db)) -> VerifiedClaimOut:
    """Aprova um rascunho (gerado pela varredura automática ou manual) e
    o torna público em /frases-verificadas."""
    claim = db.execute(select(VerifiedClaim).where(VerifiedClaim.id == claim_id)).scalar_one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="Frase verificada não encontrada")
    claim.status = ClaimStatus.PUBLISHED
    db.commit()
    db.refresh(claim)
    return _verified_claim_out(db, claim)


@router.delete("/verified-claims/{claim_id}", status_code=204)
def delete_verified_claim(claim_id: UUID, db: Session = Depends(get_db)) -> None:
    """Descarta uma frase — usado principalmente para rejeitar rascunhos
    da varredura automática que não fazem sentido publicar."""
    claim = db.execute(select(VerifiedClaim).where(VerifiedClaim.id == claim_id)).scalar_one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="Frase verificada não encontrada")
    db.delete(claim)
    db.commit()
