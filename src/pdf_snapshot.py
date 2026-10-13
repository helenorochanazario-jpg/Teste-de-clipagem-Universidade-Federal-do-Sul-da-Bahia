"""
Impressão da página da notícia em PDF.

FERRAMENTA ESCOLHIDA: Playwright (Chromium headless), não wkhtmltopdf.
Motivo: a maioria dos portais de notícia hoje depende de CSS/JS para
renderizar layout, propagandas lazy-load, paywalls parciais etc.
wkhtmltopdf usa um motor de renderização antigo (WebKit desatualizado) e
frequentemente produz PDFs quebrados nesses sites. Playwright usa Chromium
de verdade, o mesmo motor que o leitor humano usa.

Uso típico (em produção, com rede liberada):

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        pdf_bytes = snapshot_url_to_pdf(page, "https://veiculo.com.br/noticia")
        browser.close()

Este módulo isola a lógica de "como gerar o PDF a partir de uma page já
aberta" para poder testar o nome de arquivo e a preparação da página sem
precisar subir um browser real a cada teste — subir o Chromium é lento e
não seria um teste unitário, seria um teste de integração (recomendado
rodar esse separadamente, ver `tests/test_pdf_snapshot_integration.py`,
que é pulado por padrão neste ambiente por falta de acesso de rede ao
site de destino).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date


def slugify_filename(veiculo: str, data_publicacao: str, manchete: str) -> str:
    """
    Gera um nome de arquivo estável e legível para o PDF, ex.:
    '2026-09-18_a-tarde_ufsb-lanca-edital-de-pos-graduacao.pdf'
    Usado tanto para o nome no Google Drive quanto para conferência manual.
    """
    data = data_publicacao or date.today().isoformat()
    partes = f"{veiculo}-{manchete}"
    partes = unicodedata.normalize("NFKD", partes)
    partes = "".join(c for c in partes if not unicodedata.combining(c))
    partes = re.sub(r"[^a-zA-Z0-9]+", "-", partes).strip("-").lower()
    partes = partes[:120]  # evita nomes de arquivo absurdamente longos
    return f"{data}_{partes}.pdf"


PLAYWRIGHT_PDF_OPTIONS = {
    "format": "A4",
    "print_background": True,  # preserva cores/imagens de fundo do layout
    "margin": {"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
}


def snapshot_url_to_pdf(page, url: str, wait_ms: int = 2500) -> bytes:
    """
    Recebe uma `page` do Playwright já criada (injeção de dependência —
    facilita testar com um objeto falso). Navega, espera o carregamento de
    conteúdo dinâmico e retorna os bytes do PDF.
    """
    page.goto(url, wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(wait_ms)  # dá tempo para lazy-load de imagens/anúncios
    return page.pdf(**PLAYWRIGHT_PDF_OPTIONS)
