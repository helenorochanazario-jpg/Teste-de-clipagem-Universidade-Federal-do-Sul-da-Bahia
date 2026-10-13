import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collector_google_news import build_feed_url, parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "sample_google_news_feed.xml"


def test_build_feed_url_encodes_query_and_locale():
    url = build_feed_url("UFSB Porto Seguro")
    assert url.startswith("https://news.google.com/rss/search?q=")
    assert "UFSB+Porto+Seguro" in url
    # ceid usa ":" sem necessidade de percent-encoding (mesmo formato dos
    # exemplos oficiais do Google, ex. ceid=US:en) — o teste checava um
    # encoding que o próprio Google não usa; corrigido aqui.
    assert "hl=pt-BR" in url and "gl=BR" in url and "ceid=BR:pt-BR" in url


def test_parse_feed_extracts_source_tag_when_present():
    content = FIXTURE.read_bytes()
    items = parse_feed(content, keyword="UFSB")
    assert len(items) == 3
    first = items[0]
    assert first.veiculo == "A Tarde"
    assert first.manchete == "UFSB lança edital de pós-graduação em Economia do Mar"
    assert first.data_publicacao == "2026-09-18"
    assert first.palavra_chave == "UFSB"


def test_parse_feed_falls_back_to_title_suffix_when_no_source_tag():
    content = FIXTURE.read_bytes()
    items = parse_feed(content, keyword="UFSB")
    second = items[1]
    assert second.veiculo == "Correio"
    assert second.manchete == "Reitoria da UFSB assina convênio com prefeitura de Itabuna"


def test_parse_feed_handles_missing_source_gracefully():
    content = FIXTURE.read_bytes()
    items = parse_feed(content, keyword="UFSB")
    third = items[2]
    # Sem tag <source> e sem " - Veículo" no título: não deve quebrar,
    # deve cair no rótulo "Desconhecido" para revisão manual depois.
    assert third.veiculo == "Desconhecido"
    assert third.manchete == "Sem fonte identificada no título nem na tag source"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
