import argparse
import os
from pathlib import Path

from .infrai_client import InfraiClient
from .models import SnapshotRequest
from .snapshot_service import SnapshotService


def main() -> None:
    parser = argparse.ArgumentParser(description="Store one nightly commerce snapshot")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    request = SnapshotRequest.model_validate_json(args.input.read_text(encoding="utf-8"))
    client = InfraiClient()
    try:
        result = SnapshotService(
            client,
            os.environ.get("SNAPSHOT_BUCKET", "commerce-nightly"),
        ).store(request)
        print(result.model_dump_json())
    finally:
        client.close()


if __name__ == "__main__":
    main()

