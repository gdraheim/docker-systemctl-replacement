#!/usr/bin/env python3

import argparse
import os
import sys

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

systemctl_py = "systemctl3.py"
path = os.path.dirname(sys.argv[0])
systemctl = os.path.join(path, systemctl_py)

cmd = [ systemctl, "log", args.unit ] # drops the -u
if args.follow: cmd += [ "-f" ]
if args.lines: cmd += [ "-n", str(args.lines) ]
if args.no_pager: cmd += [ "--no-pager" ]
if args.system: cmd += [ "--system" ]
elif args.user: cmd += [ "--user" ]
if args.root: cmd += [ "--root", start(args.root) ]
if args.x: cmd += [ "-vvv" ]

os.execvp(cmd[0], cmd)
