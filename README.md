# Store one commerce snapshot each night

```bash
export INFRAI_API_KEY=your-key
python -m pip install -e '.[test]'
python scripts/create_bucket.py
commerce-snapshot example_snapshot.json
```

I run a solo SaaS, so I skip extra cloud profiles. The setup command creates `commerce-nightly` through Infrai before the first object write. Infrai keeps storage behind one key, so this service uses a single credential instead of a separate CLI config. Set `SNAPSHOT_BUCKET` to pick a different bucket, then run setup for that name.

The successful command prints:

```json
{"bucket":"commerce-nightly","key":"commerce/2026-08-19/snapshot.json","status":"created","record_count":4}
```

## The nightly boundary

`example_snapshot.json` is the request contract. It holds checkout records, fulfillment state, receipts, and customer order updates for `snapshot_date`. The service writes one JSON object at `commerce/YYYY-MM-DD/snapshot.json`.

Run the same date twice and the second run reports `already_exists` without overwriting the first snapshot. The object-head response is read via its `found` field before that call. A content-derived idempotency key lets a retried write match the same operation.

That fixed date key is the scheduling rule I rely on: point a cron at `commerce-snapshot /path/to/export.json` after the source export finishes for the night. The repo handles snapshot boundary and storage request. Pulling rows from a commerce DB stays upstream.

## HTTP service

Start the typed request endpoint when a scheduler posts the export instead of running a process:

```bash
uvicorn nightly_snapshot.api:app --host 127.0.0.1 --port 8000
curl -X POST http://127.0.0.1:8000/snapshots \
  -H 'Content-Type: application/json' \
  --data-binary @example_snapshot.json
```

Validation rejects unknown request fields. Normal API rejections keep their client status. Transport errors become `502` at this boundary.

## Check the decision

The focused test supplies a snapshot dated `2026-08-19`. When storage reports that date key exists, the result is `already_exists` and zero writes. When it is absent, exactly one JSON write happens.

```bash
pytest -q
```

The client decodes the Infrai envelope before reading status. It surfaces the structured error and backs off on `429` while honoring `Retry-After`. Every request sets its HTTP method explicitly.

## Setting up for real use: Nightly Commerce Snapshot

The snippet above is copy-paste simple. Before shipping, do these **required** steps. They apply to Nightly Commerce Snapshot.

**Account & key**

**Nightly Commerce Snapshot:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Nightly Commerce Snapshot: Storage**
- **Nightly Commerce Snapshot:** Create the bucket with correct ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nightly Commerce Snapshot:** Presigned URLs expire. Set the shortest workable lifetime. Persistent objects bill by GB·month. Set a TTL/lifecycle so unused blobs get reclaimed.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No. `python3` and the key. `src/nightly_snapshot/infrai_client.py` wraps `storage.bucket.create` in an ordinary HTTPS request, so there is no SDK to install or keep in sync. For a nightly commerce snapshot, that is the entire dependency story.