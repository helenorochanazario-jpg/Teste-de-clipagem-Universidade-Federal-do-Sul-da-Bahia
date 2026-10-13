"""
Deduplicação de notícias coletadas.

Duas notícias são consideradas a MESMA OCORRÊNCIA (e portanto duplicata) se:
  1. A URL normalizada (sem parâmetros de rastreamento, sem barra final,
     sem protocolo/www) já foi registrada; OU
  2. O título normalizado (minúsculo, sem acento/pontuação, espaços
     colapsados) do MESMO VEÍCULO já foi registrado — cobre o caso comum de
     a mesma notícia ser recoletada com um link levemente diferente
     (parâmetro de campanha novo, redirecionamento do Google News etc.).

Notícias iguais publicadas por VEÍCULOS DIFERENTES não são deduplicadas —
isso é reprodução/repercussão de pauta, um dado relevante para o clipping,
não uma duplicata.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# Parâmetros de URL que não mudam o conteúdo da página e devem ser
# descartados na normalização (rastreamento de campanha, redes sociais etc.)
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref", "amp",
}


def normalize_url(url: str) -> str:
    """Normaliza uma URL para fins de deduplicação (não para navegação)."""
    parsed = urlparse(url.strip())
    scheme = "https"  # ignora http vs https
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    query_pairs = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS
    ]
    query_pairs.sort()
    query = urlencode(query_pairs)
    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_title(title: str) -> str:
    """Minúsculo, sem acentos, sem pontuação, espaços colapsados."""
    title = title.strip().lower()
    title = unicodedata.normalize("NFKD", title)
    title = "".join(ch for ch in title if not unicodedata.combining(ch))
    title = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in title)
    return " ".join(title.split())


@dataclass(frozen=True)
class NewsItem:
    veiculo: str
    manchete: str
    link: str
    data_publicacao: str  # ISO 8601, ex. "2026-09-20"
    palavra_chave: str = ""

    @property
    def url_key(self) -> str:
        return normalize_url(self.link)

    @property
    def title_key(self) -> tuple[str, str]:
        return (self.veiculo.strip().lower(), normalize_title(self.manchete))


class Deduplicator:
    """
    Mantém em memória os identificadores já vistos. Para persistir entre
    execuções do GitHub Actions, carregue `seen_urls`/`seen_titles` a partir
    de uma coluna da própria planilha do Sheets (ou de um arquivo de estado
    versionado no repositório) antes de instanciar, e salve de volta ao
    final — ver `pipeline.py::load_dedup_state` / `save_dedup_state`.
    """

    def __init__(self, seen_urls: set[str] | None = None,
                 seen_titles: set[tuple[str, str]] | None = None):
        self.seen_urls: set[str] = set(seen_urls or set())
        self.seen_titles: set[tuple[str, str]] = set(seen_titles or set())

    def is_duplicate(self, item: NewsItem) -> bool:
        return item.url_key in self.seen_urls or item.title_key in self.seen_titles

    def register(self, item: NewsItem) -> None:
        self.seen_urls.add(item.url_key)
        self.seen_titles.add(item.title_key)

    def filter_new(self, items: list[NewsItem]) -> list[NewsItem]:
        """Retorna apenas os itens inéditos, na ordem recebida, registrando-os."""
        novos = []
        for item in items:
            if not self.is_duplicate(item):
                self.register(item)
                novos.append(item)
        return novos
