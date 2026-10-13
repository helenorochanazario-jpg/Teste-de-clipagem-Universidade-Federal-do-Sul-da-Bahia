"""
Upload dos PDFs de notícia para uma pasta do Google Drive.

FERRAMENTA: google-api-python-client + google-auth (bibliotecas oficiais do
Google, gratuitas, open-source), autenticando com uma CONTA DE SERVIÇO — não
com login de usuário. Isso é o que permite o GitHub Actions rodar sozinho,
sem ninguém precisar clicar em "autorizar" a cada execução.

PRÉ-REQUISITOS (fora do código, feitos uma vez no Google Cloud Console):
  1. Criar um projeto no Google Cloud e ativar a "Google Drive API".
  2. Criar uma conta de serviço, gerar uma chave JSON.
  3. Compartilhar a pasta do Drive de destino com o e-mail da conta de
     serviço (algo como nome@projeto.iam.gserviceaccount.com), papel Editor.
  4. Guardar o conteúdo do JSON como secret do GitHub Actions (ex.
     `GOOGLE_SERVICE_ACCOUNT_JSON`), nunca commitado no repositório.

Este módulo separa a MONTAGEM DO PAYLOAD (testável sem rede) da CHAMADA
REAL à API (que exige rede e credenciais, fora do alcance deste sandbox).
"""
from __future__ import annotations

import io
import json


def build_upload_metadata(filename: str, parent_folder_id: str) -> dict:
    """Corpo da requisição de criação de arquivo no Drive."""
    return {
        "name": filename,
        "parents": [parent_folder_id],
        "mimeType": "application/pdf",
    }


def load_service_account_info(json_str: str) -> dict:
    """
    Faz o parse do JSON da conta de serviço (vindo de variável de ambiente/
    secret) e valida que os campos mínimos existem, para falhar cedo e com
    mensagem clara em vez de um erro genérico da biblioteca do Google no
    meio da execução do Action.
    """
    info = json.loads(json_str)
    obrigatorios = {"type", "project_id", "private_key", "client_email"}
    faltando = obrigatorios - info.keys()
    if faltando:
        raise ValueError(
            f"JSON da conta de serviço incompleto — faltam os campos: {sorted(faltando)}"
        )
    return info


def upload_pdf(drive_service, filename: str, pdf_bytes: bytes,
                parent_folder_id: str) -> str:
    """
    Envia o PDF e retorna o link de visualização (webViewLink).
    `drive_service` é o objeto retornado por
    `googleapiclient.discovery.build("drive", "v3", credentials=...)` —
    injetado para permitir teste com um serviço falso.
    """
    from googleapiclient.http import MediaIoBaseUpload  # import local (dep pesada)

    metadata = build_upload_metadata(filename, parent_folder_id)
    media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype="application/pdf")
    created = drive_service.files().create(
        body=metadata, media_body=media, fields="id, webViewLink"
    ).execute()
    return created["webViewLink"]
