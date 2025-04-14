#! /usr/bin/env python3
# pylint: disable=line-too-long,missing-function-docstring,missing-module-docstring
# type: ignore

import argparse
import sys
import logging


try:
    from . import systemctl3
except ImportError:
    import systemctl3

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--unit', metavar='unit', type=str, required=True, help='Systemd unit to display')
    parser.add_argument('-f', '--follow', default=False, action='store_true', help='Follows the log')
    parser.add_argument('-n', '--lines', metavar='num', type=int, help='Num of lines to display')
    parser.add_argument('--no-pager', default=False, action='store_true', help='Do not pipe through a pager')
    parser.add_argument('--system', default=False, action='store_true', help='Show system units')
    parser.add_argument('--user', default=False, action='store_true', help='Show user units')
    parser.add_argument('--root', metavar='path', type=str, help='Use subdirectory path')
    parser.add_argument('-x', default=False, action='store_true', help='Switch on verbose mode')
    args = parser.parse_args()

    if args.follow:
        systemctl3.DO_FORCE = True
    if args.lines:
        systemctl3.LOG_LINES = args.lines
    if args.no_pager:
        systemctl3.NO_PAGER = True
    if args.system:
        systemctl3.USER_MODE = False
    elif args.user:
        systemctl3.USER_MODE = True
    if args.root:
        systemctl3.ROOT = args.root
    if args.x:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.WARNING)

    return systemctl3.runcommand("log", args.unit)

sys.exit(main())
