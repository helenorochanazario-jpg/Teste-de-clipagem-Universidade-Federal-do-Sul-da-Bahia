"""
Coleta retroativa via GDELT DOC 2.0 API (https://api.gdeltproject.org).

O QUE É: projeto acadêmico/aberto que indexa notícias de mais de 100 idiomas,
sem necessidade de chave de API. É a única fonte gratuita com alguma
profundidade histórica pesquisável por palavra-chave.

LIMITAÇÃO IMPORTANTE (baseada na documentação do próprio projeto, não é
suposição): a base textual pesquisável (GKG/DOC 2.0) começa efetivamente
em 2015, e a cobertura de veículos regionais brasileiros menores dentro
desse período é inconsistente — o GDELT prioriza fontes de grande alcance
e conteúdo em inglês. Ou seja: isso ajuda a preencher parte de 2015 em
diante, mas **não cobre 2013–2015 de forma confiável**, e mesmo depois de
2015 é bom complemento, não substituto de uma busca direta nos veículos
regionais (ver `collector_site_scraper.py`) e no Wayback Machine
(`collector_wayback.py`) para o período mais antigo.

Limite de requisição documentado: 1 requisição a cada 5 segundos.
"""
from __future__ import annotations

import time

import requests

from dedup import NewsItem

GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
MIN_SECONDS_BETWEEN_REQUESTS = 5
RELIABLE_FROM_DATE = "2015-01-01"  # ver aviso acima


def _to_gdelt_datetime(date_str: str) -> str:
    """'2026-09-20' -> '20260920000000' (formato exigido pela API)."""
    return date_str.replace("-", "") + "000000"


def parse_response(payload: dict, keyword: str) -> list[NewsItem]:
    """Separado de `fetch_backfill` para poder ser testado sem rede."""
    items: list[NewsItem] = []
    for art in payload.get("articles", []):
        data_publicacao = ""
        seen = art.get("seendate", "")  # formato: YYYYMMDDHHMMSS
        if len(seen) >= 8:
            data_publicacao = f"{seen[0:4]}-{seen[4:6]}-{seen[6:8]}"
        items.append(NewsItem(
            veiculo=art.get("domain", "Desconhecido"),
            manchete=art.get("title", "").strip(),
            link=art.get("url", ""),
            data_publicacao=data_publicacao,
            palavra_chave=keyword,
        ))
    return items


def fetch_backfill(keyword: str, start_date: str, end_date: str,
                    max_records: int = 250, timeout: int = 30) -> list[NewsItem]:
    """
    Busca ao vivo (requer rede) no intervalo [start_date, end_date].
    Emite aviso se start_date for anterior a RELIABLE_FROM_DATE, pois o
    resultado nesse trecho tende a ser esparso — não é erro do código, é
    limite real da cobertura da fonte.
    """
    if start_date < RELIABLE_FROM_DATE:
        print(
            f"[aviso] start_date={start_date} é anterior a {RELIABLE_FROM_DATE}: "
            "a cobertura do GDELT nesse período é esparsa para imprensa regional "
            "brasileira. Complemente com collector_wayback.py e busca direta nos "
            "sites dos veículos."
        )

    params = {
        "query": keyword,
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(max_records),
        "startdatetime": _to_gdelt_datetime(start_date),
        "enddatetime": _to_gdelt_datetime(end_date),
        "sourcelang": "por",
    }
    resp = requests.get(GDELT_DOC_ENDPOINT, params=params, timeout=timeout)
    resp.raise_for_status()
    time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
    return parse_response(resp.json(), keyword)
