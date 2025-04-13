#! /usr/bin/env python3
""" Testcases for docker-systemctl-replacement functionality """

# pylint: disable=line-too-long,too-many-lines,too-many-locals,too-many-statements,too-many-branches,too-many-arguments,too-many-positional-arguments,too-many-return-statements,too-many-nested-blocks,too-many-public-methods
# pylint: disable=bare-except,broad-exception-caught,pointless-statement,multiple-statements,f-string-without-interpolation,import-outside-toplevel,no-else-return
# pylint: disable=missing-function-docstring,unused-variable,unused-argument,unspecified-encoding,redefined-outer-name,using-constant-test,invalid-name
# pylint: disable=fixme,consider-using-with,consider-using-get,condition-evals-to-constant,chained-comparison
__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.0.1144"

from typing import List, Tuple, Generator, Iterator, Union, Optional, TextIO, Mapping

import subprocess
import os
import os.path
import time
import errno
import datetime
import unittest
import shutil
import inspect
import string
import random
import logging
import re
import sys
import collections
import signal
import shlex
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json

string_types = (str, bytes)

logg = logging.getLogger("TESTING")
_sed = "sed"
_docker = "docker"
_python = "/usr/bin/python3"
_python2 = "/usr/bin/python"
_systemctl_py = "src/systemctl3.py"
_bin_sleep="/bin/sleep"
COVERAGE = "" # make it an image name = detect_local_system()
SKIP = True
TODO = False
KEEP = 0
LONGER = 2
KILLWAIT = 20

TESTING_LISTEN = False
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

CENTOSVER = {"7.3": "7.3.1611", "7.4": "7.4.1708", "7.5": "7.5.1804", "7.6": "7.6.1810", "7.7": "7.7.1908", "7.9": "7.9.2009", "8.0": "8.0.1905", "8.1": "8.1.1911", "8.3": "8.3.2011"}
TESTED_OS = ["centos:7.3.1611", "centos:7.4.1708", "centos:7.5.1804", "centos:7.6.1810", "centos:7.7.1908", "centos:7.9.2009", "centos:8.0.1905", "centos:8.1.1911", "centos:8.3.2011"]
TESTED_OS += ["almalinux:9.1", "centos:7.5", "almalinux:9.3", "almalinux:9.4"]
TESTED_OS += ["opensuse:42.2", "opensuse:42.3", "opensuse/leap:15.0", "opensuse/leap:15.1", "opensuse/leap:15.2", "opensuse/leap:15.5", "opensuse/leap:15.6"]
TESTED_OS += ["ubuntu:14.04", "ubuntu:16.04", "ubuntu:18.04", "ubuntu:22.04", "ubuntu:24.04"]

SAVETO = "localhost:5000/systemctl"
IMAGES = "localhost:5000/systemctl/testing"
IMAGE = ""
LOCAL = 0
CENTOS = "almalinux:9.4"
UBUNTU = "ubuntu:24.04"
OPENSUSE = "opensuse/leap:15.6"
IMAGEDEF = OPENSUSE # was CENTOS but almalinux does not have python2 anymore
SOMETIME = ""

QUICK = "-c MAXTIMEOUT=9"
DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")

realpath = os.path.realpath

_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"

def _recent(top_list: Union[str, List[str]]) -> str:
    result = []
    for line in lines4(top_list):
        if "[kworker" in line: continue
        if " containerd-shim " in line: continue
        if " mplayer " in line: continue
        if " chrome " in line: continue
        if "/chrome" in line: continue
        if "/testsuite" in line: continue
        if "/xfce4" in line: continue
        if "/pulse" in line: continue
        if "/gvfs/" in line: continue
        if "/dbus-daemon" in line: continue
        if "/ibus/" in line: continue
        if "/lib/tracker" in line: continue
        if "/lib/gnome" in line: continue
        if "/lib/gdm" in line: continue
        if "signal-desktop/signal-desktop" in line: continue
        if "teams/teams" in line: continue
        if "slack/slack" in line: continue
        if "bin/telegram" in line: continue
        if "bin/nextcloud" in line: continue
        if _top_list in line: continue
        if " 1 [" in line: continue
        if " 2 [" in line: continue
        # matching on ELAPSED TIME up to 4 minutes
        if re.search("^\\s*[0]*[0123]:[0-9]*\\s", line):
            result.append(" "+line)
        if " ELAPSED " in line:
            result.append(" "+line)
    return "\n".join(result)

def reply_tool() -> str:
    here = os.path.abspath(os.path.dirname(sys.argv[0]))
    return os.path.join(here, "reply.py")

def package_tool(image: str, checks: bool = False) -> str:
    if "opensuse" in image:
        if not checks:
            # --gpgcheck-strict / --no-gpg-checks
            # --gpgcheck-allow-unsigned( --gpgcheck-allow-unsigned-repo --gpgcheck-allow-unsigned-package)
            # return "zypper --gpgcheck-allow-unsigned-repo"
            return "zypper"
        return "zypper"
    if "ubuntu" in image:
        # sources.list:
        # deb [ allow-insecure=yes ] # disables but keeps warning
        # deb [ trusted=yes ] # disables GPG
        # --allow-unauthenticated
        # -o APT::Get::AllowUnauthenticated=true
        # -o Acquire::Check-Valid-Until=false
        # -o APT::Ignore::gpg-pubkey
        # -o Acquire::AllowInsecureRepositories=true
        # -o Acquire::AllowDowngradeToInsecureRepositories=true
        if not checks:
            return "apt-get -o Acquire::AllowInsecureRepositories=true"
        return "apt-get"
    if not checks:
        return "yum --setopt=repo_gpgcheck=false"
    return "yum"
def refresh_tool(image: str, checks: bool = False) -> str:
    # https://github.com/openSUSE/docker-containers/issues/64
    #  {package} rr oss-update"
    #  {package} ar -f http://download.opensuse.org/update/leap/42.3/oss/openSUSE:Leap:42.3:Update.repo"
    if "opensuse:42.3" in image:
        cmds = [
            "zypper mr --no-gpgcheck oss-update",
            "zypper refresh"]
        return "bash -c '%s'" % (" && ".join(cmds))  # pylint: disable=consider-using-f-string
    if "opensuse/leap:15." in image:
        cmds = [
            "zypper mr --no-gpgcheck --all",
            "zypper refresh"]
        return "bash -c '%s'" % (" && ".join(cmds))  # pylint: disable=consider-using-f-string
    if "opensuse" in image:
        return "zypper refresh"
    if "ubuntu" in image:
        if not checks:
            return "apt-get -o Acquire::AllowInsecureRepositories=true update"
        return "apt-get update"
    if "almalinux" in image:
        cmds = ["echo sslverify=false >> /etc/yum.conf"]
        return "bash -c '%s'" % (" && ".join(cmds))  # pylint: disable=consider-using-f-string
    return "true"
def python_package(python: str, image: Optional[str] = None) -> str:
    package = os.path.basename(python)
    if "python2" in package:
        if image and "centos:8" in image:
            return package
        if image and "almalinux:9" in image:
            return package
        if image and "ubuntu:2" in image:
            return package
        return package.replace("python2", "python")
    return package.replace(".", "") # python3.11 => python311
def coverage_tool(image: Optional[str] = None, python: Optional[str] = None) -> str:
    image = image or IMAGE
    python = python or _python
    if python.endswith("3"):
        return python + " -m coverage"
    else:
        if image and "centos:8" in image:
            return "coverage-2"
    return "coverage2"
def coverage_run(image: Optional[str] = None, python: Optional[str] = None, append: Optional[str] = None) -> str:
    append = append or "--append"
    options = " run '--omit=*/six.py,*/extern/*.py,*/unitconfparser.py' " + append
    return coverage_tool(image, python) + options + " -- "
def coverage_package(image: Optional[str] = None, python: Optional[str] = None) -> str:
    python = python or _python
    package = "python-coverage"
    if python.endswith("3"):
        package = "python3-coverage"
        if image and "centos:8" in image:
            package = "platform-python-coverage"
    else:
        if image and "centos:8" in image:
            package = "python2-coverage"
    logg.info("detect coverage_package for %s => %s (%s)", python, package, image)
    return package
def cover(image: Optional[str] = None, python: Optional[str] = None, append: Optional[str] = None) -> str:
    if not COVERAGE: return ""
    return coverage_run(image, python, append)

def q_str(part: Union[str, int, None]) -> str:
    if part is None:
        return ""
    if isinstance(part, int):
        return str(part)
    return "'%s'" % part  # pylint: disable=consider-using-f-string
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
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> str:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out)
def output2(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> Tuple[str, int]:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> Tuple[str, str, int]:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode

BackgroundProcess = collections.namedtuple("BackgroundProcess", ["pid", "run", "log"])
def background(cmd: str, shell: bool = True) -> BackgroundProcess:
    log = open(os.devnull, "wb")
    exe = list(shlex.split(cmd))
    run = subprocess.Popen(exe, stdout=log, stderr=log)
    pid = run.pid
    logg.info("PID %s = %s", pid, cmd)
    return BackgroundProcess(pid, run, log)

def reads(filename: str) -> str:
    return decodes(open(filename, "rb").read())
def _lines4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    if isinstance(textlines, string_types):
        linelist = decodes(textlines).split("\n")
        if len(linelist) and linelist[-1] == "":
            linelist = linelist[:-1]
        return linelist
    return list(textlines)
def lines4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    linelist = []
    for line in _lines4(textlines):
        linelist.append(line.rstrip())
    return linelist
def sorted4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    return list(sorted(_lines4(textlines)))
def each_grep(pattern: str, textlines: Union[str, List[str], TextIO]) -> Iterator[str]:
    for line in _lines4(textlines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def grep(pattern: str, textlines: Union[str, List[str], TextIO]) -> List[str]:
    return list(each_grep(pattern, textlines))
def greps(textlines: Union[str, List[str], TextIO], pattern: str) -> List[str]:
    return list(each_grep(pattern, textlines))
def running(textlines: Union[str, List[str]]) -> List[str]:
    return list(each_non_runuser(each_non_defunct(textlines)))
def each_non_defunct(textlines: Union[str, List[str], Iterator[str]]) -> Iterator[str]:
    for line in _lines4(textlines):
        if '<defunct>' in line:
            continue
        yield line
def each_non_runuser(textlines: Union[str, List[str], Iterator[str]]) -> Iterator[str]:
    for line in _lines4(textlines):
        if 'runuser -u' in line:
            continue
        yield line
def each_clean(textlines: Union[str, List[str]]) -> Iterator[str]:
    for line in _lines4(textlines):
        if '<defunct>' in line:
            continue
        if 'runuser -u' in line:
            continue
        if 'ps -eo pid,' in line:
            continue
        yield line
def clean(textlines: Union[str, List[str]]) -> str:
    return " " + "\n ".join(each_clean(textlines))

def i2(part: str, indent: str = "  ") -> str:
    if isinstance(part, string_types):
        if "\n" in part.strip():
            lines = part.strip().split("\n")
            text = indent
            newline = "\n" + indent
            text += newline.join(lines)
            if part.endswith("\n"):
                text += "\n"
            return text
    return part
def o22(part: str, maxlines: int =22) -> str:
    return only22(part, maxlines=maxlines)
def oi22(part: str, maxlines: int = 22) -> str:
    return only22(part, indent="  ", maxlines=maxlines)
def only22(part: str, indent: str = "", maxlines: int = 22) -> str:
    if isinstance(part, string_types):
        if "\n" in part.strip():
            lines = part.strip().split("\n")
            if len(lines) <= maxlines:
                return indent+part.replace("\n", "\n"+indent)
            skipped = len(lines) - maxlines + 3
            lastlines = maxlines - 5 - 3
            real = lines[:5] + ["...", F"... ({skipped} lines skipped)", "..."] + lines[-lastlines:]
            text = indent
            newline = "\n" + indent
            text += newline.join(real)
            if part.endswith("\n"):
                text += "\n"
            return text
    if isinstance(part, string_types):
        if len(part) <= maxlines:
            return part
        return part[:5] + "..." + part[-14:]
    if isinstance(part, list):
        if len(part) <= maxlines:
            return part
        skipped = len(part) - maxlines + 3
        lastlines = maxlines - 5 - 3
        return part[:5] + ["...", F"... ({skipped} lines skipped)", "..."] + part[-lastlines:]
    return part

def get_USER_ID(root: bool = False) -> int:
    ID = 0
    if root: return ID
    return os.geteuid()
def get_USER(root: bool = False) -> str:
    if root: return "root"
    uid = os.geteuid()
    import pwd
    return pwd.getpwuid(uid).pw_name
def get_GROUP_ID(root: bool = False) -> int:
    ID = 0
    if root: return ID
    return os.getegid()
def get_GROUP(root: bool = False) -> str:
    if root: return "root"
    import grp
    gid = os.getegid()
    return grp.getgrgid(gid).gr_name
def get_LASTGROUP_ID(root: bool = False) -> int:
    if root: return 0 # only there is
    current = os.getegid()
    lastgid = current
    for gid in os.getgroups():
        if gid != current:
            lastgid = gid
    return lastgid
def get_LASTGROUP(root: bool = False) -> str:
    if root: return "root" # only there is
    gid = get_LASTGROUP_ID(root)
    import grp
    return grp.getgrgid(gid).gr_name

def beep() -> None:
    if os.name == "nt":
        import winsound # type: ignore[import-error] # pylint: disable=import-error
        frequency = 2500
        duration = 1000
        winsound.Beep(frequency, duration)  # type: ignore[attr-defined]
    else:
        # using 'sox' on Linux as "\a" is usually disabled
        # sx___("play -n synth 0.1 tri  1000.0")
        sx____("play -V1 -q -n -c1 synth 0.1 sine 500")

def get_proc_started(pid: int) -> float:
    """ get time process started after boot in clock ticks"""
    proc = F"/proc/{pid}/stat"
    return path_proc_started(proc)
def path_proc_started(proc: str) -> float:
    """ get time process started after boot in clock ticks"""
    if not os.path.exists(proc):
        logg.error("no such file %s", proc)
        return 0
    else:
        with open(proc, "rb") as f:
            data = f.readline()
        stat_data = data.split()
        started_ticks = stat_data[21]
        # man proc(5): "(22) starttime = The time the process started after system boot."
        #    ".. the value is expressed in clock ticks (divide by sysconf(_SC_CLK_TCK))."
        # NOTE: for containers the start time is related to the boot time of host system.

        clkTickInt = os.sysconf_names['SC_CLK_TCK']
        clockTicksPerSec = os.sysconf(clkTickInt)
        started_secs = float(started_ticks) / clockTicksPerSec
        logg.debug("Proc started time: %.3f (%s)", started_secs, proc)
        # this value is the start time from the host system

        # Variant 1:
        system_uptime = "/proc/uptime"
        with open(system_uptime, "rb") as f:
            data = f.readline()
        uptime_data = decodes(data).split()
        uptime_secs = float(uptime_data[0])
        logg.debug("System uptime secs: %.3f (%s)", uptime_secs, system_uptime)

        # get time now
        now = time.time()
        started_time = now - (uptime_secs - started_secs)
        logg.debug("Proc has been running since: %s", datetime.datetime.fromtimestamp(started_time))

        # Variant 2:
        system_stat = "/proc/stat"
        system_btime = 0.
        with open(system_stat, "rb") as f:
            for line in f:
                if line.startswith(b"btime"):
                    system_btime = float(decodes(line).split()[1])
        f.closed
        logg.debug("System btime secs: %.3f (%s)", system_btime, system_stat)

        started_btime = system_btime + started_secs
        logg.debug("Proc has been running since: %s", datetime.datetime.fromtimestamp(started_btime))

        # return started_time
        return started_btime

def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
    logg.info("::: made %s", filename)
def shell_file(filename: str, content: str) -> None:
    text_file(filename, content)
    os.chmod(filename, 0o775)
def copy_file(filename: str, target: str) -> None:
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename: str, target: str) -> None:
    copy_file(filename, target)
    os.chmod(target, 0o755)
def get_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back  # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]
# def os_path(root: Optional[str], path: Optional[str]) -> Optional[str]:
def os_path(root: Optional[str], path: str) -> str:
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(root, path)
def os_getlogin() -> str:
    """ NOT using os.getlogin() """
    import pwd
    return pwd.getpwuid(os.geteuid()).pw_name
def os_remove(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
def get_runtime_dir() -> str:
    explicit = os.environ.get("XDG_RUNTIME_DIR", "")
    if explicit: return explicit
    user = os_getlogin()
    return "/tmp/run-"+user
def docname(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

SYSTEMCTL_DEBUG_LOG = "{LOG}/systemctl.debug.log"
SYSTEMCTL_EXTRA_LOG = "{LOG}/systemctl.log"

def get_home() -> str:
    return os.path.expanduser("~")              # password directory. << from docs(os.path.expanduser)
def get_HOME(root: bool = False) -> str:
    if root: return "/root"
    return get_home()
def get_RUNTIME_DIR(root: bool = False) -> str:
    RUN = "/run"
    if root: return RUN
    return os.environ.get("XDG_RUNTIME_DIR", get_runtime_dir())
def get_CONFIG_HOME(root: bool = False) -> str:
    CONFIG = "/etc"
    if root: return CONFIG
    HOME = get_HOME(root)
    return os.environ.get("XDG_CONFIG_HOME", HOME + "/.config")
def get_LOG_DIR(root: bool = False) -> str:
    LOGDIR = "/var/log"
    if root: return LOGDIR
    CONFIG = get_CONFIG_HOME(root)
    return os.path.join(CONFIG, "log")
def expand_path(path: str, root: bool = True) -> str:
    # pylint: disable=possibly-unused-variable
    LOG = get_LOG_DIR(root)
    XDG_CONFIG_HOME=get_CONFIG_HOME(root)
    XDG_RUNTIME_DIR=get_RUNTIME_DIR(root)
    return os.path.expanduser(path.replace("${", "{").format(**locals()))

############ local mirror helpers #############
def ip_container(name: str) -> str:
    docker = _docker
    values = output(F"{docker} inspect {name}")
    values = json.loads(values)
    if not values or "NetworkSettings" not in values[0]:
        logg.critical(" %s inspect %s => %s ", docker, name, values)
    return values[0]["NetworkSettings"]["IPAddress"] # type: ignore
def detect_local_system() -> str:
    """ checks the controller host (a real machine / your laptop)
        and returns a matching image name for it (docker style) """
    docker = _docker
    mirror = _mirror
    cmd = F"{mirror} detect"
    out = output(cmd)
    return decodes(out).strip()

############ the real testsuite ##############

class DockerSystemctlReplacementTest(unittest.TestCase):
    """ testcases for systemctl.py """
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str] = None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self) -> int:
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 4000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname: Optional[str] = None, keep: bool = False) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir) and not keep:
            shutil.rmtree(newdir)
        if not os.path.isdir(newdir):
            os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            if not KEEP:
                shutil.rmtree(newdir)
        return newdir
    def rm_docker(self, testname: str) -> None:
        docker = _docker
        if not KEEP:
            sx____(F"{docker} stop -t 6 {testname}")
            sx____(F"{docker} rm -f {testname}")
    def killall(self, what: str, wait: Optional[int] = None, sig: Optional[int] = None, kill: Optional[int] = None, but: Optional[List[str]] = None) -> None:
        # logg.info("killall %s (but %s)", what, but)
        killed = 0
        if True:
            sig = sig if sig is not None else signal.SIGINT
            for nextpid in os.listdir("/proc"):
                try: pid = int(nextpid)
                except: continue
                cmdline = F"/proc/{pid}/cmdline"
                try:
                    cmd = open(cmdline).read().replace("\0", " ")
                    if fnmatch(cmd, what):
                        found = [name for name in (but or []) if name in cmd]
                        if found: continue
                        logg.info(" %s", F"kill -{sig} {pid} # {cmd}")
                        os.kill(pid, sig)
                        killed += 1
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        logg.info(" killing %s", e)
                except Exception as e:
                    logg.info(" killing %s", e)
        for checking in range(int(wait or KILLWAIT)):
            remaining = []
            for nextpid in os.listdir("/proc"):
                try: pid = int(nextpid)
                except: continue
                cmdline = F"/proc/{pid}/cmdline"
                try:
                    cmd = open(cmdline).read().replace("\0", " ")
                    if fnmatch(cmd, what):
                        found = [name for name in (but or []) if name in cmd]
                        if found: continue
                        remaining += [pid]
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        logg.info(" killing %s", e)
                except Exception as e:
                    logg.info(" killing %s", e)
            if not remaining:
                return
            if checking % 2 == 0:
                logg.info("[%02is] %ix remaining %s", checking, len(remaining), remaining)
            time.sleep(1)
        if True:
            kill = kill if kill is not None else signal.SIGKILL
            for nextpid in os.listdir("/proc"):
                try: pid = int(nextpid)
                except: continue
                cmdline = F"/proc/{pid}/cmdline"
                try:
                    cmd = open(cmdline).read().replace("\0", " ")
                    if fnmatch(cmd, what):
                        found = [name for name in (but or []) if name in cmd]
                        if found: continue
                        logg.info(" %s", F"kill -{kill} {pid} # {cmd}")
                        os.kill(pid, kill)
                        killed += 1
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        logg.info(" killing %s", e)
                except Exception as e:
                    logg.info(" killing %s", e)
    def rm_killall(self, testname: Optional[str] = None) -> None:
        self.killall("*systemctl*.py *", 10, but = ["edit ", "localtests2.py ", "dockertests3.py "])
        testname = testname or self.caller_testname()
        self.killall(F"*/{testname}_*")
    def kill(self, pid: Union[str, int], wait: Optional[int] = None, sig: Optional[int] = None) -> bool:
        pid = int(pid)
        cmdline = F"/proc/{pid}/cmdline"
        if True:
            try:
                if os.path.exists(cmdline):
                    cmd = open(cmdline).read().replace("\0", " ").strip()
                    logg.info(" %s", F"kill {pid} # {cmd}")
                    os.kill(pid, sig or signal.SIGINT)
            except IOError as e:
                if e.errno != errno.ENOENT:
                    logg.info(" killing %s", e)
            except Exception as e:
                logg.info(" killing %s", e)
        status = F"/proc/{pid}/status"
        for checking in range(int(wait or KILLWAIT)):
            if not os.path.exists(cmdline):
                return True
            try:
                if os.path.exists(status):
                    for line in open(status):
                        if line.startswith("State:"):
                            if "(zombie)" in line:
                                return True
                            if checking % 2 == 0:
                                logg.info("[%02is] wait %s - %s", checking, pid, line.strip())
            except IOError as e:
                if e.errno != errno.ENOENT:
                    logg.info(" killing %s", e)
            except Exception as e:
                logg.info(" killing %s", e)
            time.sleep(1)
        logg.warning("not killed %s", pid)
        return False
    def real_folders(self) -> Generator[str, None, None]:
        yield "/etc/systemd/system"
        yield "/var/run/systemd/system"
        yield "/usr/lib/systemd/system"
        yield "/lib/systemd/system"
        yield "/etc/init.d"
        yield "/var/run/init.d"
        yield "/var/run"
        yield "/etc/sysconfig"
        yield "/etc/systemd/system/multi-user.target.wants"
        yield "/usr/bin"
        yield "/bin"
    def rm_zzfiles(self, root: Optional[str]) -> None:
        for folder in self.real_folders():
            for item in glob(os_path(root, folder + "/zz*")):
                if os.path.islink(item):
                    logg.info("rmlink %s", item)
                    os.unlink(item)
                elif os.path.isdir(item):
                    logg.info("rmtree %s", item)
                    shutil.rmtree(item)
                else:
                    logg.info("rm %s", item)
                    os.remove(item)
            for item in glob(os_path(root, folder + "/test_*")):
                if os.path.islink(item):
                    logg.info("rmlink %s", item)
                    os.unlink(item)
                elif os.path.isdir(item):
                    logg.info("rmtree %s", item)
                    shutil.rmtree(item)
                else:
                    logg.info("rm %s", item)
                    os.remove(item)
    def coverage(self, testname: Optional[str] = None) -> None:
        if not COVERAGE:
            return
        testname = testname or self.caller_testname()
        newcoverage = ".coverage."+testname
        if os.path.isfile(".coverage"):
            time.sleep(1) # some background process may want to write data
            # shutil.copy(".coverage", newcoverage)
            with open(".coverage", "rb") as inp:
                text = inp.read()
            text2 = re.sub(rb"(\]\}\})[^{}]*(\]\}\})$", rb"\1", text)
            with open(newcoverage, "wb") as out:
                out.write(text2)
    def root(self, testdir: str, real: bool = False) -> str:
        if real: return "/"
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def socat(self) -> str:
        if False and os.path.exists("/usr/bin/socat"):
            return "/usr/bin/socat"
        else:
            return reply_tool()
    def newpassword(self) -> str:
        out = "Password."
        out += random.choice(string.ascii_uppercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(",.-+")
        out += random.choice("0123456789")
        out += random.choice("0123456789")
        return out
    def user(self) -> str:
        return os_getlogin()
    def ip_container(self, name: str) -> str:
        values = output("docker inspect "+name)
        values = json.loads(values)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"] # type: ignore
    def local_image(self, image: str) -> str:
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if os.environ.get("NONLOCAL", ""):
            return image
        add_hosts = self.start_mirror(image)
        if add_hosts:
            return F"{add_hosts} {image}"
        return image
    def local_addhosts(self, dockerfile: str) -> str:
        image = ""
        for line in open(dockerfile):
            m = re.match('[Ff][Rr][Oo][Mm] *"([^"]*)"', line)
            if m:
                image = m.group(1)
                break
            m = re.match("[Ff][Rr][Oo][Mm] *(\\w[^ ]*)", line)
            if m:
                image = m.group(1).strip()
                break
        logg.debug("--\n-- '%s' FROM '%s'", dockerfile, image)
        if image:
            return self.start_mirror(image)
        return ""
    def start_mirror(self, image: str) -> str:
        docker = _docker
        mirror = _mirror
        local = " --localmirrors" if LOCAL else ""
        cmd = F"{mirror} start {image} --add-hosts{local}"
        out = output(cmd)
        return decodes(out).strip()
    def drop_container(self, name: str) -> None:
        docker = _docker
        sx____(F"{docker} rm --force {name}")
    def drop_centos(self) -> None:
        self.drop_container("centos")
    def drop_ubuntu(self) -> None:
        self.drop_container("ubuntu")
    def drop_opensuse(self) -> None:
        self.drop_container("opensuse")
    def make_opensuse(self) -> None:
        self.make_container("opensuse", OPENSUSE)
    def make_ubuntu(self) -> None:
        self.make_container("ubuntu", UBUNTU)
    def make_centos(self) -> None:
        self.make_container("centos", CENTOS)
    def make_container(self, name: str, image: str) -> None:
        docker = _docker
        self.drop_container(name)
        local_image = self.local_image(image)
        cmd = F"{docker} run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd)
        print(F"                 # {local_image}")
        print(F"  {docker} exec -it {name} bash")
    def begin(self) -> str:
        self._started = time.monotonic() # pylint: disable=attribute-defined-outside-init
        logg.info("[[%s]]", datetime.datetime.fromtimestamp(self._started).strftime("%H:%M:%S"))
        return "-vv"
    def end(self, maximum: int = 99) -> None:
        runtime = time.monotonic() - self._started
        self.assertLess(runtime, maximum * LONGER)
    def prep_coverage(self, image: Optional[str], testname: str, cov_option: Optional[str] = None) -> None:
        """ install a shell-wrapper /usr/bin/systemctl (testdir/systemctl.sh)
            which calls the develop systemctl.py prefixed by our coverage tool.
            .
            The weird name for systemctl_py_run is special for save_coverage().
            We take the realpath of our develop systemctl.py on purpose here.
        """
        docker = _docker
        python = _python
        testdir = self.testdir(testname, keep = True)
        cov_run = cover(image, append = "--parallel-mode")
        cov_option = cov_option or ""
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/", "_")[1:]
        shell_file(systemctl_sh, F"""
            #! /bin/sh
            cd /tmp
            exec {cov_run} /{systemctl_py_run} "$@" -vv {cov_option}
            """)
        cmd = F"{docker} cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sed -i 's:/usr/bin/env python.*:/usr/bin/env {python}:' /{systemctl_py_run}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd)
    def save_coverage(self, *testnames: str) -> None:
        """ Copying the image's /tmp/.coverage to our local ./.coverage.image file.
            Since the path of systemctl.py inside the container is different
            than our develop systemctl.py we have to patch the .coverage file.
            .
            Some older coverage2 did use a binary format, so we had ensured
            the path of systemctl.py inside the container has the exact same
            length as the realpath of our develop systemctl.py outside the
            container. That way 'coverage combine' maps the results correctly."""
        if not COVERAGE:
            return
        docker = _docker
        sed = _sed
        systemctl_py = realpath(_systemctl_py)
        systemctl_py_run = systemctl_py.replace("/", "_")[1:]
        for testname in testnames:
            cmd = F"{docker} export {testname} | tar tf - | grep tmp/.coverage"
            files = output(cmd)
            for tmp_coverage in lines4(files):
                suffix = tmp_coverage.replace("tmp/.coverage", "")
                cmd = F"{docker} cp {testname}:/{tmp_coverage} .coverage.{testname}{suffix}"
                sh____(cmd)
                cmd = F"{sed} -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}{suffix}"
                sh____(cmd)
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_31001_systemctl_testfile(self) -> None:
        """ the systemctl.py file to be tested does exist """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s", root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(_systemctl_py, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
        self.coverage()
    def real_1002_systemctl_version(self) -> None:
        cmd = F"systemctl --version"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"systemd [234]\d\d"))
        self.assertFalse(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_31005_systemctl_help_command(self) -> None:
        """ for any command, 'help command' shows the documentation """
        systemctl = cover() + _systemctl_py
        cmd = F"{systemctl} help list-unit-files"
        out, end = output2(cmd)
        logg.info("%s\n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "for more information"))
        self.assertTrue(greps(out, "--type=service"))
        self.coverage()
    #
    def test_35000_systemctl_py_inside_container(self) -> None:
        """ check that we can run systemctl.py inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sed -i 's:/usr/bin/env python.*:/usr/bin/env {python}:' /usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out, "systemctl.py"))
    def test_35001_coverage_systemctl_py_inside_container(self) -> None:
        """ check that we can run systemctl.py with coverage inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF) # <<<< need to use COVERAGE image here
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        testname = self.testname()
        testdir = self.testdir()
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image) # <<<< and install the tool for the COVERAGE image
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}" # <<<< like here
            sx____(cmd)
        self.prep_coverage(image, testname)  # setup a shell-wrapper /usr/bin/systemctl calling systemctl.py
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        #
        self.save_coverage(testname)  # fetch {image}:.coverage and set path to develop systemctl.py
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out, "systemctl.py"))
    def test_35002_systemctl_py_enable_in_container(self) -> None:
        """ check that we can enable services in a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        testname = self.testname()
        testdir = self.testdir()
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl list-unit-files"
        # sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out, "zza.service.*static"))
        self.assertTrue(greps(out, "zzb.service.*disabled"))
        self.assertTrue(greps(out, "zzc.service.*enabled"))
    def test_35003_systemctl_py_default_services_in_container(self) -> None:
        """ check that we can enable services in a docker container to have default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        cmd = F"{docker} exec {testname} systemctl --all default-services -vv"
        out3 = output(cmd)
        logg.info("\ndefault-service>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out2, "zzb.service"))
        self.assertTrue(greps(out2, "zzc.service"))
        self.assertEqual(len(lines4(out2)), 2)
        self.assertTrue(greps(out3, "zzb.service"))
        self.assertTrue(greps(out3, "zzc.service"))
        # self.assertGreater(len(lines4(out2)), 2)
    #
    #
    #  compare the following with the test_4030 series
    #
    #
    def test_35030_simple_service_functions_system(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_simple_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def test_35031_runuser_simple_service_functions_user(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_simple_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def runuser_simple_service_functions(self, system: str, testname: str, testdir: str) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or OPENSUSE)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl"
        systemctl += F" --{system}"
        testsleep = testname+"_testsleep"
        testscript = testname+"_testscript.sh"
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "binkillall"), """
            #! /bin/sh
            ps -eo pid,comm,args | { while read pid comm args; do
               case "$args" in *"/bin/$1 "*)
                  echo kill $pid
                  kill $pid
               ;; esac
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testscript} 111
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/bin/kill -3 $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/bin/sleep 2
            ExecReload=/bin/kill -10 $MAINPID
            KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, testscript), F"""
            #! /bin/sh
            date +%T,enter >> {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              binkillall {testsleep} >> {logfile} 2>&1
              date +%T,stopped >> {logfile}
            {ends}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {ends}
            trap "stops" 3   # SIGQUIT
            trap "reload" 10 # SIGUSR1
            date +%T,starting >> {logfile}
            {bindir}/{testsleep} $1 >> {logfile} 2>&1 &
            pid="$!"
            while kill -0 $pid; do
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 # SIGQUIT SIGUSR1
            date +%T,leave >> {logfile}
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} cp {testdir}/binkillall {testname}:/usr/bin/binkillall"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/{testscript} {testname}:{bindir}/{testscript}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = _recent(output(_top_list))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)

        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(1) # kill is async
        cmd = F"{docker} exec {testname} cat {logfile}"
        sh____(cmd)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertTrue(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vvvv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertFalse(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertFalse(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertTrue(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process (if ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # no PID known so 'kill $MAINPID' fails
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will NOT restart an is-active service (with ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process (if ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        kill_testsleep = F"{docker} exec {testname} binkillall {testsleep}"
        sx____(kill_testsleep)
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35032_runuser_forking_service_functions_system(self) -> None:
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_forking_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35033_runuser_forking_service_functions_user(self) -> None:
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_forking_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end()
    def runuser_forking_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += F" --{system}"
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo $! > /tmp/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
               killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=forking
            PIDFile=/tmp/zzz.init.pid
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(running(top4), testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(running(top5), testsleep)
        ps6 = find_pids(running(top6), testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35034_runuser_notify_service_functions_system(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_notify_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end(188)
    def test_35035_runuser_notify_service_functions_user(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_notify_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end(266)  # TODO# too long?
    def runuser_notify_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += F" --{system}"
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
                killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} install -y socat'"
        if sx____(cmd): self.skipTest("unable to install socat in a container from "+image)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        sh____(F"{docker} exec {testname} ls -l /var/run")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = F"{docker} exec {testname} cat {logfile}"
        sh____(cmd)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = F"{docker} exec {testname} cat {logfile}"
        sh____(cmd)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(running(top4), testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(running(top5), testsleep)
        ps6 = find_pids(running(top6), testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35036_runuser_notify_service_functions_with_reload(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_notify_service_functions_with_reload("system", testname, testdir)
        self.rm_testdir()
        logg.error("too long")  # TODO
        self.end(200)
    def test_35037_runuser_notify_service_functions_with_reload_user(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        # test_35037 is triggering len(socketfile) > 100 | "new notify socketfile"
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_notify_service_functions_with_reload("user", testname, testdir)
        self.rm_testdir()
        self.end(266)  # TODO# too long?
    def runuser_notify_service_functions_with_reload(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
                killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecReload={root}/usr/bin/zzz.init reload
            ExecStop={root}/usr/bin/zzz.init stop
            TimeoutRestartSec=4
            TimeoutReloadSec=4
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} install -y socat'"
        if sx____(cmd): self.skipTest("unable to install socat in a container from "+image)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is the same PID for the service process (if ExecReload)")
        ps4 = find_pids(running(top4), testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")  # TODO#
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(running(top5), testsleep)
        ps6 = find_pids(running(top6), testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35040_runuser_oneshot_service_functions(self) -> None:
        """ check that we manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_oneshot_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35041_runuser_oneshot_service_functions_user(self) -> None:
        """ check that we manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_oneshot_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end()
    def runuser_oneshot_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35042_runuser_oneshot_and_unknown_service_functions(self) -> None:
        """ check that we manage multiple services even when some
            services are not actually known. Along with oneshot serivce
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart / we have only different exit-code."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35043_runuser_oneshot_template_service_functions(self) -> None:
        """ check that we manage oneshot template services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_oneshot_template_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35044_runuser_oneshot_template_service_functions_user(self) -> None:
        """ check that we manage oneshot template services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_oneshot_template_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end()
    def runuser_oneshot_template_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz@.service"), F"""
            [Unit]
            Description=Testing Z.%i
            [Service]
            User=somebody
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.%i.1 {root}/var/tmp/test.%i.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.%i.1
            ExecStop=/bin/rm {root}/var/tmp/test.%i.1
            ExecStopPost=/bin/rm -f {root}/var/tmp/test.%i.2
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz@.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz@.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz@rsa.service -vv"
        sh____(cmd)
        #
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz@rsa.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz@rsa.service -vvvv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz@rsa.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz@rsa.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz@rsa.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz@rsa.service -vv -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz@rsa.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35045_runuser_sysv_service_functions(self) -> None:
        """ check that we manage SysV services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            ### BEGIN INIT INFO
            # Required-Start: $local_fs $remote_fs $syslog $network
            # Required-Stop:  $local_fs $remote_fs $syslog $network
            # Default-Start:  3 5
            # Default-Stop:   0 1 2 6
            # Short-Description: Testing Z
            # Description:    Allows for SysV testing
            ### END INIT INFO
            logfile={logfile}
            sleeptime=111
            start() {begin}
               [ -d /var/run ] || mkdir -p /var/run
               (runuser -u somebody {bindir}/{testsleep} $sleeptime 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,user,args
               cat "RUNNING `cat {root}/var/run/zzz.init.pid`"
            {ends}
            stop() {begin}
               kill `cat {root}/var/run/zzz.init.pid` >>$logfile 2>&1
               killall {testsleep} >> $logfile 2>&1
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'test -d /etc/init.d || mkdir -v /etc/init.d'"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/etc/init.d/zzz"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(1) # killall is async
        sx____(F"{docker} exec {testname} bash -c 'sed s/^/.../ {logfile} | tail'")
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' may restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps6 = find_pids(running(top6), testsleep)
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        self.end(188)
    #
    #
    #  compare the following with the test_35030 series
    #  as they are doing the same with usermode-only containers
    #
    #
    def test_35100_usermode_keeps_running(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_keeps_running("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35101_usermode_keeps_running_user(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_keeps_running("user", testname, testdir)
        self.rm_testdir()
        self.end()
    def usermode_keeps_running(self, system: str, testname: str, testdir: str) -> None:
        """ check that we manage simple services in a root env
            where the usermode container keeps running on PID 1 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = testname+"_testsleep"
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart=/usr/bin/{testsleep} 8
            ExecStartPost=/bin/echo started $MAINPID
            # ExecStop=/bin/kill $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/bin/sleep 2
            ExecReload=/bin/kill -10 $MAINPID
            KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p touch /tmp/run-somebody/log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /tmp/run-somebody/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody -R /tmp/run-somebody"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {systemctl} is-system-running -vv"
        sx____(cmd)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(_top_list))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        for attempt in range(4): # 4*3 = 12s
            time.sleep(3)
            logg.info("=====================================================================")
            top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
            logg.info("\n>>>\n%s", top)
            cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
            out, err, end = output3(cmd)
            logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
            cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/gobal.systemctl.debug.log"
            sx____(cmd)
            cmd = F"tail {testdir}/gobal.systemctl.debug.log | sed -e s/^/GLOBAL:.../"
            sx____(cmd)
            cmd = F"{docker} cp {testname}:/tmp/run-somebody/log/systemctl.debug.log {testdir}/somebody.systemctl.debug.log"
            sx____(cmd)
            cmd = F"tail {testdir}/somebody.systemctl.debug.log | sed -e s/^/USER:.../"
            sx____(cmd)
            #
            # out, end = output2(cmd)
            if greps(err, "Error response from daemon"):
                break
        #
        kill_testsleep = F"killall {testsleep}"
        sx____(kill_testsleep)
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        if True:
            cmd = F"cat {testdir}/gobal.systemctl.debug.log | sed -e s/^/GLOBAL:.../"
            sx____(cmd)
            cmd = F"cat {testdir}/somebody.systemctl.debug.log | sed -e s/^/USER:.../"
            sx____(cmd)
        #
        self.assertFalse(greps(err, "Error response from daemon"))
        self.assertEqual(out.strip(), "failed") # sleep did exit but not 'stop' requested
    def test_35130_usermode_simple_service_functions_system(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_simple_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def test_35131_simple_service_functions_user(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_simple_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def usermode_simple_service_functions(self, system: str, testname: str, testdir: str) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = testname+"_testsleep"
        testscript = testname+"_testscript.sh"
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "binkillall"), """
            #! /bin/sh
            ps -eo pid,comm,args | { while read pid comm args; do
               case "$args" in *"/bin/$1 "*)
                  echo kill $pid
                  kill $pid
               ;; esac
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testscript} 111
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/bin/kill -3 $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/bin/sleep 2
            ExecReload=/bin/kill -10 $MAINPID
            KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, testscript), F"""
            #! /bin/sh
            date +%T,enter >> {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              binkillall {testsleep} >> {logfile} 2>&1
              date +%T,stopped >> {logfile}
            {ends}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {ends}
            trap "stops" 3   # SIGQUIT
            trap "reload" 10 # SIGUSR1
            date +%T,starting >> {logfile}
            {bindir}/{testsleep} $1 >> {logfile} 2>&1 &
            pid="$!"
            while kill -0 $pid; do
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 # SIGQUIT SIGUSR1
            date +%T,leave >> {logfile}
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} cp {testdir}/binkillall {testname}:/usr/bin/binkillall"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/{testscript} {testname}:{bindir}/{testscript}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(_top_list))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        time.sleep(3)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(1) # kill is async
        cmd = F"{docker} exec {testname} cat {logfile}"
        sh____(cmd)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertTrue(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vvvv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        # inspect the service's log
        log = lines4(output(F"{docker} exec {testname} cat {logfile}"))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertFalse(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertFalse(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertTrue(greps(log, "reload"))
        sh____(F"{docker} exec {testname} truncate -s0 {logfile}")
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process (if ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # no PID known so 'kill $MAINPID' fails
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will NOT restart an is-active service (with ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process (if ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        kill_testsleep = F"{docker} exec {testname} binkillall {testsleep}"
        sx____(kill_testsleep)
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35132_usermode_forking_service_functions_system(self) -> None:
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_forking_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35133_usermode_forking_service_functions_user(self) -> None:
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_forking_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end()
    def usermode_forking_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo $! > /tmp/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
               killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=forking
            PIDFile=/tmp/zzz.init.pid
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(running(top4), testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(running(top5), testsleep)
        ps6 = find_pids(running(top6), testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35134_usermode_notify_service_functions_system(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_notify_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.coverage()
        self.end(122)
    def test_35135_usermode_notify_service_functions_user(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_notify_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def usermode_notify_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
                killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} install -y socat'"
        if sx____(cmd): self.skipTest("unable to install socat in a container from "+image)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        sh____(F"{docker} exec {testname} ls -l /var/run")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = F"{docker} exec {testname} cat {logfile}"
        sh____(cmd)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = F"{docker} exec {testname} cat {logfile}"
        sh____(cmd)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(running(top4), testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(running(top5), testsleep)
        ps6 = find_pids(running(top6), testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35136_usermode_notify_service_functions_with_reload(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_notify_service_functions_with_reload("system", testname, testdir)
        self.rm_testdir()
        self.coverage()
        logg.error("too long")  # TODO
        self.end(200)
    def test_35137_usermode_notify_service_functions_with_reload_user(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        # test_35037 is triggering len(socketfile) > 100 | "new notify socketfile"
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_notify_service_functions_with_reload("user", testname, testdir)
        self.rm_testdir()
        self.coverage()
        logg.error("too long")  # TODO
        self.end(266)
    def usermode_notify_service_functions_with_reload(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
                killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecReload={root}/usr/bin/zzz.init reload
            ExecStop={root}/usr/bin/zzz.init stop
            TimeoutRestartSec=4
            TimeoutReloadSec=4
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} install -y socat'"
        if sx____(cmd): self.skipTest("unable to install socat in a container from "+image)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines4(ps_output):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                if not m: continue
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(running(top1), testsleep)
        ps2 = find_pids(running(top2), testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(running(top3), testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is the same PID for the service process (if ExecReload)")
        ps4 = find_pids(running(top4), testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")  # TODO#
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(running(top5), testsleep)
        ps6 = find_pids(running(top6), testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(F"{docker} exec {testname} ps -eo etime,pid,ppid,user,args"))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(running(top7), testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35140_usermode_oneshot_service_functions(self) -> None:
        """ check that we manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_oneshot_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35141_usermode_oneshot_service_functions_user(self) -> None:
        """ check that we manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_oneshot_service_functions("user", testname, testdir)
        self.rm_testdir()
        self.end()
    def usermode_oneshot_service_functions(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/{system}/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        #
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35142_usermode_oneshot_and_unknown_service_functions(self) -> None:
        """ check that we manage multiple services even when some
            services are not actually known. Along with oneshot serivce
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart / we have only different exit-code."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            User=somebody
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd)
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd)
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active)
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output(F"{docker} exec {testname} cat {logfile}").replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35144_usermode_sysv_service_functions(self) -> None:
        """ check that we are disallowed to manage SysV services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            ### BEGIN INIT INFO
            # Required-Start: $local_fs $remote_fs $syslog $network
            # Required-Stop:  $local_fs $remote_fs $syslog $network
            # Default-Start:  3 5
            # Default-Stop:   0 1 2 6
            # Short-Description: Testing Z
            # Description:    Allows for SysV testing
            ### END INIT INFO
            logfile={logfile}
            sleeptime=111
            start() {begin}
               [ -d /var/run ] || mkdir -p /var/run
               (runuser -u somebody {bindir}/{testsleep} $sleeptime 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,user,args
               cat "RUNNING `cat {root}/var/run/zzz.init.pid`"
            {ends}
            stop() {begin}
               kill `cat {root}/var/run/zzz.init.pid` >>$logfile 2>&1
               killall {testsleep} >>$logfile 2>&1
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'test -d /etc/init.d || mkdir -v /etc/init.d'"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/etc/init.d/zzz"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Initscript zzz.service not for --user mode"))
        #
        # .................... deleted stuff start/stop/etc
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    #
    #
    def test_35230_bad_usermode_simple_service_functions_system(self) -> None:
        """ check that we are disallowed to manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_simple_service_functions("", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35231_bad_simple_service_functions_user(self) -> None:
        """ check that we are disallowed to manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_simple_service_functions("User=foo", testname, testdir)
        self.rm_testdir()
        self.end()
    def bad_usermode_simple_service_functions(self, extra: str, testname: str, testdir: str) -> None:
        """ check that we are disallowed to manage simple services in a root env
            with commands like start, restart, stop, etc"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        testsleep = testname+"_testsleep"
        testscript = testname+"_testscript.sh"
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testscript} 111
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/bin/kill -3 $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/bin/sleep 2
            ExecReload=/bin/kill -10 $MAINPID
            KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, testscript), F"""
            #! /bin/sh
            date +%T,enter >> {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep} >> {logfile} 2>&1
              date +%T,stopped >> {logfile}
            {ends}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {ends}
            trap "stops" 3   # SIGQUIT
            trap "reload" 10 # SIGUSR1
            date +%T,starting >> {logfile}
            {bindir}/{testsleep} $1 >> {logfile} 2>&1 &
            pid="$!"
            while kill -0 $pid; do
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 # SIGQUIT SIGUSR1
            date +%T,leave >> {logfile}
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/{testscript} {testname}:{bindir}/{testscript}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/system/zzz.service"
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd)
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)  # TODO?
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vvvv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35232_bad_usermode_forking_service_functions_system(self) -> None:
        """ check that we are disallowed to manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_forking_service_functions("", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35233_bad_usermode_forking_service_functions_user(self) -> None:
        """ check that we are disallowed to manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_forking_service_functions("User=foo", testname, testdir)
        self.rm_testdir()
        self.end()
    def bad_usermode_forking_service_functions(self, extra: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo $! > /tmp/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
               killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=forking
            PIDFile=/tmp/zzz.init.pid
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/system/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_35234_bad_usermode_notify_service_functions_system(self) -> None:
        """ check that we are disallowed to manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_notify_service_functions("", testname, testdir)
        self.rm_testdir()
        self.coverage()
        self.end()
    def test_35235_bad_usermode_notify_service_functions_user(self) -> None:
        """ check that we are disallowed to manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_notify_service_functions("User=foo", testname, testdir)
        self.rm_testdir()
        self.end(266)  # TODO# too long?
    def bad_usermode_notify_service_functions(self, extra: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
                killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} install -y socat'"
        if sx____(cmd): self.skipTest("unable to install socat in a container from "+image)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/system/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35236_bad_usermode_notify_service_functions_with_reload(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_notify_service_functions_with_reload("", testname, testdir)
        self.rm_testdir()
        self.coverage()
        logg.error("too long")  # TODO
        self.end(200)
    def test_35237_bad_usermode_notify_service_functions_with_reload_user(self) -> None:
        """ check that we are disallowed to manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        # test_35037 is triggering len(socketfile) > 100 | "new notify socketfile"
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_notify_service_functions_with_reload("User=foo", testname, testdir)
        self.rm_testdir()
        self.coverage()
        logg.error("too long")  # TODO
        self.end(266)
    def bad_usermode_notify_service_functions_with_reload(self, extra: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            logfile={logfile}
            start() {begin}
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 111 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,user,args
            {ends}
            stop() {begin}
                killall {testsleep}
            {ends}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecReload={root}/usr/bin/zzz.init reload
            ExecStop={root}/usr/bin/zzz.init stop
            TimeoutRestartSec=4
            TimeoutReloadSec=4
            [Install]
            WantedBy=multi-user.target
            """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} install -y socat'"
        if sx____(cmd): self.skipTest("unable to install socat in a container from "+image)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/system/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = F"{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35240_bad_usermode_oneshot_service_functions(self) -> None:
        """ check that we are disallowed to manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_oneshot_service_functions("", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35241_bad_usermode_oneshot_service_functions_user(self) -> None:
        """ check that we are disallowed to manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_oneshot_service_functions("User=foo", testname, testdir)
        self.rm_testdir()
        self.end()
    def bad_usermode_oneshot_service_functions(self, extra: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/system/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd)
        testfiles = output(F"{docker} exec {testname} find /var/tmp -name test.*")
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        is_active = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "")  # TODO#
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = F"{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = F"{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = F"{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    def test_35290_bad_usermode_other_commands(self) -> None:
        """ check that we are disallowed to manage oneshot services in a root env
            with other commands: enable, disable, mask, unmaks,..."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_other_commands("", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_35291_bad_usermode_other_commands(self) -> None:
        """ check that we are disallowed to manage oneshot services in a root env
            with other commands: enable, disable, mask, unmaks,..."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_other_commands("User=foo", testname, testdir)
        self.rm_testdir()
        self.end()
    def bad_usermode_other_commands(self, extra: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += F" --{system}"
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=simple
            ExecStart=/usr/bin/{testsleep} 11
            [Install]
            WantedBy=multi-user.target
            """)
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)

        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        zzz_service = F"/etc/systemd/system/zzz.service"
        cmd = F"{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm -f {testname}"
        sh____(cmd)
        cmd = F"{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = F"{docker} exec {testname} {systemctl} disable zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = F"{docker} exec {testname} {systemctl} mask zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = F"{docker} exec {testname} {systemctl} unmask zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = F"{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        self.assertFalse(greps(err, "Unit zzz.service not for --user mode"))  # TODO
        self.assertEqual(out.strip(), "inactive")
        #
        cmd = F"{docker} exec {testname} {systemctl} is-failed zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertFalse(greps(err, "Unit zzz.service not for --user mode"))  # TODO
        self.assertEqual(out.strip(), "inactive")
        #
        cmd = F"{docker} exec {testname} {systemctl} is-enabled zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertFalse(greps(err, "Unit zzz.service not for --user mode"))  # TODO
        self.assertEqual(out.strip(), "disabled")
        #
        cmd = F"{docker} exec {testname} {systemctl} status zzz.service -vv"
        out, err, end = output3(cmd)
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        #
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
    #
    #
    #
    #
    #
    #
    def test_35430_systemctl_py_start_simple(self) -> None:
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE and IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        shell_file(os_path(testdir, "killall"), """
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            AssertFileIsExecutable=//usr/bin/killall
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            ExecStop=/usr/bin/killall testsleep
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines4(out)), 1)
        #
        cmd = F"{docker} exec {testname} systemctl start zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = F"{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35431_systemctl_py_start_extra_simple(self) -> None:
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines4(out)), 1)
        #
        cmd = F"{docker} exec {testname} systemctl start zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = F"{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35432_systemctl_py_start_forking(self) -> None:
        """ check that we can start forking services in a container w/ PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        shell_file(os_path(testdir, "killall"), """
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start)
               [ -d /var/run ] || mkdir -p /var/run
               (testsleep 111 0<&- &>/dev/null &
                echo $! > /var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,user,args
            ;; stop)
               killall testsleep
            ;; esac
            echo "done$1" >&2
            exit 0""")
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile=/var/run/zzz.init.pid
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines4(out)), 1)
        #
        cmd = F"{docker} exec {testname} systemctl start zzz.service -vv"
        sx____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = F"{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35433_systemctl_py_start_forking_without_pid_file(self) -> None:
        """ check that we can start forking services in a container without PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        shell_file(os_path(testdir, "killall"), """
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start)
               (testsleep 111 0<&- &>/dev/null &) &
               wait %1
               ps -o pid,ppid,user,args >&2
            ;; stop)
               killall testsleep
               echo killed all testsleep >&2
               sleep 1
            ;; esac
            echo "done$1" >&2
            exit 0""")
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines4(out)), 1)
        #
        cmd = F"{docker} exec {testname} systemctl start zzz.service -vv"
        sx____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = F"{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35435_systemctl_py_start_notify_by_timeout(self) -> None:
        """ check that we can start simple services in a container w/ notify timeout"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        shell_file(os_path(testdir, "killall"), """
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            Type=notify
            ExecStart=/usr/bin/testsleep 111
            ExecStop=/usr/bin/killall testsleep
            TimeoutSec=4
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines4(out)), 1)
        #
        cmd = F"{docker} exec {testname} systemctl start zzz.service -vvvv"
        sx____(cmd) # returncode = 1
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = F"{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35500_systemctl_py_run_default_services_in_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        cmd = F"{docker} exec {testname} systemctl default -vvvv"
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35520_systemctl_py_run_default_services_from_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image (with --init default)"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        images = IMAGES
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre=/bin/echo starting B
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStartPre=/bin/echo starting C
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"--init\",\"default\",\"-vv\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(3)
        #
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} logs {testname}"
        logs = output(cmd)
        logg.info("------- docker logs\n>\n%s", logs)
        self.assertFalse(greps(logs, "starting B"))
        self.assertFalse(greps(logs, "starting C"))
        time.sleep(6) # INITLOOPS ticks at 5sec per default
        cmd = F"{docker} logs {testname}"
        logs = output(cmd)
        logg.info("------- docker logs\n>\n%s", logs)
        self.assertTrue(greps(logs, "starting B"))
        self.assertTrue(greps(logs, "starting C"))
        #
        cmd = F"{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} logs {testname}"
        logs = output(cmd)
        logg.info("------- docker logs\n>\n%s", logs)
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35530_systemctl_py_run_default_services_from_simple_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image (without any arg)"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        images = IMAGES
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        #
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(3)
        #
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35533_systemctl_py_run_default_services_from_single_service_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--now\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(3)
        #
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} stop {testname}" # <<<
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()

    def test_35600_systemctl_py_list_units_running(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted and that we can filter the list of services shown"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(3)
        #
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        self.assertEqual(len(greps(top, "testsleep")), 2)
        self.assertEqual(len(greps(top, " 1 *.*systemctl")), 1)
        self.assertEqual(len(greps(top, " root ")), 3)
        self.assertEqual(len(greps(top, " somebody ")), 1)
        #
        check = F"{docker} exec {testname} bash -c 'ls -ld /var/run/*.status; grep PID /var/run/*.status'"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        check = F"{docker} exec {testname} systemctl list-units"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 3)
        check = F"{docker} exec {testname} systemctl list-units --state=running"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 2)
        #
        cmd = F"{docker} stop {testname}" # <<<
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()

    def test_35700_systemctl_py_restart_failed_units(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            and failed units are going to be restarted"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleepA 55
            Restart=on-failure
            RestartSec=5
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleepB 99
            Restart=on-failure
            RestartSec=9
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleepC 111
            Restart=on-failure
            RestartSec=11
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"), """
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleepD 122
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepA"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepB"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepC"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepD"
        sh____(cmd)
        cmd = F"{docker} cp /usr/bin/killall {testname}:/usr/local/bin/killall"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzd.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(3)
        #
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleepA"))
        self.assertTrue(greps(top, "testsleepB"))
        self.assertTrue(greps(top, "testsleepC"))
        self.assertTrue(greps(top, "testsleepD"))
        self.assertEqual(len(greps(top, "testsleep")), 4)
        self.assertEqual(len(greps(top, " 1 *.*systemctl")), 1)
        self.assertEqual(len(greps(top, " root ")), 5)
        self.assertEqual(len(greps(top, " somebody ")), 1)
        #
        INITLOOPSLEEP = 5
        time.sleep(INITLOOPSLEEP+1)
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        check = F"{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 4)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        # logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertFalse(greps(log, "restart"))
        #
        cmd = F"{docker} exec {testname} killall testsleepD" # <<<
        sh____(cmd)
        #
        time.sleep(INITLOOPSLEEP+1)
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        # logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertFalse(greps(log, "restart"))
        #
        check = F"{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 3)
        #
        cmd = F"{docker} exec {testname} killall testsleepC" # <<<
        sh____(cmd)
        #
        check = F"{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 2)
        #
        time.sleep(INITLOOPSLEEP+1) # max 5sec but RestartSec=9
        #
        check = F"{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 2)
        #
        time.sleep(10) # to have RestartSec=9
        #
        check = F"{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check)
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 3)
        #
        time.sleep(INITLOOPSLEEP+1)
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "restart"))
        #
        self.assertTrue(greps(log, ".zzc.service. --- restarting failed unit"))
        self.assertTrue(greps(log, ".zzd.service. Current NoCheck .Restart=no."))
        #
        cmd = F"{docker} stop {testname}" # <<<
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_35881_set_user(self) -> None:
        """ check that we can run a service with User= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
            cmd = F"{docker} exec {testname} sed -i 's/raise *$/pass/' /usr/lib64/python3.6/site-packages/coverage/misc.py"
            sx____(cmd)
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} exec {testname} find /tmp/ -name '.coverage*'"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35882_set_user_and_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35883_set_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"root *nobody *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35884_set_user_and_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group={this_group}
            SupplementaryGroups={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35885_set_user_and_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35886_set_user_and_new_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *wheel *wheel .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35887_set_new_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"root *wheel *wheel .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35888_set_user_and_new_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group=wheel
            SupplementaryGroups={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *wheel *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35889_set_user_and_new_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups=wheel
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *wheel .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35891_set_user(self) -> None:
        """ check that we can run a service with User= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
            cmd = F"{docker} exec {testname} sed -i 's/raise *$/pass/' /usr/lib64/python3.6/site-packages/coverage/misc.py"
            sx____(cmd)
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *trusted .*{testsleepA}"))
        #
        cmd = F"{docker} exec {testname} find /tmp/ -name '.coverage*'"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35892_set_user_and_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *trusted .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35893_set_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"root *nobody *nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35894_set_user_and_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group={this_group}
            SupplementaryGroups=trusted
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *trusted .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35895_set_user_and_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups=trusted
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *trusted .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35896_set_user_and_new_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *wheel *trusted .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35897_set_new_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"root *wheel *wheel .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35898_set_user_and_new_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group=wheel
            SupplementaryGroups={this_group}
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *wheel *trusted,nobody .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_35899_set_user_and_new_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        self.begin()
        self.rm_testdir()
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), F"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups=wheel
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sx____(cmd)
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd)
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = F"{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, F"somebody *nobody *(wheel|trusted),(trusted|wheel) .*{testsleepA}"))
        #
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()

    def test_36130_run_default_services_from_simple_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        #
        # sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        for attempt in range(3):
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
            if greps(top, "testsleep"):
                break
            time.sleep(1)
        # sh____(F"{docker} exec {testname} cat /var/log/systemctl.debug.log")
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36133_run_default_services_from_single_service_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--now\",\"zzc.service\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        for attempt in range(3):
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
            if greps(top, "testsleep"):
                break
            time.sleep(1)
        sh____(F"{docker} exec {testname} cat /var/log/systemctl.debug.log")
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} stop {testname}" # <<<
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36160_systemctl_py_init_default_halt_to_exit_container(self) -> None:
        """ check that we can 'halt' in a docker container to stop the service
            and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname, cov_option)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        sh____(cmd)
        sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--exit\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        for attempt in range(3):
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
            if greps(top, "testsleep"):
                break
            time.sleep(1)
        sh____(F"{docker} exec {testname} cat /var/log/systemctl.debug.log")
        self.assertTrue(greps(top, "testsleep 111"))
        #
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv status check now
        cmd = F"{docker} inspect {testname}"
        inspected = output(cmd)
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = F"{docker} exec {testname} systemctl halt"
        sh____(cmd)
        #
        waits = 3
        for attempt in range(5):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = F"{docker} inspect {testname}"
            inspected = output(cmd)
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        #
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = F"{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more procs - exit init-loop"))
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36170_systemctl_py_init_all_stop_last_service_to_exit_container(self) -> None:
        """ check that we can 'stop <service>' in a docker container to stop the service
            being the last service and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname, cov_option)
        cmd = F"{docker} exec {testname} bash -c 'test -f /etc/init.d/ondemand && systemctl disable ondemand'" # ubuntu:16.04
        sx____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--all\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        for attempt in range(3):
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
            if greps(top, "testsleep"):
                break
            time.sleep(1)
        sh____(F"{docker} exec {testname} cat /var/log/systemctl.debug.log")
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} inspect {testname}"
        inspected = output(cmd)
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = F"{docker} exec {testname} systemctl stop zzb.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl stop zzc.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd)
        #
        waits = 3
        for attempt in range(5):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = F"{docker} inspect {testname}"
            inspected = output(cmd)
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        #
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = F"{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} logs {testname}"
        logs = output(cmd)
        logg.info("\n>\n%s", logs)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more procs - exit init-loop"))
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36180_systemctl_py_init_explicit_halt_to_exit_container(self) -> None:
        """ check that we can 'halt' in a docker container to stop the service
            and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname, cov_option)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--now\",\"zzc.service\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        for attempt in range(3):
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
            if greps(top, "testsleep"):
                break
            time.sleep(1)
        sh____(F"{docker} exec {testname} cat /var/log/systemctl.debug.log")
        self.assertTrue(greps(top, "testsleep 111"))
        #
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv status check now
        cmd = F"{docker} inspect {testname}"
        inspected = output(cmd)
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = F"{docker} exec {testname} systemctl halt"
        sh____(cmd)
        #
        waits = 3
        for attempt in range(10):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = F"{docker} inspect {testname}"
            inspected = output(cmd)
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = F"{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more services - exit init-loop"))
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36190_systemctl_py_init_explicit_stop_last_service_to_exit_container(self) -> None:
        """ check that we can 'stop <service>' in a docker container to stop the service
            being the last service and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname, cov_option)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--now\",\"zzc.service\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        for attempt in range(3):
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
            if greps(top, "testsleep"):
                break
            time.sleep(1)
        sh____(F"{docker} exec {testname} cat /var/log/systemctl.debug.log")
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = F"{docker} inspect {testname}"
        inspected = output(cmd)
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = F"{docker} exec {testname} systemctl stop zzc.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd)
        #
        waits = 3
        for attempt in range(10):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = F"{docker} inspect {testname}"
            inspected = output(cmd)
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n>>>\n%s", top)
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = F"{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd)
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} logs {testname}"
        logs = output(cmd)
        logg.info("\n>\n%s", logs)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        log = lines4(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more services - exit init-loop"))
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36200_systemctl_py_switch_users_is_possible(self) -> None:
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        sometime = SOMETIME or 288
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            User=somebody
            Group=root
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            User=somebody
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"), """
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            Group=nobody
            ExecStart=/usr/bin/testsleep 122
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        if COVERAGE:
            cmd = F"{docker} exec {testname} touch /tmp/.coverage"
            sh____(cmd)
            cmd = F"{docker} exec {testname} chmod 777 /tmp/.coverage"
            sh____(cmd)
        #
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start zzb.service -v"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start zzc.service -v"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start zzd.service -v"
        sh____(cmd)
        #
        # first of all, it starts commands like the service specs without user/group
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        # but really it has some user/group changed
        cmd = F"{docker} exec {testname} ps -eo user,group,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "somebody .*root .*testsleep 99"))
        self.assertTrue(greps(top, "somebody .*nobody .*testsleep 111"))
        self.assertTrue(greps(top, "root .*nobody .*testsleep 122"))
        # and the pid file has changed as well
        cmd = F"{docker} exec {testname} ls -l /var/run/zzb.service.pid"
        out = output(cmd)
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*root .*zzb.service.pid"))
        cmd = F"{docker} exec {testname} ls -l /var/run/zzc.service.pid"
        out = output(cmd)
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*nobody .*zzc.service.pid"))
        cmd = F"{docker} exec {testname} ls -l /var/run/zzd.service.pid"
        out = output(cmd)
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "root .*nobody .*zzd.service.pid"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36201_systemctl_py_switch_users_is_possible_from_saved_container(self) -> None:
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        text_file(os_path(testdir, "zzb.service"), """
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            User=somebody
            Group=root
            ExecStart=/usr/bin/testsleep 99
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"), """
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            User=somebody
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"), """
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            Group=nobody
            ExecStart=/usr/bin/testsleep 122
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody"
        sh____(cmd)
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzd.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd)
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        # sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(5)
        #
        # first of all, it starts commands like the service specs without user/group
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        self.assertTrue(greps(top, "testsleep 122"))
        # but really it has some user/group changed
        cmd = F"{docker} exec {testname} ps -eo user,group,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "somebody .*root .*testsleep 99"))
        self.assertTrue(greps(top, "somebody .*nobody .*testsleep 111"))
        self.assertTrue(greps(top, "root .*nobody .*testsleep 122"))
        # and the pid file has changed as well
        cmd = F"{docker} exec {testname} ls -l /var/run/zzb.service.pid"
        out = output(cmd)
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*root .*zzb.service.pid"))
        cmd = F"{docker} exec {testname} ls -l /var/run/zzc.service.pid"
        out = output(cmd)
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*nobody .*zzc.service.pid"))
        cmd = F"{docker} exec {testname} ls -l /var/run/zzd.service.pid"
        out = output(cmd)
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "root .*nobody .*zzd.service.pid"))
        #
        cmd = F"{docker} stop {testname}" # <<<
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        self.assertFalse(greps(top, "testsleep 122"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36210_switch_users_and_workingdir_coverage(self) -> None:
        """ check that we can put workingdir and setuid/setgid definitions in a service
            and code parts for that are actually executed (test case without fork before) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testsleep_sh = os_path(testdir, "testsleep.sh")
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 188
        shell_file(testsleep_sh, F"""
            #! /bin/sh
            logfile="/tmp/testsleep-$1.log"
            date > $logfile
            echo "pwd": `pwd` >> $logfile
            echo "user:" `id -un` >> $logfile
            echo "group:" `id -gn` >> $logfile
            testsleep $1
            """)
        text_file(os_path(testdir, "zz4.service"), """
            [Unit]
            Description=Testing 4
            [Service]
            Type=simple
            User=somebody
            Group=root
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 4
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zz5.service"), """
            [Unit]
            Description=Testing 5
            [Service]
            Type=simple
            User=somebody
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 5
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zz6.service"), """
            [Unit]
            Description=Testing 6
            [Service]
            Type=simple
            Group=nobody
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 6
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd)
        cmd = F"{docker} cp {testsleep_sh} {testname}:/usr/bin/testsleep.sh"
        sh____(cmd)
        cmd = F"{docker} exec {testname} chmod 755 /usr/bin/testsleep.sh"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname, cov_option)
        cmd = F"{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} useradd -u 1001 somebody -g nobody"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        if COVERAGE:
            cmd = F"{docker} exec {testname} touch /tmp/.coverage"
            sh____(cmd)
            cmd = F"{docker} exec {testname} chmod 777 /tmp/.coverage"  # << switched user may write
            sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zz4.service {testname}:/etc/systemd/system/zz4.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zz5.service {testname}:/etc/systemd/system/zz5.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zz6.service {testname}:/etc/systemd/system/zz6.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl __test_start_unit zz4.service -vvvv {cov_option}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl __test_start_unit zz5.service -vv {cov_option}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl __test_start_unit zz6.service -vv {cov_option}"
        sh____(cmd)
        #
        cmd = F"{docker} cp {testname}:/tmp/testsleep-4.log {testdir}/"
        sh____(cmd)
        cmd = F"{docker} cp {testname}:/tmp/testsleep-5.log {testdir}/"
        sh____(cmd)
        cmd = F"{docker} cp {testname}:/tmp/testsleep-6.log {testdir}/"
        sh____(cmd)
        log4 = lines4(open(os_path(testdir, "testsleep-4.log")))
        log5 = lines4(open(os_path(testdir, "testsleep-5.log")))
        log6 = lines4(open(os_path(testdir, "testsleep-6.log")))
        logg.info("testsleep-4.log\n %s", "\n ".join(log4))
        logg.info("testsleep-5.log\n %s", "\n ".join(log5))
        logg.info("testsleep-6.log\n %s", "\n ".join(log6))
        self.assertTrue(greps(log4, "pwd: /srv"))
        self.assertTrue(greps(log5, "pwd: /srv"))
        self.assertTrue(greps(log6, "pwd: /srv"))
        self.assertTrue(greps(log4, "group: root"))
        self.assertTrue(greps(log4, "user: somebody"))
        self.assertTrue(greps(log5, "user: somebody"))
        self.assertTrue(greps(log5, "group: nobody"))
        self.assertTrue(greps(log6, "group: nobody"))
        self.assertTrue(greps(log6, "user: root"))
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_36600_systemctl_py_can_reap_zombies_in_a_container(self) -> None:
        """ check that we can reap zombies in a container managed by systemctl.py"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        user = self.user()
        testsleep = self.testname("sleep").replace("test","")
        shell_file(os_path(testdir, "zzz.init"), F"""
            #! /bin/bash
            case "$1" in start)
               (/usr/bin/{testsleep} 111 0<&- &>/dev/null &) &
               wait %1
               # ps -o pid,ppid,user,args >&2
            ;; stop)
               killall {testsleep}
               echo killed all {testsleep} >&2
               sleep 1
            ;; esac
            echo "done$1" >&2
            exit 0
            """)
        text_file(os_path(testdir, "zzz.service"), F"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleep}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        if COVERAGE:
            cmd = F"{docker} exec {testname} {package} install -y {python_coverage}"
            sh____(cmd)
        self.prep_coverage(image, testname, cov_option)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd)
        cmd = F"{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl default-services -v"
        out2 = output(cmd)
        logg.info("\n>\n%s", out2)
        #
        # sh____(F"{docker} exec {testname} touch /var/log/systemctl.debug.log")
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd)
        time.sleep(3)
        #
        cmd = F"{docker} exec {testname} ps -eo state,pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        # testsleep is running with parent-pid of '1'
        self.assertTrue(greps(top, " 1 root */usr/bin/.*sleep 111"))
        # and the pid '1' is systemctl (actually systemctl.py)
        self.assertTrue(greps(top, " 1 .* 0 .*systemctl"))
        # and let's check no zombies around so far:
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< no zombie yet
        #
        # check the subprocess
        m = re.search(r"(?m)^(\S+)\s+(\d+)\s+(\d+)\s+(\S+.*sleep 111.*)$", top)
        assert m is not None
        state, pid, ppid, args = m.groups()
        logg.info(" - sleep state = %s", state)
        logg.info(" - sleep pid = %s", pid)
        logg.info(" - sleep ppid = %s", ppid)
        logg.info(" - sleep args = %s", args)
        self.assertEqual(state, "S")
        self.assertEqual(ppid, "1")
        self.assertIn("sleep", args)
        #
        # and kill the subprocess
        cmd = F"{docker} exec {testname} kill {pid}"
        sh____(cmd)
        #
        time.sleep(1)
        cmd = F"{docker} exec {testname} ps -eo state,pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "Z .*sleep.*<defunct>")) # <<< we have zombie!
        for attempt in range(10):
            time.sleep(3)
            cmd = F"{docker} exec {testname} ps -eo state,pid,ppid,user,args"
            top = output(cmd)
            logg.info("\n[%s]>>>\n%s", attempt, top)
            if not greps(top, "<defunct>"):
                break
        #
        cmd = F"{docker} exec {testname} ps -eo state,pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< and it's gone!
        time.sleep(1)
        #
        cmd = F"{docker} stop {testname}"
        out3 = output(cmd)
        logg.info("\n>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()

    def test_37001_centos_httpd(self) -> None:
        """ WHEN using a systemd-enabled CentOS 7,
            THEN we can create an image with an Apache HTTP service
                 being installed and enabled.
            Without a special startup.sh script or container-cmd
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        testport=self.testport()
        name="centos-httpd"
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        logg.info("%s:%s %s", testname, testport, image)
        # WHEN
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y httpd httpd-tools"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd)
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sx____(cmd)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run -d -p {testport}:80 --name {testname} {images}:{testname}"
        sh____(cmd)
        # THEN
        tmp = self.testdir(testname)
        cmd = F"sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{testport}"
        sh____(cmd)
        cmd = F"grep OK {tmp}/{testname}.txt"
        sh____(cmd)
        # CLEAN
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_37002_centos_postgres(self) -> None:
        """ WHEN using a systemd-enabled CentOS 7,
            THEN we can create an image with an PostgreSql DB service
                 being installed and enabled.
            Without a special startup.sh script or container-cmd
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos:7" not in image:
            if SKIP: self.skipTest("centos:7 based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        testport=self.testport()
        name="centos-postgres"
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        logg.info("%s:%s %s", testname, testport, image)
        psql = PSQL_TOOL
        PG = "/var/lib/pgsql/data"
        # WHEN
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y postgresql-server postgresql-utils"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} postgresql-setup initdb"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c \"sed -i -e 's/.*listen_addresses.*/listen_addresses = '\\\"'*'\\\"'/' {PG}/postgresql.conf\""
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'sed -i -e \"s/.*host.*ident/# &/\" {PG}/pg_hba.conf'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'echo \"host all all 0.0.0.0/0 md5\" >> {PG}/pg_hba.conf'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start postgresql -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'sleep 5; ps -ax'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.11'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.OK'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl stop postgresql -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable postgresql"
        sh____(cmd)
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sx____(cmd)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run -d -p {testport}:5432 --name {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sleep 5"
        sh____(cmd)
        # THEN
        tmp = self.testdir(testname)
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = F"{login}; {psql} -p {testport} -h 127.0.0.1 -d postgres -c '{query}' > {tmp}/{testname}.txt"
        sh____(cmd)
        cmd = F"grep testuser_ok {tmp}/{testname}.txt"
        sh____(cmd)
        # CLEAN
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_37003_opensuse_syslog(self) -> None:
        """ WHEN using a systemd-enabled CentOS 7 ..."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or OPENSUSE)
        if "opensuse/leap" not in image:
            if SKIP: self.skipTest("opensuse/leap based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        # testport=self.testport()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        name="opensuse-syslog"
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        ## logg.info("%s:%s %s", testname, testport, image)
        # WHEN
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y rsyslog"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        # ?# cmd = F"{docker} exec {testname} systemctl enable syslog.socket"
        # ?# sh____(cmd)
        #
        cmd = F"{docker} exec {testname} systemctl start syslog.socket -vvv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl is-active syslog.socket -vvv"
        sx____(cmd)
        # -> it does currently return "inactive" but same for "syslog.service"
        #
        cmd = F"{docker} exec {testname} systemctl stop syslog.socket -vvv"
        sh____(cmd)
        # CLEAN
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_37011_centos_httpd_socket_notify(self) -> None:
        """ WHEN using an image for a systemd-enabled CentOS 7,
            THEN we can create an image with an Apache HTTP service
                 being installed and enabled.
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            and in the systemctl.debug.log we can see NOTIFY_SOCKET
            messages with Apache sending a READY and MAINPID value."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos" not in image:
            if SKIP: self.skipTest("centos based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y httpd httpd-tools"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd)
        #
        ## cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"start\",\"--now\",\"-vv\"]'  {testname} {images}:{testname}"
        # sh____(cmd)
        ## cmd = F"{docker} rm --force {testname}"
        # sx____(cmd)
        ## cmd = F"{docker} run --detach --name {testname} {images}:{testname} sleep 200"
        # sh____(cmd)
        # time.sleep(3)
        #
        container = ip_container(testname)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start httpd"
        sh____(cmd)
        # THEN
        time.sleep(5)
        cmd = F"wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd)
        cmd = F"grep OK {testdir}/result.txt"
        sh____(cmd)
        # STOP
        cmd = F"{docker} exec {testname} systemctl status httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl stop httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl status httpd"
        sx____(cmd)
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        # CHECK
        debug_log = lines4(open(testdir+"/systemctl.debug.log"))
        if greps(debug_log, "Oops, "):
            self.assertTrue(greps(debug_log, "Service directory option not supported: PrivateTmp=yes"))
            self.assertTrue(greps(debug_log, "unsupported directory settings. You need to create those before using the service."))
            self.assertGreater(len(greps(debug_log, " ERROR ")), 2)
        else:
            self.assertEqual(len(greps(debug_log, " ERROR ")), 0)
        self.assertTrue(greps(debug_log, "use NOTIFY_SOCKET="))
        self.assertTrue(greps(debug_log, "read_notify.*READY=1.*MAINPID="))
        self.assertTrue(greps(debug_log, "notify start done"))
        if "centos:7" in IMAGE:
            self.assertTrue(greps(debug_log, "stop '/bin/kill' '-WINCH'"))
            self.assertTrue(greps(debug_log, "wait for PID .* is done"))
        else:
            self.assertTrue(greps(debug_log, "no ExecStop => systemctl kill"))
            self.assertTrue(greps(debug_log, "done kill PID"))
        self.assertTrue(greps(debug_log, "wait [$]NOTIFY_SOCKET"))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_37020_ubuntu_apache2_with_saved_container(self) -> None:
        """ WHEN using a systemd enabled Ubuntu as the base image
            THEN we can create an image with an Apache HTTP service
                 being installed and enabled.
            Without a special startup.sh script or container-cmd
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or UBUNTU)
        if "ubuntu" not in image:
            if SKIP: self.skipTest("ubuntu-based test")
        testname = self.testname()
        port=self.testport()
        systemctl_py = _systemctl_py
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 288
        logg.info("%s:%s %s", testname, port, image)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y apache2"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'grep python /bin/systemctl || test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable apache2"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd)
        # .........................................
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sx____(cmd)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run -d -p {port}:80 --name {testname} {images}:{testname}"
        sh____(cmd)
        # THEN
        tmp = self.testdir(testname)
        cmd = F"sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{port}"
        sh____(cmd)
        cmd = F"grep OK {tmp}/{testname}.txt"
        sh____(cmd)
        # CLEAN
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    def test_37502_centos_postgres_user_mode_container(self) -> None:
        """ WHEN using a systemd-enabled CentOS 7,
            THEN we can create an image with an PostgreSql DB service
                 being installed and enabled.
            Without a special startup.sh script or container-cmd
            one can just start the image and in the container
            expecting that the service is started. Instead of a normal root-based
            start we use a --user mode start here. But we do not use special
            user-mode *.service files."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos:7" not in image:
            if SKIP: self.skipTest("centos:7 based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        testport=self.testport()
        name="centos-postgres"
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        logg.info("%s:%s %s", testname, testport, image)
        psql = PSQL_TOOL
        PG = "/var/lib/pgsql/data"
        # WHEN
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y postgresql-server postgresql-utils"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} postgresql-setup initdb"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c \"sed -i -e 's/.*listen_addresses.*/listen_addresses = '\\\"'*'\\\"'/' {PG}/postgresql.conf\""
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'sed -i -e \"s/.*host.*ident/# &/\" {PG}/pg_hba.conf'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'echo \"host all all 0.0.0.0/0 md5\" >> {PG}/pg_hba.conf'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start postgresql -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c 'sleep 5; ps -ax'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.11'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd)
        cmd = F"{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.OK'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl stop postgresql -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable postgresql"
        sh____(cmd)
        cmd = F"{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sx____(cmd)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run -d -p {testport}:5432 --name {testname} -u postgres {images}:{testname}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sleep 5"
        sh____(cmd)
        ############ the PID-1 has been run in systemctl.py --user mode #####
        # THEN
        tmp = self.testdir(testname)
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = F"{login}; {psql} -p {testport} -h 127.0.0.1 -d postgres -c '{query}' > {tmp}/{testname}.txt"
        sh____(cmd)
        cmd = F"grep testuser_ok {tmp}/{testname}.txt"
        sh____(cmd)
        # CLEAN
        cmd = F"{docker} rmi {images}:{testname}"
        sx____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
    # @unittest.expectedFailure
    def test_38001_issue_1_start_mariadb_centos(self) -> None:
        """ issue 1: mariadb on centos does not start"""
        # this was based on the expectation that "yum install mariadb" would allow
        # for a "systemctl start mysql" which in fact it doesn't. Double-checking
        # with "yum install mariadb-server" and "systemctl start mariadb" shows
        # that mariadb's unit file is buggy, because it does not specify a kill
        # signal that it's mysqld_safe controller does not ignore.
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        # image = "centos:centos7.0.1406" # <<<< can not yum-install mariadb-server ?
        # image = "centos:centos7.1.1503"
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname = self.testname()
        testdir = self.testdir()
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        # mariadb has a TimeoutSec=300 in the unit config:
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} yum install -y mariadb"
        sh____(cmd)
        if False:
            # expected in bug report but that one can not work:
            cmd = F"{docker} exec {testname} systemctl enable mysql"
            sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd)
        out = output(cmd)
        self.assertFalse(greps(out, "mysqld"))
        #
        cmd = F"{docker} exec {testname} yum install -y mariadb-server"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd)
        out = output(cmd)
        self.assertTrue(greps(out, "mariadb.service"))
        #
        cmd = F"{docker} exec {testname} systemctl start mariadb -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "mysqld "))
        had_mysqld_safe = greps(top, "mysqld_safe ")
        #
        # NOTE: mariadb-5.5.52's mysqld_safe controller does ignore systemctl kill
        # but after a TimeoutSec=300 the 'systemctl kill' will send a SIGKILL to it
        # which leaves the mysqld to be still running -> this is an upstream error.
        cmd = F"{docker} exec {testname} systemctl stop mariadb -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        # self.assertFalse(greps(top, "mysqld "))
        if greps(top, "mysqld ") and had_mysqld_safe:
            logg.critical("mysqld still running => this is an uptream error!")
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_38002_issue_2_start_rsyslog_centos(self) -> None:
        """ issue 2: rsyslog on centos does not start"""
        # this was based on a ";Requires=xy" line in the unit file
        # but our unit parser did not regard ";" as starting a comment
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname = self.testname()
        testdir = self.testdir()
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} yum install -y rsyslog"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd)
        out = output(cmd)
        self.assertTrue(greps(out, "rsyslog.service.*enabled"))
        #
        cmd = F"{docker} exec {testname} systemctl start rsyslog -vv"
        sh____(cmd)
        #
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "/usr/sbin/rsyslog"))
        #
        cmd = F"{docker} exec {testname} systemctl stop rsyslog -vv"
        sh____(cmd)
        cmd = F"{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "/usr/sbin/rsyslog"))
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_38011_centos_httpd_socket_notify(self) -> None:
        """ start/restart behaviour if a httpd has failed - issue #11 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd)
        #
        container = ip_container(testname)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start httpd"
        sh____(cmd)
        # THEN
        time.sleep(5)
        cmd = F"wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd)
        cmd = F"grep OK {testdir}/result.txt"
        sh____(cmd)
        # STOP
        cmd = F"{docker} exec {testname} systemctl status httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl stop httpd"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl status httpd"
        #
        # CRASH
        cmd = F"{docker} exec {testname} bash -c 'cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.orig'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'echo foo > /etc/httpd/conf/httpd.conf'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start httpd"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # start failed
        cmd = F"{docker} exec {testname} systemctl status httpd"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = F"{docker} exec {testname} systemctl restart httpd"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # restart failed
        #
        cmd = F"{docker} exec {testname} bash -c 'cat /etc/httpd/conf/httpd.conf.orig > /etc/httpd/conf/httpd.conf'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl restart httpd"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        cmd = F"{docker} exec {testname} systemctl stop httpd"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = F"{docker} exec {testname} systemctl status httpd"
        sx____(cmd)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_38031_centos_nginx_restart(self) -> None:
        """ start/restart behaviour if a nginx has failed - issue #31 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y epel-release"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y nginx"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl enable nginx"
        sh____(cmd)
        cmd = F"{docker} exec {testname} rpm -q --list nginx"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'rm /usr/share/nginx/html/index.html'" # newer nginx is broken
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'echo TEST_OK > /usr/share/nginx/html/index.html'"
        sh____(cmd)
        #
        container = ip_container(testname)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start nginx"
        sh____(cmd)
        # THEN
        time.sleep(5)
        cmd = F"wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd)
        cmd = F"grep OK {testdir}/result.txt"
        sh____(cmd)
        # STOP
        cmd = F"{docker} exec {testname} systemctl status nginx"
        sh____(cmd)
        #
        top = _recent(running(output(_top_list)))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "nginx"))
        #
        cmd = F"{docker} exec {testname} systemctl restart nginx"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        top = _recent(running(output(_top_list)))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "nginx"))
        #
        cmd = F"{docker} exec {testname} systemctl status nginx"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl stop nginx"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = F"{docker} exec {testname} systemctl status nginx"
        sx____(cmd)
        top = _recent(running(output(_top_list)))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "nginx"))
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_38034_testing_mask_unmask(self) -> None:
        """ Checking the issue 34 on Ubuntu """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or UBUNTU)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname = self.testname()
        testdir = self.testdir(testname)
        port=self.testport()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 288
        logg.info("%s:%s %s", testname, port, image)
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {package} install -y rsyslog"
        sh____(cmd)
        ## container = ip_container(testname)
        cmd = F"{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl status rsyslog.service"
        sx____(cmd)
        cmd = F"{docker} exec {testname} ls -l /etc/systemd/system"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl mask rsyslog.service"
        sx____(cmd)
        cmd = F"{docker} exec {testname} systemctl status rsyslog.service"
        sx____(cmd)
        cmd = F"{docker} exec {testname} ls -l /etc/systemd/system"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl start rsyslog.service"
        sx____(cmd)
        cmd = F"{docker} exec {testname} systemctl unmask rsyslog.service"
        sx____(cmd)
        cmd = F"{docker} exec {testname} systemctl status rsyslog.service"
        sx____(cmd)
        cmd = F"{docker} exec {testname} ls -l /etc/systemd/system"
        sh____(cmd)
        #
        cmd = F"{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd)
        cmd = F"{docker} stop {testname}"
        sh____(cmd)
        cmd = F"{docker} rm --force {testname}"
        sh____(cmd)
        #
        self.rm_testdir()
    text_8051_serv = """# systemctl.py cat kubelet
[Unit]
Description=kubelet: The Kubernetes Node Agent
Documentation=https://kubernetes.io/docs/home/

[Service]
ExecStart=/usr/bin/kubelet
Restart=always
StartLimitInterval=0
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    text_8051_conf = """# cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
# Note: This dropin only works with kubeadm and kubelet v1.11+
[Service]
Environment="KUBELET_KUBECONFIG_ARGS=--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf"
Environment="KUBELET_CONFIG_ARGS=--config=/var/lib/kubelet/config.yaml"
# This is a file that "kubeadm init" and "kubeadm join" generates at runtime, populating the KUBELET_KUBEADM_ARGS variable dynamically
EnvironmentFile=-/var/lib/kubelet/kubeadm-flags.env
# This is a file that the user can use for overrides of the kubelet args as a last resort. Preferably, the user should use
# the .NodeRegistration.KubeletExtraArgs object in the configuration files instead. KUBELET_EXTRA_ARGS should be sourced from this file.
EnvironmentFile=-/etc/default/kubelet
ExecStart=
ExecStart=/usr/bin/kubelet $KUBELET_KUBECONFIG_ARGS $KUBELET_CONFIG_ARGS $KUBELET_KUBEADM_ARGS $KUBELET_EXTRA_ARGS
    """
    def test_38051_systemctl_extra_conf_dirs(self) -> None:
        """ checking issue #51 on extra conf dirs """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = cover() + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/lib/systemd/system/kubelet.service"), self.text_8051_serv)
        text_file(os_path(root, "/lib/systemd/system/kubelet.service.d/10-kubeadm.conf"), self.text_8051_conf)
        #
        cmd = F"{systemctl} environment kubelet -vvv"
        out, end = output2(cmd)
        logg.debug(" %s =>%s\n%s", cmd, end, out)
        logg.info(" HAVE %s", greps(out, "HOME"))
        logg.info(" HAVE %s", greps(out, "KUBE"))
        self.assertTrue(greps(out, "KUBELET_CONFIG_ARGS=--config"))
        self.assertEqual(len(greps(out, "KUBE")), 2)
        cmd = F"{systemctl} command kubelet -vvv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines4(out)), 1)
        self.assertTrue(greps(out, "KUBELET_KUBECONFIG_ARGS"))
        self.rm_testdir()
        self.coverage()
    def test_38052_systemctl_extra_conf_dirs(self) -> None:
        """ checking issue #52 on extra conf dirs """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = cover() + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/lib/systemd/system/kubelet.service"), self.text_8051_serv)
        text_file(os_path(root, "/etc/systemd/system/kubelet.service.d/10-kubeadm.conf"), self.text_8051_conf)
        #
        cmd = F"{systemctl} environment kubelet -vvv"
        out, end = output2(cmd)
        logg.debug(" %s =>%s\n%s", cmd, end, out)
        logg.info(" HAVE %s", greps(out, "HOME"))
        logg.info(" HAVE %s", greps(out, "KUBE"))
        self.assertTrue(greps(out, "KUBELET_CONFIG_ARGS=--config"))
        self.assertEqual(len(greps(out, "KUBE")), 2)
        cmd = F"{systemctl} command kubelet -vvv"
        out, end = output2(cmd)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines4(out)), 1)
        self.assertTrue(greps(out, "KUBELET_KUBECONFIG_ARGS"))
        self.rm_testdir()
        self.coverage()

    def test_39999_drop_local_mirrors(self) -> None:
        """ a helper when using images from https://github.com/gdraheim/docker-mirror-packages-repo"
            which create containers according to self.local_image(IMAGE) """
        docker = _docker
        containers = output(F"{docker} ps -a")
        for line in lines4(containers):
            found = re.search("\\b(opensuse-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____(F"{docker} rm -f {container}")
            found = re.search("\\b(centos-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____(F"{docker} rm -f {container}")
            found = re.search("\\b(ubuntu-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____(F"{docker} rm -f {container}")

if __name__ == "__main__":
    from optparse import OptionParser  # pylint: disable=deprecated-module
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
                  help="systemctl.py file to be tested (%default)")
    _o.add_option("-D", "--docker", metavar="EXE", default=_docker,
                  help="use another docker container tool [%default]")
    _o.add_option("-p", "--python", metavar="EXE", default=_python,
                  help="use another python execution engine [%default]")
    _o.add_option("-G", "--coverage", action="count", default=0,
                  help="gather coverage.py data (use -GG for new set) [%default]")
    _o.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    _o.add_option("--keep", action="count", default=KEEP,
                  help="keep tempdir and other data after testcase [%default]")
    _o.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    _o.add_option("--sometime", metavar="SECONDS", default=SOMETIME,
                  help="SOMETIME=%default (use 666)")
    _o.add_option("--todo", action="store_true", default=TODO,
                  help="enable TODO outtakes [%default])")
    _o.add_option("-f", "--force", action="store_true", default=False,
                  help="enable the skipped IMAGE and PYTHON versions [%default])")
    _o.add_option("-C", "--chdir", metavar="PATH", default="",
                  help="change directory before running tests {%default}")
    _o.add_option("--local", "--localmirrors", action="count", default=LOCAL,
                  help="fail if local mirror was not found [%default]")
    _o.add_option("--opensuse", metavar="NAME", default=OPENSUSE,
                  help="OPENSUSE=%default")
    _o.add_option("--ubuntu", metavar="NAME", default=UBUNTU,
                  help="UBUNTU=%default")
    _o.add_option("--centos", metavar="NAME", default=CENTOS,
                  help="CENTOS=%default")
    _o.add_option("--image", metavar="NAME", default=IMAGE,
                  help="IMAGE=%default (or CENTOS)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    SKIP = not opt.force
    TODO = opt.todo
    KEEP = opt.keep
    #
    LOCAL = int(opt.local)
    OPENSUSE = opt.opensuse
    UBUNTU = opt.ubuntu
    CENTOS = opt.centos
    IMAGE = opt.image
    if CENTOS in CENTOSVER:
        CENTOS = CENTOSVER[CENTOS]
    if ":" not in CENTOS:
        CENTOS = "centos:" + CENTOS
    if ":" not in OPENSUSE and "42" in OPENSUSE:
        OPENSUSE = "opensuse:" + OPENSUSE
    if ":" not in OPENSUSE:
        OPENSUSE = "opensuse/leap:" + OPENSUSE
    if ":" not in UBUNTU:
        UBUNTU = "ubuntu:" + UBUNTU
    if OPENSUSE not in TESTED_OS:
        logg.warning("  --opensuse '%s' was never TESTED!!!", OPENSUSE)
        beep()
        time.sleep(2)
    if UBUNTU not in TESTED_OS:
        logg.warning("  --ubuntu '%s' was never TESTED!!!", UBUNTU)
        beep()
        time.sleep(2)
    if CENTOS not in TESTED_OS:
        logg.warning("  --centos '%s' was never TESTED!!!", CENTOS)
        beep()
        time.sleep(2)
    if IMAGE and IMAGE not in TESTED_OS:
        logg.warning("  --image '%s' was never TESTED!!!", IMAGE)
        beep()
        time.sleep(2)
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    _docker = opt.docker
    #
    if opt.chdir:
        os.chdir(opt.chdir)
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    #
    if opt.coverage:
        COVERAGE = detect_local_system() # so that coverage files can be merged
        if opt.coverage > 1:
            if os.path.exists(".coverage"):
                logg.info("rm .coverage")
                os.remove(".coverage")
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = ["test_*"]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if arg.endswith("/"):
                    arg = arg[:-1]
                if "*" not in arg:
                    arg += "*"
                if len(arg) > 2 and arg[1] == "_":
                    arg = "test" + arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    if not logfile:
        if xmlresults:
            import xmlrunner # type: ignore[import-error] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore
    if opt.coverage > 1:
        print(" " + coverage_tool() + " combine")
        print(" " + coverage_tool() + " report " + _systemctl_py)
        print(" " + coverage_tool() + " annotate " + _systemctl_py)
    if not testresult.wasSuccessful():
        sys.exit(1)
