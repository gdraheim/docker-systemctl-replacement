#! /usr/bin/env python3
# pylint: disable=line-too-long,bare-except,dangerous-default-value
""" build images using the local docker_mirror.py repo packages. """
from typing import List, Union, Optional, Mapping
from datetime import datetime as Time
import os.path
import sys
import subprocess
import logging
logg = logging.getLogger("local" if __name__ == "___main__" else __name__)

__copyright__ = "(C) 2025 Guido Draheim"
__contact__ = "https://github.com/gdraheim/docker-mirror-packages-repo"
__license__ = "CC0 Creative Commons Zero (Public Domain)"
__version__ = "1.7.7101"

# generalized from the testsuite.py in the docker-systemctl-replacement project

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")

NIX = ""
SKIP = True
DOCKER = "docker"
PYTHON = "/usr/bin/python3"
SAVETO = "localhost:5000/testing"
CONTAINER="into-"
RUNUSER=NIX
RUNEXE=NIX
RUNCMD=NIX
TIMEOUT = 999
_TAG="test_" + Time.now().strftime("%y%m%d%H%M")
_FROM="ubuntu:24.04"
INTO=os.environ.get("DOCKER_LOCAL_IMAGE_INTO", os.environ.get("DOCKER_LOCAL_IMAGE_TAG", _TAG))
BASE=os.environ.get("DOCKER_LOCAL_IMAGE_BASE", os.environ.get("DOCKER_LOCAL_IMAGE_FROM", _FROM))

def decodes(text: Union[str, bytes, None]) -> str:
    if text is None: return ""
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def sh____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> str:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    if err:
        logg.info("ERR %s", err)
    return decodes(out).rstrip()
def q_str(part: Union[str, int, None]) -> str:
    if part is None:
        return ""
    if isinstance(part, int):
        return str(part)
    return "'%s'" % part  # pylint: disable=consider-using-f-string

def package_tool(distro: str = NIX):
    if "centos" in distro or "almalinux" in distro or "rhel" in distro:
        return "yum --setopt=repo_gpgcheck=false"
    if "opensuse" in distro:
        return "zypper --no-gpg-checks --no-refresh"
    return "apt-get -o Acquire::AllowInsecureRepositories=true"
def package_refresh(distro: str = NIX):
    if "opensuse" in distro:
        return "zypper --no-gpg-checks refresh"
    return "apt-get -o Acquire::AllowInsecureRepositories=true update"
def package_search(distro: str = NIX):
    if "opensuse" in distro:
        return "zypper --no-refresh search"
    return "apt-cache search"

def docker_local_build(cmd2: List[str] = []) -> int:
    """" cmd2 should be given as pairs (cmd,arg) but some items are recognized by their format directly"""
    prefixes = ["FROM","from", "INTO", "into", "TAG", "tag", "COPY", "copy", "SAVE", "save", "INSTALL", "install","USER", "user","TEST", "test", "SYMLINK", "symlink"]
    mirror = _mirror
    docker = DOCKER
    tagging: str = INTO
    building: str = BASE
    timeout: int = TIMEOUT
    into: str = NIX
    runuser = RUNUSER
    runexe = RUNEXE
    runcmd = RUNCMD
    cmd: str = NIX
    search = NIX
    refresh = NIX
    distro = NIX
    package = NIX
    for ncmd in cmd2:
        arg = NIX
        if not cmd:
            if ncmd in prefixes:
                cmd = ncmd
                continue
            logg.debug("ARG %s not in %s", ncmd, prefixes)
            for prefix in prefixes:
                if ncmd.startswith(prefix + " "):
                    cmd, arg = ncmd.split(" ", 1)
                    break
            if not cmd and "@" in ncmd:
                cmd = "INSTALL"
            if not cmd and ncmd.startswith(":"):
                cmd = "MAKE"
            if not cmd:
                logg.warning("did not find a command in %s", ncmd)
                continue
        if arg is NIX:
            arg = ncmd
        if arg:
            logg.debug("CMD=%s ARG=%s", cmd, arg)
            if cmd in  ["FROM","from"]:
                building = arg
                cmd = NIX
                continue
            if cmd in  ["INTO","into","TAG","tag"]:
                if into:
                    runcmds = runexe.split(" ") + runcmd.split(" ") if runexe else runcmd.split(" ")
                    runs = F"-c 'USER {runuser}'" if runuser else NIX
                    cmds = F"-c 'CMD {runcmds}'" if runcmd else NIX
                    sx____(F"{docker} rmi {tagging}")
                    sx____(F"{docker} stop {into}")
                    sh____(F"{docker} commit {cmds} {runs} {into} {tagging}")
                    sh____(F"{docker} rm -f {into}")
                    into = NIX
                tagging = arg
                into = CONTAINER+os.path.basename(tagging).replace(":","-").replace(".","-")
                distro = output(F"{mirror} detect {building}")
                addhosts = output(F"{mirror} start {distro} --add-hosts --no-detect")
                sh____(F"{docker} rm -f {into}")
                sh____(F"{docker} run -d --name={into} --rm=true {addhosts} {building} sleep {timeout}")
                cmd = NIX
                continue
            if cmd in  ["EXE", "exe"]:
                runexe = arg
                cmd = NIX
                continue
            if cmd in  ["CMD", "cmd"]:
                runcmd = arg
                cmd = NIX
                continue
            if cmd in  ["USER", "user"]:
                runuser = arg
                continue
            if cmd in  ["SEARCH", "SEARCH"]:
                if not refresh:
                    refresh = package_refresh(distro)
                    if refresh:
                        sx____(F"{docker} exec {into} {refresh}")
                search = package_search(distro)
                pack = arg
                sx____(F"{docker} exec {into} {search} {pack}")
                cmd = NIX
                continue
            if cmd in  ["INSTALL", "install"]:
                logg.debug("install %s", arg)
                if not refresh:
                    refresh = package_refresh(distro)
                    logg.debug("install %s", refresh)
                    if refresh:
                        sx____(F"{docker} exec {into} {refresh}")
                if "@" in arg:
                    test, pack = arg.split("@", 1)
                else:
                    test, pack = NIX, arg
                package = package_tool(distro)
                logg.debug("TEST %s PACK %s FROM %s", test, pack, arg)
                if test:
                    sx____(F"{docker} exec {into} bash -c 'test -f {test} || {package} install -y {pack}'")
                else:
                    sx____(F"{docker} exec {into} {package} install -y {pack}")
                cmd = NIX
                continue
            if cmd in  ["MAKE", "MAKE"]:
                if arg.startswith(":"):
                    dst = arg[1:]
                else:
                    dst = arg
                if dst.endswith("/"):
                    sx____(F"{docker} exec {into} mkdir -p {dst}")
                else:
                    if "/" in dst:
                        dstdir = os.path.dirname(dst)
                        sx____(F"{docker} exec {into} mkdir -p {dstdir}")
                    sx____(F"{docker} exec {into} touch {dst}")
                cmd = NIX
                continue
            if cmd in  ["COPY", "copy"]:
                if ":" in arg:
                    src, dst = arg.split(":", 1)
                else:
                    src, dst = arg, NIX
                sx____(F"{docker} copy {src} {into}:{dst}")
                cmd = NIX
                continue
            if cmd in  ["SAVE", "save"]:
                if ":" in arg:
                    src, dst = arg.split(":", 1)
                else:
                    src, dst = arg, "./"
                sx____(F"{docker} copy {into}:{src} {dst}")
                cmd = NIX
                continue
            if cmd in  ["SYMLINK", "symlink"]:
                if ":" in arg:
                    src, dst = arg.split(":", 1)
                else:
                    src, dst = arg, "/tmp"
                if "/" not in dst and "/" in src:
                    srcdir=os.path.dirname(src)
                    srcname=os.path.basename(src)
                    sx____(F"{docker} exec {into} ln -s {srcname} {srcdir}/{dst}")
                else:
                    sx____(F"{docker} exec {into} ln -s {src} {dst}")
                cmd = NIX
                continue
            if cmd in  ["TEST", "test"]:
                if arg.startswith(":"):
                    dst = arg[1:]
                    sh____(F"{docker} exec {into} wc -l {dst}")
                else:
                    dst = arg
                    sh____(F"{docker} exec {into} {dst}")
                cmd = NIX
                continue
            if cmd in ["COMMIT", "commit"]:
                if into:
                    runcmds = runexe.split(" ") + runcmd.split(" ") if runexe else runcmd.split(" ")
                    runs = F"-c 'USER {runuser}'" if runuser else NIX
                    cmds = F"-c 'CMD {runcmds}'" if runcmd else NIX
                    sx____(F"{docker} rmi {tagging}")
                    sh____(F"{docker} commit {cmds} {runs} {into} {tagging}")
                    sh____(F"{docker} rm -f {into}")
                    into = NIX
                cmd = NIX
                continue
            logg.error("unknown cmd %s", cmd)
            cmd = NIX
            continue
        else:
            cmd = NIX
            logg.error("cmd %s no arg %s", cmd, arg)
    if into:
        runcmds = runexe.split(" ") + runcmd.split(" ") if runexe else runcmd.split(" ")
        runs = "-c 'USER {runuser}'" if runuser else NIX
        cmds = "-c 'CMD {runcmds}'" if runcmd else NIX
        sx____(F"{docker} rmi {tagging}")
        sh____(F"{docker} commit {cmds} {runs} {into} {tagging}")
        sh____(F"{docker} rm -f {into}")
        into = NIX
    addhosts = output(F"{mirror} stop {distro} --add-hosts --no-detect")
    return 0

if __name__ == "__main__":
    from optparse import OptionParser  # pylint: disable=deprecated-module
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("-D", "--docker", metavar="EXE", default=DOCKER,
                  help="use another docker container tool [%default]")
    _o.add_option("-p", "--python", metavar="EXE", default=PYTHON,
                  help="use another python execution engine [%default]")
    _o.add_option("-C", "--chdir", metavar="PATH", default="",
                  help="change directory before building {%default}")
    _o.add_option("-b", "--base", "--from", metavar="NAME", default=BASE,
                  help="FROM=%default (or CENTOS)")
    _o.add_option("-t", "--into", "--tag", metavar="NAME", default=INTO,
                  help="TAG=%default (")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 10)
    DOCKER=opt.docker
    PYTHON=opt.python
    BSAE=opt.base
    INTO=opt.into
    CHDIR=opt.chdir
    sys.exit(docker_local_build(args))
