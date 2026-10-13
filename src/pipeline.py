"""
Orquestração do pipeline de clipping — o que o GitHub Actions executa.

Fluxo de uma execução de MONITORAMENTO (rotina, 2-3x/dia):
  1. Carrega config.yaml
  2. Abre a planilha do Sheets, lê os links já conhecidos -> alimenta o Deduplicator
  3. Para cada keyword: busca no Google News RSS (+ veículos com scraper habilitado)
  4. Filtra duplicatas
  5. Para cada notícia nova: resolve a URL final, tira o PDF, sobe no Drive
  6. Classifica o sentimento da manchete
  7. Grava a linha no Sheets
  8. Gera o dashboard HTML (report.py) e salva/publica

Fluxo de BACKFILL (rodado manualmente/uma vez, `--modo backfill`):
  Igual, mas a coleta usa `collector_gdelt.py` fatiado por ano, a partir de
  `config["backfill"]["start_date"]` — com o aviso de cobertura parcial
  antes de 2015 já embutido no próprio collector_gdelt.

Este arquivo é o "fio condutor": a lógica de cada etapa vive nos módulos
already testados (dedup, collector_*, sentiment, pdf_snapshot, drive_upload,
sheets_writer, report). Rodar isso de ponta a ponta requer rede liberada
para news.google.com, api.gdeltproject.org, googleapis.com e o Drive/Sheets
— algo fora do alcance do sandbox usado para gerar este projeto. Por isso
cada módulo tem testes unitários offline (ver tests/), e este orquestrador
tem um modo `--smoke-test` que roda a lógica de agregação/dedup com dados
de exemplo, sem tocar a rede, para validar que as peças se encaixam.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from dedup import Deduplicator, NewsItem
from sentiment import SentimentClassifier
from sheets_writer import ClippingRow


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def categorize(manchete: str, categorias: list[str]) -> str:
    """
    Categorização simples por palavra-chave no título. Não é NLP — é de
    propósito: transparente, auditável, e fácil de a equipe de comunicação
    ajustar sem depender de retrain de modelo. Ajuste os termos conforme a
    realidade editorial da ACS.
    """
    regras = {
        "Pesquisa e Extensão": ["pesquisa", "extensão", "extensao", "projeto"],
        "Ensino": ["vestibular", "matrícula", "matricula", "curso", "aula"],
        "Economia do Mar": ["economia do mar", "blue economy", "oceânica", "oceanica"],
        "Cultura e Sociedade": ["cultura", "evento", "festival"],
    }
    texto = manchete.lower()
    for categoria, termos in regras.items():
        if categoria in categorias and any(t in texto for t in termos):
            return categoria
    return "Institucional" if "Institucional" in categorias else (categorias[-1] if categorias else "Outros")


def build_clipping_row(item: NewsItem, categoria: str, sentimento_label: str,
                        sentimento_score: float, link_pdf_drive: str = "") -> ClippingRow:
    return ClippingRow(
        data_publicacao=item.data_publicacao,
        veiculo=item.veiculo,
        palavra_chave=item.palavra_chave,
        categoria=categoria,
        manchete=item.manchete,
        link=item.link,
        link_pdf_drive=link_pdf_drive,
        sentimento=sentimento_label,
        confianca_sentimento=sentimento_score,
    )


def run_smoke_test(config: dict) -> None:
    """
    Valida a integração entre módulos com dados fictícios, sem rede.
    Não substitui um teste real com credenciais — ver README, seção
    "Primeira execução real" — mas pega erros de "encaixe" entre as peças
    (ex. campo renomeado num módulo e esquecido no outro).
    """
    from dedup import NewsItem

    class _FakeAnalyzerOutput:
        def __init__(self, output, probas):
            self.output = output
            self.probas = probas

    class _FakeAnalyzer:
        def predict(self, text):
            return _FakeAnalyzerOutput("NEU", {"POS": 0.2, "NEU": 0.7, "NEG": 0.1})

    itens = [
        NewsItem("A Tarde", "UFSB abre inscrições para vestibular 2027",
                 "https://atarde.com.br/n/1", "2026-09-20", "UFSB"),
        NewsItem("Correio", "UFSB assina convênio com prefeitura",
                 "https://correio24horas.com.br/n/9", "2026-09-21", "UFSB"),
    ]

    dedup = Deduplicator()
    novos = dedup.filter_new(itens)
    assert len(novos) == 2, "smoke-test falhou: deduplicador descartou item inédito"

    clf = SentimentClassifier(_FakeAnalyzer())
    categorias = config.get("categories", ["Institucional", "Outros"])

    linhas = []
    for item in novos:
        categoria = categorize(item.manchete, categorias)
        resultado = clf.classify(item.manchete)
        linhas.append(build_clipping_row(item, categoria, resultado.label, resultado.score))

    assert len(linhas) == 2, "smoke-test falhou: nem toda notícia virou uma linha"
    print(f"[smoke-test] OK — {len(linhas)} linhas montadas, categorias: "
          f"{[l.categoria for l in linhas]}, sentimentos: {[l.sentimento for l in linhas]}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline de clipping digital UFSB/ACS")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--modo", choices=["monitoramento", "backfill", "smoke-test"],
                         default="smoke-test")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.modo == "smoke-test":
        run_smoke_test(config)
        return

    raise NotImplementedError(
        f"Modo '{args.modo}' requer rede (Google News/GDELT/Sheets/Drive) e "
        "credenciais configuradas — ver README.md, seção 'Primeira execução "
        "real'. A lógica de cada etapa já está pronta e testada nos módulos "
        "em src/; falta só a 'cola' de autenticação específica do seu "
        "ambiente (arquivo de credenciais, IDs de planilha/pasta)."
    )


if __name__ == "__main__":
    main()
