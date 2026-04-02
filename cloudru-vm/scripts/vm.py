#!/usr/bin/env python3
"""Cloud.ru VM CLI — create and manage virtual machines.

Usage:
    python vm.py <command> [options]

Commands:
    list            List virtual machines
    get             Get VM details
    create          Create a VM
    update          Update a VM
    delete          Delete a VM
    start           Start a VM
    stop            Stop a VM
    reboot          Reboot a VM
    vnc             Get remote console URL
    flavors         List available flavors (CPU/RAM configs)
    images          List available OS images
    subnets         List available subnets
    zones           List availability zones
    disk-types      List disk types
    security-groups List security groups
    disks           List disks
    disk-create     Create a disk
    disk-delete     Delete a disk
    disk-attach     Attach a disk to VM
    disk-detach     Detach a disk from VM
    task            Get async task status

Environment variables required:
    CP_CONSOLE_KEY_ID   — Cloud.ru service account key ID
    CP_CONSOLE_SECRET   — Cloud.ru service account secret
    PROJECT_ID          — Cloud.ru project UUID
"""

import argparse

from commands import COMMANDS


def build_parser():
    parser = argparse.ArgumentParser(
        description="Cloud.ru VM CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- VM commands ---

    p_list = subparsers.add_parser("list", help="List VMs")
    p_list.add_argument("--limit", type=int, help="Max results")
    p_list.add_argument("--offset", type=int, help="Offset")
    p_list.add_argument("--state", help="Filter by state (running, stopped, etc.)")

    p_get = subparsers.add_parser("get", help="Get VM details")
    p_get.add_argument("vm_id", help="VM UUID")

    p_create = subparsers.add_parser("create", help="Create a VM")
    p_create.add_argument("--name", required=True, help="VM name (alphanumeric, starts with letter)")
    p_create.add_argument("--flavor-name", help="Flavor name (e.g. m1.medium)")
    p_create.add_argument("--flavor-id", help="Flavor UUID")
    p_create.add_argument("--image-name", help="OS image name")
    p_create.add_argument("--image-id", help="OS image UUID")
    p_create.add_argument("--zone-name", help="Availability zone name")
    p_create.add_argument("--zone-id", help="Availability zone UUID")
    p_create.add_argument("--description", help="VM description")
    p_create.add_argument("--disk-name", help="Boot disk name (default: <vm-name>-boot)")
    p_create.add_argument("--disk-size", type=int, default=20, help="Boot disk size in GB (default: 20)")
    p_create.add_argument("--disk-type-name", help="Disk type name")
    p_create.add_argument("--disk-type-id", help="Disk type UUID")
    p_create.add_argument("--subnet-id", help="Subnet UUID")
    p_create.add_argument("--subnet-name", help="Subnet name")
    p_create.add_argument("--security-group-id", help="Security group UUID")
    p_create.add_argument("--login", help="VM user login (default: user1)")
    p_create.add_argument("--password", help="VM user password")
    p_create.add_argument("--cloud-init", help="Cloud-init script (inline)")
    p_create.add_argument("--cloud-init-file", help="Path to cloud-init file")

    p_update = subparsers.add_parser("update", help="Update a VM")
    p_update.add_argument("vm_id", help="VM UUID")
    p_update.add_argument("--name", help="New name")
    p_update.add_argument("--description", help="New description")
    p_update.add_argument("--flavor-name", help="New flavor name (requires stopped VM)")
    p_update.add_argument("--flavor-id", help="New flavor UUID (requires stopped VM)")

    p_delete = subparsers.add_parser("delete", help="Delete a VM")
    p_delete.add_argument("vm_id", help="VM UUID")

    p_start = subparsers.add_parser("start", help="Start a VM")
    p_start.add_argument("vm_id", help="VM UUID")

    p_stop = subparsers.add_parser("stop", help="Stop a VM")
    p_stop.add_argument("vm_id", help="VM UUID")

    p_reboot = subparsers.add_parser("reboot", help="Reboot a VM")
    p_reboot.add_argument("vm_id", help="VM UUID")

    p_vnc = subparsers.add_parser("vnc", help="Get remote console URL")
    p_vnc.add_argument("vm_id", help="VM UUID")
    p_vnc.add_argument("--protocol", choices=["vnc", "serial"], default="vnc", help="Console type")

    # --- Infrastructure commands ---

    p_flavors = subparsers.add_parser("flavors", help="List flavors")
    p_flavors.add_argument("--limit", type=int, help="Max results")
    p_flavors.add_argument("--cpu", type=int, help="Filter by CPU count")
    p_flavors.add_argument("--ram", type=int, help="Filter by RAM (GB)")
    p_flavors.add_argument("--name", help="Filter by name")

    p_images = subparsers.add_parser("images", help="List OS images")
    p_images.add_argument("--limit", type=int, help="Max results")
    p_images.add_argument("--name", help="Filter by name")

    p_subnets = subparsers.add_parser("subnets", help="List subnets")
    p_subnets.add_argument("--limit", type=int, help="Max results")

    subparsers.add_parser("zones", help="List availability zones")
    subparsers.add_parser("disk-types", help="List disk types")

    p_sg = subparsers.add_parser("security-groups", help="List security groups")
    p_sg.add_argument("--limit", type=int, help="Max results")

    # --- Disk commands ---

    p_disks = subparsers.add_parser("disks", help="List disks")
    p_disks.add_argument("--limit", type=int, help="Max results")

    p_dc = subparsers.add_parser("disk-create", help="Create a disk")
    p_dc.add_argument("--name", required=True, help="Disk name")
    p_dc.add_argument("--size", type=int, required=True, help="Size in GB")
    p_dc.add_argument("--zone-name", help="Availability zone name")
    p_dc.add_argument("--zone-id", help="Availability zone UUID")
    p_dc.add_argument("--disk-type-name", help="Disk type name")
    p_dc.add_argument("--disk-type-id", help="Disk type UUID")

    p_dd = subparsers.add_parser("disk-delete", help="Delete a disk")
    p_dd.add_argument("disk_id", help="Disk UUID")

    p_da = subparsers.add_parser("disk-attach", help="Attach disk to VM")
    p_da.add_argument("disk_id", help="Disk UUID")
    p_da.add_argument("--vm-id", required=True, help="VM UUID")

    p_dt = subparsers.add_parser("disk-detach", help="Detach disk from VM")
    p_dt.add_argument("disk_id", help="Disk UUID")
    p_dt.add_argument("--vm-id", required=True, help="VM UUID")

    # --- Task commands ---

    p_task = subparsers.add_parser("task", help="Get async task status")
    p_task.add_argument("task_id", help="Task UUID")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    COMMANDS[args.command](args)


if __name__ == "__main__":
    main()
