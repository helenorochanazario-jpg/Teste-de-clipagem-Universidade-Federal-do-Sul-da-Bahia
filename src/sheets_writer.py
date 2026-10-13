"""
Registro estruturado das notícias coletadas no Google Sheets.

FERRAMENTA: gspread (biblioteca open-source, a mais usada e madura para
Google Sheets em Python), autenticando com a MESMA conta de serviço usada
no Drive (compartilhe a planilha com o e-mail da conta de serviço).

Por que Sheets e não um banco de dados "de verdade": é gratuito, qualquer
pessoa da equipe de comunicação consegue abrir/filtrar/exportar sem saber
SQL, e o `report.py` lê diretamente daqui para montar o dashboard. Se o
volume crescer muito (dezenas de milhares de linhas), vale migrar para
SQLite/Postgres — sinal de alerta: Sheets fica visivelmente lento acima de
~50 mil linhas.

Cabeçalho fixo da planilha (primeira linha) — mantenha esta ordem, o
restante do pipeline depende dela:
    data_publicacao | data_coleta | veiculo | palavra_chave | categoria |
    manchete | link | link_pdf_drive | sentimento | confianca_sentimento
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

HEADER = [
    "data_publicacao", "data_coleta", "veiculo", "palavra_chave", "categoria",
    "manchete", "link", "link_pdf_drive", "sentimento", "confianca_sentimento",
]


@dataclass
class ClippingRow:
    data_publicacao: str
    veiculo: str
    palavra_chave: str
    categoria: str
    manchete: str
    link: str
    link_pdf_drive: str
    sentimento: str
    confianca_sentimento: float
    data_coleta: str = ""

    def __post_init__(self):
        if not self.data_coleta:
            self.data_coleta = date.today().isoformat()

    def to_row(self) -> list:
        return [
            self.data_publicacao, self.data_coleta, self.veiculo,
            self.palavra_chave, self.categoria, self.manchete, self.link,
            self.link_pdf_drive, self.sentimento, self.confianca_sentimento,
        ]


def rows_to_append(clipping_rows: list[ClippingRow]) -> list[list]:
    """Prepara o payload de `worksheet.append_rows(...)` — testável sem rede."""
    return [row.to_row() for row in clipping_rows]


def existing_links_from_sheet_values(all_values: list[list]) -> set[str]:
    """
    A partir do conteúdo bruto já lido da planilha (`worksheet.get_all_values()`),
    extrai o conjunto de links já registrados — usado para alimentar o
    `Deduplicator` (ver dedup.py) no início de cada execução, garantindo que
    o estado de "já visto" sobrevive entre execuções do GitHub Actions.
    """
    if not all_values or all_values[0] != HEADER:
        return set()
    link_col = HEADER.index("link")
    return {row[link_col] for row in all_values[1:] if len(row) > link_col}


def append_clipping_rows(worksheet, clipping_rows: list[ClippingRow]) -> None:
    """
    `worksheet` é um objeto gspread.Worksheet — injetado para permitir teste
    com um objeto falso. Em produção:

        import gspread
        gc = gspread.service_account_from_dict(service_account_info)
        sh = gc.open_by_key(config["google"]["spreadsheet_id"])
        worksheet = sh.worksheet(config["google"]["worksheet_name"])
    """
    payload = rows_to_append(clipping_rows)
    if payload:
        worksheet.append_rows(payload, value_input_option="USER_ENTERED")
