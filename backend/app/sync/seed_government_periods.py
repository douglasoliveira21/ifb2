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
from app.sync.upsert import get_or_create_brasil, get_state

# Governadores estaduais (1995–vigente), um período por titular efetivo —
# trocas no meio do mandato (cassação, renúncia, morte, vice assume) viram
# dois registros separados, com a data exata da troca, mesma convenção já
# usada no nível federal (ver FEDERAL_PERIODS: Dilma Rousseff → Michel
# Temer em 2016-08-31).
#
# Fonte: listas consolidadas da Wikipédia em português, uma por mandato
# (1995–1999 até 2023–2027) — é uma fonte secundária, não um órgão oficial,
# diferente de todas as outras datas usadas no IFB. Mantido aqui só como
# registro histórico público de baixo risco de disputa factual (quem
# ocupou o cargo e quando), não como estatística — mesma regra do nível
# federal: nunca cor de partido, nunca tratar o titular como protagonista.
STATE_GOVERNORS: dict[str, list[tuple[str, date, date | None]]] = {}


def seed_state_governors() -> None:
    if not STATE_GOVERNORS:
        print("Governadores estaduais: nenhum dado carregado ainda (STATE_GOVERNORS vazio) — pulando.")
        return

    with SessionLocal() as db:
        added = 0
        for uf, periods in STATE_GOVERNORS.items():
            state = get_state(db, uf)
            if state is None:
                print(f"Governadores: UF '{uf}' não encontrada — rode seed_states antes.")
                continue

            existing = {
                (row.holder_name, row.start_date)
                for row in db.execute(
                    select(GovernmentPeriod).where(
                        GovernmentPeriod.location_id == state.id,
                        GovernmentPeriod.level == GovernmentLevel.state,
                    )
                ).scalars()
            }

            for holder_name, start_date, end_date in periods:
                if (holder_name, start_date) in existing:
                    continue
                db.add(
                    GovernmentPeriod(
                        location_id=state.id,
                        level=GovernmentLevel.state,
                        holder_name=holder_name,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
                added += 1

        db.commit()
    print(f"Governadores estaduais sincronizados ({added} período(s) novo(s)).")


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
    seed_state_governors()


if __name__ == "__main__":
    seed()
