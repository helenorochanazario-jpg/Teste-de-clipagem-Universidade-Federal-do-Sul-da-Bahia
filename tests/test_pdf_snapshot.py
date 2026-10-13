import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pdf_snapshot import slugify_filename, snapshot_url_to_pdf


def test_slugify_filename_basic():
    name = slugify_filename("A Tarde", "2026-09-18", "UFSB lança edital de pós-graduação!")
    assert name == "2026-09-18_a-tarde-ufsb-lanca-edital-de-pos-graduacao.pdf"


def test_slugify_filename_truncates_long_headlines():
    manchete_longa = "Notícia " * 30
    data = "2026-01-01"
    name = slugify_filename("Jornal X", data, manchete_longa)
    # limite real: len(data) + '_' + até 120 chars do corpo + '.pdf'
    assert len(name) <= len(data) + 1 + 120 + len(".pdf")
    assert name.endswith(".pdf")


def test_slugify_filename_defaults_date_when_missing():
    name = slugify_filename("Jornal X", "", "Nota sem data")
    assert name.startswith("20")  # cai no date.today(), formato ISO


class _FakePage:
    """Simula a interface mínima de uma Playwright page, sem abrir browser."""

    def __init__(self):
        self.navigated_to = None
        self.waited_ms = None

    def goto(self, url, wait_until=None, timeout=None):
        self.navigated_to = url

    def wait_for_timeout(self, ms):
        self.waited_ms = ms

    def pdf(self, **kwargs):
        assert kwargs["format"] == "A4"
        return b"%PDF-1.4 fake bytes"


def test_snapshot_url_to_pdf_calls_page_in_order():
    page = _FakePage()
    result = snapshot_url_to_pdf(page, "https://exemplo.com.br/noticia/1")
    assert page.navigated_to == "https://exemplo.com.br/noticia/1"
    assert page.waited_ms == 2500
    assert result.startswith(b"%PDF")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
