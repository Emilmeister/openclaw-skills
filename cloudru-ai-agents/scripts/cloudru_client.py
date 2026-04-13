"""Cloud.ru AI Agents client.

IAMAuth and retry logic copied from cloudru-managed-rag.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, Optional

import httpx

# Bypass corporate proxy for all Cloud.ru API calls
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_k, None)


IAM_URL = "https://iam.api.cloud.ru"
PUBLIC_API_URL = "https://ai-agents.api.cloud.ru"

RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 1.0


# --- Retry (copied from cloudru-managed-rag) ---

def _retryable(resp: httpx.Response) -> bool:
    return resp.status_code >= 500


def _request_with_retry(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
    last_exc: Optional[Exception] = None
    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            resp = client.request(method, url, **kwargs)
            if not _retryable(resp) or attempt == RETRY_MAX_ATTEMPTS - 1:
                return resp
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt == RETRY_MAX_ATTEMPTS - 1:
                raise
        sleep_time = RETRY_BACKOFF_BASE * (2 ** attempt)
        time.sleep(sleep_time)
    if last_exc:
        raise last_exc
    return resp  # type: ignore


# --- IAM Auth (copied from cloudru-managed-rag) ---

class IAMAuth(httpx.Auth):
    requires_response_body = True

    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self._token: Optional[str] = None

    def _refresh(self) -> None:
        with httpx.Client(transport=httpx.HTTPTransport(proxy=None)) as c:
            resp = c.post(
                f"{IAM_URL}/api/v1/auth/token",
                json={"keyId": self.key_id, "secret": self.key_secret},
                timeout=30,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]

    def auth_flow(self, request):
        if self._token is None:
            self._refresh()
        request.headers["Authorization"] = f"Bearer {self._token}"
        response = yield request
        if response.status_code == 401:
            self._refresh()
            request.headers["Authorization"] = f"Bearer {self._token}"
            yield request


# --- AI Agents Client ---

class CloudruAiAgentsClient:
    """Client for Cloud.ru AI Agents public API."""

    def __init__(self, key_id: str, key_secret: str):
        self._auth = IAMAuth(key_id, key_secret)
        self._client = httpx.Client(
            base_url=PUBLIC_API_URL,
            auth=self._auth,
            timeout=30.0,
            transport=httpx.HTTPTransport(proxy=None),
        )

    def _headers(self) -> Dict[str, str]:
        return {"X-Request-ID": str(uuid.uuid4())}

    # ---- Agents ----

    def list_agents(self, project_id: str, *, limit: int = 100, offset: int = 0) -> httpx.Response:
        return _request_with_retry(
            self._client, "GET", f"/api/v1/{project_id}/agents",
            params={"limit": limit, "offset": offset}, headers=self._headers(),
        )

    def get_agent(self, project_id: str, agent_id: str) -> httpx.Response:
        return _request_with_retry(
            self._client, "GET", f"/api/v1/{project_id}/agents/{agent_id}",
            headers=self._headers(),
        )

    def create_agent(self, project_id: str, body: Dict[str, Any]) -> httpx.Response:
        return _request_with_retry(
            self._client, "POST", f"/api/v1/{project_id}/agents",
            json=body, headers=self._headers(), timeout=60.0,
        )

    def update_agent(self, project_id: str, agent_id: str, body: Dict[str, Any]) -> httpx.Response:
        return _request_with_retry(
            self._client, "PATCH", f"/api/v1/{project_id}/agents/{agent_id}",
            json=body, headers=self._headers(), timeout=60.0,
        )

    def delete_agent(self, project_id: str, agent_id: str) -> httpx.Response:
        return _request_with_retry(
            self._client, "DELETE", f"/api/v1/{project_id}/agents/{agent_id}",
            headers=self._headers(),
        )

    def suspend_agent(self, project_id: str, agent_id: str) -> httpx.Response:
        return _request_with_retry(
            self._client, "PATCH", f"/api/v1/{project_id}/agents/suspend/{agent_id}",
            headers=self._headers(),
        )

    def resume_agent(self, project_id: str, agent_id: str) -> httpx.Response:
        return _request_with_retry(
            self._client, "PATCH", f"/api/v1/{project_id}/agents/resume/{agent_id}",
            headers=self._headers(),
        )
