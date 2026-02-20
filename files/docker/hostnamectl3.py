#!/usr/bin/env python3

import sys
import argparse

def set_hostname(args):
    if args.static or args.pretty or args.transient:
        try:
            if args.static:
                with open("/etc/hostname", "w") as hostname_file:
                    hostname_file.write(args.hostname + "\n")
                print(f"Static hostname set to '{args.hostname}'")
            if args.pretty:
                print(f"Pretty hostname set to '{args.hostname}' (not persisted in this fake script)")
            if args.transient:
                print(f"Transient hostname set to '{args.hostname}' (not persisted in this fake script)")
        except PermissionError:
            print("Error: Permission denied. Please run as root.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Error: No hostname specified to set.")

def show_status(args):
    try:
        with open("/etc/hostname", "r") as hostname_file:
            static_hostname = hostname_file.read().strip()
        print(f"   Static hostname: {static_hostname}")
        print(f"   Pretty hostname: (not set in this fake script)")
        print(f"  Transient hostname: (not set in this fake script)")
    except FileNotFoundError:
        print("Error: /etc/hostname not found.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Fake hostnamectl script")
    parser.add_argument("--static", action="store_true", help="Set the static hostname")
    parser.add_argument("--transient", action="store_true", help="Set the transient hostname")
    parser.add_argument("--pretty", action="store_true", help="Set the pretty hostname")
    parser.add_argument("command", nargs="?", choices=[
        "status", "hostname", "set-hostname", "icon-name", "set-icon-name",
        "chassis", "set-chassis", "deployment", "set-deployment",
        "location", "set-location", "help"
    ], help="Command to execute")
    parser.add_argument("hostname", nargs="?", help="The hostname to set (if applicable)")

    args = parser.parse_args()

    # Map obsolete commands to modern equivalents
    if args.command in ["set-hostname", "set-icon-name", "set-chassis", "set-deployment", "set-location"]:
        args.command = args.command.replace("set-", "")
    elif args.command == "hostname":
        args.command = "set-hostname"

    if args.command == "status":
        show_status(args)
    elif args.command == "set-hostname":
        if args.hostname:
            set_hostname(args)
        else:
            print("Error: No hostname specified to set.")
    elif args.command in ["icon-name", "chassis", "deployment", "location"]:
        print(f"{args.command.capitalize()} set to '{args.hostname}' (not persisted in this fake script)")
    elif args.command == "help":
        parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
