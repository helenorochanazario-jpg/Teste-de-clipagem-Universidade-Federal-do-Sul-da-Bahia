"""
Coletor genérico para a busca interna de um veículo específico.

Por que existe, além do Google News: veículos regionais pequenos (jornais
locais de Porto Seguro, Itabuna, Ilhéus, Teixeira de Freitas) muitas vezes
não são bem indexados pelo Google News. Buscar direto no site do próprio
veículo captura o que passaria batido.

Isso é necessariamente ESPECÍFICO POR SITE: cada portal tem seu HTML. Este
módulo não tenta "adivinhar" a estrutura — ele recebe os seletores CSS via
`config.yaml` (bloco `outlets`) e aplica genericamente. Para ativar um
veículo, você precisa:
  1. Abrir a página de resultado de busca do site;
  2. Inspecionar o HTML (botão direito > Inspecionar) e identificar o
     seletor do container de cada resultado, do título e do link;
  3. Preencher em config.yaml e marcar `enabled: true`.

Isso é inerentemente frágil: sites redesenham e quebram o seletor. Rode os
testes de fumaça (`pipeline.py --smoke-test`) periodicamente para detectar
isso cedo.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from dedup import NewsItem

USER_AGENT = "Mozilla/5.0 (compatible; UFSB-ACS-Clipping/1.0; +https://ufsb.edu.br)"


def parse_search_page(html: str, outlet_name: str, keyword: str,
                       selectors: dict) -> list[NewsItem]:
    """Separado de `fetch` para ser testável sem rede (ver testes)."""
    soup = BeautifulSoup(html, "html.parser")
    items: list[NewsItem] = []
    for result in soup.select(selectors["result_item"]):
        title_el = result.select_one(selectors["title"])
        link_el = result.select_one(selectors.get("link", selectors["title"]))
        if not title_el or not link_el or not link_el.get("href"):
            continue  # item malformado — pula em vez de quebrar o lote inteiro

        manchete = title_el.get_text(strip=True)
        link = link_el["href"]

        data_publicacao = ""
        date_selector = selectors.get("date")
        if date_selector:
            date_el = result.select_one(date_selector)
            if date_el:
                # Datas de sites variam muito de formato; a normalização
                # final (para ISO 8601) deve ser feita por um parser de
                # datas mais robusto (ex. dateutil) na camada do pipeline,
                # que conhece o formato específico daquele veículo.
                data_publicacao = date_el.get_text(strip=True)

        items.append(NewsItem(
            veiculo=outlet_name,
            manchete=manchete,
            link=link,
            data_publicacao=data_publicacao,
            palavra_chave=keyword,
        ))
    return items


def fetch(outlet_name: str, search_url_template: str, keyword: str,
          selectors: dict, timeout: int = 20) -> list[NewsItem]:
    """Busca ao vivo (requer rede) — usada em produção pelo pipeline."""
    url = search_url_template.format(query=quote_plus(keyword))
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return parse_search_page(resp.text, outlet_name, keyword, selectors)
