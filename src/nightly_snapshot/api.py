import os

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .models import SnapshotRequest, SnapshotResult
from .snapshot_service import SnapshotService

app = FastAPI(title="Nightly commerce snapshot")


@app.post("/snapshots", response_model=SnapshotResult)
def create_snapshot(request: SnapshotRequest) -> SnapshotResult:
    client = InfraiClient()
    try:
        service = SnapshotService(client, os.environ.get("SNAPSHOT_BUCKET", "commerce-nightly"))
        return service.store(request)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail={"code": exc.code, "message": str(exc)}) from exc
    finally:
        client.close()

