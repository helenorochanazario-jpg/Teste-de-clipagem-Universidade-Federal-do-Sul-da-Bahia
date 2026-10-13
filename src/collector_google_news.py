"""
Coleta de notícias via Google News RSS.

Por que esse é o ponto de partida (e não uma API paga tipo NewsAPI/GNews):
  - Gratuito, sem chave, sem limite de requisições documentado (mas respeite
    um intervalo entre chamadas — ver `REQUEST_DELAY_SECONDS`).
  - Cobre o "vai daqui pra frente" muito bem: cada nova consulta/keyword
    normalmente traz o que foi publicado nos últimos dias/semanas.

Limitações conhecidas (documentadas, não é suposição):
  - Cada consulta devolve no máximo ~100 itens — buscas muito genéricas
    "escondem" itens mais antigos dentro desse teto.
  - O <link> do item é um redirecionamento (news.google.com/rss/articles/...),
    não a URL final do veículo. Para o registro do clipping, resolvemos o
    redirecionamento (`resolve_final_url`) antes de salvar/gerar o PDF.
  - Não há garantia de profundidade histórica: na prática, é um feed "dos
    últimos tempos", não um arquivo pesquisável desde 2013. Para backfill,
    ver `collector_gdelt.py` e `collector_wayback.py`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import quote_plus

import feedparser
import requests

from dedup import NewsItem

REQUEST_DELAY_SECONDS = 1.5
USER_AGENT = "Mozilla/5.0 (compatible; UFSB-ACS-Clipping/1.0; +https://ufsb.edu.br)"


def build_feed_url(keyword: str, hl: str = "pt-BR", gl: str = "BR",
                    ceid: str = "BR:pt-BR", when: str | None = None) -> str:
    """
    Monta a URL do feed de busca do Google News.
    `when` aceita operadores do Google News, ex.: "7d", "1y" (opcional).
    """
    query = keyword if not when else f"{keyword} when:{when}"
    return (
        f"https://news.google.com/rss/search?q={quote_plus(query)}"
        f"&hl={hl}&gl={gl}&ceid={ceid}"
    )


def parse_feed(feed_content: str | bytes, keyword: str) -> list[NewsItem]:
    """
    Faz o parse de um conteúdo RSS já obtido (string/bytes) em NewsItem.
    Separado de `fetch_keyword` de propósito, para poder ser testado sem
    rede (ver tests/test_collector_google_news.py).
    """
    parsed = feedparser.parse(feed_content)
    items: list[NewsItem] = []
    for entry in parsed.entries:
        veiculo = ""
        if "source" in entry and getattr(entry.source, "title", None):
            veiculo = entry.source.title
        elif " - " in entry.title:
            # fallback: Google News costuma anexar " - Veículo" ao título
            veiculo = entry.title.rsplit(" - ", 1)[-1]

        manchete = entry.title
        if veiculo and manchete.endswith(f" - {veiculo}"):
            manchete = manchete[: -(len(veiculo) + 3)]

        data_publicacao = ""
        if getattr(entry, "published_parsed", None):
            data_publicacao = time.strftime("%Y-%m-%d", entry.published_parsed)

        items.append(NewsItem(
            veiculo=veiculo or "Desconhecido",
            manchete=manchete.strip(),
            link=entry.link,
            data_publicacao=data_publicacao,
            palavra_chave=keyword,
        ))
    return items


def resolve_final_url(google_news_link: str, timeout: int = 15) -> str:
    """
    Resolve o link de redirecionamento do Google News para a URL final do
    veículo, seguindo redirects HTTP. Necessário porque o PDF/registro deve
    apontar para a página real da notícia, não para news.google.com.
    """
    resp = requests.get(
        google_news_link, timeout=timeout, allow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )
    return resp.url


def fetch_keyword(keyword: str, hl: str = "pt-BR", gl: str = "BR",
                   ceid: str = "BR:pt-BR", when: str | None = None,
                   timeout: int = 15) -> list[NewsItem]:
    """Busca ao vivo (requer rede) — usada em produção pelo pipeline."""
    url = build_feed_url(keyword, hl, gl, ceid, when)
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY_SECONDS)  # gentileza com o servidor do Google
    return parse_feed(resp.content, keyword)
