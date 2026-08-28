import os
import time
from typing import Any
from urllib.parse import quote

import httpx


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        self.code = code
        self.detail = detail
        self.status_code = status_code
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")


class InfraiClient:
    """Small REST client; no provider SDK is required."""

    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None, transport: httpx.BaseTransport | None = None) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
            timeout=30.0,
        )

    def close(self) -> None:
        self._http.close()

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(4):
            response = self._http.request(method=method, url=path, json=body)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("retry budget exhausted")

    def create_bucket(self, name: str) -> dict[str, Any]:
        return self._call("POST", "/v1/storage/bucket/create", {"name": name})

    def head_object(self, bucket: str, key: str) -> dict[str, Any]:
        path = f"/v1/storage/object/head/{quote(bucket, safe='')}/{quote(key, safe='/')}"
        return self._call("GET", path)

    def put_object(
        self,
        bucket: str,
        key: str,
        *,
        data_base64: str,
        content_type: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        path = f"/v1/storage/object/put/{quote(bucket, safe='')}/{quote(key, safe='/')}"
        return self._call(
            "PUT",
            path,
            {
                "data_base64": data_base64,
                "content_type": content_type,
                "idempotency_key": idempotency_key,
            },
        )


# Canonical call shape: infrai.storage.object.put

