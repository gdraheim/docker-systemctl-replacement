#! /usr/bin/env python3
# pylint: disable=too-many-lines,line-too-long,too-many-branches,too-many-statements,too-many-public-methods,too-many-nested-blocks,too-many-locals,too-many-return-statements,too-many-instance-attributes,too-few-public-methods,too-many-arguments,too-many-positional-arguments,multiple-statements
# pylint: disable=missing-function-docstring,missing-class-docstring,consider-using-f-string,consider-using-ternary,import-outside-toplevel
# pylint: disable=no-else-return,no-else-break,unspecified-encoding,unnecessary-lambda,unnecessary-comprehension,use-yield-from,superfluous-parens
# pylint: disable=fixme,redefined-argument-from-local,chained-comparison,consider-using-in,consider-using-with.consider-using-min-builtin,consider-using-max-builtin,consider-using-get
# pylint: disable=invalid-name,redefined-outer-name,possibly-unused-variable,unnecessary-negation,unused-argument,consider-using-dict-items,consider-using-enumerate
# pylint: disable=unused-variable,protected-access
""" helper tool to find meta-information about systemctl units and docker images """

from fnmatch import fnmatchcase as fnmatch
from csv import DictWriter
import sys
import os.path as fs
import subprocess as pc

import logging
logg: logging.Logger = logging.getLogger("systemctl")
TRACE = (logging.DEBUG + logging.NOTSET) // 2
HINT = (logging.DEBUG + logging.INFO) // 2
NOTE = (logging.WARNING + logging.INFO) // 2
DONE = (logging.WARNING + logging.ERROR) // 2
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(HINT, "HINT")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(DONE, "DONE")

NEVER = False
TRUE = True
NIX = ""
ALL = "*"

RPM_QUERY = "/usr/bin/rpm"
DEB_QUERY = "/usr/bin/dpkg-query"

def whatprovides(filename):
    if not filename:
        return NIX
    if fs.exists(RPM_QUERY):
        run = pc.run([RPM_QUERY, "-q", "--whatprovides", filename], stdout=pc.PIPE, check=False)
        if run:
            return run.stdout.decode("utf-8").strip()
    elif fs.exists(DEB_QUERY):
        run = pc.run([DEB_QUERY, "-S", filename], stdout=pc.PIPE, check=False)
        if run.returncode:
            filename = filename.replace("/usr/lib/systemd/", "/lib/systemd/")
            run = pc.run([DEB_QUERY, "-S", filename], stdout=pc.PIPE, check=False)
        if b":" in run.stdout:
            packages, fileref = run.stdout.split(b":", 1)
            if b"," in packages:
                package, others = packages.split(b",", 1)
            else:
                package = packages
            fullpackage = pc.run([DEB_QUERY, "--show", package.decode('utf-8')], stdout=pc.PIPE, check=False)
            val = fullpackage.stdout.decode("utf-8").replace("\t", "-")
            if val:
                return val.strip()
    return NIX

def installed():
    if fs.exists("/usr/bin/rpm"):
        run = pc.run(["/usr/bin/rpm", "-qa"], stdout=pc.PIPE, check=False)
        return run.stdout.decode("utf-8")
    elif fs.exists("/usr/bin/dpkg-query"):
        run = pc.run(["/usr/bin/dpkg-query", "-l"], stdout=pc.PIPE, check=False)
        return run.stdout.decode("utf-8")
    else:
        logg.error("unknown package manager")
        run = None
    return NIX

def main() -> int:
    # pylint: disable=global-statement
    import optparse # pylint: disable=deprecated-module # not anymore
    cmdline = optparse.OptionParser("%prog [options] command [unit...]", description=__doc__.strip())
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="..more logger infos")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="..less logger infos")
    cmdline.add_option("-o", metavar="[file.]tab", help="format output table", default="tab")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = max(0, logging.ERROR - 10 * opt.verbose))
    if not cmdline_args:
        cmdline_args = ["list"]
    cmd, args = cmdline_args[0], cmdline_args[1:]
    output = opt.o
    hdr = []
    dat = []
    if cmd in ["list", "installed"]:
        packages = installed()
        if packages:
            for out_line in packages.splitlines():
                line = out_line.strip()
                if args:
                    for arg in args:
                        if fnmatch(line, arg):
                            dat.append({"package": line})
                            break
                else:
                    dat.append({"package": line})
        hdr=["package"]
    elif cmd in ["for","file", "whatprovides"]:
        for filename in args:
            val = whatprovides(filename)
            dat.append({"package": val, "file": filename})
        hdr = ["package", "file"]
    elif cmd in ["default-services"]:
        from systemctl3 import Systemctl
        systemctl = Systemctl()
        enabled = systemctl.target_default_services()
        for unit in enabled:
            filename = systemctl.unit_property(unit, "path")
            package = whatprovides(filename)
            dat.append({"package": package, "service": unit})
        hdr = ["service", "package"]
    out = open(output, "w", encoding=("utf-8")) if "." in output else sys.stdout
    fmt = output.rsplit(".", 1)[1] if "." in output else output
    delimiters = {"csv": ",", "zsv": ";", "tsv": "\t", "dat": "|", "data": "|"}
    tab= DictWriter(out, fieldnames=hdr, delimiter=delimiters[fmt] if fmt in delimiters else '\t')
    if fmt in ["csv", "zsv", "tsv", "dat"]:
        tab.writeheader()
    for row in dat:
        tab.writerow(row)

if __name__ == "__main__":
    main()
