# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""``rotatorctl list/get/set/dump/restore`` on the console library."""

from __future__ import annotations

import argparse
import sys

from rotatorctl.discovery import browse_mdns, merge_controllers, scan_usb
from rotatorctl.protocol import CommandError, ConsoleClient
from rotatorctl.transport import TransportError, open_target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rotatorctl")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Discover controllers on USB and mDNS")
    p_list.add_argument("--timeout", type=float, default=1.0)

    def add_target(command: argparse.ArgumentParser) -> None:
        command.add_argument("--target", required=True, help="tcp://host:port or serial://path")

    p_get = sub.add_parser("get", help="Print one setting")
    add_target(p_get)
    p_get.add_argument("name")

    p_set = sub.add_parser("set", help="Set one setting in RAM")
    add_target(p_set)
    p_set.add_argument("name")
    p_set.add_argument("value")

    p_dump = sub.add_parser("dump", help="Print the settings file")
    add_target(p_dump)

    p_restore = sub.add_parser("restore", help="Restore a settings file")
    add_target(p_restore)
    p_restore.add_argument("file")

    p_save = sub.add_parser("save", help="Write RAM settings to flash")
    add_target(p_save)

    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (CommandError, TransportError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _run(args: argparse.Namespace) -> int:
    if args.command == "list":
        found = scan_usb()
        try:
            found.extend(browse_mdns(args.timeout))
        except OSError as exc:
            print(f"mdns: {exc}", file=sys.stderr)
        rows = merge_controllers(found)
        if not rows:
            print("no controllers")
            return 0
        for info in rows:
            links = ",".join(endpoint.target for endpoint in info.endpoints)
            print(f"{info.serial or '-'}\t{info.name or '-'}\t{links}")
        return 0

    client = ConsoleClient(open_target(args.target))
    try:
        if args.command == "get":
            print(client.get(args.name))
        elif args.command == "set":
            client.set(args.name, args.value)
            print("OK")
        elif args.command == "dump":
            sys.stdout.write(client.dump_text())
        elif args.command == "restore":
            text = open(args.file, encoding="utf-8").read()
            client.restore_text(text)
            print("OK")
        elif args.command == "save":
            client.save()
            print("OK")
        else:
            raise ValueError(args.command)
    finally:
        client.close()
    return 0
