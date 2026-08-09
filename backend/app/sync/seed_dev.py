"""Popula dados de DEMONSTRAÇÃO — uso exclusivo em ambiente development.

Nunca rodar em produção. Todos os registros criados aqui têm o nome da
fonte prefixado com "[DEMO]" para deixar claro, em qualquer tela (inclusive
admin/transparência), que não são dados oficiais.

Uso: python -m app.sync.seed_dev
"""
import math
import sys
from datetime import date

from app.core.config import get_settings
from app.core.db import Base, SessionLocal, engine
from app.models.indicator_definition import IndicatorCategory, IndicatorDefinition, IndicatorPolarity
from app.models.indicator_methodology import IndicatorMethodology
from app.models.indicator_value import IndicatorValue
from app.models.location import Location, LocationType
from app.models.source import Source
from app.sync.seed_government_periods import seed as seed_government_periods
from app.sync.seed_states import seed as seed_states

DEMO_SOURCE_NAME = "[DEMO] Fonte de demonstração"


def _monthly_series(start_year: int, start_month: int, end_year: int, end_month: int,
                     base: float, trend_per_year: float, amplitude: float) -> list[tuple[date, float]]:
    """Série sintética mensal (tendência + oscilação) — apenas para preencher
    o layout em desenvolvimento local, nunca representa dado real."""
    points: list[tuple[date, float]] = []
    year, month = start_year, start_month
    i = 0
    while (year, month) <= (end_year, end_month):
        years_elapsed = i / 12
        value = base + trend_per_year * years_elapsed + amplitude * math.sin(i / 6)
        points.append((date(year, month, 1), round(value, 2)))
        month += 1
        if month > 12:
            month = 1
            year += 1
        i += 1
    return points


def seed() -> None:
    settings = get_settings()
    if settings.environment != "development":
        print("seed_dev abortado: environment != 'development'.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine, tables=[
        Source.__table__,
        Location.__table__,
        IndicatorDefinition.__table__,
        IndicatorMethodology.__table__,
        IndicatorValue.__table__,
    ])

    with SessionLocal() as db:
        source = db.query(Source).filter(Source.name == DEMO_SOURCE_NAME).one_or_none()
        if source is None:
            source = Source(
                name=DEMO_SOURCE_NAME,
                url="https://example.org/demo",
                description="Dados fictícios para desenvolvimento local. Não usar como referência.",
            )
            db.add(source)
            db.flush()

        brasil = db.query(Location).filter(Location.code == "BR").one_or_none()
        if brasil is None:
            brasil = Location(type=LocationType.country, code="BR", name="Brasil")
            db.add(brasil)
            db.flush()

        demo_indicators = [
            (
                "desemprego", "Taxa de desemprego (DEMO)", IndicatorCategory.EMPREGO_RENDA, "%",
                IndicatorPolarity.lower_is_better,
                _monthly_series(2015, 1, 2026, 7, base=11.0, trend_per_year=-0.4, amplitude=1.5),
            ),
            (
                "ipca", "IPCA — inflação 12 meses (DEMO)", IndicatorCategory.ECONOMIA, "%",
                IndicatorPolarity.lower_is_better,
                _monthly_series(2015, 1, 2026, 7, base=6.5, trend_per_year=-0.15, amplitude=2.0),
            ),
            (
                "selic", "Taxa Selic (DEMO)", IndicatorCategory.ECONOMIA, "%",
                IndicatorPolarity.neutral,
                _monthly_series(2015, 1, 2026, 7, base=12.0, trend_per_year=-0.1, amplitude=3.0),
            ),
        ]

        for slug, name, category, unit, polarity, points in demo_indicators:
            definition = db.query(IndicatorDefinition).filter(IndicatorDefinition.slug == slug).one_or_none()
            if definition is None:
                definition = IndicatorDefinition(
                    slug=slug,
                    name=name,
                    category=category,
                    unit=unit,
                    polarity=polarity,
                    description_what="Indicador de demonstração — não é dado oficial.",
                    description_how="Uso exclusivo para desenvolvimento local.",
                    update_frequency="mensal",
                    source_id=source.id,
                    enabled=True,
                )
                db.add(definition)
                db.flush()

            has_methodology = (
                db.query(IndicatorMethodology)
                .filter(IndicatorMethodology.indicator_id == definition.id)
                .first()
            )
            if has_methodology is None:
                db.add(
                    IndicatorMethodology(
                        indicator_id=definition.id,
                        version=1,
                        content=(
                            "# Metodologia (DEMO)\n\nEste texto e os valores deste indicador são "
                            "fictícios, gerados apenas para desenvolvimento local do IFB."
                        ),
                    )
                )

            for reference_date, value in points:
                exists = (
                    db.query(IndicatorValue)
                    .filter(
                        IndicatorValue.indicator_id == definition.id,
                        IndicatorValue.location_id == brasil.id,
                        IndicatorValue.reference_date == reference_date,
                    )
                    .one_or_none()
                )
                if exists is None:
                    db.add(
                        IndicatorValue(
                            indicator_id=definition.id,
                            location_id=brasil.id,
                            reference_date=reference_date,
                            value=value,
                            source_id=source.id,
                        )
                    )

        db.commit()

    seed_government_periods()
    seed_states()
    _seed_demo_state_indicator()

    with engine.connect() as conn:
        conn.exec_driver_sql("REFRESH MATERIALIZED VIEW indicators")
        conn.commit()

    print("Dados de demonstração inseridos (ambiente development).")


def _seed_demo_state_indicator() -> None:
    """Indicador demo com dado por estado (só alguns UFs têm valor — as
    demais devem exibir 'Dado ainda não disponível' nas páginas de estado,
    exatamente como aconteceria em produção)."""
    with SessionLocal() as db:
        source = db.query(Source).filter(Source.name == DEMO_SOURCE_NAME).one_or_none()
        definition = db.query(IndicatorDefinition).filter(IndicatorDefinition.slug == "desmatamento-demo").one_or_none()
        if definition is None:
            definition = IndicatorDefinition(
                slug="desmatamento-demo",
                name="Desmatamento (DEMO)",
                category=IndicatorCategory.MEIO_AMBIENTE,
                unit="km²/ano",
                polarity=IndicatorPolarity.lower_is_better,
                description_what="Indicador de demonstração — não é dado oficial.",
                description_how="Uso exclusivo para desenvolvimento local.",
                update_frequency="anual",
                source_id=source.id,
                enabled=True,
            )
            db.add(definition)
            db.flush()

        demo_state_values = {
            "AM": [(2022, 1120), (2023, 980), (2024, 850)],
            "PA": [(2022, 2400), (2023, 1900), (2024, 1600)],
            "MT": [(2022, 1300), (2023, 1100), (2024, 900)],
        }

        for uf, points in demo_state_values.items():
            location = db.query(Location).filter(Location.code == uf).one_or_none()
            if location is None:
                continue
            for year, value in points:
                exists = (
                    db.query(IndicatorValue)
                    .filter(
                        IndicatorValue.indicator_id == definition.id,
                        IndicatorValue.location_id == location.id,
                        IndicatorValue.reference_date == date(year, 1, 1),
                    )
                    .one_or_none()
                )
                if exists is None:
                    db.add(
                        IndicatorValue(
                            indicator_id=definition.id,
                            location_id=location.id,
                            reference_date=date(year, 1, 1),
                            value=value,
                            source_id=source.id,
                        )
                    )

        db.commit()


if __name__ == "__main__":
    seed()
