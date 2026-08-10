"""Seed idempotente dos municípios brasileiros (`locations`, type=municipality).

Diferente dos 27 estados (lista fixa hardcoded em `seed_states.py`), os
~5.570 municípios vêm da API pública de Localidades do IBGE — não faz
sentido manter uma lista dessas manualmente no código. Código IBGE (7
dígitos) e nome são registro público estável, mesmo tratamento dos
demais seeds (sem SyncRun, não é estatística sujeita a revisão).

Uso: python -m app.sync.seed_municipios
"""
import httpx
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.location import Location, LocationType
from app.sync.ibge_client import MUNICIPIOS_URL, REQUEST_HEADERS


def uf_from_codigo_ibge(codigo_ibge: str) -> str | None:
    """Os 2 primeiros dígitos de um código de município IBGE são sempre o
    código da UF — convenção usada para derivar o estado de um município
    sem precisar de uma coluna extra no schema (ex: 3550308 → 35 → SP)."""
    from app.sync.ibge_client import IBGE_UF_CODES

    return IBGE_UF_CODES.get(codigo_ibge[:2])


def seed(*, timeout: float = 60.0) -> None:
    response = httpx.get(MUNICIPIOS_URL, headers=REQUEST_HEADERS, timeout=timeout)
    response.raise_for_status()
    municipios = response.json()

    with SessionLocal() as db:
        existing = {
            row.code
            for row in db.execute(
                select(Location).where(Location.type == LocationType.municipality)
            ).scalars()
        }

        added = 0
        for item in municipios:
            codigo = str(item["id"])
            if codigo in existing:
                continue
            db.add(Location(type=LocationType.municipality, code=codigo, name=item["nome"]))
            added += 1

        db.commit()
    print(f"Municípios sincronizados ({added} novo(s) de {len(municipios)} no total).")


if __name__ == "__main__":
    seed()
