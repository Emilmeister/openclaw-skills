"""VM CRUD and power commands."""

import json
import subprocess
import sys

from helpers import build_client, check_response, print_json


def cmd_list(args):
    client, project_id = build_client()
    params = {}
    if args.limit:
        params["limit"] = args.limit
    if args.offset:
        params["offset"] = args.offset
    if args.state:
        params["state"] = args.state
    res = client.list_vms(project_id, **params)
    check_response(res, "listing VMs")
    data = res.json()
    print(f"Total: {data.get('total', '?')}")
    for vm in data.get("items", []):
        flavor = vm.get("flavor", {})
        image = vm.get("image", {})
        print(
            f"  {vm['id']} | {vm['name']:<30} | {vm.get('state', '?'):<12} "
            f"| {flavor.get('name', '?')} ({flavor.get('cpu', '?')}cpu/{flavor.get('ram', '?')}GB) "
            f"| {image.get('name', '?')}"
        )


def cmd_get(args):
    client, _ = build_client()
    res = client.get_vm(args.vm_id)
    check_response(res, "getting VM")
    print_json(res.json())


def cmd_create(args):
    client, project_id = build_client()

    payload = {
        "project_id": project_id,
        "name": args.name,
    }

    if args.flavor_name:
        payload["flavor_name"] = args.flavor_name
    elif args.flavor_id:
        payload["flavor_id"] = args.flavor_id

    if args.image_name:
        payload["image_name"] = args.image_name
    elif args.image_id:
        payload["image_id"] = args.image_id

    if args.zone_name:
        payload["availability_zone_name"] = args.zone_name
    elif args.zone_id:
        payload["availability_zone_id"] = args.zone_id

    if args.description:
        payload["description"] = args.description

    if args.cloud_init:
        payload["cloud_init"] = args.cloud_init
    elif args.cloud_init_file:
        with open(args.cloud_init_file) as f:
            payload["cloud_init"] = f.read()

    # Disks — at least one boot disk required
    disks = []
    disk_name = args.disk_name or f"{args.name}-boot"
    disk_size = args.disk_size or 20
    disk_item = {"name": disk_name, "size": disk_size}
    if args.disk_type_name:
        disk_item["disk_type_name"] = args.disk_type_name
    elif args.disk_type_id:
        disk_item["disk_type_id"] = args.disk_type_id
    disks.append(disk_item)
    payload["disks"] = disks

    # Interfaces
    if args.subnet_id:
        payload["interfaces"] = [{"subnet_id": args.subnet_id}]
    elif args.subnet_name:
        payload["interfaces"] = [{"subnet_name": args.subnet_name}]

    if args.security_group_id:
        if "interfaces" in payload:
            payload["interfaces"][0]["security_groups"] = [{"id": args.security_group_id}]

    # Image metadata (login, password/ssh-key, hostname)
    if args.login or args.password or args.ssh_key or args.ssh_key_file:
        image_meta = {}
        image_meta["name"] = args.login or "user1"
        image_meta["hostname"] = args.name
        # Auth: SSH key or password (one is required)
        ssh_key = None
        if args.ssh_key:
            ssh_key = args.ssh_key
        elif args.ssh_key_file:
            with open(args.ssh_key_file) as f:
                ssh_key = f.read().strip()
        if ssh_key:
            image_meta["public_key"] = ssh_key
        elif args.password:
            image_meta["linux_password"] = args.password
        payload["image_metadata"] = image_meta

    res = client.create_vm(payload)
    check_response(res, "creating VM")
    data = res.json()
    # v1.1 returns array
    if isinstance(data, list):
        for vm in data:
            print(f"Created VM: {vm.get('id', vm)}")
            task_id = vm.get("task_id")
            if task_id:
                print(f"Task ID: {task_id} (track with: vm.py task {task_id})")
    else:
        print(f"Created VM: {data.get('id', data)}")


def cmd_update(args):
    client, _ = build_client()
    payload = {}
    if args.name:
        payload["name"] = args.name
    if args.description is not None:
        payload["description"] = args.description
    if args.flavor_name:
        payload["flavor_name"] = args.flavor_name
    elif args.flavor_id:
        payload["flavor_id"] = args.flavor_id

    res = client.update_vm(args.vm_id, payload)
    check_response(res, "updating VM")
    print("Updated successfully")


def cmd_delete(args):
    client, _ = build_client()
    res = client.delete_vm(args.vm_id)
    check_response(res, "deleting VM")
    print("Deleted successfully")


def cmd_start(args):
    client, _ = build_client()
    res = client.set_power(args.vm_id, "power_on")
    check_response(res, "starting VM")
    print("Start initiated")


def cmd_stop(args):
    client, _ = build_client()
    res = client.set_power(args.vm_id, "power_off")
    check_response(res, "stopping VM")
    print("Stop initiated")


def cmd_reboot(args):
    client, _ = build_client()
    res = client.set_power(args.vm_id, "reboot")
    check_response(res, "rebooting VM")
    print("Reboot initiated")


def cmd_vnc(args):
    client, _ = build_client()
    res = client.remote_console(args.vm_id, protocol=args.protocol or "vnc")
    check_response(res, "getting console URL")
    data = res.json()
    print(f"Console URL: {data.get('url', data)}")


def _resolve_vm_ip(args):
    """Get the public (floating) or private IP of a VM."""
    client, _ = build_client()
    res = client.get_vm(args.vm_id)
    check_response(res, "getting VM")
    vm = res.json()

    # Prefer floating IP (public), fall back to private
    for iface in vm.get("interfaces", []):
        fip = iface.get("floating_ip")
        if fip and fip.get("ip_address"):
            return fip["ip_address"]

    # No floating IP — use private IP
    for iface in vm.get("interfaces", []):
        ip = iface.get("ip_address")
        if ip:
            return ip

    print("Error: VM has no IP address", file=sys.stderr)
    sys.exit(1)


def cmd_ssh(args):
    """Execute a command on VM via SSH."""
    if args.ip:
        host = args.ip
    else:
        host = _resolve_vm_ip(args)

    user = args.login or "user1"

    ssh_cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
    ]

    if args.key_file:
        ssh_cmd += ["-i", args.key_file]

    ssh_cmd.append(f"{user}@{host}")

    if args.remote_cmd:
        ssh_cmd.append(args.remote_cmd)
        result = subprocess.run(ssh_cmd, capture_output=False)
        sys.exit(result.returncode)
    else:
        # Interactive — just exec ssh
        import os
        os.execvp("ssh", ssh_cmd)


def cmd_scp(args):
    """Copy files to/from VM via SCP."""
    if args.ip:
        host = args.ip
    else:
        host = _resolve_vm_ip(args)

    user = args.login or "user1"

    scp_cmd = [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
    ]

    if args.key_file:
        scp_cmd += ["-i", args.key_file]

    if args.recursive:
        scp_cmd.append("-r")

    # Determine direction: upload (local -> remote) or download (remote -> local)
    remote_prefix = f"{user}@{host}:"
    if args.direction == "upload":
        scp_cmd += [args.local_path, f"{remote_prefix}{args.remote_path}"]
    else:
        scp_cmd += [f"{remote_prefix}{args.remote_path}", args.local_path]

    result = subprocess.run(scp_cmd, capture_output=False)
    sys.exit(result.returncode)
