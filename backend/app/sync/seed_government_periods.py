"""Seed idempotente de `government_periods` (nível federal).

Datas de posse são registro histórico público — não são estatística
sujeita a fonte/metodologia como os indicadores, por isso não passam pelo
fluxo de sync com SyncRun. Servem apenas como referência visual discreta
nos gráficos históricos (ver regra: nunca usar cor de partido, nunca tratar
o presidente como protagonista do gráfico).

Uso: python -m app.sync.seed_government_periods
"""
from datetime import date

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.government_period import GovernmentLevel, GovernmentPeriod
from app.sync.upsert import get_or_create_brasil

FEDERAL_PERIODS = [
    ("Fernando Henrique Cardoso", date(1995, 1, 1), date(1999, 1, 1)),
    ("Fernando Henrique Cardoso", date(1999, 1, 1), date(2003, 1, 1)),
    ("Luiz Inácio Lula da Silva", date(2003, 1, 1), date(2007, 1, 1)),
    ("Luiz Inácio Lula da Silva", date(2007, 1, 1), date(2011, 1, 1)),
    ("Dilma Rousseff", date(2011, 1, 1), date(2015, 1, 1)),
    ("Dilma Rousseff", date(2015, 1, 1), date(2016, 8, 31)),
    ("Michel Temer", date(2016, 8, 31), date(2019, 1, 1)),
    ("Jair Bolsonaro", date(2019, 1, 1), date(2023, 1, 1)),
    ("Luiz Inácio Lula da Silva", date(2023, 1, 1), None),
]


def seed() -> None:
    with SessionLocal() as db:
        brasil = get_or_create_brasil(db)

        existing = {
            (row.holder_name, row.start_date)
            for row in db.execute(
                select(GovernmentPeriod).where(
                    GovernmentPeriod.location_id == brasil.id,
                    GovernmentPeriod.level == GovernmentLevel.federal,
                )
            ).scalars()
        }

        for holder_name, start_date, end_date in FEDERAL_PERIODS:
            if (holder_name, start_date) in existing:
                continue
            db.add(
                GovernmentPeriod(
                    location_id=brasil.id,
                    level=GovernmentLevel.federal,
                    holder_name=holder_name,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        db.commit()
    print("Períodos de governo federal sincronizados.")


if __name__ == "__main__":
    seed()
