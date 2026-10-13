import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collector_gdelt import _to_gdelt_datetime, parse_response

SAMPLE_PAYLOAD = {
    "articles": [
        {
            "url": "https://exemplo.com.br/noticia-1",
            "title": "UFSB abre inscrições para mestrado",
            "seendate": "20260915120000",
            "domain": "exemplo.com.br",
        },
        {
            "url": "https://outro.com.br/noticia-2",
            "title": "Sem data de visualização",
            "domain": "outro.com.br",
            # 'seendate' propositalmente ausente para testar robustez
        },
    ]
}


def test_to_gdelt_datetime_format():
    assert _to_gdelt_datetime("2026-09-20") == "20260920000000"


def test_parse_response_extracts_fields():
    items = parse_response(SAMPLE_PAYLOAD, keyword="UFSB")
    assert len(items) == 2
    assert items[0].veiculo == "exemplo.com.br"
    assert items[0].data_publicacao == "2026-09-15"
    assert items[0].palavra_chave == "UFSB"


def test_parse_response_handles_missing_seendate():
    items = parse_response(SAMPLE_PAYLOAD, keyword="UFSB")
    assert items[1].data_publicacao == ""  # não deve quebrar, só fica vazio


def test_parse_response_handles_empty_payload():
    assert parse_response({}, keyword="UFSB") == []


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
