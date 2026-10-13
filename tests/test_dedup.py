import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dedup import Deduplicator, NewsItem, normalize_title, normalize_url


def test_normalize_url_strips_tracking_params_and_www():
    a = normalize_url("https://www.jornalx.com.br/noticia/123?utm_source=whatsapp&utm_medium=social")
    b = normalize_url("http://jornalx.com.br/noticia/123/")
    assert a == b


def test_normalize_url_keeps_meaningful_query_params():
    a = normalize_url("https://jornalx.com.br/busca?pagina=2")
    b = normalize_url("https://jornalx.com.br/busca?pagina=3")
    assert a != b


def test_normalize_title_ignores_case_accent_and_punctuation():
    a = normalize_title("UFSB lança edital de pós-graduação!")
    b = normalize_title("ufsb lanca edital de pos graduacao")
    assert a == b


def test_same_url_different_tracking_param_is_duplicate():
    dedup = Deduplicator()
    item1 = NewsItem("Jornal X", "UFSB inaugura laboratório", "https://jornalx.com.br/n/1?utm_source=fb", "2026-09-01")
    item2 = NewsItem("Jornal X", "UFSB inaugura laboratório", "https://jornalx.com.br/n/1?utm_source=whatsapp", "2026-09-01")
    novos = dedup.filter_new([item1, item2])
    assert len(novos) == 1


def test_same_title_same_outlet_different_link_is_duplicate():
    # Caso típico: link de redirecionamento do Google News muda a cada coleta
    dedup = Deduplicator()
    item1 = NewsItem("Jornal X", "UFSB abre inscrições para vestibular 2027",
                      "https://news.google.com/rss/articles/AAAA", "2026-09-01")
    item2 = NewsItem("Jornal X", "UFSB abre inscrições para vestibular 2027",
                      "https://news.google.com/rss/articles/BBBB", "2026-09-01")
    novos = dedup.filter_new([item1, item2])
    assert len(novos) == 1


def test_same_news_different_outlets_is_not_duplicate():
    # Repercussão da mesma pauta em veículos diferentes deve ser mantida
    dedup = Deduplicator()
    item1 = NewsItem("Jornal X", "UFSB assina convênio com prefeitura", "https://jornalx.com.br/n/1", "2026-09-01")
    item2 = NewsItem("Portal Y", "UFSB assina convênio com prefeitura", "https://portaly.com.br/n/9", "2026-09-01")
    novos = dedup.filter_new([item1, item2])
    assert len(novos) == 2


def test_filter_new_preserves_order_and_is_idempotent_across_calls():
    dedup = Deduplicator()
    item = NewsItem("Jornal X", "Nota única", "https://jornalx.com.br/n/1", "2026-09-01")
    assert len(dedup.filter_new([item])) == 1
    # Rodar de novo (simulando a próxima execução do Action) não duplica
    assert len(dedup.filter_new([item])) == 0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
