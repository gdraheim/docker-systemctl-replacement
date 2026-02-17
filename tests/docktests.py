#! /usr/bin/env python3
""" Testcases for docker-systemctl-replacement functionality """

# pylint: disable=line-too-long,too-many-lines,too-many-locals,too-many-statements,too-many-branches,too-many-arguments,too-many-positional-arguments,too-many-return-statements,too-many-nested-blocks,too-many-public-methods
# pylint: disable=bare-except,broad-exception-caught,pointless-statement,multiple-statements,f-string-without-interpolation,import-outside-toplevel,no-else-return
# pylint: disable=missing-function-docstring,unused-variable,unused-argument,unspecified-encoding,redefined-outer-name,using-constant-test,invalid-name
# pylint: disable=fixme,consider-using-with,consider-using-get,condition-evals-to-constant,chained-comparison
# pylint: disable=redefined-outer-name,unused-variable,bare-except,broad-exception-caught,pointless-statement,using-constant-test,logging-not-lazy,logging-format-interpolation,consider-using-f-string,possibly-unused-variable

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "1.7.1072"

# NOTE:
# The testcases 1000...4999 are using a --root=subdir environment
# The testcases 5000...9999 will start a docker container to work.

from typing import Dict, List, Tuple, Iterator, Iterable, Union, Optional, TextIO

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

xrange = range
string_types = (str, bytes)

logg = logging.getLogger("TESTING")
_sed = "sed"
_docker = "docker"
_python = "/usr/bin/python3"
_python2 = "/usr/bin/python"
_systemctl_py = "files/docker/systemctl3.py"
_bin_sleep="/bin/sleep"
COVERAGE = "" # make it an image name = detect_local_system()
NIX = ""
SKIP = True
TODO = False
KEEP = 0
LONGER = 2
KILLWAIT = 20

TestListen = False
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

NOT_OK: int = 1          # FOUND_ERROR
NOT_ACTIVE: int = 2      # FOUND_INACTIVE
NOT_FOUND: int = 4       # FOUND_UNKNOWN
EXIT_SIGKILL: int = 137

CENTOSVER = {"7.3": "7.3.1611", "7.4": "7.4.1708", "7.5": "7.5.1804", "7.6": "7.6.1810", "7.7": "7.7.1908", "7.9": "7.9.2009", "8.0": "8.0.1905", "8.1": "8.1.1911", "8.3": "8.3.2011"}
TESTED_OS = ["centos:7.3.1611", "centos:7.4.1708", "centos:7.5.1804", "centos:7.6.1810", "centos:7.7.1908", "centos:7.9.2009", "centos:8.0.1905", "centos:8.1.1911", "centos:8.3.2011"]
TESTED_OS += ["almalinux:9.4", "almalinux:9.1", "centos:7.5"]
TESTED_OS += ["opensuse:42.2", "opensuse:42.3", "opensuse/leap:15.0", "opensuse/leap:15.1", "opensuse/leap:15.2", "opensuse/leap:15.5", "opensuse/leap:15.6"]
TESTED_OS += ["ubuntu:14.04", "ubuntu:16.04", "ubuntu:18.04", "ubuntu:22.04", "ubuntu:24.04"]

SAVETO = "localhost:5000/systemctl"
IMAGES = "localhost:5000/systemctl/testing"
IMAGE = ""
LOCALPACKAGES = False
REMOTEPACKAGES = False
CENTOS = "almalinux:9.4"
UBUNTU = "ubuntu:22.04"
OPENSUSE = "opensuse/leap:15.6"
SOMETIME = ""

QUICK = "-c DefaultMaximumTimeout=9"
DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")

realpath = os.path.realpath

_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"

def _recent(top_list: Union[str, List[str]]) -> str:
    result = []
    for line in lines(top_list):
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

def norefresh_option(image: str) -> str:
    if "opensuse" in image:
        return "--no-refresh"
    return ""
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
        return "bash -c '%s'" % (" && ".join(cmds))
    if "opensuse/leap:15." in image:
        cmds = [
            "zypper mr --no-gpgcheck --all",
            "zypper refresh"]
        return "bash -c '%s'" % (" && ".join(cmds))
    if "opensuse" in image:
        return "zypper refresh"
    if "ubuntu" in image:
        if not checks:
            return "apt-get -o Acquire::AllowInsecureRepositories=true update"
        return "apt-get update"
    if "almalinux" in image:
        cmds = ["echo sslverify=false >> /etc/yum.conf"]
        return "bash -c '%s'" % (" && ".join(cmds))
    return "true"
def python_package(python: str, image: Optional[str] = None) -> str:
    package = os.path.basename(python)
    if package.endswith("2"):
        if image and "centos:8" in image:
            return package
        if image and "ubuntu:2" in image:
            return package
        return package[:-1]
    if image and "opensuse" in image:
        return package.replace(".", "")
    return package
def coverage_tool(image: Optional[str] = None, python: Optional[str] = None) -> str:
    image = image or IMAGE
    python = python or _python
    if "3" in python:
        return python + " -m coverage"
    else:
        if image and "centos:8" in image:
            return "coverage-2"
    return "coverage2"
def coverage_run(image: Optional[str] = None, python: Optional[str] = None, append: Optional[str] = None) -> str:
    append = append or "--append"
    options = " run '--omit=*/six.py,*/extern/*.py,*/unitconfparser.py' " + append
    return coverage_tool(image, python) + options + " -- "
def coverage_package(python: Optional[str] = None, image: Optional[str] = None) -> str:
    python = python or _python
    package = "python-coverage"
    if "3" in python:
        pythonpkg = python_package(python, image)
        package = "{pythonpkg}-coverage".format(**locals())
        if image and "centos:8" in image and python.endswith("3"):
            package = "platform-python-coverage"
    else:
        if image and "centos:8" in image:
            package = "python2-coverage"
    logg.info("detect coverage_package for %s => %s (%s)", python, package, image)
    return package
def cover(image: Optional[str] = None, python: Optional[str] = None, append: Optional[str] = None) -> str:
    if not COVERAGE: return ""
    return coverage_run(image, python, append)

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
def sh____(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Dict[str, str]]= None) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, shell=shell, env=env)
def sx____(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Dict[str, str]]= None) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, shell=shell, env=env)
def output(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Dict[str, str]]= None) -> str:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out)
def output2(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Dict[str, str]]= None) -> Tuple[str, int]:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Dict[str, str]]= None) -> Tuple[str, str, int]:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
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
def _lines(lines: Union[str, Iterable[str], TextIO]) -> List[str]:
    if isinstance(lines, string_types):
        lines = decodes(lines).split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return list(lines)
def lines(text: Union[str, Iterable[str], TextIO]) -> List[str]:
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def each_grep(pattern: str, lines: Union[str, Iterable[str], TextIO]) -> Iterator[str]:
    for line in _lines(lines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def grep(pattern: str, lines: Union[str, Iterable[str], TextIO]) -> List[str]:
    return list(each_grep(pattern, lines))
def greps(lines: Union[str, Iterable[str], TextIO], pattern: str) -> List[str]:
    return list(each_grep(pattern, lines))
def topgreps(lines: Union[str, Iterable[str], TextIO], pattern: str) -> List[str]:
    return greps(each_non_defunct(lines), pattern)
def topstr(lines: Union[str, Iterable[str]]) -> str:
    return "\n".join(each_non_runuser(lines))
def running(lines: Union[str, List[str]]) -> List[str]:
    return list(each_non_runuser(each_non_defunct(lines)))
def each_non_defunct(lines: Union[str, Iterable[str]]) -> Iterator[str]:
    for line in _lines(lines):
        if '<defunct>' in line:
            continue
        yield line
def each_non_runuser(lines: Union[str, Iterable[str]]) -> Iterator[str]:
    for line in _lines(lines):
        if 'runuser -u' in line:
            continue
        if "[gpg" in line:
            continue
        yield line
def each_clean(lines: Union[str, Iterable[str]]) -> Iterator[str]:
    for line in _lines(lines):
        if '<defunct>' in line:
            continue
        if 'runuser -u' in line:
            continue
        if "[gpg" in line:
            continue
        if 'ps -eo pid,' in line:
            continue
        yield line
def clean(lines: Union[str, List[str]]) -> str:
    return " " + "\n ".join(each_clean(lines))

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
def o22(part: str) -> str:
    return only22(part)
def oi22(part: str) -> str:
    return only22(part, indent="  ")
def only22(part: str, indent: str = "") -> str:
    if isinstance(part, string_types):
        if "\n" in part.strip():
            lines = part.strip().split("\n")
            if len(lines) <= 22:
                return part
            skipped = len(lines) - 22 + 3
            real = lines[:5] + ["...", "... (%s lines skipped)" % skipped, "..."] + lines[-14:]
            text = indent
            newline = "\n" + indent
            text += newline.join(real)
            if part.endswith("\n"):
                text += "\n"
            return text
    if isinstance(part, string_types):
        if len(part) <= 22:
            return part
        return part[:5] + "..." + part[-14:]
    if isinstance(part, list):
        if len(part) <= 22:
            return part
        skipped = len(part) - 22 + 3
        return part[:5] + ["...", "... (%s lines skipped)" % skipped, "..."] + part[-14:]
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
    import grp # pylint: disable=reimported
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
        import winsound # type: ignore[import,unused-ignore] # pylint: disable=import-error
        frequency = 2500
        duration = 1000
        winsound.Beep(frequency, duration) # type: ignore[attr-defined]
    else:
        # using 'sox' on Linux as "\a" is usually disabled
        # sx___("play -n synth 0.1 tri  1000.0")
        sx____("play -V1 -q -n -c1 synth 0.1 sine 500")

def get_proc_started(pid: int) -> float:
    """ get time process started after boot in clock ticks"""
    proc = "/proc/%s/stat" % pid
    return path_proc_started(proc)
def path_proc_started(proc: str) -> float:
    """ get time process started after boot in clock ticks"""
    if not os.path.exists(proc):
        logg.error("no such file %s", proc)
        return 0
    else:
        with open(proc, "rb") as f:
            data = f.readline()
        f.closed
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
        f.closed
        uptime_data = decodes(data).split()
        uptime_secs = float(uptime_data[0])
        logg.debug("System uptime secs: %.3f (%s)", uptime_secs, system_uptime)

        # get time now
        now = time.time()
        started_time = now - (uptime_secs - started_secs)
        logg.debug("Proc has been running since: %s" % (datetime.datetime.fromtimestamp(started_time)))

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
        logg.debug("Proc has been running since: %s" % (datetime.datetime.fromtimestamp(started_btime)))

        # return started_time
        return started_btime

def download(base_url: str, filename: str, into: str) -> None:
    if not os.path.isdir(into):
        os.makedirs(into)
    if not os.path.exists(os.path.join(into, filename)):
        sh____("cd {into} && wget {base_url}/{filename}".format(**locals()))
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
    frame = currentframe.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name # type: ignore[union-attr]
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
    LOG = get_LOG_DIR(root)
    XDG_CONFIG_HOME=get_CONFIG_HOME(root)
    XDG_RUNTIME_DIR=get_RUNTIME_DIR(root)
    return os.path.expanduser(path.replace("${", "{").format(**locals()))

def inside_container() -> bool:
    return not os.path.exists("/dev/rtc")

############ local mirror helpers #############
def ip_container(name: str) -> str:
    docker = _docker
    values = output("{docker} inspect {name}".format(**locals()))
    values = json.loads(values)
    if not values or "NetworkSettings" not in values[0]:
        logg.critical(" %s inspect %s => %s ", docker, name, values)
    return values[0]["NetworkSettings"]["IPAddress"] # type: ignore
def detect_local_system() -> str:
    """ checks the controller host (a real machine / your laptop)
        and returns a matching image name for it (docker style) """
    docker = _docker
    mirror = _mirror
    cmd = "{mirror} detect"
    out = output(cmd.format(**locals()))
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
            sx____("{docker} stop -t 6 {testname}".format(**locals()))
            sx____("{docker} rm -f {testname}".format(**locals()))
    def killall(self, what: str, wait: Optional[int] = None, sig: Optional[int] = None, but: Optional[List[str]] = None) -> None:
        # logg.info("killall %s (but %s)", what, but)
        killed = 0
        if True:
            for nextpid in os.listdir("/proc"):
                try: pid = int(nextpid)
                except: continue
                cmdline = "/proc/{pid}/cmdline".format(**locals())
                try:
                    cmd = open(cmdline).read().replace("\0", " ")
                    if fnmatch(cmd, what):
                        found = [name for name in (but or []) if name in cmd]
                        if found: continue
                        logg.info(" kill {pid} # {cmd}".format(**locals()))
                        os.kill(pid, sig or signal.SIGINT)
                        killed += 1
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        logg.info(" killing %s", e)
                except Exception as e:
                    logg.info(" killing %s", e)
        for checking in xrange(int(wait or KILLWAIT)):
            remaining = 0
            for nextpid in os.listdir("/proc"):
                try: pid = int(nextpid)
                except: continue
                cmdline = "/proc/{pid}/cmdline".format(**locals())
                try:
                    cmd = open(cmdline).read().replace("\0", " ")
                    if fnmatch(cmd, what):
                        found = [name for name in (but or []) if name in cmd]
                        if found: continue
                        remaining += 1
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        logg.info(" killing %s", e)
                except Exception as e:
                    logg.info(" killing %s", e)
            if not remaining:
                return
            if checking % 2 == 0:
                logg.info("[%02is] remaining %s", checking, remaining)
            time.sleep(1)
        if True:
            for nextpid in os.listdir("/proc"):
                try: pid = int(nextpid)
                except: continue
                cmdline = "/proc/{pid}/cmdline".format(**locals())
                try:
                    cmd = open(cmdline).read().replace("\0", " ")
                    if fnmatch(cmd, what):
                        found = [name for name in (but or []) if name in cmd]
                        if found: continue
                        logg.info(" kill {pid} # {cmd}".format(**locals()))
                        os.kill(pid, sig or signal.SIGKILL)
                        killed += 1
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        logg.info(" killing %s", e)
                except Exception as e:
                    logg.info(" killing %s", e)
    def rm_killall(self, testname: Optional[str] = None) -> None:
        self.killall("*systemctl*.py *", 10, but = ["edit ", "testsuite.py "])
        testname = testname or self.caller_testname()
        self.killall("*/{testname}_*".format(**locals()))
    def kill(self, pid: Union[str, int], wait: Optional[int] = None, sig: Optional[int] = None) -> bool:
        pid = int(pid)
        cmdline = "/proc/{pid}/cmdline".format(**locals())
        if True:
            try:
                if os.path.exists(cmdline):
                    cmd = open(cmdline).read().replace("\0", " ").strip()
                    logg.info(" kill {pid} # {cmd}".format(**locals()))
                    os.kill(pid, sig or signal.SIGINT)
            except IOError as e:
                if e.errno != errno.ENOENT:
                    logg.info(" killing %s", e)
            except Exception as e:
                logg.info(" killing %s", e)
        status = "/proc/{pid}/status".format(**locals())
        for checking in xrange(int(wait or KILLWAIT)):
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
    def makedirs(self, path: str) -> None:
        if not os.path.isdir(path):
            os.makedirs(path)
    def real_folders(self) -> Iterator[str]:
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
        testname = testname or self.caller_testname()
        newcoverage = ".coverage."+testname
        time.sleep(1)
        if os.path.isfile(".coverage"):
            # shutil.copy(".coverage", newcoverage)
            with open(".coverage", "rb") as f:
                text = f.read()
            text2 = re.sub(rb"(\]\}\})[^{}]*(\]\}\})$", rb"\1", text)
            with open(newcoverage, "wb") as f:
                f.write(text2)
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
            return "{add_hosts} {image}".format(**locals())
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
        if REMOTEPACKAGES:
            return image
        docker = _docker
        mirror = _mirror
        local = " --local" if LOCALPACKAGES else NIX
        cmd = "{mirror} start {image} --add-hosts{local}"
        out = output(cmd.format(**locals()))
        return decodes(out).strip()
    def drop_container(self, name: str) -> None:
        docker = _docker
        sx____("{docker} rm --force {name}".format(**locals()))
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
        cmd = "{docker} run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd.format(**locals()))
        print("                 # {local_image}".format(**locals()))
        print("  {docker} exec -it {name} bash".format(**locals()))
    def begin(self) -> str:
        self._started = time.time() # pylint: disable=attribute-defined-outside-init
        logg.info("[[%s]]", datetime.datetime.fromtimestamp(self._started).strftime("%H:%M:%S"))
        return "-vv"
    def end(self, maximum: int = 99) -> None:
        runtime = time.time() - self._started
        self.assertLess(runtime, maximum * LONGER)
    def assertExits(self, exitcode: int, expected: int = 0, log: str = "") -> None:
        if exitcode != expected:
            msg = ""
            if exitcode < 16:
                msg = " : "
                if exitcode & NOT_OK:
                    msg += msg + "-ERROR"
                if exitcode & NOT_ACTIVE:
                    msg += msg + "-INACTIVE"
                if exitcode & NOT_FOUND:
                    msg += msg + "-NOTFOUND"
            if exitcode > 128:
                try:
                    signum = exitcode - 128
                    for sig in signal.Signals:
                        if isinstance(sig, signal.Signals):
                            if signum == sig.value:
                                msg = " : *" + sig.name
                                break
                except:
                    if exitcode == EXIT_SIGKILL:
                        msg = ": *SIGKILL (timeout?)"
            info = "{exitcode} != {expected}{msg}".format(exitcode=exitcode,expected=expected,msg=msg)
            if log:
                logg.fatal("%s\n%s", info, log)
            raise AssertionError(info)
    def prep_coverage(self, image: Optional[str], testname: str, cov_option: Optional[str] = None) -> None:
        """ install a shell-wrapper /usr/bin/systemctl (testdir/systemctl.sh)
            which calls the develop systemctl.py prefixed by our coverage tool.
            .
            The weird name for systemctl_py_run is special for save_coverage().
            We take the realpath of our develop systemctl.py on purpose here.
        """
        docker = _docker
        testdir = self.testdir(testname, keep = True)
        cov_run = cover(image, append = "--parallel-mode")
        cov_option = cov_option or ""
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/", "_")[1:]
        shell_file(systemctl_sh, """
            #! /bin/sh
            cd /tmp
            exec {cov_run} /{systemctl_py_run} "$@" -vv {cov_option}
            """.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
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
            cmd = "{docker} export {testname} | tar tf - | grep tmp/.coverage"
            files = output(cmd.format(**locals()))
            for tmp_coverage in lines(files):
                suffix = tmp_coverage.replace("tmp/.coverage", "")
                cmd = "{docker} cp {testname}:/{tmp_coverage} .coverage.{testname}{suffix}"
                sh____(cmd.format(**locals()))
                cmd = "{sed} -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}{suffix}"
                sh____(cmd.format(**locals()))
    def build_baseimage(self, local_image: str, python: str) -> str:
        if TODO:
            return local_image
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = local_image if " " not in local_image else local_image.split(" ")[-1]
        if not image:
            return local_image
        python = python or os.path.basename(_python)
        docker = _docker
        images = IMAGES
        pythonver = python.replace(".","")
        imagever = image.replace(".","").replace(":","-").replace("/","-")
        testname = "test_{pythonver}_{imagever}".format(**locals())
        baseimage = "{images}/{testname}".format(**locals())
        cmd = "{docker} inspect {baseimage}"
        out = output(cmd.format(**locals()))
        logg.debug("docker inspect %s => %s", baseimage, out)
        oldcreated: Optional[datetime.datetime] = None
        if out.strip() and out.strip() != "[]":
            oldimage = json.loads(out)
            oldcreated = datetime.datetime.strptime(oldimage[0]["Created"].split(".")[0]+" +0000", "%Y-%m-%dT%H:%M:%S %z")
        pidstarted: Optional[datetime.datetime] = None
        pid = os.getpid()
        cmd = "ps -eo pid,lstart"
        out = output(cmd.format(**locals()), env={"LANG":"C", "LC_TIME": "C"})
        if out:
            pidprefix = "%i " % pid
            for nextline in out.splitlines():
                line = nextline.strip()
                if line.startswith(pidprefix):
                    pid_lstart = line.split(" ",1)[1]
                    pidstarted = datetime.datetime.strptime(pid_lstart, "%a %b %d %H:%M:%S %Y").astimezone()
        logg.info("pidstarted [%s] oldcreated [%s] %s", pidstarted, oldcreated, baseimage)
        assert pidstarted
        if oldcreated and oldcreated > pidstarted:
            logg.info("reuse older build of %s", baseimage)
            return local_image.replace(image, baseimage)
        logg.info("need to build fresh %s", baseimage)
        #
        pythonpkg = python_package(python, image)
        python_coverage = coverage_package(python, image)
        if "python3" in python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 188
        #
        cmd = "{docker} rmi -f {baseimage}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {image} sleep {sometime}" # to build the baseimage
        sh____(cmd.format(**locals()))
        if image:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {pythonpkg}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} commit {testname} {baseimage}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sx____(cmd.format(**locals()))
        return local_image.replace(image, baseimage)

    ################
    def test_5001_systemctl_py_inside_container(self) -> None:
        """ check that we can run systemctl.py inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {refresh}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out, "systemctl.py"))
    def test_5002_coverage_systemctl_py_inside_container(self) -> None:
        """ check that we can run systemctl.py with coverage inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS) # <<<< need to use COVERAGE image here
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        testname = self.testname()
        testdir = self.testdir()
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image) # <<<< and install the tool for the COVERAGE image
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {refresh}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd.format(**locals()))
        if "python3" in python and python != "python3":
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
            sh____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "{docker} exec {testname} {package} install -y {python_coverage}" # <<<< like here
            sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)  # setup a shell-wrapper /usr/bin/systemctl calling systemctl.py
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        self.save_coverage(testname)  # fetch {image}:.coverage and set path to develop systemctl.py
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out, "systemctl.py"))
    def test_5011_systemctl_py_enable_in_container(self) -> None:
        """ check that we can enable services in a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        testname = self.testname()
        testdir = self.testdir()
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl list-unit-files"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
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
    def test_5012_systemctl_py_default_services_in_container(self) -> None:
        """ check that we can enable services in a docker container to have default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} exec {testname} systemctl --all default-services -vv"
        out3 = output(cmd.format(**locals()))
        logg.info("\ndefault-service>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out2, "zzb.service"))
        self.assertTrue(greps(out2, "zzc.service"))
        self.assertEqual(len(lines(out2)), 2)
        self.assertTrue(greps(out3, "zzb.service"))
        self.assertTrue(greps(out3, "zzc.service"))
        # self.assertGreater(len(lines(out2)), 2)
    #
    #
    #  compare the following with the test_4030 series
    #
    #
    def test_5030_simple_service_functions_system(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_simple_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def test_5031_runuser_simple_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl"
        systemctl += " --{system}".format(**locals())
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
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, testscript), """
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
        """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} cp {testdir}/binkillall {testname}:/usr/bin/binkillall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/{testscript} {testname}:{bindir}/{testscript}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = _recent(output(_top_list))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)

        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(1) # kill is async
        cmd = "{docker} exec {testname} cat {logfile}"
        sh____(cmd.format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        # inspect the service's log
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertTrue(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vvvv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        # inspect the service's log
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertFalse(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertFalse(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertTrue(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # no PID known so 'kill $MAINPID' fails
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will NOT restart an is-active service (with ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        kill_testsleep = "{docker} exec {testname} binkillall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5032_runuser_forking_service_functions_system(self) -> None:
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
    def test_5033_runuser_forking_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --{system}".format(**locals())
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5034_runuser_notify_service_functions_system(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_notify_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end(388)
    def test_5035_runuser_notify_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 488
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --{system}".format(**locals())
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} {norefresh} install -y socat'"
        if sx____(cmd.format(**locals())): self.skipTest("unable to install socat in a container from "+image)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        sh____("{docker} exec {testname} ls -l /var/run".format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{docker} exec {testname} cat {logfile}"
        sh____(cmd.format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertExits(end, 0)
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{docker} exec {testname} cat {logfile}"
        sh____(cmd.format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertExits(end, 0)
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0, err)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertExits(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertExits(end, 0)
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5036_runuser_notify_service_functions_with_reload(self) -> None:
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
    def test_5037_runuser_notify_service_functions_with_reload_user(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        # test_5037 is triggering len(socketfile) > 100 | "new notify socketfile"
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.runuser_notify_service_functions_with_reload("user", testname, testdir)
        self.rm_testdir()
        self.end(266)  # TODO# too long?
    def runuser_notify_service_functions_with_reload(self, system: str, testname: str, testdir: str) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 488
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} {norefresh} install -y socat'"
        if sx____(cmd.format(**locals())): self.skipTest("unable to install socat in a container from "+image)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")  # TODO#
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5040_runuser_oneshot_service_functions(self) -> None:
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
    def test_5041_runuser_oneshot_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 588
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd.format(**locals()))
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5042_runuser_oneshot_and_unknown_service_functions(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5043_runuser_oneshot_template_service_functions(self) -> None:
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
    def test_5044_runuser_oneshot_template_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz@.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz@.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz@.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd.format(**locals()))
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz@rsa.service -vv"
        sh____(cmd.format(**locals()))
        #
        is_active = "{docker} exec {testname} {systemctl} is-active zzz@rsa.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz@rsa.service -vvvv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz@rsa.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz@rsa.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz@rsa.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz@rsa.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz@rsa.service -vv -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz@rsa.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.rsa.2"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test..2"))
        #
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5045_runuser_sysv_service_functions(self) -> None:
        """ check that we manage SysV services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
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
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'test -d /etc/init.d || mkdir -v /etc/init.d'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/etc/init.d/zzz"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(1) # killall is async
        sx____("{docker} exec {testname} bash -c 'sed s/^/.../ {logfile} | tail'".format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        self.end(388)
    #
    #
    #  compare the following with the test_5030 series
    #  as they are doing the same with usermode-only containers
    #
    #
    def test_5100_usermode_keeps_running(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_keeps_running("system", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_5101_usermode_keeps_running_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = testname+"_testsleep"
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p touch /tmp/run-somebody/log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /tmp/run-somebody/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody -R /tmp/run-somebody"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} is-system-running -vv"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(_top_list))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        for attempt in xrange(4): # 4*3 = 12s
            time.sleep(3)
            logg.info("=====================================================================")
            top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
            logg.info("\n>>>\n%s", top)
            cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
            out, err, end = output3(cmd.format(**locals()))
            logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/gobal.systemctl.debug.log"
            sx____(cmd.format(**locals()))
            cmd = "tail {testdir}/gobal.systemctl.debug.log | sed -e s/^/GLOBAL:.../"
            sx____(cmd.format(**locals()))
            cmd = "{docker} cp {testname}:/tmp/run-somebody/log/systemctl.debug.log {testdir}/somebody.systemctl.debug.log"
            sx____(cmd.format(**locals()))
            cmd = "tail {testdir}/somebody.systemctl.debug.log | sed -e s/^/USER:.../"
            sx____(cmd.format(**locals()))
            #
            # out, end = output2(cmd.format(**locals()))
            if greps(err, "Error response from daemon"):
                break
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        if True:
            cmd = "cat {testdir}/gobal.systemctl.debug.log | sed -e s/^/GLOBAL:.../"
            sx____(cmd.format(**locals()))
            cmd = "cat {testdir}/somebody.systemctl.debug.log | sed -e s/^/USER:.../"
            sx____(cmd.format(**locals()))
        #
        self.assertFalse(greps(err, "Error response from daemon"))
        self.assertEqual(out.strip(), "failed") # sleep did exit but not 'stop' requested
    def test_5130_usermode_simple_service_functions_system(self) -> None:
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.usermode_simple_service_functions("system", testname, testdir)
        self.rm_testdir()
        self.end(122)
    def test_5131_simple_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
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
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, testscript), """
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
        """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} cp {testdir}/binkillall {testname}:/usr/bin/binkillall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/{testscript} {testname}:{bindir}/{testscript}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output(_top_list))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        time.sleep(3)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(1) # kill is async
        cmd = "{docker} exec {testname} cat {logfile}"
        sh____(cmd.format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        # inspect the service's log
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertTrue(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vvvv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        # inspect the service's log
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        log = lines(output("{docker} exec {testname} cat {logfile}".format(**locals())))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertFalse(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertFalse(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertTrue(greps(log, "reload"))
        sh____("{docker} exec {testname} truncate -s0 {logfile}".format(**locals()))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # no PID known so 'kill $MAINPID' fails
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will NOT restart an is-active service (with ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        kill_testsleep = "{docker} exec {testname} binkillall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5132_usermode_forking_service_functions_system(self) -> None:
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
    def test_5133_usermode_forking_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5134_usermode_notify_service_functions_system(self) -> None:
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
    def test_5135_usermode_notify_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} {norefresh} install -y socat'"
        if sx____(cmd.format(**locals())): self.skipTest("unable to install socat in a container from "+image)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        sh____("{docker} exec {testname} ls -l /var/run".format(**locals()))
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{docker} exec {testname} cat {logfile}"
        sh____(cmd.format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{docker} exec {testname} cat {logfile}"
        sh____(cmd.format(**locals()))
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        self.assertEqual(end, 0)
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5136_usermode_notify_service_functions_with_reload(self) -> None:
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
    def test_5137_usermode_notify_service_functions_with_reload_user(self) -> None:
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        # test_5037 is triggering len(socketfile) > 100 | "new notify socketfile"
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 488
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} {norefresh} install -y socat'"
        if sx____(cmd.format(**locals())): self.skipTest("unable to install socat in a container from "+image)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output: Union[str, List[str]], command: str) -> List[str]:
            pids = []
            for line in _lines(ps_output):
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
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")  # TODO#
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = _recent(output("{docker} exec {testname} ps -eo etime,pid,ppid,user,args".format(**locals())))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(running(greps(top, testsleep)))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
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
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5140_usermode_oneshot_service_functions(self) -> None:
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
    def test_5141_usermode_oneshot_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/{system}/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd.format(**locals()))
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5142_usermode_oneshot_and_unknown_service_functions(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
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
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'restart' shall restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'try-restart' will restart an is-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertTrue(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service other.service -vv {quick}"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\ninactive")
        self.assertEqual(end, 3)
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        logg.info("LOG\n%s", " "+output("{docker} exec {testname} cat {logfile}".format(**locals())).replace("\n", "\n "))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5144_usermode_sysv_service_functions(self) -> None:
        """ check that we are disallowed to manage SysV services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
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
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'test -d /etc/init.d || mkdir -v /etc/init.d'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/etc/init.d/zzz"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Initscript zzz.service not for --user mode"))
        #
        # .................... deleted stuff start/stop/etc
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    #
    #
    def test_5230_bad_usermode_simple_service_functions_system(self) -> None:
        """ check that we are disallowed to manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_simple_service_functions("", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_5231_bad_simple_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 488
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
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, testscript), """
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
        """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/{testscript} {testname}:{bindir}/{testscript}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/system/zzz.service".format(**locals())
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)  # TODO?
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vvvv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5232_bad_usermode_forking_service_functions_system(self) -> None:
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
    def test_5233_bad_usermode_forking_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/system/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
    def test_5234_bad_usermode_notify_service_functions_system(self) -> None:
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
    def test_5235_bad_usermode_notify_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 488
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = testname+"_sleep"
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} {norefresh} install -y socat'"
        if sx____(cmd.format(**locals())): self.skipTest("unable to install socat in a container from "+image)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/system/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5236_bad_usermode_notify_service_functions_with_reload(self) -> None:
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
    def test_5237_bad_usermode_notify_service_functions_with_reload_user(self) -> None:
        """ check that we are disallowed to manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        # test_5037 is triggering len(socketfile) > 100 | "new notify socketfile"
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 488
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/socat || {package} {norefresh} install -y socat'"
        if sx____(cmd.format(**locals())): self.skipTest("unable to install socat in a container from "+image)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/system/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        # TODO?# self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")
        cmd = "{docker} exec {testname} {systemctl} kill zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5240_bad_usermode_oneshot_service_functions(self) -> None:
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
    def test_5241_bad_usermode_oneshot_service_functions_user(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        text_file(os_path(testdir, "zzz.service"), """
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
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/system/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 666 {logfile}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/backup {testname}:/usr/bin/backup"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/tmp/test.0"
        sh____(cmd.format(**locals()))
        testfiles = output("{docker} exec {testname} find /var/tmp -name test.*".format(**locals()))
        logg.info("found testfiles:\n%s", testfiles)
        self.assertFalse(greps(testfiles, "/var/tmp/test.1"))
        self.assertFalse(greps(testfiles, "/var/tmp/test.2"))
        #
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        is_active = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        self.assertEqual(out.strip(), "")  # TODO#
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{docker} exec {testname} {systemctl} start zzz.service -vvvv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} stop zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")
        cmd = "{docker} exec {testname} {systemctl} restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")
        cmd = "{docker} exec {testname} {systemctl} reload-or-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} reload-or-try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        logg.info("== 'try-restart' will not start a not-active service")
        cmd = "{docker} exec {testname} {systemctl} try-restart zzz.service -vv {quick}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    def test_5290_bad_usermode_other_commands(self) -> None:
        """ check that we are disallowed to manage oneshot services in a root env
            with other commands: enable, disable, mask, unmaks,..."""
        self.begin()
        testname = self.testname()
        testdir = self.testdir()
        self.bad_usermode_other_commands("", testname, testdir)
        self.rm_testdir()
        self.end()
    def test_5291_bad_usermode_other_commands(self) -> None:
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
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        quick = QUICK
        #
        user = self.user()
        root = ""
        systemctl_py = realpath(_systemctl_py)
        systemctl = "/usr/bin/systemctl" # path in container
        systemctl += " --user"
        # systemctl += " --{system}".format(**locals())
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        ends = "}"
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            {extra}
            Type=simple
            ExecStart=/usr/bin/{testsleep} 11
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        zzz_service = "/etc/systemd/system/zzz.service".format(**locals())
        cmd = "{docker} exec {testname} cp /bin/sleep {bindir}/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:{zzz_service}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chown somebody /tmp/.coverage"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]' -c 'USER somebody' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} {systemctl} enable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = "{docker} exec {testname} {systemctl} disable zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = "{docker} exec {testname} {systemctl} mask zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = "{docker} exec {testname} {systemctl} unmask zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit zzz.service not for --user mode"))
        #
        cmd = "{docker} exec {testname} {systemctl} is-active zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        self.assertFalse(greps(err, "Unit zzz.service not for --user mode"))  # TODO
        self.assertEqual(out.strip(), "inactive")
        #
        cmd = "{docker} exec {testname} {systemctl} is-failed zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertFalse(greps(err, "Unit zzz.service not for --user mode"))  # TODO
        self.assertEqual(out.strip(), "inactive")
        #
        cmd = "{docker} exec {testname} {systemctl} is-enabled zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertFalse(greps(err, "Unit zzz.service not for --user mode"))  # TODO
        self.assertEqual(out.strip(), "disabled")
        #
        cmd = "{docker} exec {testname} {systemctl} status zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 3)
        #
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
    #
    #
    #
    #
    #
    #
    def test_5430_systemctl_py_start_simple(self) -> None:
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 488
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
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            ExecStop=/usr/bin/killall testsleep
            [Install]
            WantedBy=multi-user.target""")
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", topstr(out))
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{docker} exec {testname} systemctl start zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", topstr(top))
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", topstr(top))
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5431_systemctl_py_start_extra_simple(self) -> None:
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 111
            [Install]
            WantedBy=multi-user.target""")
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/killall || {package} install -y psmisc'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{docker} exec {testname} systemctl start zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5432_systemctl_py_start_forking(self) -> None:
        """ check that we can start forking services in a container w/ PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{docker} exec {testname} systemctl start zzz.service -vv"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5433_systemctl_py_start_forking_without_pid_file(self) -> None:
        """ check that we can start forking services in a container without PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{docker} exec {testname} systemctl start zzz.service -vv"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5435_systemctl_py_start_notify_by_timeout(self) -> None:
        """ check that we can start simple services in a container w/ notify timeout"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{docker} exec {testname} systemctl start zzz.service -vvvv"
        sx____(cmd.format(**locals())) # returncode = 1
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "{docker} exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(running(greps(top, "testsleep")))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5500_systemctl_py_run_default_services_in_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} exec {testname} systemctl default -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5520_systemctl_py_run_default_services_from_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image (with --init default)"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        images = IMAGES
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"--init\",\"default\",\"-vv\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} logs {testname}"
        logs = output(cmd.format(**locals()))
        logg.info("------- docker logs\n>\n%s", logs)
        self.assertFalse(greps(logs, "starting B"))
        self.assertFalse(greps(logs, "starting C"))
        time.sleep(6) # INITLOOPS ticks at 5sec per default
        cmd = "{docker} logs {testname}"
        logs = output(cmd.format(**locals()))
        logg.info("------- docker logs\n>\n%s", logs)
        self.assertTrue(greps(logs, "starting B"))
        self.assertTrue(greps(logs, "starting C"))
        #
        cmd = "{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        cmd = "{docker} logs {testname}"
        logs = output(cmd.format(**locals()))
        logg.info("------- docker logs\n>\n%s", logs)
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5530_systemctl_py_run_default_services_from_simple_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image (without any arg)"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        images = IMAGES
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5533_systemctl_py_run_default_services_from_single_service_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} stop {testname}" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()

    def test_5600_systemctl_py_list_units_running(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted and that we can filter the list of services shown"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        self.assertEqual(len(greps(top, "testsleep")), 2)
        self.assertEqual(len(greps(top, " 1 *.*systemctl")), 1)
        self.assertEqual(len(greps(top, " root ")), 3)
        self.assertEqual(len(greps(top, " somebody ")), 1)
        #
        check = "{docker} exec {testname} bash -c 'ls -ld /var/run/*.status; grep PID /var/run/*.status'"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        check = "{docker} exec {testname} systemctl list-units"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 3)
        check = "{docker} exec {testname} systemctl list-units --state=running"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 2)
        #
        cmd = "{docker} stop {testname}" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()

    def test_5700_systemctl_py_restart_failed_units(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            and failed units are going to be restarted"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepA"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepB"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepC"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleepD"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp /usr/bin/killall {testname}:/usr/local/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
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
        InitLoopSleep = 5
        time.sleep(InitLoopSleep+1)
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        check = "{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 4)
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        # logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertFalse(greps(log, "restart"))
        #
        cmd = "{docker} exec {testname} killall testsleepD" # <<<
        sh____(cmd.format(**locals()))
        #
        time.sleep(InitLoopSleep+1)
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        # logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertFalse(greps(log, "restart"))
        #
        check = "{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 3)
        #
        cmd = "{docker} exec {testname} killall testsleepC" # <<<
        sh____(cmd.format(**locals()))
        #
        check = "{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 2)
        #
        time.sleep(InitLoopSleep+1) # max 5sec but RestartSec=9
        #
        check = "{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 2)
        #
        time.sleep(10) # to have RestartSec=9
        #
        check = "{docker} exec {testname} systemctl list-units --state=running --type=service"
        top = output(check.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertEqual(len(greps(top, "zz")), 3)
        #
        time.sleep(InitLoopSleep+1)
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "restart"))
        #
        self.assertTrue(greps(log, ".zzc.service. --- restarting failed unit"))
        self.assertTrue(greps(log, ".zzd.service. Current NoCheck .Restart=no."))
        #
        cmd = "{docker} stop {testname}" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_5881_set_user(self) -> None:
        """ check that we can run a service with User= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "{docker} exec {testname} sed -i 's/raise *$/pass/' /usr/lib64/python3.6/site-packages/coverage/misc.py"
            sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} exec {testname} find /tmp/ -name '.coverage*'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5882_set_user_and_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5883_set_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "root *nobody *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5884_set_user_and_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5885_set_user_and_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups={this_group}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5886_set_user_and_new_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *wheel *wheel .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5887_set_new_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "root *wheel *wheel .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5888_set_user_and_new_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *wheel *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5889_set_user_and_new_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups=wheel
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *wheel .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5891_set_user(self) -> None:
        """ check that we can run a service with User= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "{docker} exec {testname} sed -i 's/raise *$/pass/' /usr/lib64/python3.6/site-packages/coverage/misc.py"
            sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *trusted .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} exec {testname} find /tmp/ -name '.coverage*'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5892_set_user_and_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *trusted .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5893_set_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group={this_group}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "root *nobody *nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5894_set_user_and_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *trusted .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5895_set_user_and_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups=trusted
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *trusted .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5896_set_user_and_new_group(self) -> None:
        """ check that we can run a service with User= Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *wheel *trusted .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5897_set_new_group(self) -> None:
        """ check that we can run a service with Group= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            Group=wheel
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl  start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "root *wheel *wheel .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5898_set_user_and_new_group_and_supp_group(self) -> None:
        """ check that we can run a service with User= Group= SupplementaryGroups= settings (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
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
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *wheel *trusted,nobody .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()
    def test_5899_set_user_and_new_supp_group(self) -> None:
        """ check that we can run a service with User= SupplementaryGroups= extra (for coverage) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "python3" in _python and "centos:7" in image:
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
        python_coverage = coverage_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 388
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True -c EXEC_DUP2=False"
        testsleepA = self.testname("sleepA")
        bindir="/usr/bin"
        this_user="somebody"
        this_group="nobody"
        text_file(os_path(testdir, "zza.service"), """
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepA} 1
            User={this_user}
            SupplementaryGroups=wheel
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sx____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system /etc/systemd/user"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleepA}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep trusted /etc/group || groupadd -g 88 trusted'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep wheel /etc/group || groupadd -g 87 wheel'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody -G trusted -m"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start zza.service -vvvv"
        out, err, rc = output3(cmd.format(**locals()))
        logg.info("\n>>>(%s)\n%s\n%s", rc, i2(err), out)
        if not COVERAGE:
            self.assertEqual(rc, 0)
        #
        cmd = "{docker} exec -u somebody {testname} ps -eo pid,ppid,euser,egroup,supgrp,args"
        top = clean(output(cmd.format(**locals())))
        logg.info("\n>>>\n%s", top)
        if not COVERAGE:
            self.assertTrue(greps(top, "somebody *nobody *(wheel|trusted),(trusted|wheel) .*{testsleepA}".format(**locals())))
        #
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
        self.end()

    def test_6130_run_default_services_from_simple_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6133_run_default_services_from_single_service_saved_container(self) -> None:
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} stop {testname}" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6160_systemctl_py_init_default_halt_to_exit_container(self) -> None:
        """ check that we can 'halt' in a docker container to stop the service
            and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(2)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 111"))
        #
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv status check now
        cmd = "{docker} inspect {testname}"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = "{docker} exec {testname} systemctl halt"
        sh____(cmd.format(**locals()))
        #
        waits = 3
        for attempt in xrange(5):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = "{docker} inspect {testname}"
            inspected = output(cmd.format(**locals()))
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd.format(**locals()))
            logg.info("\n>>>\n%s", top)
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        #
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = "{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more procs - exit init-loop"))
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6170_systemctl_py_init_all_stop_last_service_to_exit_container(self) -> None:
        """ check that we can 'stop <service>' in a docker container to stop the service
            being the last service and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'test -f /etc/init.d/ondemand && systemctl disable ondemand'" # ubuntu:16.04
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"--all\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(2)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} inspect {testname}"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = "{docker} exec {testname} systemctl stop zzb.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop zzc.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd.format(**locals()))
        #
        waits = 3
        for attempt in xrange(5):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = "{docker} inspect {testname}"
            inspected = output(cmd.format(**locals()))
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd.format(**locals()))
            logg.info("\n>>>\n%s", top)
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        #
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = "{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} logs {testname}"
        logs = output(cmd.format(**locals()))
        logg.info("\n>\n%s", logs)
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more procs - exit init-loop"))
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6180_systemctl_py_init_explicit_halt_to_exit_container(self) -> None:
        """ check that we can 'halt' in a docker container to stop the service
            and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(2)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 111"))
        #
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv status check now
        cmd = "{docker} inspect {testname}"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = "{docker} exec {testname} systemctl halt"
        sh____(cmd.format(**locals()))
        #
        waits = 3
        for attempt in xrange(10):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = "{docker} inspect {testname}"
            inspected = output(cmd.format(**locals()))
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd.format(**locals()))
            logg.info("\n>>>\n%s", top)
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = "{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more procs - exit init-loop"))
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6190_systemctl_py_init_explicit_stop_last_service_to_exit_container(self) -> None:
        """ check that we can 'stop <service>' in a docker container to stop the service
            being the last service and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(2)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 111"))
        #
        cmd = "{docker} inspect {testname}"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = "{docker} exec {testname} systemctl stop zzc.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd.format(**locals()))
        #
        waits = 3
        for attempt in xrange(10):
            logg.info("[%s] waits %ss for the zombie-reaper to have cleaned up", attempt, waits)
            time.sleep(waits)
            cmd = "{docker} inspect {testname}"
            inspected = output(cmd.format(**locals()))
            state = json.loads(inspected)[0]["State"]
            logg.info("Status = %s", state["Status"])
            logg.info("ExitCode = %s", state["ExitCode"])
            if state["Status"] in ["exited"]:
                break
            cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
            top = output(cmd.format(**locals()))
            logg.info("\n>>>\n%s", top)
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = "{docker} stop {testname}" # <<< this is a no-op now
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} logs {testname}"
        logs = output(cmd.format(**locals()))
        logg.info("\n>\n%s", logs)
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        log = lines(open(testdir+"/systemctl.debug.log"))
        logg.info("systemctl.debug.log>\n\t%s", "\n\t".join(log))
        self.assertTrue(greps(log, "no more services - exit init-loop"))
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6200_systemctl_py_switch_users_is_possible(self) -> None:
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        sometime = SOMETIME or 488
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        if COVERAGE:
            cmd = "{docker} exec {testname} touch /tmp/.coverage"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} chmod 777 /tmp/.coverage"
            sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start zzb.service -v"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start zzc.service -v"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start zzd.service -v"
        sh____(cmd.format(**locals()))
        #
        # first of all, it starts commands like the service specs without user/group
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        # but really it has some user/group changed
        cmd = "{docker} exec {testname} ps -eo user,group,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "somebody .*root .*testsleep 99"))
        self.assertTrue(greps(top, "somebody .*nobody .*testsleep 111"))
        self.assertTrue(greps(top, "root .*nobody .*testsleep 122"))
        # and the pid file has changed as well
        cmd = "{docker} exec {testname} ls -l /var/run/zzb.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*root .*zzb.service.pid"))
        cmd = "{docker} exec {testname} ls -l /var/run/zzc.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*nobody .*zzc.service.pid"))
        cmd = "{docker} exec {testname} ls -l /var/run/zzd.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "root .*nobody .*zzd.service.pid"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6201_systemctl_py_switch_users_is_possible_from_saved_container(self) -> None:
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(5)
        #
        # first of all, it starts commands like the service specs without user/group
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 99"))
        self.assertTrue(greps(top, "testsleep 111"))
        self.assertTrue(greps(top, "testsleep 122"))
        # but really it has some user/group changed
        cmd = "{docker} exec {testname} ps -eo user,group,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "somebody .*root .*testsleep 99"))
        self.assertTrue(greps(top, "somebody .*nobody .*testsleep 111"))
        self.assertTrue(greps(top, "root .*nobody .*testsleep 122"))
        # and the pid file has changed as well
        cmd = "{docker} exec {testname} ls -l /var/run/zzb.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*root .*zzb.service.pid"))
        cmd = "{docker} exec {testname} ls -l /var/run/zzc.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "somebody .*nobody .*zzc.service.pid"))
        cmd = "{docker} exec {testname} ls -l /var/run/zzd.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        if TODO: self.assertTrue(greps(out, "root .*nobody .*zzd.service.pid"))
        #
        cmd = "{docker} stop {testname}" # <<<
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 99"))
        self.assertFalse(greps(top, "testsleep 111"))
        self.assertFalse(greps(top, "testsleep 122"))
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6210_switch_users_and_workingdir_coverage(self) -> None:
        """ check that we can put workingdir and setuid/setgid definitions in a service
            and code parts for that are actually executed (test case without fork before) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testsleep_sh = os_path(testdir, "testsleep.sh")
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        sometime = SOMETIME or 388
        shell_file(testsleep_sh, """
            #! /bin/sh
            logfile="/tmp/testsleep-$1.log"
            date > $logfile
            echo "pwd": `pwd` >> $logfile
            echo "user:" `id -un` >> $logfile
            echo "group:" `id -gn` >> $logfile
            testsleep $1
            """.format(**locals()))
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
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testsleep_sh} {testname}:/usr/bin/testsleep.sh"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} chmod 755 /usr/bin/testsleep.sh"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep nobody /etc/group || groupadd -g 65533 nobody'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} useradd -u 1001 somebody -g nobody"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        if COVERAGE:
            cmd = "{docker} exec {testname} touch /tmp/.coverage"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} chmod 777 /tmp/.coverage"  # << switched user may write
            sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zz4.service {testname}:/etc/systemd/system/zz4.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zz5.service {testname}:/etc/systemd/system/zz5.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zz6.service {testname}:/etc/systemd/system/zz6.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl __test_start_unit zz4.service -vvvv {cov_option}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl __test_start_unit zz5.service -vv {cov_option}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl __test_start_unit zz6.service -vv {cov_option}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} cp {testname}:/tmp/testsleep-4.log {testdir}/"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/tmp/testsleep-5.log {testdir}/"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/tmp/testsleep-6.log {testdir}/"
        sh____(cmd.format(**locals()))
        log4 = lines(open(os_path(testdir, "testsleep-4.log")))
        log5 = lines(open(os_path(testdir, "testsleep-5.log")))
        log6 = lines(open(os_path(testdir, "testsleep-6.log")))
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
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_6600_systemctl_py_can_reap_zombies_in_a_container(self) -> None:
        """ check that we can reap zombies in a container managed by systemctl.py"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        testname = self.testname()
        testdir = self.testdir()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        python_coverage = coverage_package(_python, image)
        cov_option = "--system"
        if COVERAGE:
            cov_option = "-c EXEC_SPAWN=True"
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        sometime = SOMETIME or 388
        user = self.user()
        testsleep = self.testname("sleep")
        shell_file(os_path(testdir, "zzz.init"), """
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
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"), """
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/ps || {package} install -y procps'"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sx____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
            if COVERAGE:
                cmd = "{docker} exec {testname} {package} install -y {python_coverage}"
                sh____(cmd.format(**locals()))
        self.prep_coverage(image, testname, cov_option)
        cmd = "{docker} exec {testname} cp /bin/sleep /usr/bin/{testsleep}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} mkdir -p /etc/systemd/system"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl default-services -v"
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"{cov_option}\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        cmd = "{docker} exec {testname} ps -eo state,pid,ppid,user,args"
        top = output(cmd.format(**locals()))
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
        assert m
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
        cmd = "{docker} exec {testname} kill {pid}"
        sh____(cmd.format(**locals()))
        #
        time.sleep(1)
        cmd = "{docker} exec {testname} ps -eo state,pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "Z .*sleep.*<defunct>")) # <<< we have zombie!
        for attempt in xrange(10):
            time.sleep(3)
            cmd = "{docker} exec {testname} ps -eo state,pid,ppid,user,args"
            top = output(cmd.format(**locals()))
            logg.info("\n[%s]>>>\n%s", attempt, top)
            if not greps(top, "<defunct>"):
                break
        #
        cmd = "{docker} exec {testname} ps -eo state,pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< and it's gone!
        time.sleep(1)
        #
        cmd = "{docker} stop {testname}"
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        self.save_coverage(testname)
        #
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()

    def test_7001_centos_httpd(self) -> None:
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
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 488
        logg.info("%s:%s %s", testname, testport, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --basedetach --name={testname} {bsaeimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d -p {testport}:80 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        cmd = "sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{testport}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_7002_centos_postgres(self) -> None:
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
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos:7" not in image:
            if SKIP: self.skipTest("centos:7 based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 488
        logg.info("%s:%s %s", testname, testport, image)
        psql = PSQL_TOOL
        PG = "/var/lib/pgsql/data"
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {bsaeimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y postgresql-server postgresql-utils"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} postgresql-setup initdb"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c \"sed -i -e 's/.*listen_addresses.*/listen_addresses = '\\\"'*'\\\"'/' {PG}/postgresql.conf\""
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'sed -i -e \"s/.*host.*ident/# &/\" {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'echo \"host all all 0.0.0.0/0 md5\" >> {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'sleep 5; ps -ax'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.11'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.OK'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable postgresql"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d -p {testport}:5432 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sleep 5"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -p {testport} -h 127.0.0.1 -d postgres -c '{query}' > {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_7003_opensuse_syslog(self) -> None:
        """ WHEN using a systemd-enabled CentOS 7 ..."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or OPENSUSE)
        if "opensuse" not in image:
            if SKIP: self.skipTest("opensuse based test")
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname=self.testname()
        # testport=self.testport()
        name="opensuse-syslog"
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 588
        ## logg.info("%s:%s %s", testname, testport, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y rsyslog"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        # ?# cmd = "{docker} exec {testname} systemctl enable syslog.socket"
        # ?# sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} systemctl start syslog.socket -vvv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-active syslog.socket -vvv"
        sx____(cmd.format(**locals()))
        # -> it does currently return "inactive" but same for "syslog.service"
        #
        cmd = "{docker} exec {testname} systemctl stop syslog.socket -vvv"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_7011_centos_httpd_socket_notify(self) -> None:
        """ WHEN using an image for a systemd-enabled CentOS 7,
            THEN we can create an image with an Apache HTTP service
                 being installed and enabled.
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            and in the systemctl.debug.log we can see NOTIFY_SOCKET
            messages with Apache sending a READY and MAINPID value."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos" not in image:
            if SKIP: self.skipTest("centos based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 588
        logg.info("%s:%s %s", testname, testport, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        ## cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"-vv\"]'  {testname} {images}:{testname}"
        # sh____(cmd.format(**locals()))
        ## cmd = "{docker} rm --force {testname}"
        # sx____(cmd.format(**locals()))
        ## cmd = "{docker} run --detach --name {testname} {images}:{testname} sleep 200"
        # sh____(cmd.format(**locals()))
        # time.sleep(3)
        #
        container = ip_container(testname)
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl status httpd"
        sx____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        # CHECK
        debug_log = lines(open(testdir+"/systemctl.debug.log"))
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
    def test_7020_ubuntu_apache2_with_saved_container(self) -> None:
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
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or UBUNTU)
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
        sometime = SOMETIME or 588
        logg.info("%s:%s %s", testname, port, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y apache2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'grep python /bin/systemctl || test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable apache2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        # .........................................
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d -p {port}:80 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        cmd = "sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{port}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    def test_7502_centos_postgres_user_mode_container(self) -> None:
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
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos:7" not in image:
            if SKIP: self.skipTest("centos:7 based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 588
        logg.info("%s:%s %s", testname, testport, image)
        psql = PSQL_TOOL
        PG = "/var/lib/pgsql/data"
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y postgresql-server postgresql-utils"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} postgresql-setup initdb"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c \"sed -i -e 's/.*listen_addresses.*/listen_addresses = '\\\"'*'\\\"'/' {PG}/postgresql.conf\""
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'sed -i -e \"s/.*host.*ident/# &/\" {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'echo \"host all all 0.0.0.0/0 md5\" >> {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c 'sleep 5; ps -ax'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.11'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sh -c \"echo 'CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.OK'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable postgresql"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d -p {testport}:5432 --name {testname} -u postgres {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} sleep 5"
        sh____(cmd.format(**locals()))
        ############ the PID-1 has been run in systemctl.py --user mode #####
        # THEN
        tmp = self.testdir(testname)
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -p {testport} -h 127.0.0.1 -d postgres -c '{query}' > {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_docker(testname)
        self.rm_testdir()
    # @unittest.expectedFailure
    def test_8001_issue_1_start_mariadb_centos(self) -> None:
        """ issue 1: mariadb on centos does not start"""
        # this was based on the expectation that "yum install mariadb" would allow
        # for a "systemctl start mysql" which in fact it doesn't. Double-checking
        # with "yum install mariadb-server" and "systemctl start mariadb" shows
        # that mariadb's unit file is buggy, because it does not specify a kill
        # signal that it's mysqld_safe controller does not ignore.
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 588
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        # mariadb has a TimeoutSec=300 in the unit config:
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y mariadb"
        sh____(cmd.format(**locals()))
        if False:
            # expected in bug report but that one can not work:
            cmd = "{docker} exec {testname} systemctl enable mysql"
            sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertFalse(greps(out, "mysqld"))
        #
        cmd = "{docker} exec {testname} {package} {norefresh} install -y mariadb-server"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "mariadb.service"))
        #
        cmd = "{docker} exec {testname} systemctl start mariadb -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "mysqld "))
        had_mysqld_safe = greps(top, "mysqld_safe ")
        #
        # NOTE: mariadb-5.5.52's mysqld_safe controller does ignore systemctl kill
        # but after a TimeoutSec=300 the 'systemctl kill' will send a SIGKILL to it
        # which leaves the mysqld to be still running -> this is an upstream error.
        cmd = "{docker} exec {testname} systemctl stop mariadb -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        # self.assertFalse(greps(top, "mysqld "))
        if greps(top, "mysqld ") and had_mysqld_safe:
            logg.critical("mysqld still running => this is an uptream error!")
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_8002_issue_2_start_rsyslog_centos(self) -> None:
        """ issue 2: rsyslog on centos does not start"""
        # this was based on a ";Requires=xy" line in the unit file
        # but our unit parser did not regard ";" as starting a comment
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
       images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if "python3" in _python and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname = self.testname()
        testdir = self.testdir()
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 488
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} yum install -y rsyslog"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "rsyslog.service.*enabled"))
        #
        cmd = "{docker} exec {testname} systemctl start rsyslog -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "/usr/sbin/rsyslog"))
        #
        cmd = "{docker} exec {testname} systemctl stop rsyslog -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps -eo pid,ppid,user,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "/usr/sbin/rsyslog"))
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_8011_centos_httpd_socket_notify(self) -> None:
        """ start/restart behaviour if a httpd has failed - issue #11 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 588
        logg.info("%s:%s %s", testname, testport, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        container = ip_container(testname)
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop httpd"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl status httpd"
        #
        # CRASH
        cmd = "{docker} exec {testname} bash -c 'cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.orig'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo foo > /etc/httpd/conf/httpd.conf'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # start failed
        cmd = "{docker} exec {testname} systemctl status httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{docker} exec {testname} systemctl restart httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # restart failed
        #
        cmd = "{docker} exec {testname} bash -c 'cat /etc/httpd/conf/httpd.conf.orig > /etc/httpd/conf/httpd.conf'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl restart httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        cmd = "{docker} exec {testname} systemctl stop httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = "{docker} exec {testname} systemctl status httpd"
        sx____(cmd.format(**locals()))
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_8031_centos_nginx_restart(self) -> None:
        """ start/restart behaviour if a nginx has failed - issue #31 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or CENTOS)
        if "centos" not in image:
            if SKIP: self.skipTest("centos-based test")
        if "python3" in _python and "centos:7" in image:
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
        sometime = SOMETIME or 588
        logg.info("%s:%s %s", testname, testport, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {package} install -y epel-release"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} {package} install -y nginx"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable nginx"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} rpm -q --list nginx"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'rm /usr/share/nginx/html/index.html'" # newer nginx is broken
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo TEST_OK > /usr/share/nginx/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        container = ip_container(testname)
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start nginx"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status nginx"
        sh____(cmd.format(**locals()))
        #
        top = _recent(running(output(_top_list)))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "nginx"))
        #
        cmd = "{docker} exec {testname} systemctl restart nginx"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        top = _recent(running(output(_top_list)))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "nginx"))
        #
        cmd = "{docker} exec {testname} systemctl status nginx"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop nginx"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = "{docker} exec {testname} systemctl status nginx"
        sx____(cmd.format(**locals()))
        top = _recent(running(output(_top_list)))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "nginx"))
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        #
        self.rm_docker(testname)
        self.rm_testdir()
    def test_8034_testing_mask_unmask(self) -> None:
        """ Checking the issue 34 on Ubuntu """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if COVERAGE and SKIP: self.skipTest("does not provide additional coverage")
        images = IMAGES
        image = self.local_image(COVERAGE or IMAGE or UBUNTU)
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        testname = self.testname()
        testdir = self.testdir(testname)
        port=self.testport()
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 588
        logg.info("%s:%s %s", testname, port, image)
        #
        baseimage = self.build_baseimage(image, python)
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {baseimage} sleep {sometime}"
        sh____(cmd.format(**locals()))
        if image == baseimage:
            cmd = "{docker} exec {testname} {refresh}"
            sh____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
            sh____(cmd.format(**locals()))
            if "python3" in python and python != "python3":
                cmd = "{docker} exec {testname} bash -c 'ls -l /usr/bin/python3 || ln -s {python} /usr/bin/python3'"
                sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        norefresh = norefresh_option(image)
        cmd = "{docker} exec {testname} {package} {norefresh} install -y rsyslog"
        sh____(cmd.format(**locals()))
        ## container = ip_container(testname)
        cmd = "{docker} exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl status rsyslog.service"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ls -l /etc/systemd/system"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl mask rsyslog.service"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl status rsyslog.service"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ls -l /etc/systemd/system"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start rsyslog.service"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl unmask rsyslog.service"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl status rsyslog.service"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ls -l /etc/systemd/system"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
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
    def test_8051_systemctl_extra_conf_dirs(self) -> None:
        """ checking issue #51 on extra conf dirs """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = cover() + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/lib/systemd/system/kubelet.service"), self.text_8051_serv)
        text_file(os_path(root, "/lib/systemd/system/kubelet.service.d/10-kubeadm.conf"), self.text_8051_conf)
        #
        cmd = "{systemctl} environment kubelet -vvv"
        out, end = output2(cmd.format(**locals()))
        logg.debug(" %s =>%s\n%s", cmd, end, out)
        logg.info(" HAVE %s", greps(out, "HOME"))
        logg.info(" HAVE %s", greps(out, "KUBE"))
        self.assertTrue(greps(out, "KUBELET_CONFIG_ARGS=--config"))
        self.assertEqual(len(greps(out, "KUBE")), 2)
        cmd = "{systemctl} command kubelet -vvv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 1)
        self.assertTrue(greps(out, "KUBELET_KUBECONFIG_ARGS"))
        self.rm_testdir()
        self.coverage()
    def test_8052_systemctl_extra_conf_dirs(self) -> None:
        """ checking issue #52 on extra conf dirs """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = cover() + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/lib/systemd/system/kubelet.service"), self.text_8051_serv)
        text_file(os_path(root, "/etc/systemd/system/kubelet.service.d/10-kubeadm.conf"), self.text_8051_conf)
        #
        cmd = "{systemctl} environment kubelet -vvv"
        out, end = output2(cmd.format(**locals()))
        logg.debug(" %s =>%s\n%s", cmd, end, out)
        logg.info(" HAVE %s", greps(out, "HOME"))
        logg.info(" HAVE %s", greps(out, "KUBE"))
        self.assertTrue(greps(out, "KUBELET_CONFIG_ARGS=--config"))
        self.assertEqual(len(greps(out, "KUBE")), 2)
        cmd = "{systemctl} command kubelet -vvv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 1)
        self.assertTrue(greps(out, "KUBELET_KUBECONFIG_ARGS"))
        self.rm_testdir()
        self.coverage()
    def test_8888_drop_local_mirrors(self) -> None:
        """ a helper when using images from https://github.com/gdraheim/docker-mirror-packages-repo"
            which create containers according to self.local_image(IMAGE) """
        docker = _docker
        containers = output("{docker} ps -a".format(**locals()))
        for line in lines(containers):
            found = re.search("\\b(opensuse-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____("{docker} rm -f {container}".format(**locals()))
            found = re.search("\\b(centos-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____("{docker} rm -f {container}".format(**locals()))
            found = re.search("\\b(ubuntu-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____("{docker} rm -f {container}".format(**locals()))

if __name__ == "__main__":
    from optparse import OptionParser # pylint: disable=deprecated-module # not anymore
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
    _o.add_option("-a", "--coverage", action="count", default=0,
                  help="gather coverage.py data (use -aa for new set) [%default]")
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
    _o.add_option("--local", action="store_true", default=LOCALPACKAGES,
                  help="only use local package mirrors [%default]")
    _o.add_option("--remote", action="store_true", default=REMOTEPACKAGES,
                  help="only use remote package mirrors [%default]")
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
    LOCALPACKAGES = opt.local
    REMOTEPACKAGES = opt.remote
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
        logg.warning("COVERAGE = %s", COVERAGE)
        if opt.coverage > 1:
            if os.path.exists(".coverage"):
                logg.info("rm .coverage")
                os.remove(".coverage")
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = ["test_*"]
    for arg in args:
        for testname in arg.split(","):
            if not testname: continue
            for classname in sorted(globals()):
                if not classname.endswith("Test"):
                    continue
                testclass = globals()[classname]
                for method in sorted(dir(testclass)):
                    if "*" not in testname: testname += "*"
                    if len(testname) > 2 and testname[1] == "_":
                        testname = "test" + testname[1:]
                    if fnmatch(method, testname):
                        suite.addTest(testclass(method))
    # select runner
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "wb")
        logg.info("xml results into %s", opt.xmlresults)
    if not logfile:
        if xmlresults:
            import xmlrunner # type: ignore[import,unused-ignore] # pylint: disable=import-error
            Runner = xmlrunner.XMLTestRunner
            result = Runner(xmlresults).run(suite)
        else:
            Runner = unittest.TextTestRunner
            result = Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import,unused-ignore] # pylint: disable=import-error
            Runner = xmlrunner.XMLTestRunner
        result = Runner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore[unused-ignore]
    if opt.coverage:
        print("# please run:")
        print(" " + coverage_tool() + " combine")
        print(" " + coverage_tool() + " report " + _systemctl_py)
        print(" " + coverage_tool() + " annotate " + _systemctl_py)
    if not result.wasSuccessful():
        sys.exit(1)
