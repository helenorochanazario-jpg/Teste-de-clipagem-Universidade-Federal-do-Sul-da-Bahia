import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from report import _aggregate, generate_html_report

SAMPLE_ROWS = [
    {"data_publicacao": "2026-08-10", "veiculo": "A Tarde", "categoria": "Institucional",
     "manchete": "UFSB assina convênio", "link": "https://a.com/1", "sentimento": "positivo"},
    {"data_publicacao": "2026-08-22", "veiculo": "Correio", "categoria": "Ensino",
     "manchete": "UFSB abre vestibular", "link": "https://a.com/2", "sentimento": "neutro"},
    {"data_publicacao": "2026-09-05", "veiculo": "A Tarde", "categoria": "Institucional",
     "manchete": "Reitoria critica corte de verba", "link": "https://a.com/3", "sentimento": "negativo"},
]


def test_aggregate_counts_by_veiculo():
    agg = _aggregate(SAMPLE_ROWS)
    assert agg["total"] == 3
    assert dict(zip(agg["veiculos_labels"], agg["veiculos_valores"]))["A Tarde"] == 2


def test_aggregate_sentiment_only_includes_present_labels_in_fixed_order():
    agg = _aggregate(SAMPLE_ROWS)
    assert agg["sentimento_labels"] == ["positivo", "neutro", "negativo"]
    assert agg["sentimento_valores"] == [1, 1, 1]


def test_aggregate_groups_by_month():
    agg = _aggregate(SAMPLE_ROWS)
    assert agg["meses_labels"] == ["2026-08", "2026-09"]
    assert agg["meses_valores"] == [2, 1]


def test_aggregate_handles_empty_rows_without_crashing():
    agg = _aggregate([])
    assert agg["total"] == 0
    assert agg["veiculos_labels"] == []
    assert agg["sentimento_labels"] == []


def test_generate_html_report_embeds_data_and_is_well_formed():
    html = generate_html_report(SAMPLE_ROWS, titulo="Teste")
    assert html.startswith("<!DOCTYPE html>")
    assert html.count("<canvas") == 4
    assert "UFSB assina convênio" in html
    assert "Chart.js" in html or "chart.umd.min.js" in html
    assert html.strip().endswith("</html>")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
