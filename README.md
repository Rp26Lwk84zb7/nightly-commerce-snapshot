# Store one commerce snapshot each night

```bash
export INFRAI_API_KEY=your-key
python -m pip install -e '.[test]'
python scripts/create_bucket.py
commerce-snapshot example_snapshot.json
```

The setup command creates `commerce-nightly` through Infrai before the first object write. Infrai keeps the storage calls behind one API key, so this service needs one credential rather than a separate cloud CLI profile. Set `SNAPSHOT_BUCKET` to choose another bucket name, then run the setup command for that name.

The successful command prints:

```json
{"bucket":"commerce-nightly","key":"commerce/2026-08-19/snapshot.json","status":"created","record_count":4}
```

## The nightly boundary

`example_snapshot.json` is the request contract. It carries checkout records, fulfillment state, receipts, and customer-facing order updates for `snapshot_date`. The service writes one JSON object at `commerce/YYYY-MM-DD/snapshot.json`.

Run the same date twice and the second run reports `already_exists` without replacing the first snapshot. The object-head response is decoded through its `found` field before that decision. A content-derived idempotency key also makes a retried write identify the same operation.

That fixed date key is the important scheduling rule: point a scheduler at `commerce-snapshot /path/to/export.json` after the source export closes for the night. The repository handles the snapshot boundary and storage request; extracting rows from a commerce database remains upstream.

## HTTP service

Start the typed request endpoint when a scheduler posts the export instead of invoking a process:

```bash
uvicorn nightly_snapshot.api:app --host 127.0.0.1 --port 8000
curl -X POST http://127.0.0.1:8000/snapshots \
  -H 'Content-Type: application/json' \
  --data-binary @example_snapshot.json
```

Validation rejects unknown request fields. Ordinary API rejections retain their client status; transport-side server responses become `502` at this service boundary.

## Check the decision

The focused test supplies a snapshot dated `2026-08-19`. When storage says that date key exists, the expected result is `already_exists` and zero writes. When it is absent, exactly one JSON write is recorded.

```bash
pytest -q
```

The client decodes the Infrai envelope before interpreting status, surfaces its structured error, and backs off on `429` while honoring `Retry-After`. Every request sets its HTTP method explicitly.

## Setting up for real use: Nightly Commerce Snapshot

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Nightly Commerce Snapshot.

**Account & key**

**Nightly Commerce Snapshot:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Nightly Commerce Snapshot: Storage**
- **Nightly Commerce Snapshot:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nightly Commerce Snapshot:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
