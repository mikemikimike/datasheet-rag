from __future__ import annotations

import pytest

import datasheet_rag.textract as textract


def test_config_template_does_not_advertise_unused_textract_role() -> None:
    from datasheet_rag.cli import _config_env_lines

    assert not any("RAG_TEXTRACT_ROLE_ARN" in line for line in _config_env_lines())


def test_start_analysis_requires_s3_bucket(monkeypatch) -> None:
    from datasheet_rag.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "s3_bucket", None)
    client_called = False

    def should_not_create_client():
        nonlocal client_called
        client_called = True
        raise AssertionError("Textract client must not be created before S3 preflight")

    monkeypatch.setattr(textract, "get_settings", lambda: settings)
    monkeypatch.setattr(textract, "textract_client", should_not_create_client)

    with pytest.raises(RuntimeError, match="RAG_S3_BUCKET"):
        textract.start_analysis("doc", "raw/doc.pdf")

    assert client_called is False


def test_start_analysis_uses_configured_s3_bucket(monkeypatch) -> None:
    from datasheet_rag.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "s3_bucket", "datasheets")
    captured: dict = {}

    class Client:
        def start_document_analysis(self, **params):
            captured.update(params)
            return {"JobId": "job-1"}

    monkeypatch.setattr(textract, "get_settings", lambda: settings)
    monkeypatch.setattr(textract, "textract_client", lambda: Client())

    assert textract.start_analysis("doc", "raw/doc.pdf") == "job-1"
    assert captured["DocumentLocation"]["S3Object"]["Bucket"] == "datasheets"
