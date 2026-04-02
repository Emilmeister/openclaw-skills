"""Command registry for Cloud.ru VM CLI."""

from commands.vm import cmd_list, cmd_get, cmd_create, cmd_update, cmd_delete, cmd_start, cmd_stop, cmd_reboot, cmd_vnc
from commands.infra import cmd_flavors, cmd_images, cmd_subnets, cmd_zones, cmd_disk_types, cmd_security_groups
from commands.disks import cmd_disks, cmd_disk_create, cmd_disk_delete, cmd_disk_attach, cmd_disk_detach
from commands.tasks import cmd_task

COMMANDS = {
    "list": cmd_list,
    "get": cmd_get,
    "create": cmd_create,
    "update": cmd_update,
    "delete": cmd_delete,
    "start": cmd_start,
    "stop": cmd_stop,
    "reboot": cmd_reboot,
    "vnc": cmd_vnc,
    "flavors": cmd_flavors,
    "images": cmd_images,
    "subnets": cmd_subnets,
    "zones": cmd_zones,
    "disk-types": cmd_disk_types,
    "security-groups": cmd_security_groups,
    "disks": cmd_disks,
    "disk-create": cmd_disk_create,
    "disk-delete": cmd_disk_delete,
    "disk-attach": cmd_disk_attach,
    "disk-detach": cmd_disk_detach,
    "task": cmd_task,
}
