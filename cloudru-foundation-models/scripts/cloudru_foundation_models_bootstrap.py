#!/usr/bin/env python3
"""Bootstrap Cloud.ru Evolution Foundation Models access.

Creates a service account, creates an API key for Foundation Models,
fetches the live model catalog, and prints a JSON summary that also includes
an OpenClaw custom-provider snippet.

This script intentionally uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import ssl
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen

context = ssl._create_unverified_context()

SERVICE_ACCOUNT_URL = "https://console.cloud.ru/u-api/bff-console/v2/service-accounts/add"
API_KEY_URL_TEMPLATE = (
    "https://console.cloud.ru/u-api/bff-console/v1/service-accounts/{service_account_id}/api_keys"
)
MODELS_URL = "https://foundation-models.api.cloud.ru/v1/models"
DEFAULT_PROVIDER_ID = "cloudru-foundation"
UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@dataclass
class ProjectContext:
    project_url: str
    project_id: Optional[str]
    customer_id: Optional[str]
    customer_id_source: Optional[str]
    notes: List[str]


class BootstrapError(RuntimeError):
    """Raised when the bootstrap flow cannot proceed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Cloud.ru service account and Foundation Models API key, "
            "then fetch the live model catalog and print an OpenClaw config snippet."
        )
    )
    parser.add_argument(
        "--project-url",
        default="",
        help="Current Cloud.ru project URL from the browser. Used to infer project_id and customer_id.",
    )
    parser.add_argument(
        "--project-id",
        default="",
        help="Explicit project ID. Overrides project_id inferred from --project-url.",
    )
    parser.add_argument(
        "--customer-id",
        default="",
        help=(
            "Explicit Cloud.ru customerId. Overrides customer_id inferred from --project-url. "
            "The user-supplied flow sometimes calls this secret_id."
        ),
    )
    parser.add_argument(
        "--secret-id",
        default="",
        help="Alias for --customer-id. Useful when the project URL exposes secret_id instead of customerId.",
    )
    parser.add_argument(
        "--token",
        default="",
        help="Cloud.ru console bearer token. The provided flow uses the browser access_token from localStorage.",
    )
    parser.add_argument(
        "--service-account-name",
        default="foundation-models-account",
        help="Name for the created Cloud.ru service account.",
    )
    parser.add_argument(
        "--service-account-description",
        default="foundation-models-account",
        help="Description for the created Cloud.ru service account.",
    )
    parser.add_argument(
        "--project-role",
        default="PROJECT_ROLE_PROJECT_ADMIN",
        help="Project role to assign to the service account.",
    )
    parser.add_argument(
        "--api-key-name",
        default="foundation-models-api-key",
        help="Name for the created Foundation Models API key.",
    )
    parser.add_argument(
        "--api-key-description",
        default="foundation-models-api-key",
        help="Description for the created Foundation Models API key.",
    )
    parser.add_argument(
        "--product",
        default="ml_inference_ai_marketplace",
        help="Cloud.ru product code to include when creating the API key.",
    )
    parser.add_argument(
        "--timezone",
        type=int,
        default=3,
        help="Timezone offset used in the API key restrictions payload.",
    )
    parser.add_argument(
        "--days-valid",
        type=int,
        default=365,
        help="API key validity in days. Cloud.ru docs say the maximum is one year.",
    )
    parser.add_argument(
        "--provider-id",
        default=DEFAULT_PROVIDER_ID,
        help="Provider ID to use in the generated OpenClaw config snippet.",
    )
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip the final /v1/models request.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call Cloud.ru APIs. Only parse inputs and render payloads and config snippets.",
    )
    return parser.parse_args()


def parse_project_context(
    project_url: str,
    explicit_project_id: str,
    explicit_customer_id: str,
    explicit_secret_id: str,
) -> ProjectContext:
    notes: List[str] = []
    if not project_url and not explicit_project_id:
        raise BootstrapError(
            "Pass --project-url or --project-id so the script can determine the target project."
        )

    project_id = explicit_project_id or None
    customer_id = explicit_customer_id or explicit_secret_id or None
    customer_id_source: Optional[str] = None

    if explicit_secret_id and not explicit_customer_id:
        customer_id_source = "--secret-id"
        notes.append("Using --secret-id as customerId because the API expects customerId.")
    elif explicit_customer_id:
        customer_id_source = "--customer-id"

    if not project_url:
        return ProjectContext(
            project_url="",
            project_id=project_id,
            customer_id=customer_id,
            customer_id_source=customer_id_source,
            notes=notes,
        )

    parsed = urlparse(project_url)
    query_map = collapse_query_maps(parsed)
    path_segments = [segment for segment in parsed.path.split("/") if segment]

    if not project_id:
        project_id = first_non_empty(
            query_map.get("project_id"),
            query_map.get("projectId"),
            query_map.get("project-id"),
            path_uuid_after(path_segments, "projects"),
            path_uuid_after(path_segments, "project"),
        )

    if not customer_id:
        inferred_customer = first_non_empty(
            query_map.get("customerId"),
            query_map.get("customer_id"),
            query_map.get("secret_id"),
            query_map.get("secretId"),
            query_map.get("secret-id"),
            path_uuid_after(path_segments, "customers"),
            path_uuid_after(path_segments, "customer"),
            path_uuid_after(path_segments, "organizations"),
            path_uuid_after(path_segments, "organization"),
        )
        customer_id = inferred_customer
        if query_map.get("secret_id") or query_map.get("secretId") or query_map.get("secret-id"):
            customer_id_source = "secret_id-from-url"
            notes.append(
                "Mapped secret_id from the project URL to customerId because the service-account API expects customerId."
            )
        elif inferred_customer:
            customer_id_source = "customerId-from-url"

    if not project_id:
        notes.append(
            "Could not infer project_id from the URL. Pass --project-id explicitly if the Cloud.ru URL format changed."
        )
    if not customer_id:
        notes.append(
            "Could not infer customerId from the URL. Pass --customer-id explicitly if the Cloud.ru URL format changed."
        )

    return ProjectContext(
        project_url=project_url,
        project_id=project_id,
        customer_id=customer_id,
        customer_id_source=customer_id_source,
        notes=notes,
    )


def collapse_query_maps(parsed) -> Dict[str, str]:
    query_map: Dict[str, str] = {}

    def merge(raw: str) -> None:
        if not raw:
            return
        pairs = parse_qs(raw, keep_blank_values=False)
        for key, values in pairs.items():
            if values:
                query_map[key] = unquote(values[-1])

    merge(parsed.query)

    fragment = parsed.fragment or ""
    if "?" in fragment:
        merge(fragment.split("?", 1)[1])
    elif "=" in fragment and "&" in fragment:
        merge(fragment)

    return query_map


def first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value:
            return value
    return None


def path_uuid_after(path_segments: List[str], marker: str) -> Optional[str]:
    try:
        index = path_segments.index(marker)
    except ValueError:
        return None
    if index + 1 < len(path_segments):
        candidate = path_segments[index + 1]
        if UUID_RE.fullmatch(candidate):
            return candidate
    return None


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=(dt.microsecond // 1000) * 1000).isoformat().replace(
        "+00:00", "Z"
    )


def request_json(
    url: str,
    *,
    method: str = "GET",
    bearer_token: Optional[str] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Any:
    headers = {
        "Accept": "application/json",
        "User-Agent": "PostmanRuntime/7.48.0",
    }
    data = None
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode("utf-8")

    request = Request(url=url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30, context=context) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise BootstrapError(f"{method} {url} failed with HTTP {exc.code}: {payload}") from exc
    except URLError as exc:
        raise BootstrapError(f"{method} {url} failed: {exc}") from exc


def service_account_payload(args: argparse.Namespace, context: ProjectContext) -> Dict[str, Any]:
    if not context.project_id:
        raise BootstrapError("Missing project_id. Pass --project-id or provide a parseable --project-url.")
    if not context.customer_id:
        raise BootstrapError(
            "Missing customerId. Pass --customer-id or --secret-id, or provide a project URL that exposes it."
        )
    return {
        "name": args.service_account_name,
        "description": args.service_account_description,
        "customerId": context.customer_id,
        "serviceRoles": [],
        "projectId": context.project_id,
        "projectRole": args.project_role,
        "artifactRoles": [],
        "artifactRegistries": [],
        "s3eRoles": [],
        "s3eBuckets": [],
    }


def api_key_payload(args: argparse.Namespace) -> Dict[str, Any]:
    expiry = datetime.now(timezone.utc) + timedelta(days=args.days_valid)
    return {
        "name": args.api_key_name,
        "description": args.api_key_description,
        "products": [args.product],
        "restrictions": {
            "ipAddresses": [],
            "timeRange": {
                "timeSlots": [{"start": 0, "end": 24}],
                "timezone": args.timezone,
            },
        },
        "enabled": True,
        "expiredAt": iso_z(expiry),
    }


def create_service_account(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return request_json(
        SERVICE_ACCOUNT_URL,
        method="POST",
        bearer_token=token,
        json_body=payload,
    )


def create_api_key(token: str, service_account_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = API_KEY_URL_TEMPLATE.format(service_account_id=service_account_id)
    return request_json(url, method="POST", bearer_token=token, json_body=payload)


def list_models(api_key: str) -> Dict[str, Any]:
    return request_json(MODELS_URL, method="GET", bearer_token=api_key)


def summarize_models(models_response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not models_response:
        return {"count": 0, "ids": [], "objects": []}
    data = models_response.get("data") or []
    ids: List[str] = []
    objects: List[Dict[str, Any]] = []
    for item in data:
        model_id = item.get("id")
        if model_id:
            ids.append(model_id)
        objects.append(
            {
                "id": model_id,
                "owned_by": item.get("owned_by"),
                "context_length": item.get("context_length"),
                "function_calling": item.get("function_calling", False),
                "reasoning": item.get("reasoning", False),
                "structure_output": item.get("structure_output", False),
                "type": ((item.get("metadata") or {}).get("type")),
            }
        )
    return {"count": len(ids), "ids": ids, "objects": objects}


def render_openclaw_config(provider_id: str, model_ids: List[str]) -> Dict[str, Any]:
    starter_models = model_ids[:3] if model_ids else ["GigaChat/GigaChat-2-Max"]
    provider_models = [
        {"id": model_id, "name": model_id.split("/")[-1] if "/" in model_id else model_id}
        for model_id in starter_models
    ]
    primary_model = starter_models[0]
    config = {
        "env": {
            "CLOUD_RU_FOUNDATION_MODELS_API_KEY": "<set-me>",
        },
        "agents": {
            "defaults": {
                "model": {
                    "primary": f"{provider_id}/{primary_model}",
                }
            }
        },
        "models": {
            "mode": "merge",
            "providers": {
                provider_id: {
                    "baseUrl": "https://foundation-models.api.cloud.ru/v1",
                    "apiKey": "${CLOUD_RU_FOUNDATION_MODELS_API_KEY}",
                    "api": "openai-completions",
                    "models": provider_models,
                }
            },
        },
    }
    onboard_command = (
        "export CUSTOM_API_KEY=\"$CLOUD_RU_FOUNDATION_MODELS_API_KEY\"\n"
        "openclaw onboard --non-interactive \\\n"
        "  --auth-choice custom-api-key \\\n"
        "  --custom-base-url \"https://foundation-models.api.cloud.ru/v1\" \\\n"
        f"  --custom-model-id \"{primary_model}\" \\\n"
        "  --custom-api-key \"$CUSTOM_API_KEY\" \\\n"
        "  --custom-compatibility openai"
    )
    return {
        "provider_id": provider_id,
        "primary_model": f"{provider_id}/{primary_model}",
        "config_json": config,
        "onboard_command": onboard_command,
    }


def build_result(
    args: argparse.Namespace,
    context: ProjectContext,
    sa_payload: Dict[str, Any],
    key_payload: Dict[str, Any],
    service_account: Optional[Dict[str, Any]],
    api_key: Optional[Dict[str, Any]],
    models_response: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    notes = list(context.notes)
    if args.days_valid > 365:
        notes.append("days-valid is greater than 365; Cloud.ru documentation says one year is the maximum.")
    model_summary = summarize_models(models_response)
    provider = render_openclaw_config(args.provider_id, model_summary["ids"])
    result: Dict[str, Any] = {
        "project": {
            "project_url": context.project_url,
            "project_id": context.project_id,
            "customer_id": context.customer_id,
            "customer_id_source": context.customer_id_source,
        },
        "inputs": {
            "service_account_payload": sa_payload,
            "api_key_payload": key_payload,
        },
        "service_account": service_account,
        "api_key": api_key,
        "models": model_summary,
        "openclaw": provider,
        "notes": notes,
    }
    return result


def main() -> int:
    args = parse_args()
    try:
        context = parse_project_context(
            project_url=args.project_url,
            explicit_project_id=args.project_id,
            explicit_customer_id=args.customer_id,
            explicit_secret_id=args.secret_id,
        )
        sa_payload = service_account_payload(args, context)
        key_payload = api_key_payload(args)

        if args.dry_run:
            result = build_result(
                args,
                context,
                sa_payload,
                key_payload,
                service_account=None,
                api_key=None,
                models_response=None,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if not args.token:
            raise BootstrapError(
                "Missing --token. Pass the Cloud.ru console bearer token from the browser localStorage flow."
            )

        service_account = create_service_account(args.token, sa_payload)
        service_account_id = service_account.get("id")
        if not service_account_id:
            raise BootstrapError(
                f"Cloud.ru service account response does not contain an id: {json.dumps(service_account, ensure_ascii=False)}"
            )

        api_key = create_api_key(args.token, service_account_id, key_payload)
        api_secret = api_key.get("secret")
        if not api_secret:
            raise BootstrapError(
                f"Cloud.ru API key response does not contain a secret: {json.dumps(api_key, ensure_ascii=False)}"
            )

        models_response = None
        if not args.skip_models:
            try:
                models_response = list_models(api_secret)
            except BootstrapError as exc:
                # Keep the main bootstrap result and surface the model-list error as a note.
                context.notes.append(f"Model listing failed after key creation: {exc}")

        result = build_result(
            args,
            context,
            sa_payload,
            key_payload,
            service_account=service_account,
            api_key=api_key,
            models_response=models_response,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except BootstrapError as exc:
        import traceback
        traceback.print_exc()
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
