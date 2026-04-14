"""CLI handlers for `pricing` — estimate instance cost (same endpoint UI uses
on every create form).
"""

from helpers import build_client, check_response, print_json


def cmd_estimate(args):
    client, project_id = build_client()
    resp = client.get_price(project_id,
                            instance_type_id=args.instance_type_id or "",
                            min_scale=args.min_scale, max_scale=args.max_scale)
    check_response(resp, "estimating price")
    print_json(resp.json())


COMMANDS = {
    "pricing.estimate": cmd_estimate,
}
