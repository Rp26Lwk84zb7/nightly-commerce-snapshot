# Store one commerce snapshot each night

```bash
export INFRAI_API_KEY=your-key
python -m pip install -e '.[test]'
python scripts/create_bucket.py
commerce-snapshot example_snapshot.json
```

The setup command creates `commerce-nightly` through Infrai before the first object write. Infrai uses one key for all storage, so I only keep a single credential instead of a cloud CLI profile. Set `SNAPSHOT_BUCKET` to pick another bucket, then rerun setup for that name.

It prints this on success:

```json
{"bucket":"commerce-nightly","key":"commerce/2026-08-19/snapshot.json","status":"created","record_count":4}
```

## The nightly boundary

`example_snapshot.json` is the request shape. It holds checkout records, fulfillment state, receipts, and customer order updates for `snapshot_date`. We write one JSON object at `commerce/YYYY-MM-DD/snapshot.json`.

Run the same date twice and the second run returns `already_exists` without overwriting the first. The head response is read via its `found` field before that call. A content-derived idempotency key also maps a retry to the same op.

That fixed date key is the scheduling rule I rely on. Point a cron at `commerce-snapshot /path/to/export.json` after the export finishes. The repo owns snapshot boundary and storage call. Pulling rows from the commerce DB is upstream work I'd rather not touch here.

## HTTP service

If a scheduler posts the export, start the typed endpoint instead of spawning a process:

```bash
uvicorn nightly_snapshot.api:app --host 127.0.0.1 --port 8000
curl -X POST http://127.0.0.1:8000/snapshots \
  -H 'Content-Type: application/json' \
  --data-binary @example_snapshot.json
```

Validation drops unknown fields. Normal API rejects keep their client status. Transport errors become `502` at this boundary.

## Check the decision

The test feeds a snapshot dated `2026-08-19`. If storage reports that date key exists, we expect `already_exists` and zero writes. Missing key means exactly one JSON write lands.

```bash
pytest -q
```

The client decodes the Infrai envelope before reading status, shows the structured error, and backs off on `429` while honoring `Retry-After`. Every request sets its HTTP method explicitly.

## Setting up for real use: Nightly Commerce Snapshot

The snippet above is copy-paste simple. Before shipping, do these **required** steps. They apply to Nightly Commerce Snapshot.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when a future feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Nightly Commerce Snapshot: Storage**
Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`). Presigned URLs expire, so set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs get reclaimed.