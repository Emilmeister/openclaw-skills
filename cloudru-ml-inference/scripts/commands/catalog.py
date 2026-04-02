"""Catalog commands: browse predefined models and deploy them."""

import sys

from helpers import build_client, check_response


def cmd_catalog(args):
    """List predefined models from the Cloud.ru catalog."""
    client, _ = build_client()
    params = {"limit": args.limit or 100, "offset": args.offset or 0}
    if args.query:
        params["query"] = args.query
    if args.sort:
        params["sort"] = args.sort

    res = client.get_catalog(**params)
    check_response(res, "fetching catalog")

    data = res.json()
    total = data.get("total", 0)
    has_more = data.get("hasMore", False)
    cards = data.get("modelCards", [])
    print(f"Predefined models ({len(cards)} shown, {total} total, hasMore={has_more}):\n")
    for c in cards:
        tags = ", ".join(c.get("tags", []))
        tags_str = f" [{tags}]" if tags else ""
        print(
            f"  {c['id']} | {c['name']:<40} | {c.get('vendorName',''):<10} "
            f"| {c.get('paramsBn','')}B | ctx={c.get('contextK','')}K "
            f"| {c.get('price','')} rub/hour{tags_str}"
        )


def cmd_catalog_detail(args):
    """Show detailed configs for a predefined model."""
    client, _ = build_client()
    res = client.get_catalog_detail(args.model_card_id)
    check_response(res, "fetching model card")

    data = res.json()
    card = data.get("modelCard", {})
    configs = data.get("modelCardConfigs", [])

    print(f"Model: {card.get('name', '?')}")
    print(f"Vendor: {card.get('vendorName', '?')}")
    print(f"Task: {card.get('taskType', '?')}")
    print(f"Params: {card.get('paramsBn', '?')}B | Context: {card.get('contextK', '?')}K")
    print(f"License: {card.get('licenseName', '?')}")
    print(f"Description: {card.get('description', '')[:200]}")
    print(f"\nAvailable configurations ({len(configs)}):")
    for i, cfg in enumerate(configs):
        print(
            f"\n  [{i}] GPU: {cfg.get('allowedGpu', '?')} x{cfg.get('gpuCount', '?')} "
            f"({cfg.get('gpuMemoryAllocGb', '?')}GB) | "
            f"Framework: {cfg.get('frameworkType', '?')} {cfg.get('frameworkVersion', '')} | "
            f"Price: {cfg.get('price', '?')} rub/day"
        )
        print(f"      Config ID: {cfg.get('id', '?')}")
        print(f"      Runtime: {cfg.get('runtimeTemplateId', '?')}")


def cmd_deploy(args):
    """Deploy a predefined model — fetches exact config from catalog and creates model run."""
    client, project_id = build_client()

    res = client.get_catalog_detail(args.model_card_id)
    check_response(res, "fetching model card")

    data = res.json()
    card = data.get("modelCard", {})
    configs = data.get("modelCardConfigs", [])

    if not configs:
        print("Error: no configurations available for this model", file=sys.stderr)
        sys.exit(1)

    config_index = args.config_index if args.config_index is not None else 0
    if config_index >= len(configs):
        print(f"Error: config index {config_index} out of range (0-{len(configs)-1})", file=sys.stderr)
        sys.exit(1)
    cfg = configs[config_index]

    model_name = args.name or card.get("name", "model-run")
    task_type = card.get("taskType", "ModelTaskType_GENERATE")

    payload = {
        "name": model_name,
        "frameworkType": cfg["frameworkType"],
        "resourceType": cfg["allowedGpu"],
        "gpuCount": cfg["gpuCount"],
        "gpuGbMemory": cfg["gpuMemoryAllocGb"],
        "modelTaskType": task_type,
        "runtimeTemplateId": cfg["runtimeTemplateId"],
        "modelSource": card.get("modelSource", {}),
        "servingOptions": cfg.get("servingOptions", {}),
        "scaling": cfg.get("scaling", {"minScale": 1, "maxScale": 1, "scalingRules": {"rpsType": {"value": 200}}}),
        "options": {
            "isEnabledAuth": False,
            "isEnabledLogging": False,
        },
    }

    print(f"Deploying '{card.get('name', '?')}' with config [{config_index}]:")
    print(f"  GPU: {cfg.get('allowedGpu')} x{cfg.get('gpuCount')} ({cfg.get('gpuMemoryAllocGb')}GB)")
    print(f"  Framework: {cfg.get('frameworkType')} {cfg.get('frameworkVersion', '')}")
    print(f"  Price: {cfg.get('price', '?')} rub/day")

    create_res = client.create_model_run(project_id, payload)
    check_response(create_res, "creating model run")

    result = create_res.json()
    model_run_id = result.get("modelRunId", result)
    print(f"\nCreated model run: {model_run_id}")
    print(f"Public URL: {model_run_id}.modelrun.inference.cloud.ru")
