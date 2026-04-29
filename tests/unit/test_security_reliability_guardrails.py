"""Security/reliability guardrails from ELA-37 static-scan triage."""

import pytest

from munipal.api.routes import health
from scripts import rebuild_corpus_document_index as rebuild_index
from scripts import verify_corpus_db_reconciliation as verify_reconciliation


class _FakeRedisClient:
    def __init__(self, *, ping_result=True, ping_error: Exception | None = None):
        self.ping_result = ping_result
        self.ping_error = ping_error
        self.closed = False

    async def ping(self):
        if self.ping_error:
            raise self.ping_error
        return self.ping_result

    async def aclose(self):
        self.closed = True


class _FakeRedisModule:
    def __init__(self, client: _FakeRedisClient):
        self.client = client
        self.urls: list[str] = []

    def from_url(self, url: str):
        self.urls.append(url)
        return self.client


class _Settings:
    redis_connection_url = "redis://example.test:6379/0"


@pytest.mark.asyncio
async def test_redis_readiness_uses_ping_and_closes_client(monkeypatch: pytest.MonkeyPatch):
    client = _FakeRedisClient()
    fake_redis = _FakeRedisModule(client)
    monkeypatch.setattr(health, "redis", fake_redis)

    assert await health._check_redis(_Settings()) is True
    assert fake_redis.urls == [_Settings.redis_connection_url]
    assert client.closed is True


@pytest.mark.asyncio
async def test_redis_readiness_degrades_on_ping_failure(monkeypatch: pytest.MonkeyPatch):
    client = _FakeRedisClient(ping_error=ConnectionError("down"))
    monkeypatch.setattr(health, "redis", _FakeRedisModule(client))

    assert await health._check_redis(_Settings()) is False
    assert client.closed is True


def test_sql_identifier_guard_allows_only_known_document_index_identifiers():
    assert rebuild_index._quote_allowed_identifier("document_index") == '"document_index"'
    assert rebuild_index._quote_allowed_identifier("ix_docidx_source_hash_doc_type") == '"ix_docidx_source_hash_doc_type"'
    assert verify_reconciliation._quote_allowed_identifier("document_index") == '"document_index"'


@pytest.mark.parametrize(
    "identifier",
    [
        "document_index; DROP TABLE documents",
        "document_index_legacy",
        "sqlite_master",
        "ix_docidx_source_hash_doc_type WHERE 1=1",
        "bad-name",
    ],
)
def test_sql_identifier_guard_rejects_unapproved_or_malformed_identifiers(identifier: str):
    with pytest.raises(ValueError, match="SQL identifier"):
        rebuild_index._quote_allowed_identifier(identifier)
    with pytest.raises(ValueError, match="SQL identifier"):
        verify_reconciliation._quote_allowed_identifier(identifier)
