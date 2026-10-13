import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from drive_upload import build_upload_metadata, load_service_account_info


def test_build_upload_metadata():
    meta = build_upload_metadata("2026-09-18_a-tarde_noticia.pdf", "FOLDER123")
    assert meta["name"] == "2026-09-18_a-tarde_noticia.pdf"
    assert meta["parents"] == ["FOLDER123"]
    assert meta["mimeType"] == "application/pdf"


def test_load_service_account_info_valid():
    payload = json.dumps({
        "type": "service_account",
        "project_id": "meu-projeto",
        "private_key": "-----BEGIN PRIVATE KEY-----\nFAKE\n-----END PRIVATE KEY-----\n",
        "client_email": "clipping@meu-projeto.iam.gserviceaccount.com",
    })
    info = load_service_account_info(payload)
    assert info["project_id"] == "meu-projeto"


def test_load_service_account_info_raises_clear_error_when_incomplete():
    payload = json.dumps({"type": "service_account"})  # faltam campos
    with pytest.raises(ValueError, match="project_id"):
        load_service_account_info(payload)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
