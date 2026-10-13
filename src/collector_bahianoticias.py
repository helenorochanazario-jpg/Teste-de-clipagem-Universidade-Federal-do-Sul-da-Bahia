"""
Coletor dedicado para o Bahia Notícias (bahianoticias.com.br).

BASE REAL, CONFIRMADA POR PESQUISA (não é suposição): o site mantém uma
página de tag por assunto, ex. https://www.bahianoticias.com.br/tags/ufsb,
que lista as matérias marcadas com aquele tema, mais recentes primeiro, com
histórico observado desde pelo menos 2020. Isso é uma base de coleta muito
mais confiável que busca por palavra-chave: é curada pela própria redação,
não depende de match textual, e não temos o problema de teto de ~100
resultados do Google News RSS.

POR QUE ESTE COLETOR NÃO USA SELETORES CSS COMO O GENÉRICO
(collector_site_scraper.py): a inspeção deste site foi feita via busca e
fetch de conteúdo (que retornam o texto/markdown da página, não o HTML
bruto com classes CSS) — não houve acesso a ferramentas de desenvolvedor do
navegador para confirmar nomes exatos de classe. Copiar um nome de classe
"parecido" seria inventar um seletor não verificado, exatamente o tipo de
detalhe técnico que não deve ser inventado.

Em vez disso, este coletor usa dois padrões que FORAM confirmados,
observando o conteúdo real da página:
  1. O padrão de URL de matéria: '/(secao/)?noticia/{id}-{slug}'
  2. O padrão de data ao lado de cada manchete: 'DD/MM/AAAA - HHhMM'

Extrair por padrão de URL + regex de data é, na prática, MAIS robusto a
mudanças de layout do que um seletor CSS copiado às cegas — e é honesto
sobre o que foi de fato verificado.

Se o layout mudar de um jeito que quebre esses dois padrões, o pipeline
deve logar um aviso e continuar sem quebrar as outras fontes (ver
`pipeline.py`), para que a equipe da ACS perceba e ajuste.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from dedup import NewsItem

BASE_URL = "https://www.bahianoticias.com.br"
USER_AGENT = "Mozilla/5.0 (compatible; UFSB-ACS-Clipping/1.0; +https://ufsb.edu.br)"

# Casa tanto '/municipios/noticia/51160-slug' quanto '/noticia/291068-slug'
_ARTICLE_HREF_RE = re.compile(r"^(/[a-z-]+)?/noticia/(\d+)-[a-z0-9-]+/?$", re.IGNORECASE)
_DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2})h(\d{2})")


def tag_url(tag: str) -> str:
    """ex.: tag_url('ufsb') -> 'https://www.bahianoticias.com.br/tags/ufsb'"""
    return f"{BASE_URL}/tags/{tag.strip().lower()}"


def _nearby_date(link_tag) -> str:
    """
    Procura o padrão de data 'DD/MM/AAAA - HHhMM' no texto dos irmãos
    seguintes ao link da manchete (é onde ele aparece na página real,
    logo abaixo do título). Retorna ISO 8601 ou '' se não encontrar.
    """
    node = link_tag
    for _ in range(6):  # não sobe/desce indefinidamente
        node = node.find_next(string=_DATE_RE)
        if node is None:
            return ""
        m = _DATE_RE.search(str(node))
        if m:
            dia, mes, ano = m.group(1).split("/")
            return f"{ano}-{mes}-{dia}"
    return ""


def parse_tag_page(html: str, tag: str) -> list[NewsItem]:
    """Separado de `fetch_tag` para ser testável sem rede."""
    soup = BeautifulSoup(html, "html.parser")
    items: list[NewsItem] = []
    seen_links: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = _ARTICLE_HREF_RE.match(href)
        if not m:
            continue
        full_url = urljoin(BASE_URL, href)
        if full_url in seen_links:
            continue  # o mesmo link pode aparecer 2x (imagem + título)
        manchete = a.get_text(strip=True)
        if not manchete:
            continue  # provavelmente o link da imagem, sem texto; pula
        seen_links.add(full_url)
        items.append(NewsItem(
            veiculo="Bahia Notícias",
            manchete=manchete,
            link=full_url,
            data_publicacao=_nearby_date(a),
            palavra_chave=tag,
        ))
    return items


def fetch_tag(tag: str, timeout: int = 20) -> list[NewsItem]:
    """Busca ao vivo (requer rede) — usada em produção pelo pipeline."""
    resp = requests.get(tag_url(tag), timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return parse_tag_page(resp.text, tag)
