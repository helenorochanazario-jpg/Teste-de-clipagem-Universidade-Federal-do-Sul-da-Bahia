import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collector_bahianoticias import parse_tag_page, tag_url

FIXTURE = Path(__file__).parent / "fixtures" / "sample_bahianoticias_tag_page.html"


def test_tag_url_builds_correct_path():
    assert tag_url("ufsb") == "https://www.bahianoticias.com.br/tags/ufsb"
    assert tag_url("UFSB") == "https://www.bahianoticias.com.br/tags/ufsb"  # normaliza


def test_parse_tag_page_extracts_three_articles_not_the_nav_link():
    html = FIXTURE.read_text(encoding="utf-8")
    items = parse_tag_page(html, tag="ufsb")
    assert len(items) == 3
    manchetes = [i.manchete for i in items]
    assert "Municípios" not in manchetes  # link de menu não é matéria


def test_parse_tag_page_dedupes_image_and_title_links_to_same_article():
    html = FIXTURE.read_text(encoding="utf-8")
    items = parse_tag_page(html, tag="ufsb")
    links = [i.link for i in items]
    assert len(links) == len(set(links))  # cada URL aparece uma única vez


def test_parse_tag_page_extracts_date_in_iso_format():
    html = FIXTURE.read_text(encoding="utf-8")
    items = parse_tag_page(html, tag="ufsb")
    primeiro = next(i for i in items if "peixe-leão" in i.manchete)
    assert primeiro.data_publicacao == "2026-09-17"


def test_parse_tag_page_handles_article_without_leading_section() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    items = parse_tag_page(html, tag="ufsb")
    sem_secao = next(i for i in items if "1.243 vagas" in i.manchete)
    assert sem_secao.link == "https://www.bahianoticias.com.br/noticia/48886-ufsb-abre-inscricoes-de-processo-seletivo-para-1243-vagas"


def test_parse_tag_page_sets_veiculo_and_tag_fields():
    html = FIXTURE.read_text(encoding="utf-8")
    items = parse_tag_page(html, tag="ufsb")
    assert all(i.veiculo == "Bahia Notícias" for i in items)
    assert all(i.palavra_chave == "ufsb" for i in items)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
