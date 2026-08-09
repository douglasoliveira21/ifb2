"""Seed idempotente dos 27 estados brasileiros (`locations`, type=state).

Sigla e nome de cada UF são registro público e estável (não é estatística
sujeita a fonte/metodologia) — por isso, como em `seed_government_periods`,
não passa pelo fluxo de sync com SyncRun.

Uso: python -m app.sync.seed_states
"""
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.location import Location, LocationType

STATES = [
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"), ("ES", "Espírito Santo"),
    ("GO", "Goiás"), ("MA", "Maranhão"), ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"), ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"),
    ("PE", "Pernambuco"), ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"), ("SC", "Santa Catarina"),
    ("SP", "São Paulo"), ("SE", "Sergipe"), ("TO", "Tocantins"),
]


def seed() -> None:
    with SessionLocal() as db:
        existing = {
            row.code
            for row in db.execute(select(Location).where(Location.type == LocationType.state)).scalars()
        }
        for code, name in STATES:
            if code in existing:
                continue
            db.add(Location(type=LocationType.state, code=code, name=name))
        db.commit()
    print("Estados (27 UFs) sincronizados.")


if __name__ == "__main__":
    seed()
