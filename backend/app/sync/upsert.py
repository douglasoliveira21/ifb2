from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_revision import DataRevision
from app.models.indicator_definition import IndicatorDefinition
from app.models.indicator_methodology import IndicatorMethodology
from app.models.indicator_value import IndicatorValue
from app.models.location import Location, LocationType
from app.models.source import Source
from app.sync.bcb_client import SeriesPoint
from app.sync.definitions import IndicatorSpec, SourceSpec, StaticIndicatorMeta

IndicatorMeta = IndicatorSpec | StaticIndicatorMeta


def get_or_create_source(db: Session, spec: SourceSpec) -> Source:
    source = db.execute(select(Source).where(Source.name == spec.name)).scalar_one_or_none()
    if source is None:
        source = Source(name=spec.name, url=spec.url, description=spec.description)
        db.add(source)
        db.flush()
    return source


def get_or_create_brasil(db: Session) -> Location:
    location = db.execute(select(Location).where(Location.code == "BR")).scalar_one_or_none()
    if location is None:
        location = Location(type=LocationType.country, code="BR", name="Brasil")
        db.add(location)
        db.flush()
    return location


def get_state(db: Session, uf: str) -> Location | None:
    """Retorna a UF já semeada por `app/sync/seed_states.py`. Não cria — se
    não existir, é sinal de que o seed de estados ainda não rodou."""
    return db.execute(
        select(Location).where(Location.type == LocationType.state, Location.code == uf)
    ).scalar_one_or_none()


def get_or_create_indicator_definition(
    db: Session, spec: IndicatorMeta, source: Source
) -> IndicatorDefinition:
    definition = db.execute(
        select(IndicatorDefinition).where(IndicatorDefinition.slug == spec.slug)
    ).scalar_one_or_none()

    if definition is None:
        definition = IndicatorDefinition(
            slug=spec.slug,
            name=spec.name,
            category=spec.category,
            unit=spec.unit,
            polarity=spec.polarity,
            description_what=spec.description_what,
            description_how=spec.description_how,
            update_frequency=spec.update_frequency,
            source_id=source.id,
            enabled=True,
        )
        db.add(definition)
        db.flush()
    else:
        # Metadados fixos (nome, unidade, categoria...) podem evoluir entre
        # deploys — o sync sempre reflete a definição vigente no código.
        definition.name = spec.name
        definition.category = spec.category
        definition.unit = spec.unit
        definition.polarity = spec.polarity
        definition.description_what = spec.description_what
        definition.description_how = spec.description_how
        definition.update_frequency = spec.update_frequency
        definition.source_id = source.id

    return definition


def ensure_methodology(db: Session, definition: IndicatorDefinition, content: str) -> None:
    latest = db.execute(
        select(IndicatorMethodology)
        .where(IndicatorMethodology.indicator_id == definition.id)
        .order_by(IndicatorMethodology.version.desc())
    ).scalars().first()

    if latest is not None and latest.content == content:
        return

    next_version = 1 if latest is None else latest.version + 1
    db.add(IndicatorMethodology(indicator_id=definition.id, version=next_version, content=content))


def upsert_indicator_values(
    db: Session,
    definition: IndicatorDefinition,
    location: Location,
    source: Source,
    points: list[SeriesPoint],
) -> int:
    """Insere valores novos e registra revisões quando um valor vigente muda.
    Nunca sobrescreve silenciosamente — toda mudança de valor já publicado
    gera uma linha em `data_revisions`. Retorna o número de pontos processados."""
    existing = {
        row.reference_date: row
        for row in db.execute(
            select(IndicatorValue).where(
                IndicatorValue.indicator_id == definition.id,
                IndicatorValue.location_id == location.id,
                IndicatorValue.is_revised == False,  # noqa: E712
            )
        ).scalars()
    }

    processed = 0
    for point in points:
        current = existing.get(point.reference_date)

        if current is None:
            db.add(
                IndicatorValue(
                    indicator_id=definition.id,
                    location_id=location.id,
                    reference_date=point.reference_date,
                    value=point.value,
                    source_id=source.id,
                )
            )
            processed += 1
        elif float(current.value) != point.value:
            db.add(
                DataRevision(
                    indicator_value_id=current.id,
                    previous_value=current.value,
                    new_value=point.value,
                    reason="Valor atualizado pela fonte oficial na sincronização automática.",
                    changed_by="sync",
                )
            )
            current.value = point.value
            processed += 1

    return processed
