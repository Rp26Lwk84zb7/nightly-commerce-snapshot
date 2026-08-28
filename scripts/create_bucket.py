import os

from nightly_snapshot.infrai_client import InfraiClient


def main() -> None:
    bucket = os.environ.get("SNAPSHOT_BUCKET", "commerce-nightly")
    client = InfraiClient()
    try:
        client.create_bucket(bucket)
        print(f"bucket ready: {bucket}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

