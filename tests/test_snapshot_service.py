from datetime import date
from typing import Any

from nightly_snapshot.models import SnapshotRequest
from nightly_snapshot.snapshot_service import SnapshotService


class RecordingStorage:
    def __init__(self, found: bool) -> None:
        self.found = found
        self.puts: list[dict[str, Any]] = []

    def head_object(self, bucket: str, key: str) -> dict[str, bool]:
        return {"found": self.found}

    def put_object(self, bucket: str, key: str, **body: str) -> dict[str, Any]:
        self.puts.append({"bucket": bucket, "key": key, **body})
        return {"key": key}


def request_for(day: date) -> SnapshotRequest:
    return SnapshotRequest.model_validate(
        {
            "snapshot_date": day.isoformat(),
            "checkouts": [
                {
                    "checkout_id": "co_17",
                    "customer_id": "cus_8",
                    "currency": "USD",
                    "total": "42.50",
                    "placed_at": "2026-08-19T21:10:00Z",
                }
            ],
            "fulfillments": [],
            "receipts": [],
            "customer_updates": [],
        }
    )


def test_existing_nightly_snapshot_is_not_replaced() -> None:
    storage = RecordingStorage(found=True)

    result = SnapshotService(storage, "commerce-nightly").store(request_for(date(2026, 8, 19)))  # type: ignore[arg-type]

    assert result.status == "already_exists"
    assert result.key == "commerce/2026-08-19/snapshot.json"
    assert result.record_count == 1
    assert storage.puts == []


def test_new_nightly_snapshot_is_written_once() -> None:
    storage = RecordingStorage(found=False)

    result = SnapshotService(storage, "commerce-nightly").store(request_for(date(2026, 8, 19)))  # type: ignore[arg-type]

    assert result.status == "created"
    assert len(storage.puts) == 1
    assert storage.puts[0]["content_type"] == "application/json"
    assert storage.puts[0]["idempotency_key"].startswith("nightly-commerce-2026-08-19-")

