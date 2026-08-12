"""Varredura automática de Frases Verificadas.

Lê feeds RSS de notícias, manda cada matéria nova para o modelo DeepSeek
(deepseek-v4-flash, API compatível com OpenAI) junto com os indicadores
reais do IFB, e — só quando o modelo identifica uma citação com número
checável atribuída a uma autoridade — grava um
`VerifiedClaim` com `status=DRAFT, origin=AI_SCAN`. Nunca publica
sozinho: todo rascunho fica pendente de aprovação humana em
/admin/frases-verificadas antes de aparecer em /frases-verificadas
(ver app/api/verified_claims.py, que só lista status=PUBLISHED).

Idempotente entre execuções: cada matéria processada (tenha gerado
rascunho ou não) é registrada em `scanned_articles` por URL, então rodar
de novo não reprocessa o que já foi visto — importante porque este job
roda a cada poucas horas (ver docker-compose.yml/README) e os feeds
mantêm os mesmos itens por dias.

Uso: python -m app.sync.claim_scan
"""
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.indicator_definition import IndicatorDefinition
from app.models.indicator_summary import indicator_summary
from app.models.location import Location, LocationType
from app.models.scanned_article import ScannedArticle
from app.models.verified_claim import (
    ClaimOrigin,
    ClaimStatus,
    ClaimVerdict,
    VerifiedClaim,
)

RSS_FEEDS = [
    ("G1 Política", "https://g1.globo.com/rss/g1/politica/"),
    ("G1 Economia", "https://g1.globo.com/rss/g1/economia/"),
]

# Limite de matérias novas processadas por execução — controla custo de
# API e evita que um feed com muito volume monopolize o job de 3 em 3h.
MAX_ARTICLES_PER_RUN = 25

REQUEST_HEADERS = {
    "Accept": "application/rss+xml, application/xml",
    "User-Agent": "IFB-Sync/1.0 (+https://github.com/douglasoliveira21/ifb2)",
}

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"

VERDICT_VALUES = [v.value for v in ClaimVerdict]

SCAN_TOOL = {
    "type": "function",
    "function": {
        "name": "record_scan_result",
        "description": (
            "Registra o resultado da análise de uma matéria de notícia em busca de uma citação "
            "pública, com número checável, atribuída por nome a uma autoridade (presidente, "
            "ministro, governador, prefeito, senador, deputado), sobre um tema coberto por um "
            "dos indicadores fornecidos."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "has_claim": {
                    "type": "boolean",
                    "description": (
                        "true somente se o texto contém uma citação direta ou paráfrase clara "
                        "com um número específico, atribuída por nome a uma autoridade, sobre um "
                        "tema que corresponda a um dos indicadores fornecidos. false em qualquer "
                        "outro caso — inclusive se a matéria é sobre política/economia mas não "
                        "cita nenhum número, ou cita número sem atribuir a uma pessoa nomeada."
                    ),
                },
                "speaker_name": {"type": ["string", "null"], "description": "Nome da autoridade citada."},
                "speaker_role": {"type": ["string", "null"], "description": "Cargo da autoridade, ex: Presidente da República."},
                "quote": {
                    "type": ["string", "null"],
                    "description": "A citação ou paráfrase exata do texto fornecido, em português.",
                },
                "indicator_slug": {
                    "type": ["string", "null"],
                    "description": "O slug do indicador da lista fornecida que corresponde ao tema da citação.",
                },
                "verdict": {
                    "type": ["string", "null"],
                    "enum": VERDICT_VALUES + [None],
                    "description": (
                        "Comparando o número citado com o valor real do indicador fornecido no "
                        "contexto: CONFIRMADO (bate), PARCIALMENTE_CONFIRMADO (direção certa, "
                        "número impreciso), DISTORCIDO (número real existe mas foi descrito de "
                        "forma enganosa), FALSO (contradiz o dado real), INCONCLUSIVO (não dá "
                        "pra checar com o dado disponível)."
                    ),
                },
                "explanation": {
                    "type": ["string", "null"],
                    "description": (
                        "1-2 frases em português citando o valor real do indicador (com data) e "
                        "explicando o veredito. Nunca opine sobre a pessoa, só compare o número."
                    ),
                },
            },
            "required": ["has_claim"],
        },
    },
}


@dataclass(frozen=True)
class FeedItem:
    title: str
    description: str
    link: str
    pub_date: date | None
    feed_name: str


def _parse_pub_date(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def fetch_feed_items(feed_name: str, url: str) -> list[FeedItem]:
    with httpx.Client(headers=REQUEST_HEADERS, timeout=20.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or item.findtext("{*}subtitle") or "").strip()
        pub_date = _parse_pub_date(item.findtext("pubDate"))
        if title and link:
            items.append(
                FeedItem(title=title, description=description, link=link, pub_date=pub_date, feed_name=feed_name)
            )
    return items


def _candidate_indicators(db: Session) -> list[dict]:
    """Indicadores nível Brasil com valor mais recente — contexto que o
    modelo usa pra casar a citação com um indicador real e comparar o
    número contra o dado oficial, em vez de confiar na memória dele."""
    country = db.execute(select(Location).where(Location.type == LocationType.country)).scalar_one_or_none()
    if country is None:
        return []
    rows = db.execute(
        select(indicator_summary).where(indicator_summary.c.location_id == country.id)
    ).mappings().all()
    return [
        {
            "slug": row["slug"],
            "name": row["name"],
            "category": row["category"],
            "unit": row["unit"],
            "last_value": float(row["last_value"]) if row["last_value"] is not None else None,
            "last_date": row["last_date"].isoformat() if row["last_date"] else None,
        }
        for row in rows
        if row["last_value"] is not None
    ]


def analyze_article(client: httpx.Client, item: FeedItem, indicators: list[dict]) -> dict | None:
    text = f"Título: {item.title}\n\nResumo: {item.description}"
    indicators_json = json.dumps(indicators, ensure_ascii=False)

    response = client.post(
        DEEPSEEK_API_URL,
        json={
            "model": DEEPSEEK_MODEL,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de checagem factual do Instituto Fiscaliza Brasil "
                        "(IFB), um projeto não-partidário. Sua única tarefa é identificar, em um "
                        "trecho de notícia, se alguma autoridade citou um número específico sobre "
                        "um tema coberto pelos indicadores fornecidos — e, se sim, comparar esse "
                        "número com o valor real fornecido no contexto (nunca use conhecimento "
                        "próprio sobre os números, use apenas o que está na lista de indicadores). "
                        "Seja rigoroso: na dúvida, prefira has_claim=false a inventar uma citação "
                        "que não está claramente no texto."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Indicadores disponíveis (JSON):\n{indicators_json}\n\n"
                        f"Trecho da notícia:\n{text}"
                    ),
                },
            ],
            "tools": [SCAN_TOOL],
            "tool_choice": {"type": "function", "function": {"name": "record_scan_result"}},
        },
        headers={
            "Authorization": f"Bearer {get_settings().deepseek_api_key or ''}",
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    body = response.json()
    choices = body.get("choices") or []
    if not choices:
        return None
    tool_calls = choices[0].get("message", {}).get("tool_calls") or []
    if not tool_calls:
        return None
    arguments_raw = tool_calls[0].get("function", {}).get("arguments")
    if not arguments_raw:
        return None
    return json.loads(arguments_raw)


def main() -> None:
    settings = get_settings()
    if not settings.deepseek_api_key:
        print("DEEPSEEK_API_KEY não configurada — varredura de Frases Verificadas pulada.")
        sys.exit(0)

    db = SessionLocal()
    try:
        indicators = _candidate_indicators(db)
        indicator_by_slug = {i["slug"]: i for i in indicators}
        seen_urls = {row[0] for row in db.execute(select(ScannedArticle.url)).all()}

        new_items: list[FeedItem] = []
        for feed_name, feed_url in RSS_FEEDS:
            try:
                items = fetch_feed_items(feed_name, feed_url)
            except Exception as exc:  # noqa: BLE001 — isola falha de um feed, não derruba os demais
                print(f"[{feed_name}] falha ao buscar feed: {exc}")
                continue
            for item in items:
                if item.link not in seen_urls:
                    new_items.append(item)
            print(f"[{feed_name}] {len(items)} matérias no feed, {sum(1 for i in items if i.link not in seen_urls)} novas.")

        new_items = new_items[:MAX_ARTICLES_PER_RUN]
        drafts_created = 0

        with httpx.Client(timeout=60.0) as deepseek_client:
            for item in new_items:
                claim_extracted = False
                try:
                    result = analyze_article(deepseek_client, item, indicators)
                    if result and result.get("has_claim") and result.get("indicator_slug") in indicator_by_slug:
                        verdict_raw = result.get("verdict")
                        if verdict_raw in VERDICT_VALUES and result.get("quote") and result.get("speaker_name"):
                            indicator = db.execute(
                                select(IndicatorDefinition).where(
                                    IndicatorDefinition.slug == result["indicator_slug"]
                                )
                            ).scalar_one_or_none()
                            if indicator is not None:
                                db.add(
                                    VerifiedClaim(
                                        quote=result["quote"].strip(),
                                        speaker_name=result["speaker_name"].strip(),
                                        speaker_role=(result.get("speaker_role") or "").strip() or None,
                                        claim_date=item.pub_date,
                                        source_url=item.link,
                                        indicator_id=indicator.id,
                                        verdict=ClaimVerdict(verdict_raw),
                                        explanation=(result.get("explanation") or "").strip()
                                        or "Sem explicação gerada.",
                                        status=ClaimStatus.DRAFT,
                                        origin=ClaimOrigin.AI_SCAN,
                                    )
                                )
                                claim_extracted = True
                                drafts_created += 1
                except Exception as exc:  # noqa: BLE001 — isola falha de uma matéria, não derruba as demais
                    print(f"Falha ao analisar '{item.title[:60]}': {exc}")

                db.add(ScannedArticle(url=item.link, source_feed=item.feed_name, claim_extracted=claim_extracted))
                db.commit()

        print(f"Varredura concluída: {len(new_items)} matérias novas analisadas, {drafts_created} rascunho(s) criado(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
