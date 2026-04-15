"""Shared high-level flag helpers used by create/update commands across
agents, agent systems, mcp-servers. Each helper applies a group of flags onto
the target dict, but only when user explicitly set them (so we don't clobber
server defaults or values supplied via --config-json).
"""

from typing import Any


def dig(d: dict, *keys: str) -> dict:
    """Walk/create nested dicts so `d[k0][k1]...` is returned (ready to mutate)."""
    for k in keys:
        d = d.setdefault(k, {})
    return d


def apply_scaling(scaling: dict, args) -> None:
    """Populate a scaling{} dict with minScale/maxScale/keepAlive/rps."""
    if getattr(args, "min_scale", None) is not None:
        scaling["minScale"] = args.min_scale
    if getattr(args, "max_scale", None) is not None:
        scaling["maxScale"] = args.max_scale
    if getattr(args, "keep_alive_min", None) is not None:
        scaling["isKeepAlive"] = args.keep_alive_min > 0
        scaling["keepAliveDuration"] = {
            "hours": 0, "minutes": args.keep_alive_min, "seconds": 0,
        }
    if getattr(args, "rps", None) is not None:
        dig(scaling, "scalingRules", "rps")["value"] = args.rps


def apply_integration(body: dict, args) -> None:
    """Populate body.integrationOptions.{logging,authOptions}."""
    if getattr(args, "log_group_id", None):
        dig(body, "integrationOptions", "logging").update({
            "isEnabledLogging": True, "logGroupId": args.log_group_id,
        })
    sa_id = getattr(args, "service_account_id", None)
    auth_enabled = getattr(args, "auth_enabled", None)
    if auth_enabled is not None or sa_id:
        auth = dig(body, "integrationOptions", "authOptions")
        if auth_enabled is not None:
            auth["isEnabled"] = auth_enabled
        if sa_id:
            auth["serviceAccountId"] = sa_id
            auth.setdefault("type", "AUTHENTICATION_TYPE_TOKEN_BASED")


def parse_kv_pairs(raw: str) -> dict:
    """Parse 'k1=v1,k2=v2' or multiple --env entries joined with commas."""
    out: dict = {}
    if not raw:
        return out
    for item in raw.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def apply_environment(body: dict, args) -> None:
    """Populate body.environmentOptions.rawEnvs / secretEnvs from --env/--secret-env."""
    if getattr(args, "env", None):
        raw = dig(body, "environmentOptions", "rawEnvs")
        raw.update(parse_kv_pairs(args.env))
    if getattr(args, "secret_env", None):
        sec = dig(body, "environmentOptions", "secretEnvs")
        sec.update(parse_kv_pairs(args.secret_env))
    # Ensure both dicts exist if either was set (API proto)
    if body.get("environmentOptions"):
        body["environmentOptions"].setdefault("rawEnvs", {})
        body["environmentOptions"].setdefault("secretEnvs", {})


def parse_ports(raw: str) -> list:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def add_common_scaling_flags(p) -> None:
    """Register scaling flags on an argparse subparser."""
    p.add_argument("--min-scale", type=int, help="Minimum replicas")
    p.add_argument("--max-scale", type=int, help="Maximum replicas")
    p.add_argument("--keep-alive-min", type=int,
                    help="Keep warm N minutes after last request (0 disables)")
    p.add_argument("--rps", type=int, help="RPS scaling threshold per replica")


def add_common_integration_flags(p) -> None:
    p.add_argument("--log-group-id", help="Cloud Logging group ID")
    p.add_argument("--auth-enabled", type=lambda v: v.lower() == "true",
                    help="true|false — require authentication to invoke")
    p.add_argument("--service-account-id", help="Service account for auth")


def add_environment_flags(p) -> None:
    p.add_argument("--env",
                    help="Comma-separated KEY=VALUE plain env vars")
    p.add_argument("--secret-env",
                    help="Comma-separated KEY=SECRET_REF env vars sourced from secret manager")
