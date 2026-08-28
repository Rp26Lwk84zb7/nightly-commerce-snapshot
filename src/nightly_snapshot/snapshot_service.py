import base64
import hashlib

from .infrai_client import InfraiClient
from .models import SnapshotRequest, SnapshotResult


class SnapshotService:
    def __init__(self, infrai: InfraiClient, bucket: str) -> None:
        self.infrai = infrai
        self.bucket = bucket

    def store(self, request: SnapshotRequest) -> SnapshotResult:
        key = f"commerce/{request.snapshot_date.isoformat()}/snapshot.json"
        record_count = sum(
            len(group)
            for group in (
                request.checkouts,
                request.fulfillments,
                request.receipts,
                request.customer_updates,
            )
        )
        if self.infrai.head_object(self.bucket, key).get("found") is True:
            return SnapshotResult(
                bucket=self.bucket,
                key=key,
                status="already_exists",
                record_count=record_count,
            )

        payload = request.model_dump_json().encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        self.infrai.put_object(
            self.bucket,
            key,
            data_base64=base64.b64encode(payload).decode("ascii"),
            content_type="application/json",
            idempotency_key=f"nightly-commerce-{request.snapshot_date.isoformat()}-{digest}",
        )
        return SnapshotResult(
            bucket=self.bucket,
            key=key,
            status="created",
            record_count=record_count,
        )

