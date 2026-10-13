import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sheets_writer import (
    HEADER,
    ClippingRow,
    append_clipping_rows,
    existing_links_from_sheet_values,
    rows_to_append,
)


def _sample_row(**overrides):
    defaults = dict(
        data_publicacao="2026-09-18",
        veiculo="A Tarde",
        palavra_chave="UFSB",
        categoria="Institucional",
        manchete="UFSB lança edital",
        link="https://atarde.com.br/n/1",
        link_pdf_drive="https://drive.google.com/file/d/xyz/view",
        sentimento="neutro",
        confianca_sentimento=0.82,
    )
    defaults.update(overrides)
    return ClippingRow(**defaults)


def test_clipping_row_fills_data_coleta_automatically():
    row = _sample_row()
    assert row.data_coleta  # não deve ficar vazio
    assert len(row.data_coleta) == 10  # formato ISO 'YYYY-MM-DD'


def test_rows_to_append_matches_header_order():
    row = _sample_row()
    payload = rows_to_append([row])
    assert len(payload[0]) == len(HEADER)
    assert payload[0][HEADER.index("manchete")] == "UFSB lança edital"
    assert payload[0][HEADER.index("sentimento")] == "neutro"


def test_existing_links_from_sheet_values_extracts_link_column():
    all_values = [HEADER, _sample_row().to_row()]
    links = existing_links_from_sheet_values(all_values)
    assert links == {"https://atarde.com.br/n/1"}


def test_existing_links_returns_empty_set_when_header_mismatch():
    # Planilha vazia ou com cabeçalho diferente do esperado: não deve
    # quebrar, deve tratar como "nenhum link conhecido ainda"
    assert existing_links_from_sheet_values([]) == set()
    assert existing_links_from_sheet_values([["outra", "coisa"]]) == set()


class _FakeWorksheet:
    def __init__(self):
        self.appended = None

    def append_rows(self, rows, value_input_option=None):
        self.appended = rows


def test_append_clipping_rows_calls_worksheet_with_payload():
    ws = _FakeWorksheet()
    append_clipping_rows(ws, [_sample_row()])
    assert ws.appended is not None
    assert ws.appended[0][HEADER.index("veiculo")] == "A Tarde"


def test_append_clipping_rows_noop_on_empty_list():
    ws = _FakeWorksheet()
    append_clipping_rows(ws, [])
    assert ws.appended is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
