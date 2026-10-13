import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collector_site_scraper import parse_search_page

SAMPLE_HTML = """
<html><body>
  <div class="resultado-busca">
    <h2 class="titulo"><a class="link-materia" href="/noticia/1">UFSB inaugura biblioteca em Porto Seguro</a></h2>
    <time class="data-publicacao">15/09/2026</time>
  </div>
  <div class="resultado-busca">
    <h2 class="titulo"><a class="link-materia" href="/noticia/2">Campus da UFSB recebe visita técnica</a></h2>
    <time class="data-publicacao">14/09/2026</time>
  </div>
  <div class="resultado-busca">
    <!-- item malformado: sem link -->
    <h2 class="titulo">Notícia sem link, deve ser ignorada</h2>
  </div>
</body></html>
"""

SELECTORS = {
    "result_item": "div.resultado-busca",
    "title": "h2.titulo",
    "link": "a.link-materia",
    "date": "time.data-publicacao",
}


def test_parse_search_page_extracts_valid_items():
    items = parse_search_page(SAMPLE_HTML, "Jornal Exemplo", "UFSB", SELECTORS)
    assert len(items) == 2
    assert items[0].manchete == "UFSB inaugura biblioteca em Porto Seguro"
    assert items[0].link == "/noticia/1"
    assert items[0].data_publicacao == "15/09/2026"
    assert items[0].veiculo == "Jornal Exemplo"


def test_parse_search_page_skips_malformed_item_without_crashing():
    items = parse_search_page(SAMPLE_HTML, "Jornal Exemplo", "UFSB", SELECTORS)
    manchetes = [i.manchete for i in items]
    assert "Notícia sem link, deve ser ignorada" not in manchetes


def test_parse_search_page_handles_missing_date_selector():
    selectors_sem_data = {k: v for k, v in SELECTORS.items() if k != "date"}
    items = parse_search_page(SAMPLE_HTML, "Jornal Exemplo", "UFSB", selectors_sem_data)
    assert all(i.data_publicacao == "" for i in items)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
