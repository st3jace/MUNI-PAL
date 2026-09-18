from datetime import UTC, datetime, timedelta

import pytest
from backup import PREFIX, expired_keys, validate_receipt

NOW = datetime(2026, 9, 18, 9, tzinfo=UTC)
KEY = PREFIX + "20260918T090000Z-abcdef123456.tar.age"


def receipt(hours=0):
    return {
        "snapshot_at": (NOW - timedelta(hours=hours)).isoformat(),
        "restore_verified": True,
        "key": KEY,
    }


def test_recent_verified_backup_is_healthy():
    validate_receipt(receipt(25), NOW)


@pytest.mark.parametrize("hours", [27, -1])
def test_stale_and_future_snapshots_fail_monitor(hours):
    with pytest.raises(RuntimeError):
        validate_receipt(receipt(hours), NOW)


def test_unverified_snapshot_cannot_satisfy_monitor():
    item = receipt()
    item["restore_verified"] = False
    with pytest.raises(RuntimeError):
        validate_receipt(item, NOW)


def test_retention_preserves_recent_copies_and_unrelated_objects():
    old = NOW - timedelta(days=31)
    recent = NOW - timedelta(days=29)
    items = [
        {"Key": KEY, "LastModified": old},
        {"Key": PREFIX + "20260917T090000Z-abcdef123456.tar.age", "LastModified": recent},
        {"Key": PREFIX + "latest-success.json", "LastModified": old},
        {"Key": "client-document.pdf", "LastModified": old},
        {"Key": PREFIX + "../do-not-delete.tar.age", "LastModified": old},
    ]
    assert expired_keys(items, NOW) == [KEY]


def test_retention_cannot_be_shortened_accidentally():
    with pytest.raises(RuntimeError):
        expired_keys([], NOW, keep_days=1)


def test_unrelated_backup_key_rejected_by_monitor():
    item = receipt()
    item["key"] = "another-project/backup.age"
    with pytest.raises(RuntimeError):
        validate_receipt(item, NOW)
