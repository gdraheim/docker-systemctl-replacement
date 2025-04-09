#! /usr/bin/python3
# pylint: disable=line-too-long,missing-function-docstring,missing-class-docstring,consider-using-f-string,import-outside-toplevel
# pylint: disable=too-many-lines,multiple-statements,unspecified-encoding,dangerous-default-value,unnecessary-lambda,superfluous-parens
""" run 'systemctl start' and other systemctl commands based on available *.service descriptions without a systemd daemon running in the system """
import threading
import grp
import pwd
import select
import fcntl
import string
import datetime
import socket
import time
import signal
import sys
import os
import glob
import errno
import collections
import shlex
import fnmatch
import re

from typing import Dict, Iterable, List, NoReturn, Optional, TextIO, Tuple, Type, Union, Match, Iterator, NamedTuple
from types import TracebackType

__copyright__: str = "(C) 2024-2025 Guido U. Draheim, licensed under the EUPL"
__version__: str = "2.0.1144"

import logging
logg: logging.Logger = logging.getLogger("systemctl")

if sys.version[0] != '2':
    stringtypes = str # type: ignore[name-defined] # pylint: disable=invalid-name
else:
    stringtypes = basestring # type: ignore[name-defined,misc] # pylint: disable=undefined-variable # PEP 484

NEVER = False
TRUE = True
NIX = ""
ALL = "*"
DEBUG_AFTER: bool = False
DEBUG_STATUS: bool = False
DEBUG_BOOTTIME: bool = False
DEBUG_INITLOOP: bool = False
DEBUG_KILLALL: bool = False
DEBUG_FLOCK = False
DEBUG_PRINTRESULT = False
TESTING_LISTEN = False
TESTING_ACCEPT = False

HINT = (logging.DEBUG + logging.INFO) // 2
NOTE = (logging.WARNING + logging.INFO) // 2
DONE = (logging.WARNING + logging.ERROR) // 2
logging.addLevelName(HINT, "HINT")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(DONE, "DONE")

def logg_debug_flock(msg: str, *args: Union[str, int]) -> None:
    if DEBUG_FLOCK:
        logg.debug(msg, *args) # pragma: no cover
def logg_debug_after(msg: str, *args: Union[str, int]) -> None:
    if DEBUG_AFTER:
        logg.debug(msg, *args) # pragma: no cover

NOT_A_PROBLEM: int = 0   # FOUND_OK
NOT_OK: int = 1          # FOUND_ERROR
NOT_ACTIVE: int = 2      # FOUND_INACTIVE
NOT_FOUND: int = 4       # FOUND_UNKNOWN

# defaults for options
EXTRA_VARS: List[str] = []
DO_FORCE: bool = False
DO_FULL: bool = False
LOG_LINES = 0
NO_PAGER = False
DO_NOW: int = False
NO_RELOAD = False
NO_LEGEND: bool = False
NO_ASK_PASSWORD: bool = False
PRESET_MODE: str = "all"
DO_QUIET: bool = False
ROOT: str = NIX
SHOW_ALL: int = 0
USER_MODE: bool = False
ONLY_WHAT: List[str] = []
ONLY_TYPE: List[str] = []
ONLY_STATE: List[str] = []
ONLY_PROPERTY: List[str] = []
LOG_BUFSIZE = 8192
FORCE_IPV4 = False
FORCE_IPV6 = False
INIT_MODE = 0
INIT_LOOP = 1
EXIT_MODE = 0
EXIT_NO_PROCS_LEFT = 1
EXIT_NO_SERVICES_LEFT = 2

# common default paths
SYSD_SYSTEM_FOLDERS = [
    "/etc/systemd/system",
    "/run/systemd/system",
    "/var/run/systemd/system",
    "/usr/local/lib/systemd/system",
    "/usr/lib/systemd/system",
    "/lib/systemd/system",
]
SYSD_USER_FOLDERS: List[str] = [
    "{XDG_CONFIG_HOME}/systemd/user",
    "/etc/systemd/user",
    "{XDG_RUNTIME_DIR}/systemd/user",
    "/run/systemd/user",
    "/var/run/systemd/user",
    "{XDG_DATA_HOME}/systemd/user",
    "/usr/local/lib/systemd/user",
    "/usr/lib/systemd/user",
    "/lib/systemd/user",
]
SYSV_INIT_FOLDERS = [
    "/etc/init.d",
    "/run/init.d",
    "/var/run/init.d",
]
SYSD_PRESET_FOLDERS: List[str] = [
    "/etc/systemd/system-preset",
    "/run/systemd/system-preset",
    "/var/run/systemd/system-preset",
    "/usr/local/lib/systemd/system-preset",
    "/usr/lib/systemd/system-preset",
    "/lib/systemd/system-preset",
]

# standard paths
_dev_null = "/dev/null"  # pylint: disable=invalid-name
_dev_zero = "/dev/zero"  # pylint: disable=invalid-name
_etc_hosts = "/etc/hosts"  # pylint: disable=invalid-name
_rc3_boot_folder = "/etc/rc3.d"  # pylint: disable=invalid-name
_rc3_init_folder = "/etc/init.d/rc3.d"  # pylint: disable=invalid-name
_rc5_boot_folder = "/etc/rc5.d"  # pylint: disable=invalid-name
_rc5_init_folder = "/etc/init.d/rc5.d"  # pylint: disable=invalid-name
_proc_pid_stat = "/proc/{pid}/stat"  # pylint: disable=invalid-name
_proc_pid_status = "/proc/{pid}/status"  # pylint: disable=invalid-name
_proc_pid_cmdline= "/proc/{pid}/cmdline"  # pylint: disable=invalid-name
_proc_pid_dir = "/proc"  # pylint: disable=invalid-name
_proc_sys_uptime = "/proc/uptime"  # pylint: disable=invalid-name
_proc_sys_stat = "/proc/stat"  # pylint: disable=invalid-name

# default values
SYSTEMD_VERSION: int = 219
SYSINIT_TARGET: str = "sysinit.target"
SYSINIT_WAIT: int = 5 # max for target
YIELD: float = 0.5 # for cooperative multi-tasking
MAXTIMEOUT: int = 200   # overrides all other
MinimumTimeoutStartSec: int = 4
MinimumTimeoutStopSec: int = 4
DefaultTimeoutStartSec: int = 90   # official value
DefaultTimeoutStopSec: int = 90    # official value
DefaultTimeoutAbortSec: int = 3600 # officially it none (usually larget than StopSec)
DefaultRestartSec: float = 0.1       # official value of 100ms
DefaultStartLimitIntervalSec: int = 10 # official value
DefaultStartLimitBurst: int = 5        # official value
INITLOOPSLEEP = 5
MAXLOCKWAIT: int = 0 # equals MAXTIMEOUT
DEFAULT_PATH: str = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
RESET_LOCALE: str = """LANG LANGUAGE LC_CTYPE LC_NUMERIC LC_TIME LC_COLLATE LC_MONETARY LC_MESSAGES
                       LC_PAPER LC_NAME LC_ADDRESS LC_TELEPHONE LC_MEASUREMENT LC_IDENTIFICATION LC_ALL"""
LOCALE_CONF: str ="/etc/locale.conf"
LISTEN_BACKLOG: int =2
NOTIFY_TIMEOUT = 3
NOTIFY_QUICKER = 100

DEFAULT_UNIT: str = os.environ.get("SYSTEMD_DEFAULT_UNIT", "default.target") # systemd.exe --unit=default.target
DEFAULT_TARGET: str = os.environ.get("SYSTEMD_DEFAULT_TARGET", "multi-user.target") # DEFAULT_UNIT fallback
# LOG_LEVEL = os.environ.get("SYSTEMD_LOG_LEVEL", "info") # systemd.exe --log-level
# LOG_TARGET = os.environ.get("SYSTEMD_LOG_TARGET", "journal-or-kmsg") # systemd.exe --log-target
# LOG_LOCATION = os.environ.get("SYSTEMD_LOG_LOCATION", "no") # systemd.exe --log-location
# SHOW_STATUS = os.environ.get("SYSTEMD_SHOW_STATUS", "auto") # systemd.exe --show-status
STANDARD_INPUT=os.environ.get("SYSTEMD_STANDARD_INPUT", "null")
STANDARD_OUTPUT=os.environ.get("SYSTEMD_STANDARD_OUTPUT", "journal") # systemd.exe --default-standard-output
STANDARD_ERROR=os.environ.get("SYSTEMD_STANDARD_ERROR", "inherit") # systemd.exe --default-standard-error

EXEC_SPAWN = False
EXEC_DUP2 = True
REMOVE_LOCK_FILE: bool = False
BOOT_PID_MIN: int = 0
BOOT_PID_MAX: int = -9
PROC_MAX_DEPTH: int = 100
EXPAND_VARS_MAXDEPTH: int = 20
EXPAND_KEEP_VARS: bool = True
RESTART_FAILED_UNITS: bool = True
ACTIVE_IF_ENABLED=False
OK_CONDITION_FAILURE = True

TAIL_CMDS = ["/bin/tail", "/usr/bin/tail", "/usr/local/bin/tail"]
LESS_CMDS = ["/bin/less", "/usr/bin/less", "/usr/local/bin/less"]
CAT_CMDS = ["/bin/cat", "/usr/bin/cat", "/usr/local/bin/cat"]

# The systemd default was NOTIFY_SOCKET="/var/run/systemd/notify"
NOTIFY_SOCKET_FOLDER = "{RUN}/systemd" # alias /run/systemd
JOURNAL_LOG_FOLDER: str = "{LOG}/journal"

SYSTEMCTL_DEBUG_LOG: str = "{LOG}/systemctl.debug.log"
SYSTEMCTL_EXTRA_LOG: str = "{LOG}/systemctl.log"

SYSD_RUNLEVEL_TARGETS: List[str] = ["poweroff.target", "rescue.target", "sysinit.target", "basic.target", "multi-user.target", "graphical.target", "reboot.target"]
SYSD_FEATURES_TARGETS: List[str] = ["network.target", "remote-fs.target", "local-fs.target", "timers.target", "nfs-client.target"]
SYSD_COMMON_TARGETS: List[str] = ["default.target"] + SYSD_RUNLEVEL_TARGETS + SYSD_FEATURES_TARGETS

# inside a docker we pretend the following
SYSD_ENABLED_TARGETS = ["default.target", "multi-user.target", "remote-fs.target"]
SYSD_DISABLED_TARGETS: List[str] = ["graphical.target", "resue.target", "nfs-client.target"]

SYSD_TARGET_REQUIRES = {"graphical.target": "multi-user.target", "multi-user.target": "basic.target", "basic.target": "sockets.target"}

SYSD_RUNLEVEL_FOR: Dict[str, str] = {} # the official list
SYSD_RUNLEVEL_FOR["0"] = "poweroff.target"
SYSD_RUNLEVEL_FOR["1"] = "rescue.target"
SYSD_RUNLEVEL_FOR["2"] = "multi-user.target"
SYSD_RUNLEVEL_FOR["3"] = "multi-user.target"
SYSD_RUNLEVEL_FOR["4"] = "multi-user.target"
SYSD_RUNLEVEL_FOR["5"] = "graphical.target"
SYSD_RUNLEVEL_FOR["6"] = "reboot.target"

SYSD_TARGET_FOR: Dict[str, str] = {} # by rule of thumb
SYSD_TARGET_FOR["$local_fs"] = "local-fs.target"
SYSD_TARGET_FOR["$network"] = "network.target"
SYSD_TARGET_FOR["$remote_fs"] = "remote-fs.target"
SYSD_TARGET_FOR["$timer"] = "timers.target"


# sections from conf
Unit = "Unit"  # pylint: disable=invalid-name
Service = "Service"  # pylint: disable=invalid-name
Socket = "Socket"  # pylint: disable=invalid-name
Install = "Install"  # pylint: disable=invalid-name

# https://tldp.org/LDP/abs/html/exitcodes.html
# https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

def sock_type_str(value: int) -> str:
    if value == socket.SOCK_DGRAM:
        return "UDP"
    if value == socket.SOCK_STREAM:
        return "TCP"
    if value == socket.SOCK_RAW: # pragma: no cover
        return "RAW"
    if value == socket.SOCK_RDM: # pragma: no cover
        return "RDM"
    if value == socket.SOCK_SEQPACKET: # pragma: no cover
        return "SEQ"
    return "<?>" # pragma: no cover

def yes_str(value: Union[bool, None]) -> str:
    if value is True:
        return "yes"
    if not value:
        return "no"
    return str(value) # pragma: no cover (is always bool)
def nix_str(part: Union[str, int, float, None]) -> str:
    if not part: # "", False, None, 0
        return NIX
    if part is True: # pragma: no cover (is never a bool)
        return ALL
    return str(part)
def q_str(part: Union[str, None]) -> str:
    if part is None:
        return NIX
    if isinstance(part, int): # pragma: no cover (is never int)
        return str(part)
    return "'%s'" % part
def shell_cmd(cmd: List[str]) -> str:
    return " ".join([q_str(part) for part in cmd])
def to_int_if(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default
def to_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default
def to_list(value: Union[str, List[str], Tuple[str], Tuple[str, ...], None]) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return str(value or "").split(",")
def commalist(value: Iterable[str]) -> List[str]:
    return list(_commalist(value))
def _commalist(value: Iterable[str]) -> Iterator[str]:
    for val in value:
        if not val:
            continue
        for elem in val.strip().split(","):
            yield elem
def int_mode(value: str) -> Optional[int]:
    try:
        return int(value, 8)
    except ValueError:
        return None # pragma: no cover
def unit_of(module: str) -> str:
    if "." not in module:
        return module + ".service"
    return module
def o30(part: str) -> str:
    if isinstance(part, stringtypes):
        if len(part) <= 30:
            return part
        return part[:5] + "..." + part[-21:]
    return part # pragma: no cover (is always str)
def o44(part: str) -> str:
    if isinstance(part, stringtypes):
        if len(part) <= 44:
            return part
        return part[:10] + "..." + part[-31:]
    return part # pragma: no cover (is always str)
def o77(part: str) -> str:
    if isinstance(part, stringtypes):
        if len(part) <= 77:
            return part
        return part[:20] + "..." + part[-54:]
    return part # pragma: no cover (is always str)
def delayed(attempt: int, suffix: str = ".") -> str:
    if not attempt:
        return "..%s" % (suffix)
    if attempt < 10:
        return "%+i%s" % (attempt, suffix)
    return "%i%s" % (attempt, suffix)
def fnmatched(text: str, *patterns: str) -> bool:
    if not patterns:
        return True
    for pattern in patterns:
        if fnmatch.fnmatchcase(text, pattern):
            return True
    return False

def unit_name_escape(text: str) -> str:
    # https://www.freedesktop.org/software/systemd/man/systemd.unit.html#id-1.6
    esc = re.sub("([^a-z-AZ.-/])", lambda m: "\\x%02x" % ord(m.group(1)[0]), text)
    return esc.replace("/", "-")
def unit_name_unescape(text: str) -> str:
    esc = text.replace("-", "/")
    return re.sub("\\\\x(..)", lambda m: "%c" % chr(int(m.group(1), 16)), esc)

def is_good_root(root: Optional[str]) -> bool:
    if not root:
        return True
    return root.strip(os.path.sep).count(os.path.sep) > 1
def os_path(root: Optional[str], path: str) -> str:
    if not root:
        return path
    if not path:
        return path
    if is_good_root(root) and path.startswith(root):
        return path
    if path.startswith(os.path.sep):
        path1 = path[1:]
        if path1.startswith(os.path.sep):
            if DEBUG_STATUS:
                logg.debug("path starting with '//' is not moved to _root: %s", path)
            return path # real systemd accepts //paths as well
        else:
            return os.path.join(root, path1)
    else:
        if DEBUG_STATUS:
            logg.debug("adding _root prefix to path being not absolute: %s", path)
        return os.path.join(root, path)
def path_replace_extension(path: str, old: str, new: str) -> str:
    if path.endswith(old):
        path = path[:-len(old)]
    return path + new
def get_exist_path(paths: List[str]) -> Optional[str]:
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def get_PAGER() -> List[str]:  # pylint: disable=invalid-name
    PAGER = os.environ.get("PAGER", "less")  # pylint: disable=possibly-unused-variable,invalid-name
    pager = os.environ.get("SYSTEMD_PAGER", "{PAGER}").format(**locals())
    options = os.environ.get("SYSTEMD_LESS", "FRSXMK") # see 'man timedatectl'
    if not pager: pager = "cat"
    if "less" in pager and options:
        return [pager, "-" + options]
    return [pager]

def os_getlogin() -> str:
    """ NOT using os.getlogin() """
    return pwd.getpwuid(os.geteuid()).pw_name

def get_runtime_dir() -> str:
    explicit = os.environ.get("XDG_RUNTIME_DIR", "")
    if explicit:
        return explicit
    user = os_getlogin()
    return "/tmp/run-"+user
def get_RUN(root: bool = False) -> str:  # pylint: disable=invalid-name
    tmp_var = get_TMP(root)  # pylint: disable=possibly-unused-variable
    if ROOT:
        tmp_var = ROOT
    if root:
        for p in ("/run", "/var/run", "{tmp_var}/run"):
            path = p.format(**locals())
            if os.path.isdir(path) and os.access(path, os.W_OK):
                return path
        os.makedirs(path) # "/tmp/run"
        return path
    else:
        uid = get_USER_ID(root)  # pylint: disable=possibly-unused-variable
        for p in ("/run/user/{uid}", "/var/run/user/{uid}", "{tmp_var}/run-{uid}"):
            path = p.format(**locals())
            if os.path.isdir(path) and os.access(path, os.W_OK):
                return path
        os.makedirs(path, 0o700) # "/tmp/run/user/{uid}"
        return path
def get_PID_DIR(root: bool = False) -> str:  # pylint: disable=invalid-name
    if root:
        return get_RUN(root)
    else:
        return os.path.join(get_RUN(root), "run") # compat with older systemctl.py

def get_home() -> str:
    if NEVER: # pragma: no cover
        explicit = os.environ.get("HOME", "")   # >> On Unix, an initial ~ (tilde) is replaced by the
        if explicit:                            # environment variable HOME if it is set; otherwise
            return explicit                     # the current users home directory is looked up in the
        uid = os.geteuid()                      # password directory through the built-in module pwd.
        return pwd.getpwuid(uid).pw_name        # An initial ~user i looked up directly in the
    return os.path.expanduser("~")              # password directory. << from docs(os.path.expanduser)
def get_HOME(root: bool = False) -> str:  # pylint: disable=invalid-name
    if root:
        return "/root"
    return get_home()
def get_USER_ID(root: bool = False) -> int:  # pylint: disable=invalid-name
    ID = 0  # pylint: disable=invalid-name
    if root:
        return ID
    return os.geteuid()
def get_USER(root: bool = False) -> str:  # pylint: disable=invalid-name
    if root:
        return "root"
    uid = os.geteuid()
    return pwd.getpwuid(uid).pw_name
def get_GROUP_ID(root: bool = False) -> int:  # pylint: disable=invalid-name
    ID = 0  # pylint: disable=invalid-name
    if root:
        return ID
    return os.getegid()
def get_GROUP(root: bool = False) -> str:  # pylint: disable=invalid-name
    if root:
        return "root"
    gid = os.getegid()
    return grp.getgrgid(gid).gr_name
def get_TMP(root: bool = False) -> str:  # pylint: disable=invalid-name
    TMP = "/tmp"  # pylint: disable=invalid-name
    if root:
        return TMP
    return os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", TMP)))
def get_VARTMP(root: bool = False) -> str:  # pylint: disable=invalid-name
    VARTMP = "/var/tmp"  # pylint: disable=invalid-name
    if root:
        return VARTMP
    return os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", VARTMP)))
def get_SHELL(root: bool = False) -> str:  # pylint: disable=invalid-name
    SHELL = "/bin/sh"  # pylint: disable=invalid-name
    if root:
        return SHELL
    return os.environ.get("SHELL", SHELL)
def get_RUNTIME_DIR(root: bool = False) -> str:  # pylint: disable=invalid-name
    RUN = "/run"  # pylint: disable=invalid-name
    if root:
        return RUN
    return os.environ.get("XDG_RUNTIME_DIR", get_runtime_dir())
def get_CONFIG_HOME(root: bool = False) -> str:  # pylint: disable=invalid-name
    CONFIG = "/etc"  # pylint: disable=invalid-name
    if root:
        return CONFIG
    HOME = get_HOME(root)  # pylint: disable=invalid-name
    return os.environ.get("XDG_CONFIG_HOME", HOME + "/.config")
def get_CACHE_HOME(root: bool = False) -> str:  # pylint: disable=invalid-name
    CACHE = "/var/cache"  # pylint: disable=invalid-name
    if root:
        return CACHE
    HOME = get_HOME(root)  # pylint: disable=invalid-name
    return os.environ.get("XDG_CACHE_HOME", HOME + "/.cache")
def get_DATA_HOME(root: bool = False) -> str:  # pylint: disable=invalid-name
    SHARE = "/usr/share"  # pylint: disable=invalid-name
    if root:
        return SHARE
    HOME = get_HOME(root)  # pylint: disable=invalid-name
    return os.environ.get("XDG_DATA_HOME", HOME + "/.local/share")
def get_LOG_DIR(root: bool = False) -> str:  # pylint: disable=invalid-name
    LOGDIR = "/var/log"  # pylint: disable=invalid-name
    if root:
        return LOGDIR
    CONFIG = get_CONFIG_HOME(root)  # pylint: disable=invalid-name
    return os.path.join(CONFIG, "log")
def get_VARLIB_HOME(root: bool = False) -> str:  # pylint: disable=invalid-name
    VARLIB = "/var/lib"  # pylint: disable=invalid-name
    if root:
        return VARLIB
    CONFIG = get_CONFIG_HOME(root)  # pylint: disable=invalid-name
    return CONFIG
def expand_path(path: str, root: bool = False) -> str:
    # pylint: disable=possibly-unused-variable,invalid-name
    HOME = get_HOME(root)
    RUN = get_RUN(root)
    LOG = get_LOG_DIR(root)
    XDG_DATA_HOME=get_DATA_HOME(root)
    XDG_CONFIG_HOME=get_CONFIG_HOME(root)
    XDG_RUNTIME_DIR=get_RUNTIME_DIR(root)
    return os.path.expanduser(path.replace("${", "{").format(**locals()))

def shutil_fchown(fileno: int, user: Optional[str], group: Optional[str]) -> None:
    if user or group:
        uid, gid = -1, -1
        if user:
            uid = pwd.getpwnam(user).pw_uid
            gid = pwd.getpwnam(user).pw_gid
        if group:
            gid = grp.getgrnam(group).gr_gid
        os.fchown(fileno, uid, gid)
def shutil_setuid(user: Optional[str] = None, group: Optional[str] = None, xgroups: Optional[List[str]] = None) -> Dict[str, str]:
    """ set fork-child uid/gid (returns pw-info env-settings)"""
    if group:
        gid = grp.getgrnam(group).gr_gid
        os.setgid(gid)
        logg.debug("setgid %s for %s", gid, q_str(group))
        groups = [gid]
        try:
            os.setgroups(groups)
            logg.debug("setgroups %s < (%s)", groups, group)
        except OSError as e: # pragma: no cover (it will occur in non-root mode anyway)
            logg.debug("setgroups %s < (%s) >> %s", groups, group, e)
    if user:
        pw = pwd.getpwnam(user)
        gid = pw.pw_gid
        if not group:
            os.setgid(gid)
            logg.debug("setgid %s for user %s", gid, q_str(user))
        groupnames = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
        groups = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
        if xgroups:
            groups += [g.gr_gid for g in grp.getgrall() if g.gr_name in xgroups and g.gr_gid not in groups]
        if not groups:
            if group:
                gid = grp.getgrnam(group).gr_gid
            groups = [gid]
        try:
            os.setgroups(groups)
            logg.debug("setgroups %s > %s ", groups, groupnames)
        except OSError as e: # pragma: no cover (it will occur in non-root mode anyway)
            logg.debug("setgroups %s > %s >> %s", groups, groupnames, e)
        uid = pw.pw_uid
        os.setuid(uid)
        logg.debug("setuid %s for user %s", uid, q_str(user))
        home = pw.pw_dir
        shell = pw.pw_shell
        logname = pw.pw_name
        return {"USER": user, "LOGNAME": logname, "HOME": home, "SHELL": shell}
    return {}

def shutil_truncate(filename: str) -> None:
    """ truncates the file (or creates a new empty file)"""
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    with open(filename, "w") as f:
        f.write("")

# http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
def pid_exists(pid: int) -> bool:
    """Check whether pid exists in the current process table."""
    if pid is None: # pragma: no cover (is never null)
        return False
    return _pid_exists(int(pid))
def _pid_exists(pid: int) -> bool:
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True
def pid_zombie(pid: int) -> bool:
    """ may be a pid exists but it is only a zombie """
    if pid is None:
        return False
    return _pid_zombie(int(pid))
def _pid_zombie(pid: int) -> bool:
    """ may be a pid exists but it is only a zombie """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    check = _proc_pid_status.format(**locals())
    try:
        with open(check) as f:
            for line in f:
                if line.startswith("State:"):
                    return "Z" in line
    except IOError as e:
        if e.errno != errno.ENOENT:
            logg.error("%s (%s) >> %s", check, e.errno, e)
        return False
    return False

def checkprefix(cmd: str) -> Tuple[str, str]:
    prefix = ""
    for i, c in enumerate(cmd):
        if c in "-+!@:":
            prefix = prefix + c
        else:
            newcmd = cmd[i:]
            return prefix, newcmd
    return prefix, NIX

class ExecMode(NamedTuple):
    mode: str
    check: bool
    nouser: bool
    noexpand: bool
    argv0: bool
def exec_path(cmd: str) -> Tuple[ExecMode, str]:
    """ Hint: exec_path values are usually not moved by --root (while load_path are)"""
    prefix, newcmd = checkprefix(cmd)
    check = "-" not in prefix
    nouser = "+" in prefix or "!" in prefix
    noexpand = ":" in prefix
    argv0 = "@" in prefix
    mode = ExecMode(prefix, check, nouser, noexpand, argv0)
    return mode, newcmd
class LoadMode(NamedTuple):
    mode: str
    check: bool
def load_path(ref: str) -> Tuple[LoadMode, str]:
    """ Hint: load_path values are usually moved by --root (while exec_path are not)"""
    prefix, filename = "", ref
    while filename.startswith("-"):
        prefix = prefix + filename[0]
        filename = filename[1:]
    check = "-" not in prefix
    mode = LoadMode(prefix, check)
    return mode, filename

# https://github.com/phusion/baseimage-docker/blob/rel-0.9.16/image/bin/my_init
def ignore_signals_and_raise_keyboard_interrupt(signame: str) -> None:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    raise KeyboardInterrupt(signame)

_default_dict_type: Type[Dict[str, List[str]]] = collections.OrderedDict
_default_conf_type: Type[Dict[str, Dict[str, List[str]]]] = collections.OrderedDict

class SystemctlConfData:
    """ A *.service files has a structure similar to an *.ini file so
        that data is structured in sections and values. Actually the
        values are lists - the raw data is in .getlist(). Otherwise
        .get() will return the first line that was encountered. """
    _defaults: Dict[str, str]
    _conf_type: Type[Dict[str, Dict[str, List[str]]]]
    _dict_type: Type[Dict[str, List[str]]]
    _allow_no_value: bool
    _conf: Dict[str, Dict[str, List[str]]]
    _files: List[str]
    def __init__(self, defaults: Optional[Dict[str, str]] = None, dict_type: Optional[Type[Dict[str, List[str]]]] = None, conf_type: Optional[Type[Dict[str, Dict[str, List[str]]]]] = None, allow_no_value: bool = False) -> None:
        self._defaults = defaults or {}
        self._conf_type = conf_type or _default_conf_type
        self._dict_type = dict_type or _default_dict_type
        self._allow_no_value = allow_no_value
        self._conf = self._conf_type()
        self._files = []
    def defaults(self) -> Dict[str, str]:
        return self._defaults
    def sections(self) -> List[str]:
        return list(self._conf.keys())
    def add_section(self, section: str) -> None:
        if section not in self._conf:
            self._conf[section] = self._dict_type()
    def has_section(self, section: str) -> bool:
        return section in self._conf
    def has_option(self, section: str, option: str) -> bool:
        if section not in self._conf:
            return False
        return option in self._conf[section]
    def set(self, section: str, option: str, value: Optional[str]) -> None:
        if section not in self._conf:
            self._conf[section] = self._dict_type()
        if value is None:
            self._conf[section][option] = []
        elif option not in self._conf[section]:
            self._conf[section][option] = [value]
        else:
            self._conf[section][option].append(value)
    def getstr(self, section: str, option: str, default: Optional[str] = None, allow_no_value: bool = False) -> str:
        done = self.get(section, option, nix_str(default), allow_no_value)
        if done is None:
            return nix_str(default)
        return done
    def get(self, section: str, option: str, default: Optional[str] = None, allow_no_value: bool = False) -> Optional[str]:
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._conf:
            if default is not None:
                return default
            if allow_no_value:
                return None
            logg.warning("section %s does not exist", section)
            logg.warning("  have %s", self.sections())
            raise AttributeError(F"section {section} does not exist")
        if option not in self._conf[section]:
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError(F"option {option} in {section} does not exist")
        if not self._conf[section][option]: # i.e. an empty list
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError(F"option {option} in {section} is None")
        return self._conf[section][option][0] # the first line in the list of configs
    def getlist(self, section: str, option: str, default: Optional[List[str]] = None, allow_no_value: bool = False) -> List[str]:
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._conf:
            if default is not None:
                return default
            if allow_no_value:
                return []
            logg.warning("section %s does not exist", section)
            logg.warning("  have %s", self.sections())
            raise AttributeError(F"section {section} does not exist")
        if option not in self._conf[section]:
            if default is not None:
                return default
            if allow_no_value:
                return []
            raise AttributeError(F"option {option} in {section} does not exist")
        return self._conf[section][option] # returns a list, possibly empty
    def filenames(self) -> List[str]:
        return self._files

class SystemctlConfigParser(SystemctlConfData):
    """ A *.service files has a structure similar to an *.ini file but it is
        actually not like it. Settings may occur multiple times in each section
        and they create an implicit list. In reality all the settings are
        globally uniqute, so that an 'environment' can be printed without
        adding prefixes. Settings are continued with a backslash at the end
        of the line.  """
    # def __init__(self, defaults=None, dict_type=None, allow_no_value=False):
    #   SystemctlConfData.__init__(self, defaults, dict_type, allow_no_value)
    def read(self, filename: str) -> 'SystemctlConfigParser':
        return self.read_sysd(filename)
    def read_sysd(self, filename: str) -> 'SystemctlConfigParser':
        section = "GLOBAL"
        nextline = False
        name, text = "", ""
        if os.path.isfile(filename):
            self._files.append(filename)
        with open(filename) as f:
            for orig_line in f:
                if nextline:
                    text += orig_line
                    if text.rstrip().endswith("\\") or text.rstrip().endswith("\\\n"):
                        text = text.rstrip() + "\n"
                    else:
                        self.set(section, name, text)
                        nextline = False
                    continue
                line = orig_line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                if line.startswith(";"):
                    continue
                if line.startswith(".include"):
                    logg.error("the '.include' syntax is deprecated. Use x.service.d/ drop-in files!")
                    includefile = re.sub(r'^\.include[ ]*', '', line).rstrip()
                    if not os.path.isfile(includefile):
                        raise FileNotFoundError("tried to include file that doesn't exist: %s" % includefile)
                    self.read_sysd(includefile)
                    continue
                if line.startswith("["):
                    x = line.find("]")
                    if x > 0:
                        section = line[1:x]
                        self.add_section(section)
                    continue
                m = re.match(r"(\w+) *=(.*)", line)
                if not m:
                    logg.warning("bad ini line: %s", line)
                    raise ValueError("bad ini line")
                name, text = m.group(1), m.group(2).strip()
                if text.endswith("\\") or text.endswith("\\\n"):
                    nextline = True
                    text = text + "\n"
                else:
                    # hint: an empty line shall reset the value-list
                    self.set(section, name, text and text or None)
            if nextline:
                self.set(section, name, text)
        return self
    def read_sysv(self, filename: str) -> 'SystemctlConfigParser':
        """ an LSB header is scanned and converted to (almost)
            equivalent settings of a SystemD ini-style input """
        initinfo = False
        section = "GLOBAL"
        if os.path.isfile(filename):
            self._files.append(filename)
        with open(filename) as f:
            for orig_line in f:
                line = orig_line.strip()
                if line.startswith("#"):
                    if " BEGIN INIT INFO" in line:
                        initinfo = True
                        section = "init.d"
                    if " END INIT INFO" in line:
                        initinfo = False
                    if initinfo:
                        m = re.match(r"\S+\s*(\w[\w_-]*):(.*)", line)
                        if m:
                            key, val = m.group(1), m.group(2).strip()
                            self.set(section, key, val)
                    continue
        self.systemd_sysv_generator(filename)
        return self
    def systemd_sysv_generator(self, filename: str) -> None:
        """ see systemd-sysv-generator(8) """
        self.set(Unit, "SourcePath", filename)
        description = self.get("init.d", "Description", "")
        if description:
            self.set(Unit, "Description", description)
        check = self.get("init.d", "Required-Start", "")
        if check:
            for item in check.split(" "):
                if item.strip() in SYSD_TARGET_FOR:
                    self.set(Unit, "Requires", SYSD_TARGET_FOR[item.strip()])
        provides = self.get("init.d", "Provides", "")
        if provides:
            self.set(Install, "Alias", provides)
        # if already in multi-user.target then start it there.
        runlevels = self.getstr("init.d", "Default-Start", "3 5")
        for item in runlevels.split(" "):
            if item.strip() in SYSD_RUNLEVEL_FOR:
                self.set(Install, "WantedBy", SYSD_RUNLEVEL_FOR[item.strip()])
        self.set(Service, "Restart", "no")
        self.set(Service, "TimeoutSec", nix_str(MAXTIMEOUT))
        self.set(Service, "KillMode", "process")
        self.set(Service, "GuessMainPID", "no")
        # self.set(Service, "RemainAfterExit", "yes")
        # self.set(Service, "SuccessExitStatus", "5 6")
        self.set(Service, "ExecStart", filename + " start")
        self.set(Service, "ExecStop", filename + " stop")
        if description: # LSB style initscript
            self.set(Service, "ExecReload", filename + " reload")
        self.set(Service, "Type", "forking") # not "sysv" anymore

# UnitConfParser = ConfigParser.RawConfigParser
UnitConfParser = SystemctlConfigParser

class SystemctlSocket:
    """ support for Socket unit descriptors """
    def __init__(self, conf: 'SystemctlConf', sock: socket.socket, skip: bool = False) -> None:
        self.conf = conf
        self.sock = sock
        self.skip = skip
    def fileno(self) -> int:
        return self.sock.fileno()
    def listen(self, backlog: Optional[int] = None) -> None:
        if backlog is None:
            backlog = LISTEN_BACKLOG
        dgram = (self.sock.type == socket.SOCK_DGRAM)
        if not dgram and not self.skip:
            self.sock.listen(backlog)
    def name(self) -> str:
        return self.conf.name()
    def addr(self) -> str:
        sock_stream = self.conf.get(Socket, "ListenStream", "")
        data_stream = self.conf.get(Socket, "ListenDatagram", "")
        return sock_stream or data_stream
    def close(self) -> None:
        self.sock.close()

class SystemctlConf:
    """ status of loaded *.service descriptors (and other unit files) from the system environment """
    data: SystemctlConfData
    env: Dict[str, str]
    status: Optional[Dict[str, str]]
    masked: Optional[str]
    module: Optional[str]
    nonloaded_path: str
    drop_in_files: Dict[str, str]
    _root: str
    _user_mode: bool
    def __init__(self, data: SystemctlConfData, module: Optional[str] = None) -> None:
        self.data = data # UnitConfParser
        self.env = {}
        self.status = None
        self.masked = None
        self.module = module
        self.nonloaded_path = ""
        self.drop_in_files = {}
        self._root = ROOT
        self._user_mode = USER_MODE
    def root_mode(self) -> bool:
        return not self._user_mode
    def loaded(self) -> str:
        files = self.data.filenames()
        if self.masked:
            return "masked"
        if len(files):
            return "loaded"
        return ""
    def filename(self) -> Optional[str]:
        """ returns the last filename that was parsed """
        files = self.data.filenames()
        if files:
            return files[0]
        return None
    def overrides(self) -> List[str]:
        """ drop-in files are loaded alphabetically by name, not by full path """
        return [self.drop_in_files[name] for name in sorted(self.drop_in_files)]
    def name(self) -> str:
        """ the unit id or defaults to the file name """
        name = self.module or ""
        filename = self.filename()
        if filename:
            name = os.path.basename(filename)
        return self.module or name
    def set(self, section: str, name: str, value: Optional[str]) -> None:
        return self.data.set(section, name, value)
    def get(self, section: str, name: str, default: Optional[str], allow_no_value: bool = False) -> str:
        return self.data.getstr(section, name, default, allow_no_value)
    def getlist(self, section: str, name: str, default: Optional[List[str]] = None, allow_no_value: bool = False) -> List[str]:
        return self.data.getlist(section, name, default or [], allow_no_value)
    def getbool(self, section: str, name: str, default: Optional[str] = None) -> bool:
        value = self.data.get(section, name, default or "no")
        if value:
            if value[0] in "TtYy123456789":
                return True
        return False

class PresetFile:
    """ scanning *.preset files to adjust the *.service default status """
    _files: List[str]
    _lines: List[str]
    def __init__(self) -> None:
        self._files = []
        self._lines = []
    def filename(self) -> Optional[str]:
        """ returns the last filename that was parsed """
        if self._files:
            return self._files[-1]
        return None
    def read(self, filename: str) -> 'PresetFile':
        self._files.append(filename)
        with open(filename) as f:
            for line in f:
                self._lines.append(line.strip())
        return self
    def get_preset(self, unit: str) -> Optional[str]:
        for line in self._lines:
            m = re.match(r"(enable|disable)\s+(\S+)", line)
            if m:
                status, pattern = m.group(1), m.group(2)
                if fnmatch.fnmatchcase(unit, pattern):
                    logg.debug("%s %s => %s %s", status, pattern, unit, q_str(self.filename()))
                    return status
        return None

## with waitlock(conf): self.start()
class waitlock:  # pylint: disable=invalid-name
    """ with-statement for mutex on modules - allowing to run multiple systemctl units in parallel, or guarding the global lock."""
    conf: SystemctlConf
    opened: int
    lockfolder: str
    def __init__(self, conf: SystemctlConf) -> None:
        self.conf = conf # currently unused
        self.opened = -1
        self.lockfolder = expand_path(NOTIFY_SOCKET_FOLDER, conf.root_mode())
        try:
            folder = self.lockfolder
            if not os.path.isdir(folder):
                os.makedirs(folder)
        except OSError as e:
            logg.warning("oops >> %s", e)
    def lockfile(self) -> str:
        unit = ""
        if self.conf:
            unit = self.conf.name()
        return os.path.join(self.lockfolder, str(unit or "global") + ".lock")
    def __enter__(self) -> bool:
        try:
            lockfile = self.lockfile()
            lockname = os.path.basename(lockfile)
            self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
            for attempt in range(int(MAXLOCKWAIT or MAXTIMEOUT)):
                try:
                    logg_debug_flock("[%s] %s trying %s _______ ", os.getpid(), delayed(attempt), lockname)
                    fcntl.flock(self.opened, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    st = os.fstat(self.opened)
                    if not st.st_nlink:
                        logg_debug_flock("[%s] %s %s got deleted, trying again", os.getpid(), delayed(attempt), lockname)
                        os.close(self.opened)
                        self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
                        continue
                    content = "{ 'systemctl': %s, 'lock': '%s' }\n" % (os.getpid(), lockname)
                    os.write(self.opened, content.encode("utf-8"))
                    logg_debug_flock("[%s] %s holding lock on %s", os.getpid(), delayed(attempt), lockname)
                    return True
                except IOError as e:
                    whom = os.read(self.opened, 4096)
                    os.lseek(self.opened, 0, os.SEEK_SET)
                    logg.debug("[%s] %s could not get lock >> %s", os.getpid(), delayed(attempt), e)
                    logg.info(" [%s] %s systemctl locked by %s", os.getpid(), delayed(attempt), whom.rstrip())
                    time.sleep(1) # until MAXLOCKWAIT
                    continue
            logg.error("[%s] not able to get the lock to %s", os.getpid(), lockname)
        except OSError as e:
            logg.warning("[%s] oops >> %s", os.getpid(), e)
        # TODO# raise Exception("no lock for %s", self.unit or "global")
        return False
    def __exit__(self, exc: Optional[Type[BaseException]], value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        try:
            os.lseek(self.opened, 0, os.SEEK_SET)
            os.ftruncate(self.opened, 0)
            if REMOVE_LOCK_FILE: # an optional implementation
                lockfile = self.lockfile()
                lockname = os.path.basename(lockfile)
                os.unlink(lockfile) # ino is kept allocated because opened by this process
                logg.debug("[%s] lockfile removed for %s", os.getpid(), lockname)
            fcntl.flock(self.opened, fcntl.LOCK_UN)
            os.close(self.opened) # implies an unlock but that has happend like 6 seconds later
            self.opened = -1
        except OSError as e:
            logg.warning("oops >> %s", e)

class SystemctlWaitPID(NamedTuple):
    pid: Optional[int]
    returncode: Optional[int]
    signal: int

def must_have_failed(waitpid: SystemctlWaitPID, cmd: List[str]) -> SystemctlWaitPID:
    # found to be needed on ubuntu:16.04 to match test result from ubuntu:18.04 and other distros
    # .... I have tracked it down that python's os.waitpid() returns an exitcode==0 even when the
    # .... underlying process has actually failed with an exitcode<>0. It is unknown where that
    # .... bug comes from but it seems a bit serious to trash some very basic unix functionality.
    # .... Essentially a parent process does not get the correct exitcode from its own children.
    if cmd and cmd[0] == "/bin/kill":
        pid = None
        for arg in cmd[1:]:
            if not arg.startswith("-"):
                pid = arg
        if pid is None: # unknown $MAINPID
            if not waitpid.returncode:
                logg.error("waitpid %s did return %s => correcting as 11", cmd, waitpid.returncode)
            waitpid = SystemctlWaitPID(waitpid.pid, 11, waitpid.signal)
    return waitpid

def subprocess_waitpid(pid: int) -> SystemctlWaitPID:
    run_pid, run_stat = os.waitpid(pid, 0)
    return SystemctlWaitPID(run_pid, os.WEXITSTATUS(run_stat), os.WTERMSIG(run_stat))
def subprocess_testpid(pid: int) -> SystemctlWaitPID:
    run_pid, run_stat = os.waitpid(pid, os.WNOHANG)
    if run_pid:
        return SystemctlWaitPID(run_pid, os.WEXITSTATUS(run_stat), os.WTERMSIG(run_stat))
    else:
        return SystemctlWaitPID(pid, None, 0)

class SystemctlUnitName(NamedTuple):
    fullname: str
    name: str
    prefix: str
    instance: str
    suffix: str
    component: str

def parse_unit(fullname: str) -> SystemctlUnitName: # -> object(prefix, instance, suffix, ...., name, component)
    name, suffix = fullname, ""
    has_suffix = fullname.rfind(".")
    if has_suffix > 0:
        name = fullname[:has_suffix]
        suffix = fullname[has_suffix+1:]
    prefix, instance = name, ""
    has_instance = name.find("@")
    if has_instance > 0:
        prefix = name[:has_instance]
        instance = name[has_instance+1:]
    component = ""
    has_component = prefix.rfind("-")
    if has_component > 0:
        component = prefix[has_component+1:]
    return SystemctlUnitName(fullname, name, prefix, instance, suffix, component)

def time_to_seconds(text: str, maximum: float) -> float:
    value = 0.
    for part in str(text).split(" "):
        item = part.strip()
        if item == "infinity":
            return maximum
        if item.endswith("m"):
            try: value += 60 * int(item[:-1])
            except ValueError: pass # pragma: no cover
        if item.endswith("min"):
            try: value += 60 * int(item[:-3])
            except ValueError: pass # pragma: no cover
        elif item.endswith("ms"):
            try: value += int(item[:-2]) / 1000.
            except ValueError: pass # pragma: no cover
        elif item.endswith("s"):
            try: value += int(item[:-1])
            except ValueError: pass # pragma: no cover
        elif item:
            try: value += int(item)
            except ValueError: pass # pragma: no cover
    if value > maximum:
        return maximum
    if not value and text.strip() == "0":
        return 0.
    if not value:
        return 1.
    return value
def seconds_to_time(seconds: float) -> str:
    seconds = float(seconds)
    mins = int(int(seconds) / 60)
    secs = int(int(seconds) - (mins * 60))
    msecs = int(int(seconds * 1000) - (secs * 1000 + mins * 60000))
    if mins and secs and msecs:
        return "%smin %ss %sms" % (mins, secs, msecs)
    elif mins and secs:
        return "%smin %ss" % (mins, secs)
    elif secs and msecs:
        return "%ss %sms" % (secs, msecs)
    elif mins and msecs:
        return "%smin %sms" % (mins, msecs)
    elif mins:
        return "%smin" % (mins)
    else:
        return "%ss" % (secs)

def get_Before(conf: SystemctlConf) -> List[str]:  # pylint: disable=invalid-name
    result: List[str] = []
    beforelist = conf.getlist(Unit, "Before", [])
    for befores in beforelist:
        for before in befores.split(" "):
            name = before.strip()
            if name and name not in result:
                result.append(name)
    return result

def get_After(conf: SystemctlConf) -> List[str]:  # pylint: disable=invalid-name
    result: List[str] = []
    afterlist = conf.getlist(Unit, "After", [])
    for afters in afterlist:
        for after in afters.split(" "):
            name = after.strip()
            if name and name not in result:
                result.append(name)
    return result

def compare_after(conf1: SystemctlConf, conf2: SystemctlConf) -> int:
    unit1 = conf1.name()
    unit2 = conf2.name()
    for after in get_After(conf1):
        if after == unit2:
            logg.debug("%s After %s", unit1, unit2)
            return -1
    for after in get_After(conf2):
        if after == unit1:
            logg.debug("%s After %s", unit2, unit1)
            return 1
    for before in get_Before(conf1):
        if before == unit2:
            logg.debug("%s Before %s", unit1, unit2)
            return 1
    for before in get_Before(conf2):
        if before == unit1:
            logg.debug("%s Before %s", unit2, unit1)
            return -1
    return 0

def sorted_after(conflist: Iterable[SystemctlConf]) -> List[SystemctlConf]:
    # the normal sorted() does only look at two items
    # so if "A after C" and a list [A, B, C] then
    # it will see "A = B" and "B = C" assuming that
    # "A = C" and the list is already sorted.
    #
    # To make a totalsorted we have to create a marker
    # that informs sorted() that also B has a relation.
    # It only works when 'after' has a direction, so
    # anything without 'before' is a 'after'. In that
    # case we find that "B after C".
    class SortTuple:
        """ sort systemctl unit names """
        def __init__(self, rank: int, conf: SystemctlConf) -> None:
            self.rank = rank
            self.conf = conf
    sortlist = [SortTuple(0, conf) for conf in conflist]
    for check in range(len(sortlist)): # maxrank = len(sortlist)
        changed = 0
        # TODO: replace total-sort into start-rank by a better algo
        for index1, item1 in enumerate(sortlist):
            for index2, item2 in enumerate(sortlist):
                if index1 == index2: continue
                before = compare_after(item1.conf, item2.conf)
                if before > 0 and item1.rank <= item2.rank:
                    logg_debug_after("  %-30s before %s", item1.conf.name(), item2.conf.name())
                    item1.rank = item2.rank + 1
                    changed += 1
                if before < 0 and item2.rank <= item1.rank:
                    logg_debug_after("  %-30s before %s", item2.conf.name(), item1.conf.name())
                    item2.rank = item1.rank + 1
                    changed += 1
        if not changed:
            logg_debug_after("done in check %s of %s", check, len(sortlist))
            break
            # because Requires is almost always the same as the After clauses
            # we are mostly done in round 1 as the list is in required order
    for conf in conflist:
        logg_debug_after(".. %s", conf.name())
    for item in sortlist:
        logg_debug_after("(%s) %s", item.rank, item.conf.name())
    sortedlist = sorted(sortlist, key = lambda item: -item.rank)
    for item in sortedlist:
        logg_debug_after("[%s] %s", item.rank, item.conf.name())
    return [item.conf for item in sortedlist]

def read_env_file(filename: str, root: Optional[str] = NIX) -> Iterator[Tuple[str, str]]:
    try:
        with open(os_path(root, filename)) as f:
            for real_line in f:
                line = real_line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r"(?:export +)?([\w_]+)[=]'([^']*)'", line)
                if m:
                    yield m.group(1), m.group(2)
                    continue
                m = re.match(r'(?:export +)?([\w_]+)[=]"([^"]*)"', line)
                if m:
                    yield m.group(1), m.group(2)
                    continue
                m = re.match(r'(?:export +)?([\w_]+)[=](.*)', line)
                if m:
                    yield m.group(1), m.group(2)
                    continue
    except OSError as e:
        logg.info("while reading %s >> %s", filename, e)


class SystemctlLoadedUnits:
    """ database of loaded unit descriptors and expansion helpers for them. """
    _root: str
    _user_mode: bool
    _user_getlogin: str
    _extra_vars: List[str]
    _SYSTEMD_UNIT_PATH: Optional[str]
    _SYSTEMD_SYSVINIT_PATH: Optional[str]
    _SYSTEMD_PRESET_PATH: Optional[str]
    _loaded_file_sysv: Dict[str, SystemctlConf]
    _loaded_file_sysd: Dict[str, SystemctlConf]
    _file_for_unit_sysv: Optional[Dict[str, str]]
    _file_for_unit_sysd: Optional[Dict[str, str]]
    _preset_file_list: Optional[Dict[str, PresetFile]]
    def __init__(self, root: str = NIX) -> None:
        self._root = root or ROOT
        self._user_mode = USER_MODE
        self._user_getlogin = os_getlogin()
        self._extra_vars = EXTRA_VARS
        self._SYSTEMD_UNIT_PATH = None  # pylint: disable=invalid-name
        self._SYSTEMD_SYSVINIT_PATH = None  # pylint: disable=invalid-name
        self._SYSTEMD_PRESET_PATH = None  # pylint: disable=invalid-name
        # and the actual internal runtime state
        self._loaded_file_sysv = {} # /etc/init.d/name => config data
        self._loaded_file_sysd = {} # /etc/systemd/system/name.service => config data
        self._file_for_unit_sysv = None # name.service => /etc/init.d/name
        self._file_for_unit_sysd = None # name.service => /etc/systemd/system/name.service
        self._preset_file_list = None # /etc/systemd/system-preset/* => file content
    def user(self) -> str:
        return self._user_getlogin
    def user_mode(self) -> bool:
        return self._user_mode
    def user_folder(self) -> str:
        for folder in self.user_folders():
            if folder:
                return folder
        raise FileNotFoundError("did not find any systemd/user folder")
    def system_folder(self) -> str:
        for folder in self.system_folders():
            if folder:
                return folder
        raise FileNotFoundError("did not find any systemd/system folder")
    def preset_folders(self) -> Iterable[str]:
        SYSTEMD_PRESET_PATH = self.get_SYSTEMD_PRESET_PATH()  # pylint: disable=invalid-name
        for path in SYSTEMD_PRESET_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_PRESET_PATH.endswith(":"):
            for p in SYSD_PRESET_FOLDERS:
                yield expand_path(p.strip())
    def init_folders(self) -> Iterable[str]:
        SYSTEMD_SYSVINIT_PATH = self.get_SYSTEMD_SYSVINIT_PATH() # pylint: disable=invalid-name
        for path in SYSTEMD_SYSVINIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_SYSVINIT_PATH.endswith(":"):
            for p in SYSV_INIT_FOLDERS:
                yield expand_path(p.strip())
    def user_folders(self) -> Iterable[str]:
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH() # pylint: disable=invalid-name
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            for p in SYSD_USER_FOLDERS:
                yield expand_path(p.strip())
    def system_folders(self) -> Iterable[str]:
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH() # pylint: disable=invalid-name
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            for p in SYSD_SYSTEM_FOLDERS:
                yield expand_path(p.strip())
    def get_SYSTEMD_UNIT_PATH(self) -> str: # pylint: disable=invalid-name
        if self._SYSTEMD_UNIT_PATH is None:
            self._SYSTEMD_UNIT_PATH = os.environ.get("SYSTEMD_UNIT_PATH", ":")
        assert self._SYSTEMD_UNIT_PATH is not None
        return self._SYSTEMD_UNIT_PATH
    def get_SYSTEMD_SYSVINIT_PATH(self) -> str: # pylint: disable=invalid-name
        if self._SYSTEMD_SYSVINIT_PATH is None:
            self._SYSTEMD_SYSVINIT_PATH = os.environ.get("SYSTEMD_SYSVINIT_PATH", ":")
        assert self._SYSTEMD_SYSVINIT_PATH is not None
        return self._SYSTEMD_SYSVINIT_PATH
    def get_SYSTEMD_PRESET_PATH(self) -> str: # pylint: disable=invalid-name
        if self._SYSTEMD_PRESET_PATH is None:
            self._SYSTEMD_PRESET_PATH = os.environ.get("SYSTEMD_PRESET_PATH", ":")
        assert self._SYSTEMD_PRESET_PATH is not None
        return self._SYSTEMD_PRESET_PATH
    def sysd_folders(self) -> Iterable[str]:
        """ if --user then these folders are preferred """
        if self.user_mode():
            for folder in self.user_folders():
                yield folder
        if TRUE:
            for folder in self.system_folders():
                yield folder
    def scan_unit_sysd_files(self) -> List[str]: # -> [ unit-names,... ]
        """ reads all unit files, returns the first filename for the unit given """
        if self._file_for_unit_sysd is None:
            self._file_for_unit_sysd = {}
            for folder in self.sysd_folders():
                if not folder:
                    continue
                folder = os_path(self._root, folder)
                if not os.path.isdir(folder):
                    continue
                for name in os.listdir(folder):
                    path = os.path.join(folder, name)
                    if os.path.isdir(path):
                        continue
                    service_name = name
                    if service_name not in self._file_for_unit_sysd:
                        self._file_for_unit_sysd[service_name] = path
            logg.debug("found %s sysd files", len(self._file_for_unit_sysd))
        return list(self._file_for_unit_sysd.keys())
    def scan_unit_sysv_files(self) -> List[str]: # -> [ unit-names,... ]
        """ reads all init.d files, returns the first filename when unit is a '.service' """
        if self._file_for_unit_sysv is None:
            self._file_for_unit_sysv = {}
            for folder in self.init_folders():
                if not folder:
                    continue
                folder = os_path(self._root, folder)
                if not os.path.isdir(folder):
                    continue
                for name in os.listdir(folder):
                    path = os.path.join(folder, name)
                    if os.path.isdir(path):
                        continue
                    service_name = name + ".service" # simulate systemd
                    if service_name not in self._file_for_unit_sysv:
                        self._file_for_unit_sysv[service_name] = path
            logg.debug("found %s sysv files", len(self._file_for_unit_sysv))
        return list(self._file_for_unit_sysv.keys())
    def unit_sysd_file(self, module: Optional[str] = None) -> Optional[str]: # -> filename?
        """ file path for the given module (systemd) """
        self.scan_unit_sysd_files()
        assert self._file_for_unit_sysd is not None
        if module and module in self._file_for_unit_sysd:
            return self._file_for_unit_sysd[module]
        if module and unit_of(module) in self._file_for_unit_sysd:
            return self._file_for_unit_sysd[unit_of(module)]
        return None
    def unit_sysv_file(self, module: Optional[str] = None) -> Optional[str]: # -> filename?
        """ file path for the given module (sysv) """
        self.scan_unit_sysv_files()
        assert self._file_for_unit_sysv is not None
        if module and module in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[module]
        if module and unit_of(module) in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[unit_of(module)]
        return None
    def unit_file(self, module: Optional[str] = None) -> Optional[str]: # -> filename?
        """ file path for the given module (sysv or systemd) """
        path = self.unit_sysd_file(module)
        if path is not None:
            return path
        path = self.unit_sysv_file(module)
        if path is not None:
            return path
        return None
    def is_sysv_file(self, filename: Optional[str]) -> Optional[bool]:
        """ for routines that have a special treatment for init.d services """
        self.unit_file() # scan all
        assert self._file_for_unit_sysd is not None
        assert self._file_for_unit_sysv is not None
        if not filename:
            return None
        if filename in self._file_for_unit_sysd.values():
            return False
        if filename in self._file_for_unit_sysv.values():
            return True
        return None # not True
    def is_user_conf(self, conf: SystemctlConf) -> bool:
        if not conf: # pragma: no cover (is never null)
            return False
        filename = conf.nonloaded_path or conf.filename()
        if filename and "/user/" in filename:
            return True
        return False
    def not_user_conf(self, conf: SystemctlConf) -> bool:
        """ conf can not be started as user service (when --user)"""
        if conf is None: # pragma: no cover (is never null)
            return True
        if not self.user_mode():
            logg.debug("%s no --user mode >> accept", q_str(conf.filename()))
            return False
        if self.is_user_conf(conf):
            logg.debug("%s is /user/ conf >> accept", q_str(conf.filename()))
            return False
        # to allow for 'docker run -u user' with system services
        user = self.get_User(conf)
        if user and user == self.user():
            logg.debug("%s with User=%s >> accept", q_str(conf.filename()), user)
            return False
        return True
    def find_drop_in_files(self, unit: str) -> Dict[str, str]:
        """ search for some.service.d/extra.conf files """
        result: Dict[str, str] = {}
        basename_d = unit + ".d"
        for folder in self.sysd_folders():
            if not folder:
                continue
            folder = os_path(self._root, folder)
            override_d = os_path(folder, basename_d)
            if not os.path.isdir(override_d):
                continue
            for name in os.listdir(override_d):
                path = os.path.join(override_d, name)
                if os.path.isdir(path):
                    continue
                if not path.endswith(".conf"):
                    continue
                if name not in result:
                    result[name] = path
        return result
    def load_sysd_template_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: # -> conf?
        """ read the unit template with a UnitConfParser (systemd) """
        if module and "@" in module:
            unit = parse_unit(module)
            service = "%s@.service" % unit.prefix
            conf = self.load_sysd_unit_conf(service)
            if conf:
                conf.module = module
            return conf
        return None
    def load_sysd_unit_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: # -> conf?
        """ read the unit file with a UnitConfParser (systemd) """
        path = self.unit_sysd_file(module)
        if not path:
            return None
        assert self._loaded_file_sysd is not None
        if path in self._loaded_file_sysd:
            return self._loaded_file_sysd[path]
        masked = None
        if os.path.islink(path) and os.readlink(path).startswith("/dev"):
            masked = os.readlink(path)
        drop_in_files: Dict[str, str] = {}
        data = UnitConfParser()
        if not masked:
            data.read_sysd(path)
            drop_in_files = self.find_drop_in_files(os.path.basename(path))
            # load in alphabetic order, irrespective of location
            for name in sorted(drop_in_files):
                path = drop_in_files[name]
                data.read_sysd(path)
        conf = SystemctlConf(data, module)
        conf.masked = masked
        conf.nonloaded_path = path # if masked
        conf.drop_in_files = drop_in_files
        conf._root = self._root  # pylint: disable=protected-access
        self._loaded_file_sysd[path] = conf
        return conf
    def load_sysv_unit_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: # -> conf?
        """ read the unit file with a UnitConfParser (sysv) """
        path = self.unit_sysv_file(module)
        if not path:
            return None
        assert self._loaded_file_sysv is not None
        if path in self._loaded_file_sysv:
            return self._loaded_file_sysv[path]
        data = UnitConfParser()
        data.read_sysv(path)
        conf = SystemctlConf(data, module)
        conf._root = self._root  # pylint: disable=protected-access
        self._loaded_file_sysv[path] = conf
        return conf
    def load_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: # -> conf | None(not-found)
        """ read the unit file with a UnitConfParser (sysv or systemd) """
        try:
            conf = self.load_sysd_unit_conf(module)
            if conf is not None:
                return conf
            conf = self.load_sysd_template_conf(module)
            if conf is not None:
                return conf
            conf = self.load_sysv_unit_conf(module)
            if conf is not None:
                return conf
        except Exception as e:  # pylint: disable=broad-exception-caught
            logg.warning("%s not loaded >> %s", module, e)
        return None
    def default_conf(self, module: str, description: Optional[str] = None) -> SystemctlConf: # -> conf
        """ a unit conf that can be printed to the user where
            attributes are empty and loaded() is False """
        data = UnitConfParser()
        data.set(Unit, "Description", description or ("NOT-FOUND " + str(module)))
        # assert(not data.loaded())
        conf = SystemctlConf(data, module)
        conf._root = self._root  # pylint: disable=protected-access
        return conf
    def get_conf(self, module: str) -> SystemctlConf: # -> conf (conf | default-conf)
        """ accept that a unit does not exist
            and return a unit conf that says 'not-loaded' """
        conf = self.load_conf(module)
        if conf is not None:
            return conf
        return self.default_conf(module)
    def match_sysd_templates(self, modules: Optional[List[str]] = None) -> Iterable[str]: # -> generate[ unit ]
        """ make a file glob on all known template units (systemd areas).
            It returns no modules (!!) if no modules pattern were given.
            The module string should contain an instance name already. """
        modules = to_list(modules)
        if not modules:
            return
        self.scan_unit_sysd_files()
        assert self._file_for_unit_sysd is not None
        for item in sorted(self._file_for_unit_sysd.keys()):
            if "@" not in item:
                continue
            service_unit = parse_unit(item)
            for module in modules:
                if "@" not in module:
                    continue
                module_unit = parse_unit(module)
                if service_unit.prefix == module_unit.prefix:
                    yield "%s@%s.%s" % (service_unit.prefix, module_unit.instance, service_unit.suffix)
    def match_sysd_units(self, modules: Optional[List[str]] = None) -> Iterable[str]: # -> generate[ unit ]
        """ make a file glob on all known units (systemd areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        suffix = ".service"
        modules = to_list(modules)
        self.scan_unit_sysd_files()
        assert self._file_for_unit_sysd is not None
        for item in sorted(self._file_for_unit_sysd.keys()):
            if "." not in item:
                pass
            elif not modules:
                yield item
            elif [module for module in modules if fnmatch.fnmatchcase(item, module)]:
                yield item
            elif [module for module in modules if module+suffix == item]:
                yield item
    def match_sysv_units(self, modules: Optional[List[str]] = None) -> Iterable[str]: # -> generate[ unit ]
        """ make a file glob on all known units (sysv areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        suffix = ".service"
        modules = to_list(modules)
        self.scan_unit_sysv_files()
        assert self._file_for_unit_sysv is not None
        for item in sorted(self._file_for_unit_sysv.keys()):
            if not modules:
                yield item
            elif [module for module in modules if fnmatch.fnmatchcase(item, module)]:
                yield item
            elif [module for module in modules if module+suffix == item]:
                yield item
    def match_units(self, modules: Optional[List[str]] = None) -> List[str]: # -> [ units,.. ]
        """ Helper for about any command with multiple units which can
            actually be glob patterns on their respective unit name.
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        found: List[str] = []
        for unit in self.match_sysd_units(modules):
            if unit not in found:
                found.append(unit)
        for unit in self.match_sysd_templates(modules):
            if unit not in found:
                found.append(unit)
        for unit in self.match_sysv_units(modules):
            if unit not in found:
                found.append(unit)
        return found
    def list_all(self) -> List[Tuple[str, str, str]]:
        """ the basic loading state of all units """
        self.unit_file() # scan all
        assert self._file_for_unit_sysd is not None
        assert self._file_for_unit_sysv is not None
        result: List[Tuple[str, str, str]] = []
        for name, value in self._file_for_unit_sysd.items():
            result += [(name, "SysD", value)]
        for name, value in self._file_for_unit_sysv.items():
            result += [(name, "SysV", value)]
        return result
    def each_target_file(self) -> Iterable[Tuple[str, str]]:
        folders = self.system_folders()
        if self.user_mode():
            folders = self.user_folders()
        for folder1 in folders:
            folder = os_path(self._root, folder1)
            if not os.path.isdir(folder):
                continue
            for filename in os.listdir(folder):
                if filename.endswith(".target"):
                    yield (filename, os.path.join(folder, filename))
    def get_target_conf(self, module: str) -> SystemctlConf: # -> conf (conf | default-conf)
        """ accept that a unit does not exist
            and return a unit conf that says 'not-loaded' """
        conf = self.load_conf(module)
        if conf is not None:
            return conf
        target_conf = self.default_conf(module)
        if module in SYSD_TARGET_REQUIRES:
            target_conf.set(Unit, "Requires", SYSD_TARGET_REQUIRES[module])
        return target_conf
    def get_target_list(self, module: str) -> List[str]:
        """ the Requires= in target units are only accepted if known """
        target = module
        if "." not in target: target += ".target"
        targets = [target]
        conf = self.get_target_conf(module)
        requires = conf.get(Unit, "Requires", "")
        while requires in SYSD_TARGET_REQUIRES:
            targets = [requires] + targets
            requires = SYSD_TARGET_REQUIRES[requires]
        logg.debug("the [%s] requires %s", module, targets)
        return targets
    def get_InstallTarget(self, conf: SystemctlConf, default: Optional[str] = None) -> Optional[str]: # pylint: disable=invalid-name
        if not conf:
            return default
        return conf.get(Install, "WantedBy", default, True)
    def get_TimeoutStartSec(self, conf: SystemctlConf, section: str = Service) -> float: # pylint: disable=invalid-name
        timeout = conf.get(section, "TimeoutSec", nix_str(DefaultTimeoutStartSec))
        timeout = conf.get(section, "TimeoutStartSec", timeout)
        return time_to_seconds(timeout, MAXTIMEOUT)
    def get_SocketTimeoutSec(self, conf: SystemctlConf, section: str = Socket) -> float: # pylint: disable=invalid-name
        timeout = conf.get(section, "TimeoutSec", nix_str(DefaultTimeoutStartSec))
        return time_to_seconds(timeout, MAXTIMEOUT)
    def get_RemainAfterExit(self, conf: SystemctlConf, section: str = Service) -> bool: # pylint: disable=invalid-name
        return conf.getbool(section, "RemainAfterExit", "no")
    def get_StatusFile(self, conf: SystemctlConf, section: str = Service) -> Optional[str]:  # pylint: disable=invalid-name
        """ file where to store a status mark """
        return conf.get(section, "StatusFile", None)
    def get_RuntimeDirectoryPreserve(self, conf: SystemctlConf, section: str = Service) -> bool: # pylint: disable=invalid-name
        return conf.getbool(section, "RuntimeDirectoryPreserve", "no")
    def get_RuntimeDirectory(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return self.expand_special(conf.get(section, "RuntimeDirectory", ""), conf)
    def get_StateDirectory(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return self.expand_special(conf.get(section, "StateDirectory", ""), conf)
    def get_CacheDirectory(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return self.expand_special(conf.get(section, "CacheDirectory", ""), conf)
    def get_LogsDirectory(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return self.expand_special(conf.get(section, "LogsDirectory", ""), conf)
    def get_ConfigurationDirectory(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return self.expand_special(conf.get(section, "ConfigurationDirectory", ""), conf)
    def get_RuntimeDirectoryMode(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return conf.get(section, "RuntimeDirectoryMode", "")
    def get_StateDirectoryMode(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return conf.get(section, "StateDirectoryMode", "")
    def get_CacheDirectoryMode(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return conf.get(section, "CacheDirectoryMode", "")
    def get_LogsDirectoryMode(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return conf.get(section, "LogsDirectoryMode", "")
    def get_ConfigurationDirectoryMode(self, conf: SystemctlConf, section: str = Service) -> str: # pylint: disable=invalid-name
        return conf.get(section, "ConfigurationDirectoryMode", "")
    def get_WorkingDirectory(self, conf: SystemctlConf) -> str: # pylint: disable=invalid-name
        return conf.get(Service, "WorkingDirectory", "")
    def get_TimeoutStopSec(self, conf: SystemctlConf) -> float: # pylint: disable=invalid-name
        timeout = conf.get(Service, "TimeoutSec", nix_str(DefaultTimeoutStartSec))
        timeout = conf.get(Service, "TimeoutStopSec", timeout)
        return time_to_seconds(timeout, MAXTIMEOUT)
    def get_SendSIGKILL(self, conf: SystemctlConf) -> bool: # pylint: disable=invalid-name
        return conf.getbool(Service, "SendSIGKILL", "yes")
    def get_SendSIGHUP(self, conf: SystemctlConf) -> bool: # pylint: disable=invalid-name
        return conf.getbool(Service, "SendSIGHUP", "no")
    def get_KillMode(self, conf: SystemctlConf) -> str: # pylint: disable=invalid-name
        return conf.get(Service, "KillMode", "control-group")
    def get_KillSignal(self, conf: SystemctlConf) -> str: # pylint: disable=invalid-name
        return conf.get(Service, "KillSignal", "SIGTERM")
    def get_StartLimitBurst(self, conf: SystemctlConf) -> int: # pylint: disable=invalid-name
        defaults = DefaultStartLimitBurst
        return to_int(conf.get(Service, "StartLimitBurst", nix_str(defaults)), defaults) # 5
    def get_StartLimitIntervalSec(self, conf: SystemctlConf, maximum: Optional[int] = None) -> float: # pylint: disable=invalid-name
        maximum = maximum or 999
        defaults = DefaultStartLimitIntervalSec
        interval = conf.get(Service, "StartLimitIntervalSec", nix_str(defaults)) # 10s
        return time_to_seconds(interval, maximum)
    def get_RestartSec(self, conf: SystemctlConf, maximum: Optional[int] = None) -> float: # pylint: disable=invalid-name
        maximum = maximum or MAXTIMEOUT
        delay = conf.get(Service, "RestartSec", nix_str(DefaultRestartSec))
        return time_to_seconds(delay, maximum)
    def get_description(self, unit: str, default: str = NIX) -> str:
        return self.get_Description(self.load_conf(unit)) or default
    def get_Description(self, conf: Optional[SystemctlConf], default: str = NIX) -> str: # -> text # pylint: disable=invalid-name
        """ Unit.Description could be empty sometimes """
        if not conf:
            return default or ""
        description = conf.get(Unit, "Description", default)
        return self.expand_special(description, conf)
    def get_User(self, conf: SystemctlConf) -> Optional[str]: # pylint: disable=invalid-name
        return self.expand_special(conf.get(Service, "User", ""), conf)
    def get_Group(self, conf: SystemctlConf) -> Optional[str]: # pylint: disable=invalid-name
        return self.expand_special(conf.get(Service, "Group", ""), conf)
    def get_SupplementaryGroups(self, conf: SystemctlConf) -> List[str]: # pylint: disable=invalid-name
        return self.expand_list(conf.getlist(Service, "SupplementaryGroups", []), conf)
    def expand_list(self, group_lines: List[str], conf: SystemctlConf) -> List[str]:
        result = []
        for line in group_lines:
            for item in line.split():
                if item:
                    result.append(self.expand_special(item, conf))
        return result
    def expand_special(self, cmd: str, conf: SystemctlConf) -> str:
        """ expand %i %t and similar special vars. They are being expanded
            before any other expand_env takes place which handles shell-style
            $HOME references. """
        def xx(arg: str) -> str:
            return unit_name_unescape(arg)
        def yy(arg: str) -> str:
            return arg
        def get_confs(conf: SystemctlConf) -> Dict[str, str]:
            confs={"%": "%"}
            if conf is None: # pragma: no cover (is never null)
                return confs
            unit = parse_unit(conf.name())
            # pylint: disable=invalid-name
            root = conf.root_mode()
            VARTMP = get_VARTMP(root)     # $TMPDIR              # "/var/tmp"
            TMP = get_TMP(root)           # $TMPDIR              # "/tmp"
            RUN = get_RUNTIME_DIR(root)   # $XDG_RUNTIME_DIR     # "/run"
            ETC = get_CONFIG_HOME(root)   # $XDG_CONFIG_HOME     # "/etc"
            DAT = get_VARLIB_HOME(root)   # $XDG_CONFIG_HOME     # "/var/lib"
            LOG = get_LOG_DIR(root)       # $XDG_CONFIG_HOME/log # "/var/log"
            CACHE = get_CACHE_HOME(root)  # $XDG_CACHE_HOME      # "/var/cache"
            HOME = get_HOME(root)         # $HOME or ~           # "/root"
            USER = get_USER(root)         # geteuid().pw_name    # "root"
            USER_ID = get_USER_ID(root)   # geteuid()            # 0
            GROUP = get_GROUP(root)       # getegid().gr_name    # "root"
            GROUP_ID = get_GROUP_ID(root) # getegid()            # 0
            SHELL = get_SHELL(root)       # $SHELL               # "/bin/sh"
            # confs["b"] = boot_ID
            confs["C"] = os_path(self._root, CACHE) # Cache directory root
            confs["E"] = os_path(self._root, ETC)   # Configuration directory root
            confs["F"] = nix_str(conf.filename())      # EXTRA
            confs["f"] = "/%s" % xx(unit.instance or unit.prefix)
            confs["h"] = HOME                       # User home directory
            # confs["H"] = host_NAME
            confs["i"] = yy(unit.instance)
            confs["I"] = xx(unit.instance)       # same as %i but escaping undone
            confs["j"] = yy(unit.component)      # final component of the prefix
            confs["J"] = xx(unit.component)      # unescaped final component
            confs["L"] = os_path(self._root, LOG)
            # confs["m"] = machine_ID
            confs["n"] = yy(unit.fullname)         # Full unit name
            confs["N"] = yy(unit.name)             # Same as "%n", but with the type suffix removed.
            confs["p"] = yy(unit.prefix)           # before the first "@" or same as %n
            confs["P"] = xx(unit.prefix)           # same as %p but escaping undone
            confs["s"] = SHELL
            confs["S"] = os_path(self._root, DAT)
            confs["t"] = os_path(self._root, RUN)
            confs["T"] = os_path(self._root, TMP)
            confs["g"] = GROUP
            confs["G"] = str(GROUP_ID)
            confs["u"] = USER
            confs["U"] = str(USER_ID)
            confs["V"] = os_path(self._root, VARTMP)
            return confs
        def get_conf1(m: Match[str]) -> str:
            confs = get_confs(conf)
            if m.group(1) in confs:
                return confs[m.group(1)]
            logg.warning("can not expand %%%s", m.group(1))
            return ""
        result = ""
        if cmd:
            result = re.sub("[%](.)", lambda m: get_conf1(m), cmd)
            # ++# logg.info("expanded => %s", result)
        return result
    def extra_vars(self) -> List[str]:
        return self._extra_vars # from command line
    def get_env(self, conf: SystemctlConf) -> Dict[str, str]:
        env = os.environ.copy()
        for env_part in conf.getlist(Service, "Environment", []):
            for name, value in self.read_env_part(self.expand_special(env_part, conf)):
                env[name] = value # a '$word' is not special here (lazy expansion)
        for env_file in conf.getlist(Service, "EnvironmentFile", []):
            for name, value in self.read_env_file(self.expand_special(env_file, conf)):
                env[name] = self.expand_env(value, env) # but nonlazy expansion here
        logg.debug("extra-vars %s", self.extra_vars())
        for extra in self.extra_vars():
            if extra.startswith("@"):
                for name, value in self.read_env_file(extra[1:]):
                    logg.info("override %s=%s", name, value)
                    env[name] = self.expand_env(value, env)
            else:
                for name, value in self.read_env_part(extra):
                    logg.info("override %s=%s", name, value)
                    env[name] = value # a '$word' is not special here
        return env
    def expand_env(self, cmd: str, env: Dict[str, str]) -> str:
        def get_env1(m: Match[str]) -> str:
            name = m.group(1)
            if name in env:
                return env[name]
            namevar = "$%s" % name
            logg.debug("can not expand %s", namevar)
            return (EXPAND_KEEP_VARS and namevar or "")
        def get_env2(m: Match[str]) -> str:
            name = m.group(1)
            if name in env:
                return env[name]
            namevar = "${%s}" % name
            logg.debug("can not expand %s", namevar)
            return (EXPAND_KEEP_VARS and namevar or "")
        #
        maxdepth = EXPAND_VARS_MAXDEPTH
        expanded = re.sub(r"[$](\w+)", lambda m: get_env1(m), cmd.replace("\\\n", ""))
        for _ in range(maxdepth):
            new_text = re.sub(r"[$][{](\w+)[}]", lambda m: get_env2(m), expanded)
            if new_text == expanded:
                return expanded
            expanded = new_text
        logg.error("shell variable expansion exceeded maxdepth %s", maxdepth)
        return expanded
    def read_env_file(self, env_file: str) -> Iterable[Tuple[str, str]]: # -> generate[ (name,value) ]
        """ EnvironmentFile=<name> is being scanned """
        mode, env_file = load_path(env_file)
        real_file = os_path(self._root, env_file)
        if not os.path.exists(real_file):
            if mode.check:
                logg.error("file does not exist: %s", real_file)
            else:
                logg.debug("file does not exist: %s", real_file)
            return
        for name, value in read_env_file(env_file, self._root):
            yield name, value
    def read_env_part(self, env_part: str) -> Iterable[Tuple[str, str]]: # -> generate[ (name, value) ]
        """ Environment=<name>=<value> is being scanned """
        # systemd Environment= spec says it is a space-separated list of
        # assignments. In order to use a space or an equals sign in a value
        # one should enclose the whole assignment with double quotes:
        # Environment="VAR1=word word" VAR2=word3 "VAR3=$word 5 6"
        # and the $word is not expanded by other environment variables.
        try:
            for real_line in env_part.split("\n"):
                line = real_line.strip()
                for found in re.finditer(r'\s*("[\w_]+=[^"]*"|[\w_]+=\S*)', line):
                    part = found.group(1)
                    if part.startswith('"'):
                        part = part[1:-1]
                    name, value = part.split("=", 1)
                    yield name, value
        except OSError as e:
            logg.info("while reading %s >> %s", env_part, e)
    def get_dependencies_unit(self, unit: str, styles: Optional[List[str]] = None) -> Dict[str, str]:
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants", "PropagateReloadTo", "Conflicts", ]
        conf = self.get_conf(unit)
        deps: Dict[str, str] = {}
        for style in styles:
            if style.startswith("."):
                for folder in self.sysd_folders():
                    if not folder:
                        continue
                    require_path = os.path.join(folder, unit + style)
                    if self._root:
                        require_path = os_path(self._root, require_path)
                    if os.path.isdir(require_path):
                        for required in os.listdir(require_path):
                            if required not in deps:
                                deps[required] = style
            else:
                for requirelist in conf.getlist(Unit, style, []):
                    for required in requirelist.strip().split(" "):
                        deps[required.strip()] = style
        return deps
    def get_required_dependencies(self, unit: str, styles: Optional[List[str]] = None) -> Dict[str, str]:
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo",
                            ".requires", ".wants"]
        return self.get_dependencies_unit(unit, styles)
    def get_start_dependencies(self, unit: str, styles: Optional[List[str]] = None) -> Dict[str, List[str]]: # pragma: no cover
        """ the list of services to be started as well / TODO: unused """
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants"]
        deps: Dict[str, List[str]] = {}
        unit_deps = self.get_dependencies_unit(unit)
        for dep_unit, dep_style in unit_deps.items():
            if dep_style in styles:
                if dep_unit in deps:
                    if dep_style not in deps[dep_unit]:
                        deps[dep_unit].append(dep_style)
                else:
                    deps[dep_unit] = [dep_style]
                next_deps = self.get_start_dependencies(dep_unit)
                for dep, styles in next_deps.items():
                    for style in styles:
                        if dep in deps:
                            if style not in deps[dep]:
                                deps[dep].append(style)
                        else:
                            deps[dep] = [style]
        return deps
    def sorted_after(self, unitlist: List[str]) -> List[str]:
        """ get correct start order for the unit list (ignoring masked units) """
        conflist = [self.get_conf(unit) for unit in unitlist]
        if TRUE:
            conflist = []
            for unit in unitlist:
                conf = self.get_conf(unit)
                if conf.masked:
                    logg.debug("ignoring masked unit %s", unit)
                    continue
                conflist.append(conf)
        sortlist = sorted_after(conflist)
        return [item.name() for item in sortlist]
    def list_dependencies(self, unit: str, indent: Optional[str] = None) -> Iterable[str]:
        return self._list_dependencies(unit, "", indent)
    def list_all_dependencies(self, unit: str, indent: Optional[str] = None) -> Iterable[str]:
        return self._list_dependencies(unit, "notloaded+restrict", indent)
    def _list_dependencies(self, unit: str, show: str = NIX, indent: Optional[str] = None, mark: Optional[str] = None, loop: List[str] = []) -> Iterable[str]:
        mapping: Dict[str, str] = {}
        mapping["Requires"] = "required to start"
        mapping["Wants"] = "wanted to start"
        mapping["Requisite"] = "required started"
        mapping["Bindsto"] = "binds to start"
        mapping["PartOf"] = "part of started"
        mapping[".requires"] = ".required to start"
        mapping[".wants"] = ".wanted to start"
        mapping["PropagateReloadTo"] = "(to be reloaded as well)"
        mapping["Conflicts"] = "(to be stopped on conflict)"
        restrict = ["Requires", "Requisite", "ConsistsOf", "Wants",
                    "BindsTo", ".requires", ".wants"]
        indent = indent or ""
        mark = mark or ""
        deps = self.get_dependencies_unit(unit)
        conf = self.get_conf(unit)
        if not conf.loaded():
            if "notloaded" in show:
                yield "%s(%s): %s" % (indent, unit, mark)
        else:
            yield "%s%s: %s" % (indent, unit, mark)
            for stop_recursion in ["Conflict", "conflict", "reloaded", "Propagate"]:
                if stop_recursion in mark:
                    return
            for dep in deps:  # pylint: disable=consider-using-dict-items
                if dep in loop:
                    logg.debug("detected loop at %s", dep)
                    continue
                new_loop = loop + list(deps.keys())
                new_indent = indent + "| "
                new_mark = deps[dep]
                if "restrict" not in show:
                    if new_mark not in restrict:
                        continue
                if new_mark in mapping:
                    new_mark = mapping[new_mark]
                restrict = ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants"]
                for line in self._list_dependencies(dep, show, new_indent, new_mark, new_loop):
                    yield line
    def list_start_dependencies_units(self, units: List[str]) -> List[Tuple[str, str]]:
        unit_order: List[str] = []
        deps: Dict[str, List[str]] = {}
        for unit in units:
            unit_order.append(unit)
            # unit_deps = self.get_start_dependencies(unit) # TODO
            unit_deps = self.get_dependencies_unit(unit)
            for dep_unit, styles in unit_deps.items():
                dep_styles = to_list(styles)
                for dep_style in dep_styles:
                    if dep_unit in deps:
                        if dep_style not in deps[dep_unit]:
                            deps[dep_unit].append(dep_style)
                    else:
                        deps[dep_unit] = [dep_style]
        deps_conf: List[SystemctlConf] = []
        for dep in deps:
            if dep in unit_order:
                continue
            conf = self.get_conf(dep)
            if conf.loaded():
                deps_conf.append(conf)
        for unit in unit_order:
            deps[unit] = ["Requested"]
            conf = self.get_conf(unit)
            if conf.loaded():
                deps_conf.append(conf)
        result: List[Tuple[str, str]] = []
        sortlist = sorted_after(deps_conf)
        for item in sortlist:
            line = (item.name(), "(%s)" % (" ".join(deps[item.name()])))
            result.append(line)
        return result
    def load_preset_files(self, *modules: str) -> List[str]: # -> [ preset-file-names,... ]
        """ reads all preset files, returns the scanned files """
        if self._preset_file_list is None:
            self._preset_file_list = {}
            assert self._preset_file_list is not None
            for folder in self.preset_folders():
                if not folder:
                    continue
                if self._root:
                    folder = os_path(self._root, folder)
                if not os.path.isdir(folder):
                    continue
                for name in os.listdir(folder):
                    if not name.endswith(".preset"):
                        continue
                    if name not in self._preset_file_list:
                        path = os.path.join(folder, name)
                        if os.path.isdir(path):
                            continue
                        preset = PresetFile().read(path)
                        self._preset_file_list[name] = preset
            logg.debug("found %s preset files", len(self._preset_file_list))
        return sorted([name for name in self._preset_file_list if fnmatched(name, *modules)])
    def get_preset_of_unit(self, unit: str) -> Optional[str]:
        """ get-preset [UNIT] check the *.preset of this unit
        """
        self.load_preset_files()
        assert self._preset_file_list is not None
        for filename in sorted(self._preset_file_list.keys()):
            preset = self._preset_file_list[filename]
            status = preset.get_preset(unit)
            if status:
                return status
        return None
    def check_env_conditions(self, conf: SystemctlConf, section: str = Unit, warning: int = logging.WARNING) -> List[str]:
        problems: List[str] = []
        unit = conf.name()
        for spec in ["ConditionEnvironment", "AssertEnvironment"]:
            warn = logging.ERROR if "Assert" in spec else warning
            checklist = conf.getlist(section, spec)
            for checkname in checklist:
                mode, want = checkprefix(checkname)
                wantvalue: Optional[str] = None
                if "=" in want:
                    name, wantvalue = want.split("=", 1)
                else:
                    name = want
                value = os.environ.get(name)
                if value is None:
                    if "!" not in mode:
                        logg.log(warn, "%s: %s - $%s not found", unit, spec, name)
                        problems += [spec]
                else:
                    if "!" in mode:
                        if wantvalue is not None and value == wantvalue:
                            logg.log(warn, "%s: %s - $%s wrong value - avoid '%s' have '%s'", unit, spec, name, wantvalue, value)
                            problems += [spec]
                        elif wantvalue is not None:
                            logg.debug("%s: %s - $%s was found - ok as avoid '%s' have '%s'", unit, spec, name, wantvalue, value)
                        else:
                            logg.log(warn, "%s: %s - $%s was found", unit, spec, name)
                            problems += [spec]
                    elif wantvalue is not None and value != wantvalue:
                        logg.log(warn, "%s: %s - $%s wrong value - want '%s' have '%s'", unit, spec, name, wantvalue, value)
                        problems += [spec]
        return problems
    def check_system_conditions(self, conf: SystemctlConf, section: str = Unit, warning: int = logging.WARNING) -> List[str]:
        problems: List[str] = []
        unit = conf.name()
        import platform
        for spec in ["ConditionArchitecture", "AssertArchitecture"]:
            warn = logging.ERROR if "Assert" in spec else warning
            checklist = conf.getlist(section, spec)
            for checkname in checklist:
                mode, want = checkprefix(checkname)
                have = platform.machine().replace("_", "-")
                if not want:
                    logg.debug("%s: %s - nothing to check", unit, spec)
                elif not have:
                    logg.info("%s: %s - nothing to check", unit, spec)
                elif have != want:
                    if "!" not in mode:
                        logg.log(warn, "%s: %s - want %s - have %s", unit, spec, want, have)
                        problems += [spec]
                else:
                    if "!" in mode:
                        logg.log(warn, "%s: %s - avoid %s - have %s", unit, spec, want, have)
                        problems += [spec]
        for spec in ["ConditionHost", "AssertHost"]:
            warn = logging.ERROR if "Assert" in spec else warning
            checklist = conf.getlist(section, spec)
            for checkname in checklist:
                mode, want = checkprefix(checkname)
                have = platform.node()
                if not want:
                    logg.debug("%s: %s - nothing to check", unit, spec)
                elif not have:
                    logg.info("%s: %s - nothing to check", unit, spec)
                elif have != want:
                    if "!" not in mode:
                        logg.log(warn, "%s: %s - want %s - have %s", unit, spec, want, have)
                        problems += [spec]
                else:
                    if "!" in mode:
                        logg.log(warn, "%s: %s - avoid %s - have %s", unit, spec, want, have)
                        problems += [spec]
        return problems
    def check_file_conditions(self, conf: SystemctlConf, section: str = Unit, warning: int = logging.WARNING) -> List[str]:
        # added in Systemctl 244
        problems: List[str] = []
        unit = conf.name()
        for spec in ["ConditionPathExistsGlob", "AssertPathExistsGlob"]:
            warn = logging.ERROR if "Assert" in spec else warning
            checklist = conf.getlist(section, spec)
            for checkfile in checklist:
                mode, filename = checkprefix(checkfile)
                filepath = os_path(self._root, filename)
                found = len(glob.glob(filepath))
                if found:
                    if "!" in mode:
                        logg.log(warn, "%s: %s - found %s files in: %s", unit, spec, found, filename)
                        problems += [spec+"="+checkfile]
                    else:
                        logg.debug("%s: %s ....found [%s]", unit, spec, filepath)
                else:
                    if "!" not in mode:
                        logg.log(warn, "%s: %s - no files found: %s", unit, spec, filename)
                        problems += [spec+"="+checkfile]
                    else:
                        logg.debug("%s: %s....notfound [%s]", unit, spec, filepath)
        for spec in ["ConditionPathExists", "ConditionPathIsDirectory", "ConditionPathIsSymbolicLink", "ConditionPathIsMountPoint",
                     "ConditionPathIsReadWrite", "ConditionDirectoryNotEmpty", "ConditionFileIsExecutable", "ConditionFileNotEmpty",
                     "AssertPathExists", "AssertPathIsDirectory", "AssertPathIsSymbolicLink", "AssertPathIsMountPoint",
                     "AssertPathIsReadWrite", "AssertDirectoryNotEmpty", "AssertFileIsExecutable", "AssertFileNotEmpty"]:
            warn = logging.ERROR if "Assert" in spec else warning
            checklist = conf.getlist(section, spec)
            if checklist:
                logg.info(" --> checking %s %s", spec, checklist)
            for checkfile in checklist:
                mode, checkname = checkprefix(checkfile)
                filename = self.expand_special(checkname, conf)
                if not os.path.isabs(filename):
                    logg.error("%s: %s - path not absolute: %s", unit, spec, filename)
                    problems += [spec+"="+checkfile]
                    continue
                filepath = os_path(NIX if filename.startswith("//") else self._root, filename)
                if not os.path.exists(filepath):
                    logg.error("not found %s", filepath)
                    if "!" not in mode:
                        logg.log(warn, "%s: %s - path not found: %s", unit, spec, filename)
                        problems += [spec+"="+checkfile]
                else:
                    if "PathExists" in spec:
                        if "!" in mode:
                            logg.log(warn, "%s: %s - must not exist: %s", unit, spec, filename)
                            problems += [spec+"="+checkfile]
                    if "FileNotEmpty" in spec:
                        if not os.path.isfile(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not a file: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        elif not os.path.getsize(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - file is empty: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - file is not empty: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                    if "DirectoryNotEmpty" in spec:
                        if not os.path.isdir(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not a directory: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        elif not os.listdir(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - directory is empty: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - directory is not empty: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                    if "IsDirectory" in spec:
                        if not os.path.isdir(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not a directory: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - is a directory: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                    if "IsSymbolicLink" in spec:
                        if not os.path.islink(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not a symbolic link: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - not a symbolic link: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                    if "IsMountPoint" in spec:
                        if not os.path.ismount(filepath):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not a mount point: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - is a mount point: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                    if "IsReadWrite" in spec:
                        if not os.access(filepath, os.R_OK):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not readable: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        elif not os.access(filepath, os.W_OK):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not writable: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - is readwrite: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                    if "IsExecutable" in spec:
                        if not os.access(filepath, os.X_OK):
                            if "!" not in mode:
                                logg.log(warn, "%s: %s - not executable: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
                        else:
                            if "!" in mode:
                                logg.log(warn, "%s: %s - is executable: %s", unit, spec, filename)
                                problems += [spec+"="+checkfile]
        return problems
    def syntax_check(self, conf: SystemctlConf, *, conditions: bool = True) -> int:
        errors = 0
        if conditions:
            errors += len(self.check_file_conditions(conf, warning=logging.INFO)) # conditions may be get active later
        filename = conf.filename()
        if filename and filename.endswith(".service"):
            errors += self.syntax_check_service(conf)
        if TRUE:
            errors += self.syntax_check_enable(conf)
        return errors
    def syntax_check_enable(self, conf: SystemctlConf, section: str = Install) -> int:
        errors = 0
        unit = conf.name()
        target = conf.get(section, "WantedBy", NIX)
        if target and target not in SYSD_TARGET_REQUIRES:
            logg.error("%s: [Install] WantedBy unknown: %s", unit, target)
            logg.info(" must be in %s", list(SYSD_TARGET_REQUIRES.keys()))
            errors += 1
        return errors
    def syntax_check_service(self, conf: SystemctlConf, section: str = Service) -> int:
        unit = conf.name()
        if not conf.data.has_section(Service):
            logg.error(" %s: a .service file without [Service] section", unit)
            return 101
        errors = 0
        haveType = conf.get(section, "Type", "simple")  # pylint: disable=invalid-name
        haveExecStart = conf.getlist(section, "ExecStart", [])  # pylint: disable=invalid-name
        haveExecStop = conf.getlist(section, "ExecStop", [])  # pylint: disable=invalid-name
        haveExecReload = conf.getlist(section, "ExecReload", [])  # pylint: disable=invalid-name
        usedExecStart: List[str] = []  # pylint: disable=invalid-name
        usedExecStop: List[str] = []  # pylint: disable=invalid-name
        usedExecReload: List[str] = []  # pylint: disable=invalid-name
        if haveType not in ["simple", "exec", "forking", "notify", "oneshot", "dbus", "idle"]:
            logg.error(" %s: Failed to parse service type, ignoring: %s", unit, haveType)
            errors += 100
        for line in haveExecStart:
            mode, exe = exec_path(line)
            if not exe.startswith("/"):
                if mode.check:
                    logg.error("  %s: %s Executable path is not absolute.", unit, section)
                else:
                    logg.warning("%s: %s Executable path is not absolute.", unit, section)
                logg.info("%s: %s exe = %s", unit, section, exe)
                errors += 1
            usedExecStart.append(line)
        for line in haveExecStop:
            mode, exe = exec_path(line)
            if not exe.startswith("/"):
                if mode.check:
                    logg.error("  %s: %s Executable path is not absolute.", unit, section)
                else:
                    logg.warning("%s: %s Executable path is not absolute.", unit, section)
                logg.info("%s: %s exe = %s", unit, section, exe)
                errors += 1
            usedExecStop.append(line)
        for line in haveExecReload:
            mode, exe = exec_path(line)
            if not exe.startswith("/"):
                if mode.check:
                    logg.error("  %s: %s Executable path is not absolute.", unit, section)
                else:
                    logg.warning("%s: %s Executable path is not absolute.", unit, section)
                logg.info("%s: %s exe = %s", unit, section, exe)
                errors += 1
            usedExecReload.append(line)
        if haveType in ["simple", "exec", "notify", "forking", "idle"]:
            if not usedExecStart and not usedExecStop:
                logg.error(" %s: %s lacks both ExecStart and ExecStop= setting. Refusing.", unit, section)
                errors += 101
            elif not usedExecStart and haveType != "oneshot":
                logg.error(" %s: %s has no ExecStart= setting, which is only allowed for Type=oneshot services. Refusing.", unit, section)
                errors += 101
        if len(usedExecStart) > 1 and haveType != "oneshot":
            logg.error(" %s: there may be only one %s ExecStart statement (unless for 'oneshot' services)."
                       + "\n\t\t\tYou can use ExecStartPre / ExecStartPost to add additional commands.", unit, section)
            errors += 1
        if len(usedExecStop) > 1 and haveType != "oneshot":
            logg.info(" %s: there should be only one %s ExecStop statement (unless for 'oneshot' services)."
                      + "\n\t\t\tYou can use ExecStopPost to add additional commands (also executed on failed Start)", unit, section)
        if len(usedExecReload) > 1:
            logg.info(" %s: there should be only one %s ExecReload statement."
                      + "\n\t\t\tUse ' ; ' for multiple commands (ExecReloadPost or ExedReloadPre do not exist)", unit, section)
        if len(usedExecReload) > 0 and "/bin/kill " in usedExecReload[0]:
            logg.warning(" %s: the use of /bin/kill is not recommended for %s ExecReload as it is asynchronous."
                         + "\n\t\t\tThat means all the dependencies will perform the reload simultaneously / out of order.", unit, section)
        if conf.getlist(Service, "ExecRestart", []):  # pragma: no cover
            logg.error(" %s: there no such thing as an %s ExecRestart (ignored)", unit, section)
        if conf.getlist(Service, "ExecRestartPre", []):  # pragma: no cover
            logg.error(" %s: there no such thing as an %s ExecRestartPre (ignored)", unit, section)
        if conf.getlist(Service, "ExecRestartPost", []):  # pragma: no cover
            logg.error(" %s: there no such thing as an %s ExecRestartPost (ignored)", unit, section)
        if conf.getlist(Service, "ExecReloadPre", []):  # pragma: no cover
            logg.error(" %s: there no such thing as an %s ExecReloadPre (ignored)", unit, section)
        if conf.getlist(Service, "ExecReloadPost", []):  # pragma: no cover
            logg.error(" %s: there no such thing as an %s ExecReloadPost (ignored)", unit, section)
        if conf.getlist(Service, "ExecStopPre", []):  # pragma: no cover
            logg.error(" %s: there no such thing as an %s ExecStopPre (ignored)", unit, section)
        for env_file in conf.getlist(Service, "EnvironmentFile", []):
            if env_file.startswith("-"): continue
            if not os.path.isfile(os_path(self._root, self.expand_special(env_file, conf))):
                logg.error(" %s: Failed to load environment files: %s", unit, env_file)
                errors += 101
        return errors
    def exec_check(self, conf: SystemctlConf, env: Dict[str, str], section: str = Service, exectype: str = NIX) -> bool:
        if conf is None: # pragma: no cover (is never null)
            return True
        if not conf.data.has_section(section):
            return True  # pragma: no cover
        if self.is_sysv_file(conf.filename()):
            return True # we don't care about that
        unit = conf.name()
        abspath = 0
        notexists = 0
        badusers = 0
        badgroups = 0
        for execs in ["ExecStartPre", "ExecStart", "ExecStartPost", "ExecStop", "ExecStopPost", "ExecReload"]:
            if not execs.startswith(exectype):
                continue
            for cmd in conf.getlist(section, execs, []):
                mode, newcmd = self.expand_cmd(cmd, env, conf)
                if not newcmd:
                    continue
                exe = newcmd[0]
                if not exe:
                    continue
                if exe[0] != "/":
                    logg.error(" %s: Exec is not an absolute path:  %s=%s", unit, execs, cmd)
                    abspath += 1
                if not os.path.isfile(exe):
                    logg.error(" %s: Exec command does not exist: (%s) %s", unit, execs, exe)
                    if mode.check:
                        notexists += 1
                    newexe1 = os.path.join("/usr/bin", exe)
                    newexe2 = os.path.join("/bin", exe)
                    if os.path.exists(newexe1):
                        logg.error(" %s: but this does exist: %s  %s", unit, " " * len(execs), newexe1)
                    elif os.path.exists(newexe2):
                        logg.error(" %s: but this does exist: %s      %s", unit, " " * len(execs), newexe2)
        users = [conf.get(section, "User", ""), conf.get(section, "SocketUser", "")]
        groups = [conf.get(section, "Group", ""), conf.get(section, "SocketGroup", "")] + conf.getlist(section, "SupplementaryGroups")
        for user in users:
            if user:
                try: pwd.getpwnam(self.expand_special(user, conf))
                except (OSError, LookupError) as e:
                    logg.error(" %s: User does not exist: %s (%s)", unit, user, getattr(e, "__doc__", ""))
                    badusers += 1
        for group in groups:
            if group:
                try: grp.getgrnam(self.expand_special(group, conf))
                except (OSError, LookupError) as e:
                    logg.error(" %s: Group does not exist: %s (%s)", unit, group, getattr(e, "__doc__", ""))
                    badgroups += 1
        tmpproblems = 0
        for setting in ("RootDirectory", "RootImage", "BindPaths", "BindReadOnlyPaths",
                        "ReadWritePaths", "ReadOnlyPaths", "TemporaryFileSystem"):
            setting_value = conf.get(section, setting, "")
            if setting_value:
                logg.info("%s: %s private directory remounts ignored: %s=%s", unit, section, setting, setting_value)
                tmpproblems += 1
        for setting in ("PrivateTmp", "PrivateDevices", "PrivateNetwork", "PrivateUsers", "DynamicUser",
                        "ProtectSystem", "ProjectHome", "ProtectHostname", "PrivateMounts", "MountAPIVFS"):
            setting_yes = conf.getbool(section, setting, "no")
            if setting_yes:
                logg.info("%s: %s private directory option is ignored: %s=yes", unit, section, setting)
                tmpproblems += 1
        if not abspath and not notexists and not badusers and not badgroups:
            return True
        if TRUE:
            filename = nix_str(conf.filename())
            if len(filename) > 44: filename = o44(filename)
            logg.error(" !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            if abspath:
                logg.error(" The SystemD ExecXY commands must always be absolute paths by definition.")
                time.sleep(1)
            if notexists:
                logg.error(" Oops, %s executable paths were not found in the current environment. Refusing.", notexists)
                time.sleep(1)
            if badusers or badgroups:
                logg.error(" Oops, %s user names and %s group names were not found. Refusing.", badusers, badgroups)
                time.sleep(1)
            if tmpproblems:
                logg.info("  Note, %s private directory settings are ignored. The application should not depend on it.", tmpproblems)
                time.sleep(1)
            logg.error(" !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return False
    def expand_cmd(self, cmd: str, env: Dict[str, str], conf: SystemctlConf) -> Tuple[ExecMode, List[str]]:
        mode, exe = exec_path(cmd)
        if mode.noexpand:
            newcmd = self.split_cmd(exe)
        else:
            newcmd = self.split_cmd_and_expand(exe, env, conf)
        if mode.argv0:
            if len(newcmd) > 1:
                del newcmd[1] # TODO: keep but allow execve calls to pick it up
        return mode, newcmd
    def split_cmd(self, cmd: str) -> List[str]:
        cmd2 = cmd.replace("\\\n", "")
        newcmd: List[str] = []
        for part in shlex.split(cmd2):
            newcmd += [part]
        return newcmd
    def split_cmd_and_expand(self, cmd: str, env: Dict[str, str], conf: SystemctlConf) -> List[str]:
        """ expand ExecCmd statements including %i and $MAINPID """
        cmd2 = cmd.replace("\\\n", "")
        # according to documentation, when bar="one two" then the expansion
        # of '$bar' is ["one","two"] and '${bar}' becomes ["one two"]. We
        # tackle that by expand $bar before shlex, and the rest thereafter.
        def get_env1(m: Match[str]) -> str:
            name = m.group(1)
            if name in env:
                return env[name]
            logg.debug("can not expand $%s", name)
            return ""  # empty string
        def get_env2(m: Match[str]) -> str:
            name = m.group(1)
            if name in env:
                return env[name]
            logg.debug("can not expand $%s}}", name)
            return ""  # empty string
        cmd3 = re.sub(r"[$](\w+)", lambda m: get_env1(m), cmd2)
        newcmd: List[str] = []
        for part in shlex.split(cmd3):
            part2 = self.expand_special(part, conf)
            newcmd += [re.sub(r"[$][{](\w+)[}]", lambda m: get_env2(m), part2)] # type: ignore[arg-type]
        return newcmd

class SystemctlListenThread(threading.Thread):
    """ support LISTEN modules """
    def __init__(self, systemctl: 'Systemctl') -> None:
        threading.Thread.__init__(self, name="listen")
        self.systemctl = systemctl
        self.stopped = threading.Event()
    def stop(self) -> None:
        self.stopped.set()
    def run(self) -> None:
        READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR # pylint: disable=invalid-name
        READ_WRITE = READ_ONLY | select.POLLOUT # pylint: disable=invalid-name,unused-variable
        me = os.getpid()
        if DEBUG_INITLOOP: # pragma: no cover
            logg.info("[%s] listen: new thread", me)
        socketlist = self.systemctl.socketlist()
        if not socketlist:
            return
        if DEBUG_INITLOOP: # pragma: no cover
            logg.info("[%s] listen: start thread", me)
        listen = select.poll()
        for sock in socketlist:
            listen.register(sock, READ_ONLY)
            sock.listen()
            logg.debug("[%s] listen: %s :%s", me, sock.name(), sock.addr())
        started = time.monotonic()
        while not self.stopped.is_set():
            try:
                sleep_sec = self.systemctl.loop_sleep - (time.monotonic() - started)
                if sleep_sec < YIELD:
                    sleep_sec = YIELD
                sleeping = sleep_sec
                while sleeping > 2:
                    time.sleep(1) # accept signals atleast every second
                    sleeping = self.systemctl.loop_sleep - (time.monotonic() - started)
                    if sleeping < YIELD:
                        sleeping = YIELD
                        break
                time.sleep(sleeping) # remainder waits less that 2 seconds
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[%s] listen: poll", me)
                accepting = listen.poll(100) # milliseconds
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[%s] listen: poll (%s)", me, len(accepting))
                for sock_fileno, _ in accepting:
                    for sock in socketlist:
                        if sock.fileno() == sock_fileno:
                            if not self.stopped.is_set():
                                if self.systemctl.loop_lock.acquire():
                                    logg.debug("[%s] listen: accept %s :%s", me, sock.name(), sock_fileno)
                                    self.systemctl.do_accept_socket_from(sock.conf, sock.sock)
            except Exception as e:
                logg.info("[%s] listen: interrupted >> %s", me, e)
                raise
        for sock in socketlist:
            try:
                listen.unregister(sock)
                sock.close()
            except OSError as e:
                logg.warning("[%s] listen: close socket >> %s", me, e)
        return

class Systemctl:
    """ emulation for systemctl commands """
    error: int
    _force: bool
    _full: bool
    _no_ask_password: bool
    _no_legend: bool
    _do_now: int
    _preset_mode: str
    _quiet: bool
    _root: str
    _show_all: int
    _unit_property: Optional[str]
    _unit_state: Optional[str]
    _unit_type: Optional[str]
    _systemd_version: int
    _pid_file_folder: str
    _journal_log_folder: str
    _default_target: str
    _sysinit_target: Optional[SystemctlConf]
    exit_mode: int
    init_mode: int
    _init: int
    _log_file: Dict[str, int]
    _log_hold: Dict[str, bytes]
    _boottime: Optional[float]
    _restarted_unit: Dict[str, List[float]]
    _restart_failed_units: Dict[str, float]
    _sockets: Dict[str, SystemctlSocket]
    _default_services: Dict[str, List[str]] # [target-name] -> List[service-name]
    loop_sleep: int
    loop: threading.Lock
    units: SystemctlLoadedUnits
    def __init__(self) -> None:
        self.error = NOT_A_PROBLEM # program exitcode or process returncode
        # from command line options or the defaults
        self._force = DO_FORCE
        self._full = DO_FULL
        self._no_ask_password = NO_ASK_PASSWORD
        self._no_legend = NO_LEGEND
        self._do_now = DO_NOW
        self._preset_mode = PRESET_MODE
        self._quiet = DO_QUIET
        self._root = ROOT
        self._show_all = SHOW_ALL
        self._only_what = commalist(ONLY_WHAT) or [""]
        self._only_property = commalist(ONLY_PROPERTY)
        self._only_state = commalist(ONLY_STATE)
        self._only_type = commalist(ONLY_TYPE)
        # some common constants that may be changed
        self._systemd_version = SYSTEMD_VERSION
        self._journal_log_folder = JOURNAL_LOG_FOLDER
        # and the actual internal runtime state
        self._default_target = DEFAULT_TARGET
        self._sysinit_target = None # stores a UnitConf()
        self.exit_mode = EXIT_MODE or 0
        self.init_mode = INIT_MODE or 0
        self._log_file = {} # init-loop
        self._log_hold = {} # init-loop
        self._boottime = None # cache self.get_boottime()
        self._restarted_unit = {}
        self._restart_failed_units = {}
        self._sockets = {}
        self._default_services = {}
        self.loop_sleep = max(1, INITLOOPSLEEP // INIT_MODE) if INIT_MODE else INITLOOPSLEEP
        self.loop_lock = threading.Lock()
        self.units = SystemctlLoadedUnits(self._root)
    def get_unit_type(self, module: str) -> Optional[str]:
        _nam, ext = os.path.splitext(module)
        if ext in [".service", ".socket", ".target"]:
            return ext[1:]
        logg.debug("unknown unit type %s", module)
        return None
    def get_unit_section(self, module: str, default: str = Service) -> str:
        return string.capwords(self.get_unit_type(module) or default)
    def get_unit_section_from(self, conf: SystemctlConf, default: str = Service) -> str:
        return self.get_unit_section(conf.name(), default)
    def list_service_units(self, *modules: str) -> List[Tuple[str, str, str]]: # -> [ (unit,loaded+active+substate,description) ]
        """ show all the service units """
        result: Dict[str, str] = {}
        active: Dict[str, str] = {}
        substate: Dict[str, str] = {}
        description: Dict[str, str] = {}
        for unit in self.units.match_units(to_list(modules)):
            result[unit] = "not-found"
            active[unit] = "inactive"
            substate[unit] = "dead"
            description[unit] = ""
            try:
                conf = self.units.get_conf(unit)
                result[unit] = "loaded"
                description[unit] = self.units.get_Description(conf)
                active[unit] = self.active_state(conf)
                substate[unit] = self.active_substate(conf) or "unknown"
            except OSError as e:
                logg.warning("list-units >> %s", e)
            if self._only_state:
                if result[unit] in self._only_state:
                    pass
                elif active[unit] in self._only_state:
                    pass
                elif substate[unit] in self._only_state:
                    pass
                else:
                    del result[unit]
        return [(unit, result[unit] + " " + active[unit] + " " + substate[unit], description[unit]) for unit in sorted(result)]
    def list_units_modules(self, *modules: str) -> List[Tuple[str, str, str]]: # -> [ (unit,loaded,description) ]
        """ list-units [PATTERN]... -- list loaded units.
        If one or more PATTERNs are specified, only units matching one of
        them are shown. NOTE: This is the default command."""
        hint = "To show all installed unit files use 'systemctl list-unit-files'."
        result = self.list_service_units(*modules)
        if self._no_legend:
            return result
        found = "%s loaded units listed." % len(result)
        return result + [("", "", ""), (found, "", ""), (hint, "", "")]
    def list_service_unit_files(self, *modules: str) -> List[Tuple[str, str]]: # -> [ (unit,enabled) ]
        """ show all the service units and the enabled status"""
        logg.debug("list service unit files for %s", modules)
        result: Dict[str, Optional[SystemctlConf]] = {}
        enabled: Dict[str, str] = {}
        for unit in self.units.match_units(to_list(modules)):
            if self._only_type and self.get_unit_type(unit) not in self._only_type:
                continue
            result[unit] = None
            enabled[unit] = ""
            try:
                conf = self.units.get_conf(unit)
                if self.units.not_user_conf(conf):
                    result[unit] = None
                    continue
                result[unit] = conf
                enabled[unit] = self.enabled_state(conf)
            except OSError as e:
                logg.warning("list-units >> %s", e)
        return [(unit, enabled[unit]) for unit in sorted(result) if result[unit]]
    def list_target_unit_files(self, *modules: str) -> List[Tuple[str, str]]: # -> [ (unit,enabled) ]
        """ show all the target units and the enabled status"""
        enabled: Dict[str, str] = {}
        targets: Dict[str, Optional[str]] = {}
        for target, filepath in self.units.each_target_file():
            logg.info("target %s", filepath)
            targets[target] = filepath
            enabled[target] = "static"
        for unit in SYSD_COMMON_TARGETS:
            targets[unit] = None
            enabled[unit] = "static"
            if unit in SYSD_ENABLED_TARGETS:
                enabled[unit] = "enabled"
            if unit in SYSD_DISABLED_TARGETS:
                enabled[unit] = "disabled"
        return [(unit, enabled[unit]) for unit in sorted(targets) if fnmatched(unit, *modules)]
    def list_service_unit_basics(self) -> List[Tuple[str, str, str]]:
        """ show all the basic loading state of services """
        return self.units.list_all()
    def list_unit_files_modules(self, *modules: str) -> List[Tuple[str, str]]: # -> [ (unit,enabled) ]
        """ list-unit-files [PATTERN]... -- list installed unit files.
        List installed unit files and their enablement state (as reported
        by is-enabled). If one or more PATTERNs are specified, only units
        whose filename (just the last component of the path) matches one of
        them are shown. This command reacts to limitations of --type being
        --type=service or --type=target (and --now for some basics)."""
        result: List[Tuple[str, str]] = []
        if self._do_now:
            basics = self.list_service_unit_basics()
            result = [(name, sysv + " " + filename) for name, sysv, filename in basics]
        elif self._only_type:
            if "target" in self._only_type:
                result = self.list_target_unit_files(*modules)
            if "service" in self._only_type:
                result = self.list_service_unit_files(*modules)
        else:
            result = self.list_target_unit_files()
            result += self.list_service_unit_files(*modules)
        if self._no_legend:
            return result
        found = "%s unit files listed." % len(result)
        return [("UNIT FILE", "STATE")] + result + [("", ""), (found, "")]
    ##
    ##
    def read_pid_file(self, pid_file: str, default: Optional[int] = None) -> Optional[int]:
        pid = default
        if not pid_file:
            return default
        if not os.path.isfile(pid_file):
            return default
        if self.truncate_old(pid_file):
            return default
        try:
            # some pid-files from applications contain multiple lines
            with open(pid_file) as f:
                for line in f:
                    if line.strip():
                        pid = to_int_if(line.strip())
                        break
        except (OSError, ValueError) as e:
            logg.warning("bad read of pid file '%s' >> %s", pid_file, e)
        return pid
    def wait_pid_file(self, pid_file: str, timeout: Optional[int] = None) -> Optional[int]: # -> pid?
        """ wait some seconds for the pid file to appear and return the pid """
        timeout = int(timeout or (DefaultTimeoutStartSec/2))
        timeout = max(timeout, (MinimumTimeoutStartSec))
        dirpath = os.path.dirname(os.path.abspath(pid_file))
        for attempt in range(timeout):
            logg.debug("%s wait pid file %s", delayed(attempt), pid_file)
            if not os.path.isdir(dirpath):
                time.sleep(1) # until TimeoutStartSec/2
                continue
            pid = self.read_pid_file(pid_file)
            if not pid:
                time.sleep(1) # until TimeoutStartSec/2
                continue
            if not pid_exists(pid):
                time.sleep(1) # until TimeoutStartSec/2
                continue
            return pid
        return None
    def get_pid_file(self, unit: str) -> str:
        """ actual file path of pid file (internal) """
        conf = self.units.get_conf(unit)
        return self.pid_file(conf) or self.status_file(conf)
    def pid_file(self, conf: SystemctlConf, default: str = NIX) -> str:
        """ get the specified pid file path (not a computed default) """
        pid_file = self.get_PIDFile(conf) or default
        return os_path(self._root, self.units.expand_special(pid_file, conf))
    def get_PIDFile(self, conf: SystemctlConf, default: Optional[str] = None) -> str: # pylint: disable=invalid-name
        return conf.get(Service, "PIDFile", default)
    def read_mainpid_from(self, conf: SystemctlConf, default: Optional[int] = None) -> Optional[int]:
        """ MAINPID is either the PIDFile content written from the application
            or it is the value in the status file written by this systemctl.py code """
        pid_file = self.pid_file(conf)
        if pid_file:
            return self.read_pid_file(pid_file, default)
        status = self.read_status_from(conf)
        if "MainPID" in status:
            return to_int_if(status["MainPID"], default)
        return default
    def clean_pid_file_from(self, conf: SystemctlConf) -> None:
        pid_file = self.pid_file(conf)
        if pid_file and os.path.isfile(pid_file):
            try:
                os.remove(pid_file)
            except OSError as e:
                logg.warning("while rm %s >> %s", pid_file, e)
        self.write_status_from(conf, MainPID=None)
    def get_status_file(self, unit: str) -> str: # for testing
        conf = self.units.get_conf(unit)
        return self.status_file(conf)
    def status_file(self, conf: SystemctlConf) -> str:
        status_file = self.get_StatusFile(conf)
        # this not a real setting, but do the expand_special anyway
        return os_path(self._root, self.units.expand_special(status_file, conf))
    def get_StatusFile(self, conf: SystemctlConf) -> str: # -> text # pylint: disable=invalid-name
        """ file where to store a status mark """
        status_file = self.units.get_StatusFile(conf)
        if status_file:
            return status_file
        root = conf.root_mode()
        folder = get_PID_DIR(root)
        name = "%s.status" % conf.name()
        return os.path.join(folder, name)
    def clean_status_from(self, conf: SystemctlConf) -> None:
        status_file = self.status_file(conf)
        if os.path.exists(status_file):
            os.remove(status_file)
        conf.status = {}
    def write_status_from(self, conf: SystemctlConf, **status: Union[str, int, None]) -> bool: # -> bool(written)
        """ if a status_file is known then path is created and the
            give status is written as the only content. """
        status_file = self.status_file(conf)
        # if not status_file: return False
        dirpath = os.path.dirname(os.path.abspath(status_file))
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        if conf.status is None:
            conf.status = self.read_status_from(conf)
        if TRUE:
            for key in sorted(status.keys()):
                value = status[key]
                if key.upper() == "AS": key = "ActiveState"
                if key.upper() == "EXIT": key = "ExecMainCode"
                if value is None:
                    try: del conf.status[key]
                    except KeyError: pass
                else:
                    conf.status[key] = nix_str(value)
        try:
            with open(status_file, "w") as f:
                for key in sorted(conf.status):
                    value = conf.status[key]
                    if key == "MainPID" and str(value) == "0":
                        logg.warning("[status] ignore writing MainPID=0")
                        continue
                    content = F"{key}={value}\n"
                    logg.debug("[status] writing to %s |%s", status_file, content.strip().replace("\n","|"))
                    f.write(content)
        except IOError as e:
            logg.error("[status] writing to %s >> %s << STATUS %s", status_file, e, status)
        return True
    def read_status_from(self, conf: SystemctlConf) -> Dict[str, str]:
        status_file = self.status_file(conf)
        status: Dict[str, str] = {}
        # if not status_file: return status
        if not os.path.isfile(status_file):
            if DEBUG_STATUS: logg.debug("[status] no status file: %s\n returning %s", status_file, status)
            return status
        if self.truncate_old(status_file):
            if DEBUG_STATUS: logg.debug("[status] old status file: %s\n returning %s", status_file, status)
            return status
        try:
            if DEBUG_STATUS: logg.debug("reading %s", status_file)
            with open(status_file) as f:
                for line in f:
                    if line.strip():
                        m = re.match(r"(\w+)[:=](.*)", line)
                        if m:
                            key, value = m.group(1), m.group(2)
                            if key.strip():
                                status[key.strip()] = value.strip()
                        else:  # pragma: no cover
                            logg.warning("[status] ignored %s", line.strip())
        except (OSError, ValueError) as e:
            logg.warning("[status] bad read of status file '%s'", status_file)
            logg.debug("  [status] bad read of status file >> %s", e)
        return status
    def get_status_from(self, conf: SystemctlConf, name: str, default: Optional[str] = None) -> Optional[str]:
        if conf.status is None:
            conf.status = self.read_status_from(conf)
        return conf.status.get(name, default)
    def set_status_from(self, conf: SystemctlConf, name: str, value: Optional[str]) -> None:
        if conf.status is None:
            conf.status = self.read_status_from(conf)
        if value is None:
            try: del conf.status[name]
            except KeyError: pass
        else:
            conf.status[name] = value
    #
    def get_boottime(self) -> float:
        """ detects the boot time of the container - in general the start time of PID 1 """
        if self._boottime is None:
            self._boottime = self.get_boottime_from_proc()
        assert self._boottime is not None
        return self._boottime
    def get_boottime_from_proc(self) -> float:
        """ detects the latest boot time by looking at the start time of available process"""
        pid1 = BOOT_PID_MIN or 0
        pid_max = BOOT_PID_MAX
        if pid_max < 0:
            pid_max = pid1 - pid_max
        for pid in range(pid1, pid_max):
            proc = _proc_pid_stat.format(pid = pid)
            try:
                if os.path.exists(proc):
                    # return os.path.getmtime(proc) # did sometimes change
                    return self.path_proc_started(proc)
            except OSError as e: # pragma: no cover
                logg.warning("boottime - could not access %s >> %s", proc, e)
        if DEBUG_BOOTTIME:
            logg.debug(" boottime from the oldest entry in /proc [nothing in %s..%s]", pid1, pid_max)
        return self.get_boottime_from_old_proc()
    def get_boottime_from_old_proc(self) -> float:
        booted = time.time()
        for pid in os.listdir(_proc_pid_dir):
            if not pid or not pid[0].isdigit():
                continue
            proc = _proc_pid_stat.format(pid = pid)
            try:
                if os.path.exists(proc):
                    # ctime = os.path.getmtime(proc)
                    ctime = self.path_proc_started(proc)
                    if ctime < booted:
                        booted = ctime
            except OSError as e: # pragma: no cover
                logg.warning("could not access %s >> %s", proc, e)
        return booted

    # Use uptime, time process running in ticks, and current time to determine process boot time
    # You can't use the modified timestamp of the status file because it isn't static.
    # ... using clock ticks it is known to be a linear time on Linux
    def path_proc_started(self, proc: str) -> float:
        # get time process started after boot in clock ticks
        with open(proc) as file_stat:
            data_stat = file_stat.readline()
        file_stat.close()
        stat_data = data_stat.split()
        started_ticks = stat_data[21]
        # man proc(5): "(22) starttime = The time the process started after system boot."
        #    ".. the value is expressed in clock ticks (divide by sysconf(_SC_CLK_TCK))."
        # NOTE: for containers the start time is related to the boot time of host system.
        ticks_per_sec = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
        started_secs = float(started_ticks) / ticks_per_sec
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT .. Proc started time:  %.3f (%s)", started_secs, proc)
        # this value is the start time from the host system

        # Variant 1:
        system_uptime = _proc_sys_uptime
        with open(system_uptime, "rb") as file_uptime:
            data_uptime = file_uptime.readline()
        file_uptime.close()
        uptime_data = data_uptime.decode().split()
        uptime_secs = float(uptime_data[0])
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 1. System uptime secs: %.3f (%s)", uptime_secs, system_uptime)

        # get time now
        now = time.time()
        started_time = now - (uptime_secs - started_secs)
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 1. -> %s (/proc has been running)", datetime.datetime.fromtimestamp(started_time))

        # Variant 2:
        system_stat = _proc_sys_stat
        system_btime = 0.
        with open(system_stat, "rb") as f:
            for line in f:
                assert isinstance(line, bytes)
                if line.startswith(b"btime"):
                    system_btime = float(line.decode().split()[1])
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 2. System btime secs: %.3f (%s)", system_btime, system_stat)

        started_btime = system_btime + started_secs
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 2. -> %s (/proc has been running)", datetime.datetime.fromtimestamp(started_btime))

        # return started_time
        return started_btime

    def get_filetime(self, filename: str) -> float:
        return os.path.getmtime(filename)
    def truncate_old(self, filename: str) -> bool:
        filetime = self.get_filetime(filename)
        boottime = self.get_boottime()
        if filetime >= boottime:
            if DEBUG_BOOTTIME:
                logg.debug("  file time: %s (%s)", datetime.datetime.fromtimestamp(filetime), o30(filename))
                logg.debug("  boot time: %s (%s)", datetime.datetime.fromtimestamp(boottime), "status modified later")
            return False # OK
        if DEBUG_BOOTTIME:
            logg.info("  file time: %s (%s)", datetime.datetime.fromtimestamp(filetime), o30(filename))
            logg.info("  boot time: %s (%s)", datetime.datetime.fromtimestamp(boottime), "status TRUNCATED NOW")
        try:
            shutil_truncate(filename)
        except OSError as e:
            logg.warning("while truncating >> %s", e)
        return True # truncated
    def getsize(self, filename: str) -> int:
        if filename is None: # pragma: no cover (is never null)
            return 0
        if not os.path.isfile(filename):
            return 0
        if self.truncate_old(filename):
            return 0
        try:
            return os.path.getsize(filename)
        except OSError as e:
            logg.warning("while reading file size: %s >> %s", filename, e)
            return 0
    #
    def command_of_unit(self, unit: str) -> Union[None, List[str]]:
        """ command [UNIT]. -- show service settings (experimental)
            or use -p VarName to show another property than 'ExecStart' """
        found: List[str]
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            self.error |= NOT_FOUND
            return None
        if self._only_property:
            found = []
            for prop in self._only_property:
                found += conf.getlist(Service, prop)
            return found
        return conf.getlist(Service, "ExecStart")
    def environment_of_unit(self, unit: str) -> Union[None, Dict[str, str]]:
        """ environment [UNIT]. -- show environment parts """
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            self.error |= NOT_FOUND
            return None
        return self.units.get_env(conf)
    def system_exec_env(self) -> List[str]:
        """ show-environment -- show init environment parts """
        return list(self.each_system_exec_env({}))
    def each_system_exec_env(self, env: Dict[str, str]) -> Iterator[str]:
        """ show init environment parts """
        values = self.extend_exec_env(env)
        for name in sorted(values):
            yield "%s=%s" %(name, values[name])
    def remove_service_directories(self, conf: SystemctlConf, section: str = Service) -> bool:
        ok = True
        want_runtime_folders = self.units.get_RuntimeDirectory(conf, section)
        keep_runtime_folders = self.units.get_RuntimeDirectoryPreserve(conf, section)
        if not keep_runtime_folders:
            root = conf.root_mode()
            for name in want_runtime_folders.split(" "):
                if not name.strip(): continue
                runtime_dir = get_RUNTIME_DIR(root)
                path = os.path.join(runtime_dir, name)
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
                if runtime_dir == "/run":
                    for var_run in ("/var/run", "/tmp/run"):
                        if os.path.isdir(var_run):
                            var_path = os.path.join(var_run, name)
                            var_dirpath = os_path(self._root, var_path)
                            self.do_rm_tree(var_dirpath)
        if not ok:
            logg.debug("could not fully remove service directory %s", path)
        return ok
    def do_rm_tree(self, path: str) -> bool:
        ok = True
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for item in filenames:
                    filepath = os.path.join(dirpath, item)
                    try:
                        os.remove(filepath)
                    except OSError as e: # pragma: no cover
                        logg.debug("not removed file: %s >> %s", filepath, e)
                        ok = False
                for item in dirnames:
                    dir_path = os.path.join(dirpath, item)
                    try:
                        os.rmdir(dir_path)
                    except OSError as e: # pragma: no cover
                        logg.debug("not removed dir: %s >> %s", dir_path, e)
                        ok = False
            try:
                os.rmdir(path)
            except OSError as e:
                logg.debug("not removed top dir: %s >> %s", path, e)
                ok = False # pragma: no cover
        logg.debug("%s rm_tree %s", ok and "done" or "fail", path)
        return ok
    def clean_service_directories(self, conf: SystemctlConf, which: str = NIX) -> bool:
        ok = True
        section = self.get_unit_section_from(conf)
        want_runtime_folders = self.units.get_RuntimeDirectory(conf, section)
        want_state_folders = self.units.get_StateDirectory(conf, section)
        want_cache_folders = self.units.get_CacheDirectory(conf, section)
        want_logs_folders = self.units.get_LogsDirectory(conf, section)
        want_config_folders = self.units.get_ConfigurationDirectory(conf, section)
        root = conf.root_mode()
        for name in want_runtime_folders.split(" "):
            if not name.strip(): continue
            runtime_dir = get_RUNTIME_DIR(root)
            path = os.path.join(runtime_dir, name)
            if which in ["all", "runtime", ""]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
                if runtime_dir == "/run":
                    for var_run in ("/var/run", "/tmp/run"):
                        var_path = os.path.join(var_run, name)
                        var_dirpath = os_path(self._root, var_path)
                        self.do_rm_tree(var_dirpath)
        for name in want_state_folders.split(" "):
            if not name.strip(): continue
            state_dir = get_VARLIB_HOME(root)
            path = os.path.join(state_dir, name)
            if which in ["all", "state"]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        for name in want_cache_folders.split(" "):
            if not name.strip(): continue
            cache_dir = get_CACHE_HOME(root)
            path = os.path.join(cache_dir, name)
            if which in ["all", "cache", ""]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        for name in want_logs_folders.split(" "):
            if not name.strip(): continue
            logs_dir = get_LOG_DIR(root)
            path = os.path.join(logs_dir, name)
            if which in ["all", "logs"]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        for name in want_config_folders.split(" "):
            if not name.strip(): continue
            config_dir = get_CONFIG_HOME(root)
            path = os.path.join(config_dir, name)
            if which in ["all", "configuration", ""]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        return ok
    def env_service_directories(self, conf: SystemctlConf) -> Dict[str, str]:
        envs = {}
        section = self.get_unit_section_from(conf)
        want_runtime_folders = self.units.get_RuntimeDirectory(conf, section)
        want_state_folders = self.units.get_StateDirectory(conf, section)
        want_cache_folders = self.units.get_CacheDirectory(conf, section)
        want_logs_folders = self.units.get_LogsDirectory(conf, section)
        want_config_folders = self.units.get_ConfigurationDirectory(conf, section)
        root = conf.root_mode()
        for name in want_runtime_folders.split(" "):
            if not name.strip(): continue
            runtime_dir = get_RUNTIME_DIR(root)
            path = os.path.join(runtime_dir, name)
            envs["RUNTIME_DIRECTORY"] = path
        for name in want_state_folders.split(" "):
            if not name.strip(): continue
            state_dir = get_VARLIB_HOME(root)
            path = os.path.join(state_dir, name)
            envs["STATE_DIRECTORY"] = path
        for name in want_cache_folders.split(" "):
            if not name.strip(): continue
            cache_dir = get_CACHE_HOME(root)
            path = os.path.join(cache_dir, name)
            envs["CACHE_DIRECTORY"] = path
        for name in want_logs_folders.split(" "):
            if not name.strip(): continue
            logs_dir = get_LOG_DIR(root)
            path = os.path.join(logs_dir, name)
            envs["LOGS_DIRECTORY"] = path
        for name in want_config_folders.split(" "):
            if not name.strip(): continue
            config_dir = get_CONFIG_HOME(root)
            path = os.path.join(config_dir, name)
            envs["CONFIGURATION_DIRECTORY"] = path
        return envs
    def create_service_directories(self, conf: SystemctlConf) -> Dict[str, str]:
        envs = {}
        section = self.get_unit_section_from(conf)
        want_runtime_folders = self.units.get_RuntimeDirectory(conf, section)  # pylint: disable=invalid-name
        mode_runtime_folders = self.units.get_RuntimeDirectoryMode(conf, section)  # pylint: disable=invalid-name
        want_state_folders = self.units.get_StateDirectory(conf, section)  # pylint: disable=invalid-name
        mode_state_folders = self.units.get_StateDirectoryMode(conf, section)  # pylint: disable=invalid-name
        want_cache_folders = self.units.get_CacheDirectory(conf, section)  # pylint: disable=invalid-name
        mode_cache_folders = self.units.get_CacheDirectoryMode(conf, section)  # pylint: disable=invalid-name
        want_logs_folders = self.units.get_LogsDirectory(conf, section)  # pylint: disable=invalid-name
        mode_logs_folders = self.units.get_LogsDirectoryMode(conf, section)  # pylint: disable=invalid-name
        want_config_folders = self.units.get_ConfigurationDirectory(conf, section)  # pylint: disable=invalid-name
        mode_config_folders = self.units.get_ConfigurationDirectoryMode(conf, section)  # pylint: disable=invalid-name
        root = conf.root_mode()
        user = self.units.get_User(conf)
        group = self.units.get_Group(conf)
        for name in want_runtime_folders.split(" "):
            if not name.strip(): continue
            runtime_dir = get_RUNTIME_DIR(root)
            path = os.path.join(runtime_dir, name)
            logg.debug("RuntimeDirectory %s", path)
            self.make_service_directory(path, mode_runtime_folders)
            self.chown_service_directory(path, user, group)
            envs["RUNTIME_DIRECTORY"] = path
            if runtime_dir == "/run":
                for var_run in ("/var/run", "/tmp/run"):
                    if os.path.isdir(var_run):
                        var_path = os.path.join(var_run, name)
                        var_dirpath = os_path(self._root, var_path)
                        if os.path.isdir(var_dirpath):
                            if not os.path.islink(var_dirpath):
                                logg.debug("not a symlink: %s", var_dirpath)
                            continue
                        dirpath = os_path(self._root, path)
                        basepath = os.path.dirname(var_dirpath)
                        if not os.path.isdir(basepath):
                            os.makedirs(basepath)
                        try:
                            os.symlink(dirpath, var_dirpath)
                        except OSError as e:
                            logg.debug("var symlink %s >> %s", var_dirpath, e)
        for name in want_state_folders.split(" "):
            if not name.strip(): continue
            state_dir = get_VARLIB_HOME(root)
            path = os.path.join(state_dir, name)
            logg.debug("StateDirectory %s", path)
            self.make_service_directory(path, mode_state_folders)
            self.chown_service_directory(path, user, group)
            envs["STATE_DIRECTORY"] = path
        for name in want_cache_folders.split(" "):
            if not name.strip(): continue
            cache_dir = get_CACHE_HOME(root)
            path = os.path.join(cache_dir, name)
            logg.debug("CacheDirectory %s", path)
            self.make_service_directory(path, mode_cache_folders)
            self.chown_service_directory(path, user, group)
            envs["CACHE_DIRECTORY"] = path
        for name in want_logs_folders.split(" "):
            if not name.strip(): continue
            logs_dir = get_LOG_DIR(root)
            path = os.path.join(logs_dir, name)
            logg.debug("LogsDirectory %s", path)
            self.make_service_directory(path, mode_logs_folders)
            self.chown_service_directory(path, user, group)
            envs["LOGS_DIRECTORY"] = path
        for name in want_config_folders.split(" "):
            if not name.strip(): continue
            config_dir = get_CONFIG_HOME(root)
            path = os.path.join(config_dir, name)
            logg.debug("ConfigurationDirectory %s", path)
            self.make_service_directory(path, mode_config_folders)
            # not done according the standard
            # self.chown_service_directory(path, user, group)
            envs["CONFIGURATION_DIRECTORY"] = path
        return envs
    def make_service_directory(self, path: str, mode: str) -> bool:
        ok = True
        dirpath = os_path(self._root, path)
        if not os.path.isdir(dirpath):
            try:
                os.makedirs(dirpath)
                logg.info("created directory path: %s", dirpath)
            except OSError as e: # pragma: no cover
                logg.debug("errors directory path: %s >> %s", dirpath, e)
                ok = False
            filemode = int_mode(mode)
            if filemode:
                try:
                    os.chmod(dirpath, filemode)
                except OSError as e: # pragma: no cover
                    logg.debug("errors directory path: %s >> %s", dirpath, e)
                    ok = False
        else:
            logg.debug("path did already exist: %s", dirpath)
        if not ok:
            logg.debug("could not fully create service directory %s", path)
        return ok
    def chown_service_directory(self, path: str, user: Optional[str], group: Optional[str]) -> bool:
        # the standard defines an optimization so that if the parent
        # directory does have the correct user and group then there
        # is no other chown on files and subdirectories to be done.
        dirpath = os_path(self._root, path)
        if not os.path.isdir(dirpath):
            logg.debug("chown did not find %s", dirpath)
            return True
        if user or group:
            st = os.stat(dirpath)
            st_user = pwd.getpwuid(st.st_uid).pw_name
            st_group = grp.getgrgid(st.st_gid).gr_name
            change = False
            if user and (user.strip() != st_user and user.strip() != str(st.st_uid)):
                change = True
            if group and (group.strip() != st_group and group.strip() != str(st.st_gid)):
                change = True
            if change:
                logg.debug("do chown %s", dirpath)
                try:
                    ok = self.do_chown_tree(dirpath, user, group)
                    logg.info("changed %s:%s %s", user, group, ok)
                    return ok
                except OSError as e:
                    logg.info("oops %s >> %s", dirpath, e)
            else:
                logg.debug("untouched %s", dirpath)
        return True
    def do_chown_tree(self, path: str, user: Optional[str], group: Optional[str]) -> bool:
        ok = True
        uid, gid = -1, -1
        if user:
            uid = pwd.getpwnam(user).pw_uid
            gid = pwd.getpwnam(user).pw_gid
        if group:
            gid = grp.getgrnam(group).gr_gid
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            for item in filenames:
                filepath = os.path.join(dirpath, item)
                try:
                    os.chown(filepath, uid, gid)
                except OSError as e: # pragma: no cover
                    logg.debug("could not set %s:%s on %s >> %s", user, group, filepath, e)
                    ok = False
            for item in dirnames:
                dir_path = os.path.join(dirpath, item)
                try:
                    os.chown(dir_path, uid, gid)
                except OSError as e: # pragma: no cover
                    logg.debug("could not set %s:%s on %s >> %s", user, group, dir_path, e)
                    ok = False
        try:
            os.chown(path, uid, gid)
        except OSError as e: # pragma: no cover
            logg.debug("could not set %s:%s on %s >> %s", user, group, path, e)
            ok = False
        if not ok:
            logg.debug("could not chown %s:%s service directory %s", user, group, path)
        return ok
    def clean_modules(self, *modules: str) -> bool:
        """ clean [UNIT]... -- remove the state directories
        /// it recognizes --what=all or any of configuration, state, cache, logs, runtime
            while an empty value (the default) removes cache and runtime directories"""
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        ok = self.clean_units(units)
        return ok and not missing
    def clean_units(self, units: List[str], what: str = NIX) -> bool:
        if not what:
            what = self._only_what[0]
        ok = True
        for unit in units:
            ok = self.clean_unit(unit, what) and ok
        return ok
    def clean_unit(self, unit: str, what: str = NIX) -> bool:
        conf = self.units.load_conf(unit)
        if not conf:
            return False
        return self.clean_unit_from(conf, what)
    def clean_unit_from(self, conf: SystemctlConf, what: str) -> bool:
        if self.is_active_from(conf):
            logg.warning("can not clean active unit: %s", conf.name())
            return False
        return self.clean_service_directories(conf, what)
    def log_modules(self, *modules: str) -> bool:
        """ logs [UNIT]... -- start 'less' on the log files for the services
        /// use '-f' to follow and '-n lines' to limit output using 'tail',
            using '--no-pager' just does a full 'cat'"""
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        lines = LOG_LINES
        follow = DO_FORCE
        result = self.log_units(units, lines, follow)
        if result:
            self.error = result
            return False
        return not missing
    def log_units(self, units: List[str], lines: Optional[int] = None, follow: bool = False) -> int:
        result = 0
        for unit in self.units.sorted_after(units):
            exitcode = self.log_unit(unit, lines, follow)
            if exitcode < 0:
                return exitcode
            if exitcode > result:
                result = exitcode
        return result
    def log_unit(self, unit: str, lines: Optional[int] = None, follow: bool = False) -> int:
        conf = self.units.load_conf(unit)
        if not conf:
            return -1
        return self.log_unit_from(conf, lines, follow)
    def log_unit_from(self, conf: SystemctlConf, lines: Optional[int] = None, follow: bool = False) -> int:
        cmd_args: List[Union[str, bytes]] = []
        log_path = self.journal_log(conf)
        if follow:
            tail_cmd = get_exist_path(TAIL_CMDS)
            if tail_cmd is None:
                print("tail command not found")
                return 1
            cmd = [tail_cmd, "-n", str(lines or 10), "-F", log_path]
            logg.debug("journalctl %s -> %s", conf.name(), cmd)
            cmd_args = [arg for arg in cmd] # satisfy mypy
            return os.execvp(cmd_args[0], cmd_args)
        elif lines:
            tail_cmd = get_exist_path(TAIL_CMDS)
            if tail_cmd is None:
                print("tail command not found")
                return 1
            cmd = [tail_cmd, "-n", str(lines or 10), log_path]
            logg.debug("journalctl %s -> %s", conf.name(), cmd)
            cmd_args = [arg for arg in cmd] # satisfy mypy
            return os.execvp(cmd_args[0], cmd_args)
        elif NO_PAGER:
            cat_cmd = get_exist_path(CAT_CMDS)
            if cat_cmd is None:
                print("cat command not found")
                return 1
            cmd = [cat_cmd, log_path]
            logg.debug("journalctl %s -> %s", conf.name(), cmd)
            cmd_args = [arg for arg in cmd] # satisfy mypy
            return os.execvp(cmd_args[0], cmd_args)
        else:
            less_cmd = get_exist_path(LESS_CMDS)
            if less_cmd is None:
                print("less command not found")
                return 1
            cmd = [less_cmd, log_path]
            logg.debug("journalctl %s -> %s", conf.name(), cmd)
            cmd_args = [arg for arg in cmd] # satisfy mypy
            return os.execvp(cmd_args[0], cmd_args)
    def journal_log(self, conf: SystemctlConf) -> str:
        return os_path(self._root, self.get_journal_log(conf))
    def get_journal_log(self, conf: SystemctlConf) -> str:
        """ /var/log/zzz.service.log or /var/log/default.unit.log """
        filename = os.path.basename(nix_str(conf.filename()))
        unitname = (conf.name() or "default")+".unit"
        name = filename or unitname
        log_folder = expand_path(self._journal_log_folder, conf.root_mode())
        log_file = name.replace(os.path.sep, ".") + ".log"
        if log_file.startswith("."):
            log_file = "dot."+log_file
        return os.path.join(log_folder, log_file)
    def open_journal_log(self, conf: SystemctlConf) -> TextIO:
        log_file = self.journal_log(conf)
        log_folder = os.path.dirname(log_file)
        if not os.path.isdir(log_folder):
            os.makedirs(log_folder)
        return open(os.path.join(log_file), "a")
    def chdir_workingdir(self, conf: SystemctlConf) -> Union[str, bool, None]:
        """ if specified then change the working directory """
        # the original systemd will start in '/' even if User= is given
        if self._root:
            os.chdir(self._root)
        workingdir = self.units.get_WorkingDirectory(conf)
        mode, workingdir = load_path(workingdir)
        if workingdir:
            into = os_path(self._root, self.units.expand_special(workingdir, conf))
            try:
                logg.debug("chdir workingdir '%s'", into)
                os.chdir(into)
                return False
            except OSError as e:
                if mode.check:
                    logg.error("chdir workingdir '%s' >> %s", into, e)
                    return into
                else:
                    logg.debug("chdir workingdir '%s' >> %s", into, e)
                    return None
        return None
    class NotifySocket(NamedTuple):
        socket: socket.socket
        socketfile: str
    def get_notify_socket_from(self, conf: SystemctlConf, socketfile: Optional[str] = None, debug: bool = False) -> str:
        """ creates a notify-socket for the (non-privileged) user """
        notify_socket_folder = expand_path(NOTIFY_SOCKET_FOLDER, conf.root_mode())
        notify_folder = os_path(self._root, notify_socket_folder)
        notify_name = "notify." + str(conf.name() or "systemctl")
        notify_socket = os.path.join(notify_folder, notify_name)
        socketfile = socketfile or notify_socket
        if len(socketfile) > 100:
            # occurs during testsuite.py for ~user/test.tmp/root path
            if debug:
                logg.debug("https://unix.stackexchange.com/questions/367008/%s",
                           "why-is-socket-path-length-limited-to-a-hundred-chars")
                logg.debug("old notify socketfile (%s) = %s", len(socketfile), socketfile)
            notify_name44 = o44(notify_name)
            notify_name77 = o77(notify_name)
            socketfile = os.path.join(notify_folder, notify_name77)
            if len(socketfile) > 100:
                socketfile = os.path.join(notify_folder, notify_name44)
            pref = "zz.%i.%s" % (get_USER_ID(), o30(os.path.basename(notify_socket_folder)))
            if len(socketfile) > 100:
                socketfile = os.path.join(get_TMP(), pref, notify_name)
            if len(socketfile) > 100:
                socketfile = os.path.join(get_TMP(), pref, notify_name77)
            if len(socketfile) > 100: # pragma: no cover
                socketfile = os.path.join(get_TMP(), pref, notify_name44)
            if len(socketfile) > 100: # pragma: no cover
                socketfile = os.path.join(get_TMP(), notify_name44)
            if debug:
                logg.info("new notify socketfile (%s) = %s", len(socketfile), socketfile)
        return socketfile
    def notify_socket_from(self, conf: SystemctlConf, socketfile: Optional[str] = None) -> NotifySocket:
        socketfile = self.get_notify_socket_from(conf, socketfile, debug=True)
        try:
            if not os.path.isdir(os.path.dirname(socketfile)):
                os.makedirs(os.path.dirname(socketfile))
            if os.path.exists(socketfile):
                os.unlink(socketfile)
        except OSError as e:
            logg.warning("error %s >> %s", socketfile, e)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(socketfile)
        os.chmod(socketfile, 0o777) # the service my run under some User=setting
        return Systemctl.NotifySocket(sock, socketfile)
    def read_notify_socket(self, notify: NotifySocket, timeout: float) -> str:
        notify.socket.settimeout(timeout or MAXTIMEOUT)
        result = ""
        try:
            _result, _addr = notify.socket.recvfrom(4096)
            assert isinstance(_result, bytes)
            if _result:
                result = _result.decode("utf-8")
                result_txt = result.replace("\n", "|")
                result_len = len(result)
                logg.debug("read_notify_socket(%s):%s", result_len, result_txt)
        except socket.timeout as e:
            if timeout > 2:
                logg.debug("socket.timeout >> %s", e)
        return result
    def wait_notify_socket(self, notify: NotifySocket, timeout: float, pid: Optional[int] = None, pid_file: Optional[str] = None) -> Dict[str, str]:
        if not os.path.exists(notify.socketfile):
            logg.info("no $NOTIFY_SOCKET exists")
            return {}
        #
        notify_timeout = max(NOTIFY_TIMEOUT, int(timeout / NOTIFY_QUICKER))  # timeout is usually set to TimeoutStart
        wait_mainpid = notify_timeout # Apache sends READY before MAINPID
        status = ""
        logg.info("wait $NOTIFY_SOCKET, timeout %s (waiting %s)", timeout, notify_timeout)
        waiting = " ---"
        results: Dict[str, str] = {}
        for attempt in range(int(timeout)+1):
            if pid and not self.is_active_pid(pid):
                logg.info("seen dead PID %s", pid)
                return results
            if not attempt: # first one
                time.sleep(1) # until TimeoutStartSec
                continue
            result = self.read_notify_socket(notify, 1) # sleep max 1 second
            for line in result.splitlines():
                # for name, value in self.read_env_part(line)
                if "=" not in line:
                    continue
                name, value = line.split("=", 1)
                results[name] = value
                if name in ["STATUS", "ACTIVESTATE", "MAINPID", "READY"]:
                    hint="seen notify %s     " % (waiting)
                    logg.debug("%s :%s=%s", hint, name, value)
            if status != results.get("STATUS", ""):
                wait_mainpid = notify_timeout
                status = results.get("STATUS", "")
            if "READY" not in results:
                time.sleep(1) # until TimeoutStart/NOTIFY_QUICKER
                continue
            if "MAINPID" not in results and not pid_file:
                wait_mainpid -= 1
                if wait_mainpid > 0:
                    waiting = "%4i" % (-wait_mainpid)
                    time.sleep(1) # until TimeoutStart/NOTIFY_QUICKER
                    continue
            break # READY and MAINPID
        if "READY" not in results:
            logg.info(".... timeout while waiting for 'READY=1' status on $NOTIFY_SOCKET")
        elif "MAINPID" not in results:
            logg.info(".... seen 'READY=1' but no MAINPID update status on $NOTIFY_SOCKET")
        logg.debug("notify = %s", results)
        try:
            notify.socket.close()
        except OSError as e:
            logg.debug("socket.close >> %s", e)
        return results
    def start_modules(self, *modules: str) -> bool:
        """ start [UNIT]... -- start these units
        /// SPECIAL: with --init it will run the init-loop and stop the units afterwards,
            and when not units are given then the init-loop is simply run forever (aka 'init' proc).
        /// --now is like --exit when no services left
        /// --all is like --exit --exit when no procs left """
        init = self.init_mode
        if self._do_now and not init:
            logg.warning("no --init mode")
        if init and not self.exit_mode:
            if self._do_now:
                self.exit_mode |= EXIT_NO_SERVICES_LEFT
            if self._show_all:
                self.exit_mode |= EXIT_NO_PROCS_LEFT
        if not modules and init:
            target = "start"
            if self.exit_mode:
                # a plain init loop would return as nothing is running
                logg.info(" [%s] default system", target)
                return self.default_system()
            else:
                reached = "stop"
                if self.exit_mode & EXIT_NO_PROCS_LEFT:
                    reached = "no procs left!"
                if self.exit_mode & EXIT_NO_SERVICES_LEFT:
                    reached = "no services left!"
                logg.info(" [%s] init loop until %s", target, reached)
                result = self.init_loop_until_stop([])
                return not not result  # pylint: disable=unnecessary-negation
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.start_units(units, init) and not missing
    def start_units(self, units: List[str], init: int = 0) -> bool:
        """ fails if any unit does not start
        /// SPECIAL: may run the init-loop and
            stop the named units afterwards """
        self.wait_system()
        if init:
            target = "systemctl-start.target"
            reached = "stop"
            if self.exit_mode & EXIT_NO_PROCS_LEFT:
                reached = "no procs left"
            if self.exit_mode & EXIT_NO_SERVICES_LEFT:
                reached = "no services left"
            logg.info(" [%s] init loop until %s", target, reached)
            self._default_services[target] = units
            stopped = self.start_target_system(target, init = init)
            logg.info(" [%s] stopped %s", target, stopped)
            return True
        done = True
        started_units = []
        for unit in self.units.sorted_after(units):
            started_units.append(unit)
            if not self.start_unit(unit):
                done = False
        return done
    def start_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.debug("unit could not be loaded (%s)", unit)
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.start_unit_from(conf)
    def start_unit_from(self, conf: SystemctlConf) -> bool:
        if not conf:
            return False
        if self.units.syntax_check(conf, conditions=False) > 100:
            return False
        with waitlock(conf):
            logg.debug(" start unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_start_unit_from(conf)
    def do_start_unit_from(self, conf: SystemctlConf) -> bool:
        blocked = self.units.check_env_conditions(conf, warning=logging.ERROR)
        if blocked:
            logg.error("%s: %s system conditions have failed: can not start", conf.name(), len(blocked))
            asserts = [cond for cond in blocked if cond.startswith("Assert")]
            if asserts:
                logg.error("Assertion failed on job for %s", conf.name())
                return False
            else: # original systemctl silently skips the unit without having them started
                logg.info("%s was skipped due to an unmet condition (%s)", conf.name(), " and ".join(blocked))
                return OK_CONDITION_FAILURE
        impossible = self.units.check_system_conditions(conf, warning=logging.ERROR)
        if impossible:
            logg.error("%s: %s system conditions have failed: can not start", conf.name(), len(impossible))
            asserts = [cond for cond in impossible if cond.startswith("Assert")]
            if asserts:
                logg.error("Assertion failed on job for %s", conf.name())
                return False
            else: # original systemctl silently skips the unit without having them started
                logg.info("%s was skipped due to an unmet condition (%s)", conf.name(), " and ".join(impossible))
                return OK_CONDITION_FAILURE
        missing = self.units.check_file_conditions(conf, warning=logging.ERROR)
        if missing:
            logg.error("%s: %s file conditions have failed: can not start", conf.name(), len(missing))
            asserts = [cond for cond in missing if cond.startswith("Assert")]
            if asserts:
                logg.error("Assertion failed on job for %s", conf.name())
                return False
            else: # original systemctl silently skips the unit without having them started
                logg.info("%s was skipped due to an unmet condition (%s)", conf.name(), " and ".join(missing))
                return OK_CONDITION_FAILURE
        if conf.name().endswith(".service"):
            return self.do_start_service_from(conf)
        elif conf.name().endswith(".socket"):
            return self.do_start_socket_from(conf)
        elif conf.name().endswith(".target"):
            return self.do_start_target_from(conf)
        else:
            logg.error("start not implemented for unit type: %s", conf.name())
            return False
    def do_start_service_from(self, conf: SystemctlConf) -> bool:
        timeout = self.units.get_TimeoutStartSec(conf)
        doRemainAfterExit = self.units.get_RemainAfterExit(conf)  # pylint: disable=invalid-name
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.units.get_env(conf)
        if not self._quiet:
            okee = self.units.exec_check(conf, env, Service, "Exec") # all...
            if not okee and NO_RELOAD:
                return False
        service_directories = self.create_service_directories(conf)
        env.update(service_directories) # atleast sshd did check for /run/sshd
        # for StopPost on failure:
        returncode = 0
        service_result = "success"
        if TRUE:
            if runs in ["simple", "exec", "forking", "notify", "idle"]:
                env["MAINPID"] = nix_str(self.read_mainpid_from(conf))
            for cmd in conf.getlist(Service, "ExecStartPre", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info(" pre-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug(" pre-start done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
                if run.returncode and exe.check:
                    logg.error("the ExecStartPre control process exited with error code")
                    active = "failed"
                    self.write_status_from(conf, AS=active)
                    if self._only_what[0] not in ["none", "keep"]:
                        self.remove_service_directories(conf) # cleanup that /run/sshd
                    return False
        if runs in ["oneshot"]:
            if self.get_status_from(conf, "ActiveState", "unknown") == "active":
                logg.warning("the service was already up once")
                return True
            for cmd in conf.getlist(Service, "ExecStart", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    logg.error("%s start %s (%s) <-%s>", runs, service_result,
                               run.returncode or "OK", run.signal or "")
                    break
                logg.info("%s start done (%s) <-%s>", runs,
                          run.returncode or "OK", run.signal or "")
            if TRUE:
                self.set_status_from(conf, "ExecMainCode", nix_str(returncode))
                active = returncode and "failed" or "active"
                self.write_status_from(conf, AS=active)
        elif runs in ["simple", "exec", "idle"]:
            pid = self.read_mainpid_from(conf)
            if self.is_active_pid(pid):
                logg.warning("the service is already running on PID %s", pid)
                return True
            if doRemainAfterExit:
                logg.debug("%s RemainAfterExit -> AS=active", runs)
                self.write_status_from(conf, AS="active")
            cmdlist = conf.getlist(Service, "ExecStart", [])
            for idx, cmd in enumerate(cmdlist):
                logg.debug("ExecStart[%s]: %s", idx, cmd)
            for cmd in cmdlist:
                pid = self.read_mainpid_from(conf)
                env["MAINPID"] = nix_str(pid)
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                self.write_status_from(conf, MainPID=forkpid)
                logg.info("%s started PID %s", runs, forkpid)
                env["MAINPID"] = nix_str(forkpid)
                time.sleep(YIELD)
                run = subprocess_testpid(forkpid)
                if run.returncode is not None:
                    logg.info("%s stopped PID %s (%s) <-%s>", runs, run.pid,
                              run.returncode or "OK", run.signal or "")
                    if doRemainAfterExit:
                        self.set_status_from(conf, "ExecMainCode", nix_str(run.returncode))
                        active = run.returncode and "failed" or "active"
                        self.write_status_from(conf, AS=active)
                    if run.returncode and exe.check:
                        service_result = "failed"
                        break
        elif runs in ["notify"]:
            # "notify" is the same as "simple" but we create a $NOTIFY_SOCKET
            # and wait for startup completion by checking the socket messages
            pid_file = self.pid_file(conf)
            pid = self.read_mainpid_from(conf)
            if self.is_active_pid(pid):
                logg.error("the service is already running on PID %s", pid)
                return False
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                logg.debug("use NOTIFY_SOCKET=%s", notify.socketfile)
            if doRemainAfterExit:
                logg.debug("%s RemainAfterExit -> AS=active", runs)
                self.write_status_from(conf, AS="active")
            cmdlist = conf.getlist(Service, "ExecStart", [])
            for idx, cmd in enumerate(cmdlist):
                logg.debug("ExecStart[%s]: %s", idx, cmd)
            mainpid = None
            for cmd in cmdlist:
                mainpid = self.read_mainpid_from(conf)
                env["MAINPID"] = nix_str(mainpid)
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                # via NOTIFY # self.write_status_from(conf, MainPID=forkpid)
                logg.info("%s started PID %s", runs, forkpid)
                mainpid = forkpid
                self.write_status_from(conf, MainPID=mainpid)
                env["MAINPID"] = nix_str(mainpid)
                time.sleep(YIELD)
                run = subprocess_testpid(forkpid)
                if run.returncode is not None:
                    logg.info("%s stopped PID %s (%s) <-%s>", runs, run.pid,
                              run.returncode or "OK", run.signal or "")
                    if doRemainAfterExit:
                        self.set_status_from(conf, "ExecMainCode", nix_str(run.returncode))
                        active = run.returncode and "failed" or "active"
                        self.write_status_from(conf, AS=active)
                    if run.returncode and exe.check:
                        service_result = "failed"
                        break
            if service_result in ["success"] and mainpid:
                logg.debug("okay, waiting on socket for %ss", timeout)
                results = self.wait_notify_socket(notify, timeout, mainpid, pid_file)
                if "MAINPID" in results:
                    new_pid = to_int_if(results["MAINPID"])
                    if new_pid and new_pid != mainpid:
                        logg.info("NEW PID %s from sd_notify (was PID %s)", new_pid, mainpid)
                        self.write_status_from(conf, MainPID=new_pid)
                        mainpid = new_pid
                logg.info("%s start done %s", runs, mainpid)
                pid = self.read_mainpid_from(conf)
                if pid:
                    env["MAINPID"] = nix_str(pid)
                else:
                    service_result = "timeout" # "could not start service"
        elif runs in ["forking"]:
            pid_file = self.pid_file(conf)
            for cmd in conf.getlist(Service, "ExecStart", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                if not newcmd: continue
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                logg.info("%s started PID %s", runs, forkpid)
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                logg.info("%s stopped PID %s (%s) <-%s>", runs, run.pid,
                          run.returncode or "OK", run.signal or "")
            if pid_file and service_result in ["success"]:
                pid = self.wait_pid_file(pid_file) # application PIDFile
                logg.info("%s start done PID %s [%s]", runs, pid, pid_file)
                if pid:
                    env["MAINPID"] = nix_str(pid)
            if not pid_file:
                time.sleep(MinimumTimeoutStartSec)
                logg.warning("No PIDFile for forking %s", q_str(conf.filename()))
                self.set_status_from(conf, "ExecMainCode", nix_str(returncode))
                active = returncode and "failed" or "active"
                self.write_status_from(conf, AS=active)
        else:
            logg.error("unsupported run type '%s'", runs)
            return False
        # POST sequence
        if not self.is_active_from(conf):
            logg.warning("%s start not active", runs)
            # according to the systemd documentation, a failed start-sequence
            # should execute the ExecStopPost sequence allowing some cleanup.
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Service, "ExecStopPost", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("post-fail %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-fail done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
            if self._only_what[0] not in ["none", "keep"]:
                self.remove_service_directories(conf)
            return False
        else:
            for cmd in conf.getlist(Service, "ExecStartPost", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("post-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-start done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
            return True
    def listen_modules(self, *modules: str) -> bool:
        """ listen [UNIT]... -- listen socket units"""
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.listen_units(units) and not missing
    def listen_units(self, units: List[str]) -> bool:
        """ fails if any socket does not start """
        self.wait_system()
        done = True
        started_units = []
        active_units = []
        for unit in self.units.sorted_after(units):
            started_units.append(unit)
            if not self.listen_unit(unit):
                done = False
            else:
                active_units.append(unit)
        if active_units:
            logg.info("init-loop start")
            sig = self.init_loop_until_stop(started_units)
            logg.info("init-loop %s", sig)
        for unit in reversed(started_units):
            pass # self.stop_unit(unit)
        return done
    def listen_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.debug("unit could not be loaded (%s)", unit)
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.listen_unit_from(conf)
    def listen_unit_from(self, conf: SystemctlConf) -> bool:
        if not conf:
            return False
        with waitlock(conf):
            logg.debug(" listen unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_listen_unit_from(conf)
    def do_listen_unit_from(self, conf: SystemctlConf) -> bool:
        if conf.name().endswith(".socket"):
            return self.do_start_socket_from(conf)
        else:
            logg.error("listen not implemented for unit type: %s", conf.name())
            return False
    def do_accept_socket_from(self, conf: SystemctlConf, sock: socket.socket) -> bool:
        logg.debug("%s: accepting %s", conf.name(), sock.fileno())
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.units.load_conf(service_unit)
        if service_conf is None or TESTING_ACCEPT:  # pragma: no cover
            if sock.type == socket.SOCK_STREAM:
                conn, _addr = sock.accept()
                data = conn.recv(1024)
                logg.debug("%s: '%s'", conf.name(), data)
                conn.send(b"ERROR: "+data.upper())
                conn.close()
                return False
            if sock.type == socket.SOCK_DGRAM:
                data, sender = sock.recvfrom(1024)
                logg.debug("%s: '%s'", conf.name(), data)
                sock.sendto(b"ERROR: "+data.upper(), sender)
                return False
            logg.error("can not accept socket type %s", sock_type_str(sock.type))
            return False
        return self.do_start_service_from(service_conf)
    def get_socket_service_from(self, conf: SystemctlConf) -> str:
        socket_unit = conf.name()
        accept = conf.getbool(Socket, "Accept", "no")
        service_type = accept and "@.service" or ".service"
        service_name = path_replace_extension(socket_unit, ".socket", service_type)
        service_unit = conf.get(Socket, Service, service_name)
        logg.debug("socket %s -> service %s", socket_unit, service_unit)
        return service_unit
    def do_start_socket_from(self, conf: SystemctlConf) -> bool:
        runs = "socket"
        # timeout = self.get_SocketTimeoutSec(conf)
        # stream = conf.get(Socket, "ListenStream", "")
        accept = conf.getbool(Socket, "Accept", "no")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.units.load_conf(service_unit)
        if service_conf is None:
            logg.debug("unit could not be loaded (%s)", service_unit)
            logg.error("Unit %s not found.", service_unit)
            return False
        env = self.units.get_env(conf)
        if not self._quiet:
            okee = self.units.exec_check(conf, env, Socket, "Exec") # all...
            if not okee and NO_RELOAD:
                return False
        if TRUE:
            for cmd in conf.getlist(Socket, "ExecStartPre", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s pre-start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("%s pre-start done (%s) <-%s>", runs,
                           run.returncode or "OK", run.signal or "")
                if run.returncode and exe.check:
                    logg.error("the ExecStartPre control process exited with error code")
                    active = "failed"
                    self.write_status_from(conf, AS=active)
                    return False
        # service_directories = self.create_service_directories(conf)
        # env.update(service_directories)
        listening=False
        if not accept:
            sock = self.create_socket(conf)
            if sock and TESTING_LISTEN:
                listening=True
                self._sockets[conf.name()] = SystemctlSocket(conf, sock)
                service_result = "success"
                state = sock and "active" or "failed"
                self.write_status_from(conf, AS=state)
        if not listening:
            # we do not listen but have the service started right away
            done = self.do_start_service_from(service_conf)
            service_result = done and "success" or "failed"
            if not self.is_active_from(service_conf):
                service_result = "failed"
            state = service_result
            if service_result in ["success"]:
                state = "active"
            self.write_status_from(conf, AS=state)
        # POST sequence
        if service_result in ["failed"]:
            # according to the systemd documentation, a failed start-sequence
            # should execute the ExecStopPost sequence allowing some cleanup.
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Socket, "ExecStopPost", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s post-fail %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("%s post-fail done (%s) <-%s>", runs,
                           run.returncode or "OK", run.signal or "")
            return False
        else:
            for cmd in conf.getlist(Socket, "ExecStartPost", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s post-start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("%s post-start done (%s) <-%s>", runs,
                           run.returncode or "OK", run.signal or "")
            return True
    def socketlist(self) -> List[SystemctlSocket]:
        return list(self._sockets.values())
    def create_socket(self, conf: SystemctlConf) -> Optional[socket.socket]:
        unsupported = ["ListenUSBFunction", "ListenMessageQueue", "ListenNetlink"]
        unsupported += ["ListenSpecial", "ListenFIFO", "ListenSequentialPacket"]
        for item in unsupported:
            if conf.get(Socket, item, ""):
                logg.warning("%s: %s sockets are not implemented", conf.name(), item)
                self.error |= NOT_OK
                return None
        data_stream = conf.get(Socket, "ListenDatagram", "")
        sock_stream = conf.get(Socket, "ListenStream", "")
        addr_stream = sock_stream or data_stream
        m = re.match(r"(/.*)", addr_stream)
        if m:
            path = m.group(1)
            sock = self.create_unix_socket(conf, path, not sock_stream)
            self.set_status_from(conf, "path", path)
            return sock
        m = re.match(r"(\d+[.]\d*[.]\d*[.]\d+):(\d+)", addr_stream)
        if m:
            addr, port = m.group(1), m.group(2)
            sock = self.create_port_ipv4_socket(conf, addr, port, not sock_stream)
            self.set_status_from(conf, "port", port)
            self.set_status_from(conf, "addr", addr)
            return sock
        m = re.match(r"\[([0-9a-fA-F:]*)\]:(\d+)", addr_stream)
        if m:
            addr, port = m.group(1), m.group(2)
            sock = self.create_port_ipv6_socket(conf, addr, port, not sock_stream)
            self.set_status_from(conf, "port", port)
            self.set_status_from(conf, "addr", addr)
            return sock
        m = re.match(r"(\d+)$", addr_stream)
        if m:
            port = m.group(1)
            sock = self.create_port_socket(conf, port, not sock_stream)
            self.set_status_from(conf, "port", port)
            return sock
        if re.match("@.*", addr_stream):
            logg.warning("%s: abstract namespace socket not implemented (%s)", conf.name(), addr_stream)
            return None
        if re.match("vsock:.*", addr_stream):
            logg.warning("%s: virtual machine socket not implemented (%s)", conf.name(), addr_stream)
            return None
        logg.error("%s: unknown socket address type (%s)", conf.name(), addr_stream)
        return None
    def create_unix_socket(self, conf: SystemctlConf, path: str, dgram: bool) -> Optional[socket.socket]:
        sock_stream = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_UNIX, sock_stream)
        try:
            dirmode = conf.get(Socket, "DirectoryMode", "0755")
            mode = conf.get(Socket, "SocketMode", "0666")
            user = conf.get(Socket, "SocketUser", "")
            group = conf.get(Socket, "SocketGroup", "")
            symlinks = conf.getlist(Socket, "SymLinks", [])
            dirpath = os.path.dirname(path)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath, int(dirmode, 8))
            if os.path.exists(path):
                os.unlink(path)
            sock.bind(path)
            os.fchmod(sock.fileno(), int(mode, 8))
            shutil_fchown(sock.fileno(), user, group)
            if symlinks:
                logg.warning("%s: symlinks for socket not implemented (%s)", conf.name(), path)
        except OSError as e:
            logg.error("%s: create socket failed [%s] >> %s", conf.name(), path, e)
            sock.close()
            return None
        return sock
    def create_port_socket(self, conf: SystemctlConf, port: str, dgram: bool) -> Optional[socket.socket]:
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET, inet)
        try:
            sock.bind(('', int(port)))
            logg.info("%s: bound socket at %s %s:%s", conf.name(), sock_type_str(inet), ALL, port)
        except OSError as e:
            logg.error("%s: create socket failed (%s:%s) >> %s", conf.name(), ALL, port, e)
            sock.close()
            return None
        return sock
    def create_port_ipv4_socket(self, conf: SystemctlConf, addr: str, port: str, dgram: bool) -> Optional[socket.socket]:
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET, inet)
        try:
            sock.bind((addr, int(port)))
            logg.info("%s: bound socket at %s %s:%s", conf.name(), sock_type_str(inet), addr, port)
        except OSError as e:
            logg.error("%s: create socket failed (%s:%s) >> %s", conf.name(), addr, port, e)
            sock.close()
            return None
        return sock
    def create_port_ipv6_socket(self, conf: SystemctlConf, addr: str, port: str, dgram: bool) -> Optional[socket.socket]:
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET6, inet)
        try:
            sock.bind((addr, int(port)))
            logg.info("%s: bound socket at %s [%s]:%s", conf.name(), sock_type_str(inet), addr, port)
        except OSError as e:
            logg.error("%s: create socket failed ([%s]:%s) >> %s", conf.name(), addr, port, e)
            sock.close()
            return None
        return sock
    def extend_exec_env(self, env: Dict[str, str]) -> Dict[str, str]:
        env = env.copy()
        # implant DEFAULT_PATH into $PATH
        path = env.get("PATH", DEFAULT_PATH)
        parts = path.split(os.pathsep)
        for part in DEFAULT_PATH.split(os.pathsep):
            if part and part not in parts:
                parts.append(part)
        env["PATH"] = str(os.pathsep).join(parts)
        # reset locale to system default
        for name in RESET_LOCALE.split():
            if name in env:
                del env[name]
        locale = {}
        localepath = env.get("LOCALE_CONF", LOCALE_CONF)
        localeparts = localepath.split(os.pathsep)
        for filename in localeparts:
            if os.path.isfile(filename):
                for var, val in read_env_file(filename, self._root):
                    locale[var] = val
                    env[var] = val
        if "LANG" not in locale:
            env["LANG"] = locale.get("LANGUAGE", locale.get("LC_CTYPE", "C"))
        return env
    def skip_journal_log(self, conf: SystemctlConf) -> bool:
        if self.get_unit_type(conf.name()) not in ["service"]:
            return True
        std_out = conf.get(Service, "StandardOutput", STANDARD_OUTPUT)
        std_err = conf.get(Service, "StandardError", STANDARD_ERROR)
        out, err = False, False
        if std_out in ["null"]: out = True
        if std_out.startswith("file:"): out = True
        if std_err in ["inherit"]: std_err = std_out
        if std_err in ["null"]: err = True
        if std_err.startswith("file:"): err = True
        if std_err.startswith("append:"): err = True
        return out and err
    def dup2_journal_log(self, conf: SystemctlConf) -> None:
        out: Optional[TextIO]
        msg = ""
        std_inp = conf.get(Service, "StandardInput", STANDARD_INPUT)
        std_out = conf.get(Service, "StandardOutput", STANDARD_OUTPUT)
        std_err = conf.get(Service, "StandardError", STANDARD_ERROR)
        inp, out, err = None, None, None
        if std_inp in ["null"]:
            inp = open(_dev_null, "r")
        elif std_inp.startswith("file:"):
            fname = std_inp[len("file:"):]
            if os.path.exists(fname):
                inp = open(fname, "r")
            else:
                inp = open(_dev_zero, "r")
        else:
            inp = open(_dev_zero, "r")
        assert inp is not None
        try:
            if std_out in ["null"]:
                out = open(_dev_null, "w")
            elif std_out.startswith("file:"):
                fname = std_out[len("file:"):]
                fdir = os.path.dirname(fname)
                if not os.path.exists(fdir):
                    os.makedirs(fdir)
                out = open(fname, "w")
            elif std_out.startswith("append:"):
                fname = std_out[len("append:"):]
                fdir = os.path.dirname(fname)
                if not os.path.exists(fdir):
                    os.makedirs(fdir)
                out = open(fname, "a")
        except (OSError, IOError) as e:
            msg += "\n%s >> %s" % (fname, e)
        except Exception as e: # pylint: disable=broad-exception-caught
            msg += "\n%s >> %s >> %s" % (fname, type(e), e)
        if out is None:
            out = self.open_journal_log(conf)
            err = out
        assert out is not None
        try:
            if std_err in ["inherit"]:
                err = out
            elif std_err in ["null"]:
                err = open(_dev_null, "w")
            elif std_err.startswith("file:"):
                fname = std_err[len("file:"):]
                fdir = os.path.dirname(fname)
                if not os.path.exists(fdir):
                    os.makedirs(fdir)
                err = open(fname, "w")
            elif std_err.startswith("append:"):
                fname = std_err[len("append:"):]
                fdir = os.path.dirname(fname)
                if not os.path.exists(fdir):
                    os.makedirs(fdir)
                err = open(fname, "a")
        except (OSError, IOError) as e:
            msg += "\n%s >> %s" % (fname, e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            msg += "\n%s >> %s >> %s" % (fname, type(e), e)
        if err is None:
            err = self.open_journal_log(conf)
        assert err is not None
        if msg:
            err.write("ERROR:")
            err.write(msg.strip())
            err.write("\n")
        if EXEC_DUP2:
            os.dup2(inp.fileno(), sys.stdin.fileno())
            os.dup2(out.fileno(), sys.stdout.fileno())
            os.dup2(err.fileno(), sys.stderr.fileno())
    def execve_from(self, conf: SystemctlConf, cmd: List[str], env: Dict[str, str]) -> NoReturn:
        """ this code is commonly run in a child process // returns exit-code"""
        # runs = conf.get(Service, "Type", "simple").lower()
        # logg.debug("%s process for %s => %s", runs, nix_str(conf.name()), q_str(conf.filename()))
        self.dup2_journal_log(conf)
        cmd_args: List[Union[str, bytes]] = []
        #
        runuser = self.units.get_User(conf)
        rungroup = self.units.get_Group(conf)
        xgroups = self.units.get_SupplementaryGroups(conf)
        envs = shutil_setuid(runuser, rungroup, xgroups)
        badpath = self.chdir_workingdir(conf) # some dirs need setuid before
        if badpath:
            logg.error("(%s): bad workingdir: '%s'", shell_cmd(cmd), badpath)
            sys.exit(1)
        env = self.extend_exec_env(env)
        env.update(envs) # set $HOME to ~$USER
        try:
            if EXEC_SPAWN:
                cmd_args = [arg for arg in cmd] # satisfy mypy
                exitcode = os.spawnvpe(os.P_WAIT, cmd[0], cmd_args, env)
                sys.exit(exitcode)
            else: # pragma: no cover
                os.execve(cmd[0], cmd, env)
                sys.exit(11) # pragma: no cover (can not be reached / bug like mypy#8401)
        except (OSError, RuntimeError) as e:
            logg.error("(%s) >> %s", shell_cmd(cmd), e)
            sys.exit(1)
    def test_start_unit(self, unit: str) -> None:
        """ helper function to test the code that is normally forked off """
        conf = self.units.load_conf(unit)
        if not conf:
            return None
        env = self.units.get_env(conf)
        for cmd in conf.getlist(Service, "ExecStart", []):
            _xe, newcmd = self.units.expand_cmd(cmd, env, conf)
            self.execve_from(conf, newcmd, env)
        return None
    def stop_modules(self, *modules: str) -> bool:
        """ stop [UNIT]... -- stop these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.stop_units(units) and not missing
    def stop_units(self, units: List[str]) -> bool:
        """ fails if any unit fails to stop """
        self.wait_system()
        done = True
        for unit in reversed(self.units.sorted_after(units)):
            if not self.stop_unit(unit):
                done = False
        return done
    def stop_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.stop_unit_from(conf)

    def stop_unit_from(self, conf: SystemctlConf) -> bool:
        if not conf:
            return False
        if self.units.syntax_check(conf) > 100:
            return False
        with waitlock(conf):
            logg.info(" stop unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_stop_unit_from(conf)
    def do_stop_unit_from(self, conf: SystemctlConf) -> bool:
        if conf.name().endswith(".service"):
            return self.do_stop_service_from(conf)
        elif conf.name().endswith(".socket"):
            return self.do_stop_socket_from(conf)
        elif conf.name().endswith(".target"):
            return self.do_stop_target_from(conf)
        else:
            logg.error("stop not implemented for unit type: %s", conf.name())
            return False
    def do_stop_service_from(self, conf: SystemctlConf) -> bool:
        pid: Optional[int]
        timeout = self.units.get_TimeoutStopSec(conf)
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.units.get_env(conf)
        if not self._quiet:
            okee = self.units.exec_check(conf, env, Service, "ExecStop")
            if not okee and NO_RELOAD:
                return False
        service_directories = self.env_service_directories(conf)
        env.update(service_directories)
        returncode = 0
        service_result = "success"
        if runs in ["oneshot"]:
            status_file = self.status_file(conf)
            if self.get_status_from(conf, "ActiveState", "unknown") == "inactive":
                logg.warning("the service is already down once")
                return True
            for cmd in conf.getlist(Service, "ExecStop", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            if TRUE:
                if returncode:
                    self.set_status_from(conf, "ExecStopCode", nix_str(returncode))
                    self.write_status_from(conf, AS="failed")
                else:
                    self.clean_status_from(conf) # "inactive"
        # fallback Stop => Kill for ["simple","notify","forking"]
        elif not conf.getlist(Service, "ExecStop", []):
            logg.info("no ExecStop => systemctl kill")
            if TRUE:
                self.do_kill_unit_from(conf)
                self.clean_pid_file_from(conf)
                self.clean_status_from(conf) # "inactive"
        elif runs in ["simple", "exec", "notify", "idle"]:
            status_file = self.status_file(conf)
            size = os.path.exists(status_file) and os.path.getsize(status_file)
            logg.debug("STATUS %s (%s bytes)", status_file, size)
            pid = 0
            for cmd in conf.getlist(Service, "ExecStop", []):
                env["MAINPID"] = nix_str(self.read_mainpid_from(conf))
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                run = must_have_failed(run, newcmd) # TODO: a workaround
                # self.write_status_from(conf, MainPID=run.pid) # no ExecStop
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = to_int_if(env.get("MAINPID"))
            if pid:
                if self.wait_vanished_pid(pid, timeout):
                    self.clean_pid_file_from(conf)
                    self.clean_status_from(conf) # "inactive"
            else:
                logg.info("%s sleep as no PID was found on Stop", runs)
                time.sleep(MinimumTimeoutStopSec)
                pid = self.read_mainpid_from(conf)
                if not pid or not pid_exists(pid) or pid_zombie(pid):
                    self.clean_pid_file_from(conf)
                self.clean_status_from(conf) # "inactive"
        elif runs in ["forking"]:
            status_file = self.status_file(conf)
            pid_file = self.pid_file(conf)
            for cmd in conf.getlist(Service, "ExecStop", []):
                # active = self.is_active_from(conf)
                if pid_file:
                    new_pid = self.read_mainpid_from(conf)
                    if new_pid:
                        env["MAINPID"] = nix_str(new_pid)
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("fork stop %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = to_int_if(env.get("MAINPID"))
            if pid:
                if self.wait_vanished_pid(pid, timeout):
                    self.clean_pid_file_from(conf)
            else:
                logg.info("%s sleep as no PID was found on Stop", runs)
                time.sleep(MinimumTimeoutStopSec)
                pid = self.read_mainpid_from(conf)
                if not pid or not pid_exists(pid) or pid_zombie(pid):
                    self.clean_pid_file_from(conf)
            if returncode:
                if os.path.isfile(status_file):
                    self.set_status_from(conf, "ExecStopCode", nix_str(returncode))
                    self.write_status_from(conf, AS="failed")
            else:
                self.clean_status_from(conf) # "inactive"
        else:
            logg.error("unsupported run type '%s'", runs)
            return False
        # POST sequence
        if not self.is_active_from(conf):
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Service, "ExecStopPost", []):
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("post-stop %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-stop done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
        if self._only_what[0] not in ["none", "keep"]:
            self.remove_service_directories(conf)
        return service_result == "success"
    def do_stop_socket_from(self, conf: SystemctlConf) -> bool:
        runs = "socket"
        # timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool(Socket, "Accept", "no")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.units.load_conf(service_unit)
        if service_conf is None:
            logg.debug("unit could not be loaded (%s)", service_unit)
            logg.error("Unit %s not found.", service_unit)
            return False
        env = self.units.get_env(conf)
        if not self._quiet:
            okee = self.units.exec_check(conf, env, Socket, "ExecStop")
            if not okee and NO_RELOAD:
                return False
        if not accept:
            # we do not listen but have the service started right away
            done = self.do_stop_service_from(service_conf)
            service_result = done and "success" or "failed"
        else:
            done = self.do_stop_service_from(service_conf)
            service_result = done and "success" or "failed"
        # service_directories = self.env_service_directories(conf)
        # env.update(service_directories)
        # POST sequence
        if not self.is_active_from(conf):
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Socket, "ExecStopPost", []):
                _xe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s post-stop %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("%s post-stop done (%s) <-%s>", runs,
                           run.returncode or "OK", run.signal or "")
        return service_result == "success"
    def wait_vanished_pid(self, pid: int, timeout: float) -> bool:
        if not pid:
            return True
        if not self.is_active_pid(pid):
            return True
        for attempt in range(int(timeout)):
            time.sleep(1) # until TimeoutStopSec
            logg.debug("%s wait for PID %s to vanish (%ss)", delayed(attempt), pid, timeout)
            if not self.is_active_pid(pid):
                logg.info(" %s wait for PID %s is done", delayed(attempt), pid)
                return True
        logg.info("%s wait for PID %s failed", delayed(int(timeout)), pid)
        return False
    def reload_modules(self, *modules: str) -> bool:
        """ reload [UNIT]... -- reload these units """
        self.wait_system()
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.reload_units(units) and not missing
    def reload_units(self, units: List[str]) -> bool:
        """ fails if any unit fails to reload """
        self.wait_system()
        done = True
        for unit in self.units.sorted_after(units):
            if not self.reload_unit(unit):
                done = False
        return done
    def reload_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reload_unit_from(conf)
    def reload_unit_from(self, conf: SystemctlConf) -> bool:
        if not conf:
            return False
        if self.units.syntax_check(conf) > 100:
            return False
        with waitlock(conf):
            logg.info(" reload unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_reload_unit_from(conf)
    def do_reload_unit_from(self, conf: SystemctlConf) -> bool:
        if conf.name().endswith(".service"):
            return self.do_reload_service_from(conf)
        elif conf.name().endswith(".socket"):
            service_unit = self.get_socket_service_from(conf)
            service_conf = self.units.load_conf(service_unit)
            if service_conf:
                return self.do_reload_service_from(service_conf)
            else:
                logg.error("no %s found for unit type: %s", service_unit, conf.name())
                return False
        elif conf.name().endswith(".target"):
            return self.do_reload_target_from(conf)
        else:
            logg.error("reload not implemented for unit type: %s", conf.name())
            return False
    def do_reload_service_from(self, conf: SystemctlConf) -> bool:
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.units.get_env(conf)
        if not self._quiet:
            okee = self.units.exec_check(conf, env, Service, "ExecReload")
            if not okee and NO_RELOAD:
                return False
        initscript = conf.filename()
        if self.units.is_sysv_file(initscript):
            if initscript:
                newcmd = [initscript, "reload"]
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                logg.info("%s reload %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: nocover
                run = subprocess_waitpid(forkpid)
                self.set_status_from(conf, "ExecReloadCode", nix_str(run.returncode))
                if run.returncode:
                    self.write_status_from(conf, AS="failed")
                    return False
                else:
                    self.write_status_from(conf, AS="active")
                    return True
        service_directories = self.env_service_directories(conf)
        env.update(service_directories)
        if runs in ["simple", "exec", "notify", "forking", "idle"]:
            if not self.is_active_from(conf):
                logg.info("no reload on inactive service %s", conf.name())
                return True
            for cmd in conf.getlist(Service, "ExecReload", []):
                env["MAINPID"] = nix_str(self.read_mainpid_from(conf))
                exe, newcmd = self.units.expand_cmd(cmd, env, conf)
                logg.info("%s reload %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    logg.error("Job for %s failed because the control process exited with error code. (%s)",
                               conf.name(), run.returncode)
                    return False
            time.sleep(YIELD)
            return True
        elif runs in ["oneshot"]:
            logg.debug("ignored run type '%s' for reload", runs)
            return True
        else:
            logg.error("unsupported run type '%s'", runs)
            return False
    def restart_modules(self, *modules: str) -> bool:
        """ restart [UNIT]... -- restart these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.restart_units(units) and not missing
    def restart_units(self, units: List[str]) -> bool:
        """ fails if any unit fails to restart """
        self.wait_system()
        done = True
        for unit in self.units.sorted_after(units):
            if not self.restart_unit(unit):
                done = False
        return done
    def restart_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.restart_unit_from(conf)
    def restart_unit_from(self, conf: SystemctlConf) -> bool:
        if not conf:
            return False
        if self.units.syntax_check(conf) > 100:
            return False
        with waitlock(conf):
            if conf.name().endswith(".service"):
                logg.info(" restart service %s => %s", conf.name(), q_str(conf.filename()))
                if not self.is_active_from(conf):
                    return self.do_start_unit_from(conf)
                else:
                    return self.do_restart_unit_from(conf)
            else:
                return self.do_restart_unit_from(conf)
    def do_restart_unit_from(self, conf: SystemctlConf) -> bool:
        logg.info("(restart) => stop/start %s", conf.name())
        self.do_stop_unit_from(conf)
        return self.do_start_unit_from(conf)
    def try_restart_modules(self, *modules: str) -> bool:
        """ try-restart [UNIT]... -- try restart these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.try_restart_units(units) and not missing
    def try_restart_units(self, units: List[str]) -> bool:
        """ fails if any module fails to try-restart """
        self.wait_system()
        done = True
        for unit in self.units.sorted_after(units):
            if not self.try_restart_unit(unit):
                done = False
        return done
    def try_restart_unit(self, unit: str) -> bool:
        """ only do 'restart' if 'active' """
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        with waitlock(conf):
            logg.info(" try-restart unit %s => %s", conf.name(), q_str(conf.filename()))
            if self.is_active_from(conf):
                return self.do_restart_unit_from(conf)
        return True
    def reload_or_restart_modules(self, *modules: str) -> bool:
        """ reload-or-restart [UNIT]... -- reload or restart these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.reload_or_restart_units(units) and not missing
    def reload_or_restart_units(self, units: List[str]) -> bool:
        """ fails if any unit does not reload-or-restart """
        self.wait_system()
        done = True
        for unit in self.units.sorted_after(units):
            if not self.reload_or_restart_unit(unit):
                done = False
        return done
    def reload_or_restart_unit(self, unit: str) -> bool:
        """ do 'reload' if specified, otherwise do 'restart' """
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reload_or_restart_unit_from(conf)
    def reload_or_restart_unit_from(self, conf: SystemctlConf) -> bool:
        """ do 'reload' if specified, otherwise do 'restart' """
        if not conf:
            return False
        with waitlock(conf):
            logg.info(" reload-or-restart unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_reload_or_restart_unit_from(conf)
    def do_reload_or_restart_unit_from(self, conf: SystemctlConf) -> bool:
        if not self.is_active_from(conf):
            # try: self.stop_unit_from(conf)
            # except Exception as e: pass
            return self.do_start_unit_from(conf)
        elif conf.getlist(Service, "ExecReload", []):
            logg.info("found service to have ExecReload -> 'reload'")
            return self.do_reload_unit_from(conf)
        else:
            logg.info("found service without ExecReload -> 'restart'")
            return self.do_restart_unit_from(conf)
    def reload_or_try_restart_modules(self, *modules: str) -> bool:
        """ reload-or-try-restart [UNIT]... -- reload or try restart these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.reload_or_try_restart_units(units) and not missing
    def reload_or_try_restart_units(self, units: List[str]) -> bool:
        """ fails if any unit fails to reload-or-try-restart """
        self.wait_system()
        done = True
        for unit in self.units.sorted_after(units):
            if not self.reload_or_try_restart_unit(unit):
                done = False
        return done
    def reload_or_try_restart_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reload_or_try_restart_unit_from(conf)
    def reload_or_try_restart_unit_from(self, conf: SystemctlConf) -> bool:
        with waitlock(conf):
            logg.info(" reload-or-try-restart unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_reload_or_try_restart_unit_from(conf)
    def do_reload_or_try_restart_unit_from(self, conf: SystemctlConf) -> bool:
        if conf.getlist(Service, "ExecReload", []):
            return self.do_reload_unit_from(conf)
        elif not self.is_active_from(conf):
            return True
        else:
            return self.do_restart_unit_from(conf)
    def kill_modules(self, *modules: str) -> bool:
        """ kill [UNIT]... -- kill these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        return self.kill_units(units) and not missing
    def kill_units(self, units: List[str]) -> bool:
        """ fails if any unit could not be killed """
        self.wait_system()
        done = True
        for unit in reversed(self.units.sorted_after(units)):
            if not self.kill_unit(unit):
                done = False
        return done
    def kill_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.kill_unit_from(conf)
    def kill_unit_from(self, conf: SystemctlConf) -> bool:
        if not conf:
            return False
        with waitlock(conf):
            logg.info(" kill unit %s => %s", conf.name(), q_str(conf.filename()))
            return self.do_kill_unit_from(conf)
    def do_kill_unit_from(self, conf: SystemctlConf) -> bool:
        started = time.monotonic()
        doSendSIGKILL = self.units.get_SendSIGKILL(conf)  # pylint: disable=invalid-name
        doSendSIGHUP = self.units.get_SendSIGHUP(conf)  # pylint: disable=invalid-name
        useKillMode = self.units.get_KillMode(conf)  # pylint: disable=invalid-name
        useKillSignal = self.units.get_KillSignal(conf)  # pylint: disable=invalid-name
        kill_signal = getattr(signal, useKillSignal)
        timeout = self.units.get_TimeoutStopSec(conf)
        status_file = self.status_file(conf)
        size = os.path.exists(status_file) and os.path.getsize(status_file)
        logg.debug("STATUS %s (%s bytes)", status_file, size)
        mainpid = self.read_mainpid_from(conf)
        self.clean_status_from(conf) # clear RemainAfterExit and TimeoutStartSec
        if not mainpid:
            if useKillMode in ["control-group"]:
                logg.warning("no main PID %s", q_str(conf.filename()))
                logg.warning("and there is no control-group here")
            else:
                logg.info("no main PID %s", q_str(conf.filename()))
            return False
        if not pid_exists(mainpid) or pid_zombie(mainpid):
            logg.debug("ignoring children when mainpid is already dead")
            # because we list child processes, not processes in control-group
            return True
        pidlist = self.pidlist_of(mainpid) # here
        if pid_exists(mainpid):
            logg.info("stop kill PID %s", mainpid)
            self._kill_pid(mainpid, kill_signal)
        if useKillMode in ["control-group"]:
            if len(pidlist) > 1:
                logg.info("stop control-group PIDs %s", pidlist)
            for pid in pidlist:
                if pid != mainpid:
                    self._kill_pid(pid, kill_signal)
        if doSendSIGHUP:
            logg.info("stop SendSIGHUP to PIDs %s", pidlist)
            for pid in pidlist:
                self._kill_pid(pid, signal.SIGHUP)
        # wait for the processes to have exited
        while True:
            dead = True
            for pid in pidlist:
                if pid_exists(pid) and not pid_zombie(pid):
                    dead = False
                    break
            if dead:
                break
            if time.monotonic() > started + timeout:
                logg.info("service PIDs not stopped after %s", timeout)
                break
            time.sleep(1) # until TimeoutStopSec
        if dead or not doSendSIGKILL:
            logg.info("done kill PID %s %s", mainpid, dead and "OK")
            return dead
        if useKillMode in ["control-group", "mixed"]:
            logg.info("hard kill PIDs %s", pidlist)
            for pid in pidlist:
                if pid != mainpid:
                    self._kill_pid(pid, signal.SIGKILL)
            time.sleep(YIELD)
        # useKillMode in [ "control-group", "mixed", "process" ]
        if pid_exists(mainpid):
            logg.info("hard kill PID %s", mainpid)
            self._kill_pid(mainpid, signal.SIGKILL)
            time.sleep(YIELD)
        dead = not pid_exists(mainpid) or pid_zombie(mainpid)
        logg.info("done hard kill PID %s %s", mainpid, dead and "OK")
        return dead
    def _kill_pid(self, pid: int, kill_signal: Optional[int] = None) -> bool:
        try:
            sig = kill_signal or signal.SIGTERM
            os.kill(pid, sig)
        except OSError as e:
            if e.errno == errno.ESRCH or e.errno == errno.ENOENT:
                logg.debug("kill PID %s => No such process", pid)
                return True
            else:
                logg.error("kill PID %s => %s", pid, str(e))
                return False
        return not pid_exists(pid) or pid_zombie(pid)
    def is_active_modules(self, *modules: str) -> List[str]:
        """ is-active [UNIT].. -- check if these units are in active state
        implements True if all is-active = True """
        # systemctl returns multiple lines, one for each argument
        #   "active" when is_active
        #   "inactive" when not is_active
        #   "unknown" when not enabled
        # The return code is set to
        #   0 when "active"
        #   1 when unit is not found
        #   3 when any "inactive" or "unknown"
        # However: # TODO! BUG in original systemctl!
        #   documentation says " exit code 0 if at least one is active"
        #   and "Unless --quiet is specified, print the unit state"
        units: List[str]
        units = []
        missing: List[str] = []
        results: List[str] = []
        for module in modules:
            units = self.units.match_units(to_list(module))
            if not units:
                missing.append(unit_of(module))
                results += ["inactive"]
                continue
            for unit in units:
                active = self.get_active_unit(unit)
                enabled = self.enabled_unit(unit)
                if enabled != "enabled" and ACTIVE_IF_ENABLED:
                    active = "inactive" # "unknown"
                results += [active]
                break
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
            self.error |= NOT_ACTIVE
        # how it should work:
        status = "active" in results  # pylint: disable=unused-variable
        # how 'systemctl' works:
        non_active = [result for result in results if result != "active"]
        if non_active:
            self.error |= NOT_ACTIVE
        if non_active:
            self.error |= NOT_OK # status
        if DO_QUIET:
            return []
        return results
    def is_active_from(self, conf: SystemctlConf) -> bool:
        """ used in try-restart/other commands to check if needed. """
        if not conf:
            return False
        return self.active_state(conf) == "active"
    def active_pid_from(self, conf: SystemctlConf) -> Optional[int]:
        if not conf:
            return False
        pid = self.read_mainpid_from(conf)
        return self.is_active_pid(pid)
    def is_active_pid(self, pid: Optional[int]) -> Optional[int]:
        """ returns pid if the pid is still an active process """
        if pid and pid_exists(pid) and not pid_zombie(pid):
            return pid # usually a string (not null)
        return None
    def get_active_unit(self, unit: str) -> str:
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        conf = self.units.load_conf(unit)
        if not conf:
            logg.warning("Unit %s not found.", unit)
            return "unknown"
        else:
            return self.active_state(conf)
    def active_state(self, conf: SystemctlConf) -> str:
        if conf.name().endswith(".service"):
            return self.get_active_service_from(conf)
        elif conf.name().endswith(".socket"):
            service_unit = self.get_socket_service_from(conf)
            service_conf = self.units.load_conf(service_unit)
            return self.get_active_service_from(service_conf)
        elif conf.name().endswith(".target"):
            return self.get_active_target_from(conf)
        else:
            logg.debug("is-active not implemented for unit type: %s", conf.name())
            return "unknown" # TODO: "inactive" ?
    def get_active_service_from(self, conf: Optional[SystemctlConf]) -> str:
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        # used in try-restart/other commands to check if needed.
        if not conf:
            return "unknown"
        pid_file = self.pid_file(conf)
        if pid_file: # application PIDFile
            if not os.path.exists(pid_file):
                return "inactive"
        status_file = self.status_file(conf)
        if self.getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if DEBUG_STATUS:
                    logg.info("get_status_from %s => %s", conf.name(), state)
                return state
        pid = self.read_mainpid_from(conf)
        if DEBUG_STATUS:
            logg.debug("pid_file '%s' => PID %s", pid_file or status_file, nix_str(pid))
        if pid:
            if not pid_exists(pid) or pid_zombie(pid):
                return "failed"
            return "active"
        else:
            return "inactive"
    def get_active_target_from(self, conf: SystemctlConf) -> str:
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        return self.get_active_target(conf.name())
    def get_active_target(self, target: str) -> str:
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        if target in self.get_active_target_list():
            status = self.is_system_running()
            if status in ["running"]:
                return "active"
            return "inactive"
        else:
            services = self.target_default_services(target)
            result = "active"
            for service in services:
                conf = self.units.load_conf(service)
                if conf:
                    state = self.active_state(conf)
                    if state in ["failed"]:
                        result = state
                    elif state not in ["active"]:
                        result = state
            return result
    def get_active_target_list(self) -> List[str]:
        current_target = self.get_default_target()
        target_list = self.units.get_target_list(current_target)
        target_list += [DEFAULT_UNIT] # upper end
        target_list += [SYSINIT_TARGET] # lower end
        return target_list
    def active_substate(self, conf: SystemctlConf) -> Optional[str]:
        """ returns 'running' 'exited' 'dead' 'failed' 'plugged' 'mounted' """
        if not conf:
            return None
        pid_file = self.pid_file(conf)
        if pid_file:
            if not os.path.exists(pid_file):
                return "dead"
        status_file = self.status_file(conf)
        if self.getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if state in ["active"]:
                    return self.get_status_from(conf, "SubState", "running")
                else:
                    return self.get_status_from(conf, "SubState", "dead")
        pid = self.read_mainpid_from(conf)
        if DEBUG_STATUS:
            logg.debug("pid_file '%s' => PID %s", pid_file or status_file, nix_str(pid))
        if pid:
            if not pid_exists(pid) or pid_zombie(pid):
                return "failed"
            return "running"
        else:
            return "dead"
    def is_failed_modules(self, *modules: str) -> List[str]:
        """ is-failed [UNIT]... -- check if these units are in failes state
        implements True if any is-active = True """
        units: List[str] = []
        missing: List[str] = []
        results: List[str] = []
        for module in modules:
            units = self.units.match_units(to_list(module))
            if not units:
                missing.append(unit_of(module))
                results += ["inactive"]
                continue
            for unit in units:
                active = self.get_active_unit(unit)
                enabled = self.enabled_unit(unit)
                if enabled != "enabled" and ACTIVE_IF_ENABLED:
                    active = "inactive"
                results += [active]
                break
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        if "failed" in results:
            self.error = 0
        else:
            self.error |= NOT_OK
        if DO_QUIET:
            return []
        return results
    def is_failed_from(self, conf: SystemctlConf) -> bool:
        if conf is None:
            return True
        return self.active_state(conf) == "failed"
    def reset_failed_modules(self, *modules: str) -> bool:
        """ reset-failed [UNIT]... -- Reset failed state for all, one, or more units """
        units: List[str] = []
        missing: List[str] = []
        status = True
        for module in modules:
            units = self.units.match_units(to_list(module))
            if not units:
                missing.append(unit_of(module))
                continue
            for unit in units:
                if not self.reset_failed_unit(unit):
                    logg.error("Unit %s could not be reset.", unit_of(module))
                    status = False
                break
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
            self.error |= NOT_OK
        return status
    def reset_failed_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if not conf:
            logg.warning("Unit %s not found.", unit)
            return False
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reset_failed_from(conf)
    def reset_failed_from(self, conf: SystemctlConf) -> bool:
        if conf is None:
            return True
        if not self.is_failed_from(conf):
            return False
        done = False
        status_file = self.status_file(conf)
        if status_file and os.path.exists(status_file):
            try:
                os.remove(status_file)
                done = True
                logg.debug("done rm %s", status_file)
            except OSError as e:
                logg.error("while rm %s >> %s", status_file, e)
        pid_file = self.pid_file(conf)
        if pid_file and os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                done = True
                logg.debug("done rm %s", pid_file)
            except OSError as e:
                logg.error("while rm %s >> %s", pid_file, e)
        return done
    def status_modules(self, *modules: str) -> str:
        """ status [UNIT]... -- check the status of these units.
        """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
            # self.error |= NOT_OK | NOT_ACTIVE # 3
            # # same as (dead) # original behaviour
        return self.status_units(units)
    def status_units(self, units: List[str]) -> str:
        """ concatenates the status output of all units
            and the last non-successful statuscode """
        status = 0
        result = ""
        for unit in units:
            status1, result1 = self.status_unit(unit)
            if status1: status = status1
            if result: result += "\n\n"
            result += result1
        if status:
            self.error |= NOT_OK | NOT_ACTIVE # 3
        return result
    def status_unit(self, unit: str) -> Tuple[int, str]:
        conf = self.units.get_conf(unit)
        result = "%s - %s" % (unit, self.units.get_Description(conf))
        loaded = conf.loaded()
        if loaded:
            # pylint: disable=possibly-unused-variable
            filename = str(conf.filename())
            enabled = self.enabled_state(conf)
            result += F"\n    Loaded: {loaded} ({filename}, {enabled})"
            for path in conf.overrides():
                result += F"\n    Drop-In: {path}"
        else:
            result += "\n    Loaded: failed"
            return 3, result
        active = self.active_state(conf)
        substate = self.active_substate(conf)
        result += F"\n    Active: {active} ({substate})"
        if active == "active":
            return 0, result
        else:
            return 3, result
    def cat_modules(self, *modules: str) -> str:
        """ cat [UNIT]... show the *.system file for these"
        """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
            self.error |= NOT_OK
        result = self.cat_units(units)
        return result
    def cat_units(self, units: List[str]) -> str:
        done = True
        result = ""
        for unit in units:
            text = self.cat_unit(unit)
            if not text:
                done = False
            else:
                if result:
                    result += "\n\n"
                result += text
        if not done:
            self.error = NOT_OK
        return result
    def cat_unit(self, unit: str) -> Optional[str]:
        try:
            unit_file = self.units.unit_file(unit)
            if unit_file:
                return open(unit_file).read()
            logg.error("No files found for %s", unit)
        except OSError as e:
            print(F"Unit {unit} is not-loaded: {e}")
        self.error |= NOT_OK
        return None
    ##
    ##
    def preset_modules(self, *modules: str) -> bool:
        """ preset [UNIT]... -- set 'enabled' when in *.preset
        """
        if self.units.user_mode():
            logg.warning("preset makes no sense in --user mode")
            return True
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOIUND
        return self.preset_units(units) and not missing
    def preset_units(self, units: List[str]) -> bool:
        """ fails if any unit could not be changed """
        self.wait_system()
        fails = 0
        found = 0
        for unit in units:
            status = self.units.get_preset_of_unit(unit)
            if not status: continue
            found += 1
            if status.startswith("enable"):
                if self._preset_mode == "disable": continue
                logg.info("preset enable %s", unit)
                if not self.enable_unit(unit):
                    logg.warning("failed to enable %s", unit)
                    fails += 1
            if status.startswith("disable"):
                if self._preset_mode == "enable": continue
                logg.info("preset disable %s", unit)
                if not self.disable_unit(unit):
                    logg.warning("failed to disable %s", unit)
                    fails += 1
        return not fails and not not found  # pylint:  disable=unnecessary-negation
    def preset_all_modules(self, *modules: str) -> bool:
        """ preset-all --- run 'preset' on all services
        enable or disable services according to *.preset files
        """
        if self.units.user_mode():
            logg.warning("preset-all makes no sense in --user mode")
            return True
        units = self.units.match_units()
        return self.preset_units([unit for unit in units if fnmatched(unit, *modules)])
    def enablefolders(self, wanted: str) -> Iterable[str]:
        if self.units.user_mode():
            for folder in self.units.user_folders():
                yield self.default_enablefolder(wanted, folder)
        if TRUE:
            for folder in self.units.system_folders():
                yield self.default_enablefolder(wanted, folder)
    def enablefolder(self, wanted: str) -> str:
        if self.units.user_mode():
            user_folder = self.units.user_folder()
            return self.default_enablefolder(wanted, user_folder)
        else:
            return self.default_enablefolder(wanted)
    def default_enablefolder(self, wanted: str, basefolder: Optional[str] = None) -> str:
        basefolder = basefolder or self.units.system_folder()
        if not wanted:
            return wanted
        if not wanted.endswith(".wants"):
            wanted = wanted + ".wants"
        return os.path.join(basefolder, wanted)
    def enable_modules(self, *modules: str) -> bool:
        """ enable [UNIT]... -- enable these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                logg.debug("[enable] matched %s", unit)
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        return self.enable_units(units) and not missing
    def enable_units(self, units: List[str]) -> bool:
        self.wait_system()
        done = True
        for unit in units:
            if not self.enable_unit(unit):
                done = False
            elif self._do_now:
                self.start_unit(unit)
        return done
    def enable_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        unit_file = conf.filename()
        if unit_file is None:
            logg.error("Unit file %s not found.", unit)
            return False
        if self.units.is_sysv_file(unit_file):
            if self.units.user_mode():
                logg.error("Initscript %s not for --user mode", unit)
                return False
            return self.enable_unit_sysv(unit_file)
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.enable_unit_from(conf)
    def enable_unit_from(self, conf: SystemctlConf) -> bool:
        wanted = self.units.get_InstallTarget(conf)
        if not wanted and not self._force:
            logg.debug("%s has no target", conf.name())
            return False # "static" is-enabled
        target = wanted or self.get_default_target()
        folder = self.enablefolder(target)
        if self._root:
            folder = os_path(self._root, folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        source = conf.filename()
        if not source: # pragma: no cover (was checked before)
            logg.debug("%s has no real file", conf.name())
            return False
        symlink = os.path.join(folder, conf.name())
        if TRUE:
            _f = self._force and "-f" or ""
            logg.info("ln -s %s %s %s", _f, q_str(source), q_str(symlink))
        if self._force and os.path.islink(symlink):
            os.remove(target)
        if not os.path.islink(symlink):
            os.symlink(source, symlink)
        return True
    def rc3_root_folder(self) -> str:
        old_folder = os_path(self._root, _rc3_boot_folder)
        new_folder = os_path(self._root, _rc3_init_folder)
        if os.path.isdir(old_folder): # pragma: no cover
            return old_folder
        return new_folder
    def rc5_root_folder(self) -> str:
        old_folder = os_path(self._root, _rc5_boot_folder)
        new_folder = os_path(self._root, _rc5_init_folder)
        if os.path.isdir(old_folder): # pragma: no cover
            return old_folder
        return new_folder
    def enable_unit_sysv(self, unit_file: str) -> bool:
        # a "multi-user.target"/rc3 is also started in /rc5
        rc3 = self._enable_unit_sysv(unit_file, self.rc3_root_folder())
        rc5 = self._enable_unit_sysv(unit_file, self.rc5_root_folder())
        return rc3 and rc5
    def _enable_unit_sysv(self, unit_file: str, rc_folder: str) -> bool:
        name = os.path.basename(unit_file)
        start = "S50"+name
        stop = "K50"+name
        if not os.path.isdir(rc_folder):
            os.makedirs(rc_folder)
        # do not double existing entries
        for found in os.listdir(rc_folder):
            m = re.match(r"S\d\d(.*)", found) # match start files
            if m and m.group(1) == name:
                start = found
            m = re.match(r"K\d\d(.*)", found) # match stop files
            if m and m.group(1) == name:
                stop = found
        start_file = os.path.join(rc_folder, start)
        if not os.path.exists(start_file):
            os.symlink(unit_file, start_file)
        stop_file = os.path.join(rc_folder, stop)
        if not os.path.exists(stop_file):
            os.symlink(unit_file, stop_file)
        return True
    def disable_modules(self, *modules: str) -> bool:
        """ disable [UNIT]... -- disable these units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        return self.disable_units(units) and not missing
    def disable_units(self, units: List[str]) -> bool:
        self.wait_system()
        done = True
        for unit in units:
            if not self.disable_unit(unit):
                done = False
            elif self._do_now:
                self.stop_unit(unit)
        return done
    def disable_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        unit_file = conf.filename()
        if unit_file is None:
            logg.error("Unit file %s not found.", unit)
            return False
        if self.units.is_sysv_file(unit_file):
            if self.units.user_mode():
                logg.error("Initscript %s not for --user mode", unit)
                return False
            return self.disable_unit_sysv(unit_file)
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.disable_unit_from(conf)
    def disable_unit_from(self, conf: SystemctlConf) -> bool:
        wanted = self.units.get_InstallTarget(conf)
        if not wanted and not self._force:
            logg.debug("%s has no target", conf.name())
            return False # "static" is-enabled
        target = wanted or self.get_default_target()
        for folder in self.enablefolders(target):
            if self._root:
                folder = os_path(self._root, folder)
            symlink = os.path.join(folder, conf.name())
            if os.path.exists(symlink):
                try:
                    _f = self._force and "-f" or ""
                    logg.info("rm %s %s", _f, q_str(symlink))
                    if os.path.islink(symlink) or self._force:
                        os.remove(symlink)
                except (OSError, IOError) as e:
                    logg.error("disable %s >> %s", symlink, e)
        return True
    def disable_unit_sysv(self, unit_file: str) -> bool:
        rc3 = self._disable_unit_sysv(unit_file, self.rc3_root_folder())
        rc5 = self._disable_unit_sysv(unit_file, self.rc5_root_folder())
        return rc3 and rc5
    def _disable_unit_sysv(self, unit_file: str, rc_folder: str) -> bool:
        # a "multi-user.target"/rc3 is also started in /rc5
        name = os.path.basename(unit_file)
        start = "S50"+name
        stop = "K50"+name
        # do not forget the existing entries
        for found in os.listdir(rc_folder):
            m = re.match(r"S\d\d(.*)", found) # match start files
            if m and m.group(1) == name:
                start = found
            m = re.match(r"K\d\d(.*)", found) # match stop files
            if m and m.group(1) == name:
                stop = found
        start_file = os.path.join(rc_folder, start)
        if os.path.exists(start_file):
            os.unlink(start_file)
        stop_file = os.path.join(rc_folder, stop)
        if os.path.exists(stop_file):
            os.unlink(stop_file)
        return True
    def is_enabled_sysv(self, unit_file: str) -> bool:
        name = os.path.basename(unit_file)
        target = os.path.join(self.rc3_root_folder(), "S50%s" % name)
        if os.path.exists(target):
            return True
        return False
    def is_enabled_modules(self, *modules: str) -> List[str]:
        """ is-enabled [UNIT]... -- check if these units are enabled
        returns True if any of them is enabled."""
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        return self.is_enabled_units(units) # and not missing
    def is_enabled_units(self, units: List[str]) -> List[str]:
        """ true if any is enabled, and a list of infos """
        result = False
        infos: List[str] = []
        for unit in units:
            infos += [self.enabled_unit(unit)]
            if self.is_enabled_unit(unit):
                result = True
        if not result:
            self.error |= NOT_OK
        return infos
    def is_enabled_unit(self, unit: str) -> bool:
        conf = self.units.load_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        unit_file = conf.filename()
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.is_sysv_file(unit_file):
            return self.is_enabled_sysv(unit_file)
        state = self.is_enabled(conf)
        if state in ["enabled", "static"]:
            return True
        return False # ["disabled", "masked"]
    def enabled_unit(self, unit: str) -> str:
        conf = self.units.get_conf(unit)
        return self.enabled_state(conf)
    def enabled_state(self, conf: SystemctlConf) -> str:
        unit_file = nix_str(conf.filename())
        if self.units.is_sysv_file(unit_file):
            state = self.is_enabled_sysv(unit_file)
            if state:
                return "enabled"
            return "disabled"
        return self.is_enabled(conf)
    def is_enabled(self, conf: SystemctlConf) -> str:
        if conf.masked:
            return "masked"
        wanted = self.units.get_InstallTarget(conf)
        target = wanted or self.get_default_target()
        for folder in self.enablefolders(target):
            if self._root:
                folder = os_path(self._root, folder)
            target = os.path.join(folder, conf.name())
            if os.path.isfile(target):
                return "enabled"
        if not wanted:
            return "static"
        return "disabled"
    def mask_modules(self, *modules: str) -> bool:
        """ mask [UNIT]... -- mask non-startable units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.mask_units(units) and not missing
    def mask_units(self, units: List[str]) -> bool:
        self.wait_system()
        done = True
        for unit in units:
            if not self.mask_unit(unit):
                done = False
        return done
    def mask_unit(self, unit: str) -> bool:
        unit_file = self.units.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.is_sysv_file(unit_file):
            logg.error("Initscript %s can not be masked", unit)
            return False
        conf = self.units.get_conf(unit)
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        folder = self.mask_folder()
        if self._root:
            folder = os_path(self._root, folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        dev_null = _dev_null
        if TRUE:
            _f = self._force and "-f" or ""
            logg.debug("ln -s %s %s %s", _f, dev_null, q_str(target))
        if self._force and os.path.islink(target):
            os.remove(target)
        if not os.path.exists(target):
            os.symlink(dev_null, target)
            logg.info("Created symlink %s -> %s", q_str(target), dev_null)
            return True
        elif os.path.islink(target):
            logg.debug("mask symlink does already exist: %s", target)
            return True
        else:
            logg.error("mask target does already exist: %s", target)
            return False
    def mask_folder(self) -> str:
        for folder in self.mask_folders():
            if folder:
                return folder
        raise FileNotFoundError("did not find any systemd/system folder")
    def mask_folders(self) -> Iterable[str]:
        if self.units.user_mode():
            for folder in self.units.user_folders():
                yield folder
        if TRUE:
            for folder in self.units.system_folders():
                yield folder
    def unmask_modules(self, *modules: str) -> bool:
        """ unmask [UNIT]... -- unmask non-startable units """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            self.error |= NOT_FOUND
        return self.unmask_units(units) and not missing
    def unmask_units(self, units: List[str]) -> bool:
        self.wait_system()
        done = True
        for unit in units:
            if not self.unmask_unit(unit):
                done = False
        return done
    def unmask_unit(self, unit: str) -> bool:
        unit_file = self.units.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.units.is_sysv_file(unit_file):
            logg.error("Initscript %s can not be un/masked", unit)
            return False
        conf = self.units.get_conf(unit)
        if self.units.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        folder = self.mask_folder()
        if self._root:
            folder = os_path(self._root, folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        if TRUE:
            _f = self._force and "-f" or ""
            logg.info("rm %s %s", _f, q_str(target))
        if os.path.islink(target):
            os.remove(target)
            return True
        elif not os.path.exists(target):
            logg.debug("Symlink did not exist anymore: %s", target)
            return True
        else:
            logg.warning("target is not a symlink: %s", target)
            return True
    def list_dependencies_modules(self, *modules: str) -> List[str]:
        """ [UNIT]... show the dependency tree"
        """
        missing: List[str] = []
        units: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        return self.list_dependencies_units(units) # and not missing
    def list_dependencies_units(self, units: List[str]) -> List[str]:
        result: List[str] = []
        for unit in units:
            if result:
                result += ["", ""]
            result += self.list_dependencies_unit(unit)
        return result
    def list_dependencies_unit(self, unit: str) -> List[str]:
        result: List[str] = []
        if self._show_all:
            for line in self.units.list_all_dependencies(unit, ""):
                result += [line]
        else:
            for line in self.units.list_dependencies(unit, ""):
                result += [line]
        return result
    def list_start_dependencies_modules(self, *modules: str) -> List[Tuple[str, str]]:
        """ list-dependencies [UNIT]... -- show the dependency tree (experimental)"
        """
        return self.units.list_start_dependencies_units(list(modules))
    def daemon_reload_target(self) -> bool:
        """ daemon-reload -- reload will only check the service files
            The returncode will tell the number of warnings,
            and it is over 100 if it can not continue even
            for the relaxed systemctl.py style of execution. """
        if self._do_now:
            logg.debug("loop_sleep=%s", self.loop_sleep)
        errors = 0
        for unit in self.units.match_units():
            try:
                conf = self.units.get_conf(unit)
            except OSError as e:
                logg.error("%s: can not read unit file %s >> %s", unit, q_str(unit), e)
                continue
            errors += self.units.syntax_check(conf)
        if errors:
            logg.warning(" (%s) found %s problems", errors, errors % 100)
        return True # errors
    def show_modules(self, *modules: str) -> List[str]:
        """ show [UNIT]... -- Show properties of one or more units
           Show properties of one or more units (or the manager itself).
           If no argument is specified, properties of the manager will be
           shown. If a unit name is specified, properties of the unit is
           shown. By default, empty properties are suppressed. Use --all to
           show those too. To select specific properties to show, use
           --property=. This command is intended to be used whenever
           computer-parsable output is required. Use status if you are looking
           for formatted human-readable output.
           /
           NOTE: only a subset of properties is implemented """
        notfound: List[str] = []
        units: List[str] = []
        missing: List[str] = []
        for module in modules:
            matched = self.units.match_units(to_list(module))
            if not matched:
                units += [module]
                missing.append(unit_of(module))
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        if missing:
            logg.error("Unit %s not found.", " and ".join(missing))
            # self.error |= NOT_FOUND
        return self.show_units(units) + notfound # and not missing
    def show_units(self, units: List[str]) -> List[str]:
        logg.debug("show --property=%s", ",".join(self._only_property))
        result: List[str] = []
        for unit in units:
            if result: result += [""]
            for var, value in self.show_unit_items(unit):
                if self._only_property:
                    if var not in self._only_property:
                        continue
                else:
                    if not value and not self._show_all:
                        continue
                result += ["%s=%s" % (var, value)]
        return result
    def show_unit_items(self, unit: str) -> Iterable[Tuple[str, str]]:
        """ __show_unit_items [UNIT] -- show properties of a unit.
        """
        logg.info("try read unit %s", unit)
        conf = self.units.get_conf(unit)
        for entry in self.each_unit_items(unit, conf):
            yield entry
    def each_unit_items(self, unit: str, conf: SystemctlConf) -> Iterable[Tuple[str, str]]:
        loaded = conf.loaded()
        if not loaded:
            loaded = "not-loaded"
            if "NOT-FOUND" in self.units.get_Description(conf):
                loaded = "not-found"
        names = {unit: 1, conf.name(): 1}
        yield "Id", conf.name()
        yield "Names", " ".join(sorted(names.keys()))
        yield "Description", self.units.get_Description(conf) # conf.get(Unit, "Description")
        yield "PIDFile", self.get_PIDFile(conf) # not self.pid_file_from w/o default location
        yield "PIDFilePath", self.pid_file(conf)
        yield "MainPID", nix_str(self.active_pid_from(conf))            # status["MainPID"] or PIDFile-read
        yield "SubState", self.active_substate(conf) or "unknown"  # status["SubState"] or notify-result
        yield "ActiveState", self.active_state(conf) or "unknown" # status["ActiveState"]
        yield "LoadState", loaded
        yield "UnitFileState", self.enabled_state(conf)
        yield "StatusFile", self.get_StatusFile(conf)
        yield "StatusFilePath", self.status_file(conf)
        yield "JournalFile", self.get_journal_log(conf)
        yield "JournalFilePath", self.journal_log(conf)
        yield "NotifySocket", self.get_notify_socket_from(conf)
        yield "User", self.units.get_User(conf) or ""
        yield "Group", self.units.get_Group(conf) or ""
        yield "SupplementaryGroups", " ".join(self.units.get_SupplementaryGroups(conf))
        yield "TimeoutStartUSec", seconds_to_time(self.units.get_TimeoutStartSec(conf))
        yield "TimeoutStopUSec", seconds_to_time(self.units.get_TimeoutStopSec(conf))
        yield "NeedDaemonReload", "no"
        yield "SendSIGKILL", yes_str(self.units.get_SendSIGKILL(conf))
        yield "SendSIGHUP", yes_str(self.units.get_SendSIGHUP(conf))
        yield "KillMode", nix_str(self.units.get_KillMode(conf))
        yield "KillSignal", nix_str(self.units.get_KillSignal(conf))
        yield "StartLimitBurst", nix_str(self.units.get_StartLimitBurst(conf))
        yield "StartLimitIntervalSec", seconds_to_time(self.units.get_StartLimitIntervalSec(conf))
        yield "RestartSec", seconds_to_time(self.units.get_RestartSec(conf))
        yield "RemainAfterExit", yes_str(self.units.get_RemainAfterExit(conf))
        yield "WorkingDirectory", nix_str(self.units.get_WorkingDirectory(conf))
        env_parts = []
        for env_part in conf.getlist(Service, "Environment", []):
            env_parts.append(self.units.expand_special(env_part, conf))
        if env_parts:
            yield "Environment", " ".join(env_parts)
        env_files = []
        for env_file in conf.getlist(Service, "EnvironmentFile", []):
            env_files.append(self.units.expand_special(env_file, conf))
        if env_files:
            yield "EnvironmentFile", " ".join(env_files)
    #
    igno_centos = ["netconsole", "network"]
    igno_opensuse = ["raw", "pppoe", "*.local", "boot.*", "rpmconf*", "postfix*"]
    igno_ubuntu = ["mount*", "umount*", "ondemand", "*.local", "e2scrub_reap"]
    igno_always = ["network*", "dbus*", "systemd-*", "kdump*", "kmod*"]
    igno_always += ["purge-kernels.service", "after-local.service", "dm-event.*"] # as on opensuse
    igno_targets = ["remote-fs.target"]
    def _ignored_unit(self, unit: str, ignore_list: List[str]) -> bool:
        for ignore in ignore_list:
            if fnmatch.fnmatchcase(unit, ignore):
                return True # ignore
            if fnmatch.fnmatchcase(unit, ignore+".service"):
                return True # ignore
        return False
    def default_services_modules(self, *modules: str) -> List[str]:
        """ default-services -- show the default services
            This is used internally to know the list of service to be started in the 'get-default'
            target runlevel when the container is started through default initialisation. It will
            ignore a number of services - use '--all' to show a longer list of services and
            use '--all --all' if not even a minimal filter shall be used.
        """
        results: List[str] = []
        targets = modules or [self.get_default_target()]
        for target in targets:
            units = self.target_default_services(target)
            logg.debug(" %s # %s", " ".join(units), target)
            for unit in units:
                if unit not in results:
                    results.append(unit)
        return results
    def target_default_services(self, target: Optional[str] = None, sysv: str = "S") -> List[str]:
        """ knows about systemctl-start and systemctl-init targets with their explicit list of services to start"""
        if target in self._default_services:
            units = self._default_services[target]
            services = []
            for unit in units:
                if unit.endswith(".target"):
                    for target in self.units.get_target_list(unit):
                        services += self.target_enabled_services(target, sysv)
                else:
                    services += [unit]
            return services
        return self.target_enabled_services(target, sysv)
    def target_enabled_services(self, target: Optional[str] = None, sysv: str = "S") -> List[str]:
        """ get the default services for a target - this will ignore a number of services,
            use '--all' and '--all --all' to get more services.
        """
        igno = self.igno_centos + self.igno_opensuse + self.igno_ubuntu + self.igno_always
        if self._show_all:
            igno = self.igno_always
            if self._show_all > 1:
                igno = []
        logg.debug("ignored services filter for default.target:\n\t%s", igno)
        default_target = target or self.get_default_target()
        return self.enabled_target_services(default_target, sysv, igno)
    def enabled_target_services(self, target: str, sysv: str = "S", igno: List[str] = []) -> List[str]:
        units: List[str] = []
        if self.units.user_mode():
            targetlist = self.units.get_target_list(target)
            logg.debug("check for %s user services : %s", target, targetlist)
            for targets in targetlist:
                for unit in self.enabled_target_user_local_units(targets, ".target", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.required_target_units(targets, ".socket", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.enabled_target_user_local_units(targets, ".socket", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.required_target_units(targets, ".service", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.enabled_target_user_local_units(targets, ".service", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.enabled_target_user_system_units(targets, ".service", igno):
                    if unit not in units:
                        units.append(unit)
        else:
            targetlist = self.units.get_target_list(target)
            logg.debug("check for %s system services: %s", target, targetlist)
            for targets in targetlist:
                for unit in self.enabled_target_configured_system_units(targets, ".target", igno + self.igno_targets):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.required_target_units(targets, ".socket", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.enabled_target_installed_system_units(targets, ".socket", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.required_target_units(targets, ".service", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.enabled_target_installed_system_units(targets, ".service", igno):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self.enabled_target_sysv_units(targets, sysv, igno):
                    if unit not in units:
                        units.append(unit)
        return units
    def enabled_target_user_local_units(self, target: str, unit_kind: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str] = []
        for basefolder in self.units.user_folders():
            if not basefolder:
                continue
            folder = self.default_enablefolder(target, basefolder)
            if self._root:
                folder = os_path(self._root, folder)
            if os.path.isdir(folder):
                for unit in sorted(os.listdir(folder)):
                    path = os.path.join(folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(unit_kind):
                        units.append(unit)
        return units
    def enabled_target_user_system_units(self, target: str, unit_kind: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str] = []
        for basefolder in self.units.system_folders():
            if not basefolder:
                continue
            folder = self.default_enablefolder(target, basefolder)
            if self._root:
                folder = os_path(self._root, folder)
            if os.path.isdir(folder):
                for unit in sorted(os.listdir(folder)):
                    path = os.path.join(folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(unit_kind):
                        conf = self.units.load_conf(unit)
                        if conf is None:
                            pass
                        elif self.units.not_user_conf(conf):
                            pass
                        else:
                            units.append(unit)
        return units
    def enabled_target_installed_system_units(self, target: str, unit_type: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str] = []
        for basefolder in self.units.system_folders():
            if not basefolder:
                continue
            folder = self.default_enablefolder(target, basefolder)
            if self._root:
                folder = os_path(self._root, folder)
            if os.path.isdir(folder):
                for unit in sorted(os.listdir(folder)):
                    path = os.path.join(folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(unit_type):
                        units.append(unit)
        return units
    def enabled_target_configured_system_units(self, target: str, unit_type: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str] = []
        if TRUE:
            folder = self.default_enablefolder(target)
            if self._root:
                folder = os_path(self._root, folder)
            if os.path.isdir(folder):
                for unit in sorted(os.listdir(folder)):
                    path = os.path.join(folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(unit_type):
                        units.append(unit)
        return units
    def enabled_target_sysv_units(self, target: str, sysv: str = "S", igno: List[str] = []) -> List[str]:
        units: List[str] = []
        folders: List[str] = []
        if target in ["multi-user.target", DEFAULT_UNIT]:
            folders += [self.rc3_root_folder()]
        if target in ["graphical.target"]:
            folders += [self.rc5_root_folder()]
        for folder in folders:
            if not os.path.isdir(folder):
                logg.debug("note: non-existent %s", folder)
                continue
            for unit in sorted(os.listdir(folder)):
                path = os.path.join(folder, unit)
                if os.path.isdir(path): continue
                m = re.match(sysv+r"\d\d(.*)", unit)
                if m:
                    service = m.group(1)
                    unit = service + ".service"
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    units.append(unit)
        return units
    def required_target_units(self, target: str, unit_type: str, igno: List[str]) -> List[str]:
        units: List[str] = []
        deps = self.units.get_required_dependencies(target)
        for unit in sorted(deps):
            if self._ignored_unit(unit, igno):
                continue # ignore
            if unit.endswith(unit_type):
                if unit not in units:
                    units.append(unit)
        return units
    def default_system(self, arg: bool = True) -> bool:
        """ default -- start units for default system level
            This will go through the enabled services in the default 'multi-user.target'.
            However some services are ignored as being known to be installation garbage
            from unintended services. Use '--all' so start all of the installed services
            and with '--all --all' even those services that are otherwise wrong.
            /// SPECIAL: with --now or --init the init-loop is run and afterwards
                a system_halt is performed with the enabled services to be stopped."""
        self.sysinit_status(SubState = "initializing")
        logg.info("system default requested [init] %s", arg)
        init = self.init_mode or self._do_now
        if not self.exit_mode and self._do_now:
            self.exit_mode |= EXIT_NO_SERVICES_LEFT
        return self.start_system_default(init = init)
    def start_system_default(self, init: int = 0) -> bool:
        """ detect the default.target services and start them.
            When --init is given then the init-loop is run and
            the services are stopped again by 'systemctl halt'."""
        target = self.get_default_target()
        services = self.start_target_system(target, init)
        return not not services  # pylint: disable=unnecessary-negation
    def start_target_system(self, target: str, init: int = 0) -> List[str]:
        services = self.target_default_services(target, "S")
        logg.debug("[%s] system starts %s", target, services)
        units = []
        for unit in self.units.sorted_after(services):
            units.append(unit)
        self.sysinit_status(SubState = "starting")
        for unit in units:
            self.start_unit(unit)
        logg.info("[%s] system is up --init=%s", target, init)
        if init:
            logg.info("[%s] init-loop start", target)
            sig = self.init_loop_until_stop(services)
            logg.info("[%s] init-loop stop on %s", target, sig)
            self.sysinit_status(SubState = "stopping")
            for unit in reversed(units):
                self.stop_unit(unit)
            logg.info("[%s] system is down", target)
        return units
    def do_start_target_from(self, conf: SystemctlConf) -> bool:
        target = conf.name()
        # services = self.start_target_system(target)
        services = self.target_default_services(target, "S")
        units = [service for service in services if not self.is_running_unit(service)]
        logg.debug("start %s is starting %s from %s", target, units, services)
        return self.start_units(units)
    def stop_system_default(self) -> bool:
        """ detect the default.target services and stop them.
            This is commonly run through 'systemctl halt' or
            at the end of a 'systemctl --init default' loop."""
        target = self.get_default_target()
        services = self.stop_target_system(target)
        logg.info("[%s] system is down", target)
        return not not services  # pylint: disable=unnecessary-negation
    def stop_target_system(self, target: str) -> List[str]:
        services = self.target_default_services(target, "K")
        self.sysinit_status(SubState = "stopping")
        self.stop_units(services)
        return services
    def do_stop_target_from(self, conf: SystemctlConf) -> bool:
        target = conf.name()
        # services = self.stop_target_system(target)
        services = self.target_default_services(target, "K")
        units = [service for service in services if self.is_running_unit(service)]
        logg.debug("stop %s is stopping %s from %s", target, units, services)
        return self.stop_units(units)
    def do_reload_target_from(self, conf: SystemctlConf) -> bool:
        target = conf.name()
        return self.reload_target_system(target)
    def reload_target_system(self, target: str) -> bool:
        services = self.target_default_services(target, "S")
        units = [service for service in services if self.is_running_unit(service)]
        return self.reload_units(units)
    def halt_target(self, arg: bool = True) -> bool:
        """ halt -- stop units from default system level """
        logg.info("system halt requested - %s", arg)
        done = self.stop_system_default()
        try:
            os.kill(1, signal.SIGQUIT) # exit init-loop on no_more_procs
        except OSError as e:
            logg.warning("SIGQUIT to init-loop on PID-1 >> %s", e)
        return done
    def system_get_default(self) -> str:
        """ get current default run-level"""
        return self.get_default_target()
    def get_targets_folder(self) -> str:
        return os_path(self._root, self.mask_folder())
    def get_default_target_file(self) -> str:
        targets_folder = self.get_targets_folder()
        return os.path.join(targets_folder, DEFAULT_UNIT)
    def get_default_target(self, default_target: Optional[str] = None) -> str:
        """ get-default -- get current default run-level"""
        current = default_target or self._default_target
        default_target_file = self.get_default_target_file()
        if os.path.islink(default_target_file):
            current = os.path.basename(os.readlink(default_target_file))
        return current
    def set_default_modules(self, *modules: str) -> str:
        """ set-default [UNIT] -- set current default run-level"""
        if not modules:
            logg.debug(".. no runlevel given")
            self.error |= NOT_OK
            return "Too few arguments"
        current = self.get_default_target()
        default_target_file = self.get_default_target_file()
        msg = ""
        for module in modules:
            if module == current:
                continue
            targetfile = None
            for targetname, targetpath in self.units.each_target_file():
                if targetname == module:
                    targetfile = targetpath
            if not targetfile:
                self.error |= NOT_OK | NOT_ACTIVE # 3
                msg = "No such runlevel %s" % (module)
                continue
            #
            if os.path.islink(default_target_file):
                os.unlink(default_target_file)
            if not os.path.isdir(os.path.dirname(default_target_file)):
                os.makedirs(os.path.dirname(default_target_file))
            os.symlink(targetfile, default_target_file)
            msg = "Created symlink from %s -> %s" % (default_target_file, targetfile)
            logg.debug("%s", msg)
        return msg
    def start_log_files(self, units: List[str]) -> None:
        self._log_file = {}
        self._log_hold = {}
        for unit in units:
            conf = self.units.load_conf(unit)
            if not conf: continue
            if self.skip_journal_log(conf): continue
            log_file = self.journal_log(conf)
            try:
                opened = os.open(log_file, os.O_RDONLY | os.O_NONBLOCK)
                self._log_file[unit] = opened
                self._log_hold[unit] = b""
            except OSError as e:
                logg.error("can not open %s log: %s >> %s", unit, log_file, e)
    def read_log_files(self, units: List[str]) -> None:
        self.print_log_files(units)
    def print_log_files(self, units: List[str], stdout: int = 1) -> int:
        BUFSIZE=LOG_BUFSIZE # 8192  # pylint: disable=invalid-name
        printed = 0
        for unit in units:
            if unit in self._log_file:
                new_text = b""
                while True:
                    buf = os.read(self._log_file[unit], BUFSIZE)
                    if not buf: break
                    new_text += buf
                    continue
                text = self._log_hold[unit] + new_text
                if not text: continue
                lines = text.split(b"\n")
                if not text.endswith(b"\n"):
                    self._log_hold[unit] = lines[-1]
                    lines = lines[:-1]
                for line in lines:
                    prefix = unit.encode("utf-8")
                    content = prefix+b": "+line+b"\n"
                    try:
                        os.write(stdout, content)
                        try:
                            os.fsync(stdout)
                        except OSError:
                            pass
                        printed += 1
                    except BlockingIOError:
                        pass
        return printed
    def stop_log_files(self, units: List[str]) -> None:
        for unit in units:
            try:
                if unit in self._log_file:
                    if self._log_file[unit]:
                        os.close(self._log_file[unit])
            except OSError as e:
                logg.error("can not close log: %s >> %s", unit, e)
        self._log_file = {}
        self._log_hold = {}
    def restart_failed_units(self, units: List[str], maximum: Optional[int] = None) -> List[str]:
        """ This function will restart failed units.
        /
        NOTE that with standard settings the LimitBurst implementation has no effect. If
        the init-loop is ticking at the default of INITLOOPSLEEP of 5sec and the LimitBurst 
        default is 5x within a default 10secs time frame then within those 10sec only 2 loop
        rounds have come here checking for possible restarts. You can directly shorten
        the interval ('-c INITLOOPSLEEP=1') or have it indirectly shorter from the
        service descriptor's RestartSec ("RestartSec=2s").
        """
        me = os.getpid()
        maximum = maximum or DefaultStartLimitIntervalSec
        # restartDelay = YIELD
        for unit in units:
            now = time.monotonic()
            try:
                conf = self.units.load_conf(unit)
                if not conf: continue
                restart_policy = conf.get(Service, "Restart", "no")
                if restart_policy in ["no", "on-success"]:
                    logg.debug("[%s] [%s] Current NoCheck (Restart=%s)", me, unit, restart_policy)
                    continue
                restart_sec = self.units.get_RestartSec(conf)
                if restart_sec == 0:
                    if self.loop_sleep > 1:
                        logg.warning("[%s] set loop-sleep from %ss to 1 (caused by RestartSec=0!)",
                                     unit, self.loop_sleep)
                        self.loop_sleep = 1
                elif restart_sec > 0.9 and restart_sec < self.loop_sleep:
                    restart_sleep = int(restart_sec + 0.2)
                    if restart_sleep < self.loop_sleep:
                        logg.warning("[%s] set loop-sleep from %ss to %s (caused by RestartSec=%.3fs)",
                                     unit, self.loop_sleep, restart_sleep, restart_sec)
                        self.loop_sleep = restart_sleep
                active_state = self.active_state(conf)
                is_failed = active_state in ["failed"]
                logg.debug("[%s] [%s] Current Status: %s (%s)", me, unit, active_state, is_failed)
                if not is_failed:
                    if unit in self._restart_failed_units:
                        del self._restart_failed_units[unit]
                    continue
                limit_burst = self.units.get_StartLimitBurst(conf)
                limit_secs = self.units.get_StartLimitIntervalSec(conf)
                if limit_burst > 1 and limit_secs >= 1:
                    try:
                        if unit not in self._restarted_unit:
                            self._restarted_unit[unit] = []
                            # we want to register restarts from now on
                        restarted = self._restarted_unit[unit]
                        logg.debug("[%s] [%s] Current limit-secs=%ss limit-burst=%sx (restarted %sx)",
                                   me, unit, limit_secs, limit_burst, len(restarted))
                        oldest = 0.
                        interval = 0.
                        if len(restarted) >= limit_burst:
                            logg.debug("[%s] [%s] restarted %s",
                                       me, unit, ["%.3fs" % (sec - now) for sec in restarted])
                            while len(restarted):
                                oldest = restarted[0]
                                interval = time.monotonic() - oldest
                                if interval > limit_secs:
                                    restarted = restarted[1:]
                                    continue
                                break
                            self._restarted_unit[unit] = restarted
                            logg.debug("[%s] [%s] ratelimit %s",
                                       me, unit, ["%.3fs" % (t - now) for t in restarted])
                            # all values in restarted have a time below limitSecs
                        if len(restarted) >= limit_burst:
                            logg.info("[%s] [%s] Blocking Restart - oldest %s is %s ago (allowed %s)",
                                      me, unit, oldest, interval, limit_secs)
                            self.write_status_from(conf, AS="error")
                            unit = "" # dropped out
                            continue
                    except OSError as e:
                        logg.error("[%s] burst exception >> %s", unit, e)
                if unit: # not dropped out
                    if unit not in self._restart_failed_units:
                        self._restart_failed_units[unit] = now + restart_sec
                        logg.debug("[%s] [%s] restart scheduled in %+.3fs",
                                   me, unit, (self._restart_failed_units[unit] - now))
            except Exception as e: # pylint: disable=broad-exception-caught
                logg.error("[%s] [%s] An error occurred while restart checking >> %s", me, unit, e)
        if not self._restart_failed_units:
            self.error |= NOT_OK
            return []
        # NOTE: this function is only called from InitLoop when "running"
        # let's check if any of the restart_units has its restartSec expired
        now = time.monotonic()
        restart_done: List[str] = []
        logg.debug("[%s] Restart checking  %s",
                   me, ["%+.3fs" % (sec - now) for sec in self._restart_failed_units.values()])
        for unit in sorted(self._restart_failed_units):
            restart_at = self._restart_failed_units[unit]
            if restart_at > now:
                continue
            restart_done.append(unit)
            try:
                conf = self.units.load_conf(unit)
                if not conf: continue
                active_state = self.active_state(conf)
                is_failed = active_state in ["failed"]
                logg.debug("[%s] [%s] Restart Status: %s (%s)", me, unit, active_state, is_failed)
                if is_failed:
                    logg.debug("[%s] [%s] --- restarting failed unit...", me, unit)
                    self.restart_unit(unit)
                    logg.debug("[%s] [%s] --- has been restarted.", me, unit)
                    if unit in self._restarted_unit:
                        self._restarted_unit[unit].append(time.monotonic())
            except Exception as e: # pylint: disable=broad-exception-caught
                logg.error("[%s] [%s] An error occurred while restarting >> %s", me, unit, e)
        for unit in restart_done:
            if unit in self._restart_failed_units:
                del self._restart_failed_units[unit]
        logg.debug("[%s] Restart remaining %s",
                   me, ["%+.3fs" % (sec - now) for sec in self._restart_failed_units.values()])
        return restart_done

    def init_loop_until_stop(self, units: List[str]) -> Optional[str]:
        """ this is the init-loop - it checks for any zombies to be reaped and
            waits for an interrupt. When a SIGTERM /SIGINT /Control-C signal
            is received then the signal name is returned. Any other signal will
            just raise an Exception like one would normally expect. As a special
            the 'systemctl halt' emits SIGQUIT which puts it into no_more_procs mode."""
        signal.signal(signal.SIGQUIT, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGQUIT"))
        signal.signal(signal.SIGINT, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGINT"))
        signal.signal(signal.SIGTERM, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGTERM"))
        result: Optional[str] = None
        #
        self.start_log_files(units)
        logg.debug("[init] start listen")
        listen = SystemctlListenThread(self)
        logg.debug("[init] starts listen")
        listen.start()
        logg.debug("[init] started listen")
        self.sysinit_status(ActiveState = "active", SubState = "running")
        logg.info("[init] running every %ss checking %s %s", self.loop_sleep,
            "services" if EXIT_MODE & EXIT_NO_SERVICES_LEFT else "-", "procs" if EXIT_MODE & EXIT_NO_PROCS_LEFT else "-")
        lasttime = time.monotonic()
        while True:
            try:
                sleep_sec = self.loop_sleep - (time.monotonic() - lasttime)
                if sleep_sec < YIELD:
                    sleep_sec = YIELD
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[init] WAIT (loop-sleep %ss) sleeping %ss", self.loop_sleep, sleep_sec)
                sleeping = sleep_sec
                while sleeping > 2:
                    time.sleep(1) # accept signals atleast every second
                    sleeping = self.loop_sleep - (time.monotonic() - lasttime)
                    if sleeping < YIELD:
                        sleeping = YIELD
                        break
                time.sleep(sleeping) # remainder waits less that 2 seconds
                lasttime = time.monotonic()
                self.loop_lock.acquire()
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[init] NEXT (after %ss)", sleep_sec)
                self.read_log_files(units)
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[init] reap zombies - check current processes")
                running = self.reap_zombies(loop="init")
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[init-loop] reap zombies - found %s running procs", running)
                if self.exit_mode & EXIT_NO_SERVICES_LEFT:
                    active = []
                    for unit in units:
                        conf = self.units.load_conf(unit)
                        if not conf: continue
                        if self.is_active_from(conf):
                            active.append(unit)
                    if not active:
                        logg.info("[init] no more services - exit init-loop")
                        break
                    elif NEVER:
                        logg.debug("[init] active services - %s", " and ".join(active))
                if self.exit_mode & EXIT_NO_PROCS_LEFT:
                    if not running:
                        logg.info("[init] no more procs - exit init-loop")
                        break
                if RESTART_FAILED_UNITS:
                    self.restart_failed_units(units)
                self.loop_lock.release()
            except KeyboardInterrupt as e:
                if e.args and e.args[0] == "SIGQUIT":
                    # the original systemd puts a coredump on that signal.
                    logg.info("[init] SIGQUIT - enabling no more procs check")
                    self.exit_mode |= EXIT_NO_PROCS_LEFT
                    continue
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                logg.info("[init] interrupted - exit init-loop >> %s", e)
                result = str(e) or "STOPPED"
                break
            except Exception as e:
                logg.info("[init] interrupted >> %s", e)
                raise
        self.sysinit_status(ActiveState = None, SubState = "degraded")
        try:
            self.loop_lock.release() # may be already unlocked here
        except (OSError, RuntimeError, threading.ThreadError) as e:
            logg.debug("[init] loop_lock release %s >> %s", type(e), e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logg.error("[init] loop_lock release %s >> %s", type(e), e)
        listen.stop()
        listen.join(2)
        self.read_log_files(units)
        self.read_log_files(units)
        self.stop_log_files(units)
        logg.debug("[init-loop] done")
        return result
    def reap_zombies_target(self) -> str:
        """ reap-zombies -- check to reap children (internal) """
        running = self.reap_zombies()
        return F"remaining {running} process"  # with strip-python3 0.1.1092
    def reap_zombies(self, loop: str = "loop") -> int:
        """ check to reap children """
        selfpid = os.getpid()
        running = 0
        for pid_entry in os.listdir(_proc_pid_dir):
            pid = to_int_if(pid_entry)
            if pid is None:
                continue
            if pid == selfpid:
                continue
            proc_status = _proc_pid_status.format(pid = pid)
            if os.path.isfile(proc_status):
                zombie = False
                ppid = -1
                try:
                    with open(proc_status) as f:
                        for line in f:
                            m = re.match(r"State:\s*Z.*", line)
                            if m: zombie = True
                            m = re.match(r"PPid:\s*(\d+)", line)
                            if m: ppid = int(m.group(1))
                except IOError as e:
                    logg.warning("[%s] %s >> %s", loop, proc_status, e)
                    continue
                if zombie and ppid == os.getpid():
                    logg.info("[%s] reap zombie %s", loop, pid)
                    try: os.waitpid(pid, os.WNOHANG)
                    except OSError as e:
                        logg.warning("[%s] reap zombie %s: %s", loop, pid, e.strerror)
            if os.path.isfile(proc_status):
                if pid > 1:
                    running += 1
        return running # except PID 0 and PID 1
    def sysinit_status(self, **status: Optional[str]) -> None:
        conf = self.sysinit_target()
        self.write_status_from(conf, **status)
    def sysinit_target(self) -> SystemctlConf:
        if not self._sysinit_target:
            self._sysinit_target = self.units.default_conf(SYSINIT_TARGET, "System Initialization")
        assert self._sysinit_target is not None
        return self._sysinit_target
    def is_system_running(self) -> str:
        """ is-system-running -- show sysinit status (substate) """
        conf = self.sysinit_target()
        if not self.is_running(conf):
            time.sleep(YIELD)
        if not self.is_running(conf):
            return "offline"
        status = self.read_status_from(conf)
        return status.get("SubState", "unknown")
    def is_system_running_info(self) -> Optional[str]:
        state = self.is_system_running()
        if state not in ["running"]:
            self.error |= NOT_OK # 1
        if self._quiet:
            return None
        return state
    def wait_system(self, target: Optional[str] = None) -> None:
        target = target or SYSINIT_TARGET
        for attempt in range(int(SYSINIT_WAIT)):
            state = self.is_system_running()
            if "init" in state:
                if target in [SYSINIT_TARGET, "basic.target"]:
                    logg.info("[%s] %s system not initialized - wait", target, delayed(attempt))
                    time.sleep(1)
                    continue
            if "start" in state or "stop" in state:
                if target in ["basic.target"]:
                    logg.info("[%s] %s system not running - wait", target, delayed(attempt))
                    time.sleep(1)
                    continue
            if "running" not in state:
                logg.info("[%s] %s system is %s -- ready", target, delayed(attempt), state)
            break
    def is_running(self, conf: SystemctlConf) -> bool:
        status_file = self.status_file(conf)
        pid_file = self.pid_file(conf)
        return self.getsize(status_file) > 0 or self.getsize(pid_file) > 0
    def is_running_unit(self, unit: str) -> bool:
        conf = self.units.get_conf(unit)
        return self.is_running(conf)
    def pidlist_of(self, pid: Optional[int]) -> List[int]:
        if not pid:
            return []
        pidlist = [pid]
        pids = [pid]
        for _ in range(PROC_MAX_DEPTH):
            for pid_entry in os.listdir(_proc_pid_dir):
                pid = to_int_if(pid_entry)
                if pid is None:
                    continue
                proc_status = _proc_pid_status.format(**locals())
                if os.path.isfile(proc_status):
                    try:
                        with open(proc_status) as f:
                            for line in f:
                                if line.startswith("PPid:"):
                                    ppid_text = line[len("PPid:"):].strip()
                                    try: ppid = int(ppid_text)
                                    except ValueError: continue
                                    if ppid in pidlist and pid not in pids:
                                        pids += [pid]
                    except IOError as e:
                        logg.warning("%s >> %s", proc_status, e)
                        continue
            if len(pids) != len(pidlist):
                pidlist = pids[:]
                continue
        return pids
    def echo(self, *targets: str) -> str:
        line = " ".join(*targets)
        logg.info(" == echo == %s", line)
        return line
    def killall(self, *targets: str) -> bool:
        mapping: Dict[str, signal.Signals] = {}
        mapping[":3"] = signal.SIGQUIT
        mapping[":QUIT"] = signal.SIGQUIT
        mapping[":6"] = signal.SIGABRT
        mapping[":ABRT"] = signal.SIGABRT
        mapping[":9"] = signal.SIGKILL
        mapping[":KILL"] = signal.SIGKILL
        sig: signal.Signals = signal.SIGTERM
        for target in targets:
            if target.startswith(":"):
                if target in mapping:
                    sig = mapping[target]
                else: # pragma: no cover
                    logg.error("unsupported %s", target)
                continue
            for pid_entry in os.listdir(_proc_pid_dir):
                pid = to_int_if(pid_entry)
                if pid:
                    try:
                        cmdline = _proc_pid_cmdline.format(**locals())
                        with open(cmdline) as f:
                            cmd = f.read().split("\0")
                        if DEBUG_KILLALL: logg.debug("cmdline %s", cmd)
                        found = None
                        cmd_exe = os.path.basename(cmd[0])
                        if DEBUG_KILLALL: logg.debug("cmd.exe '%s'", cmd_exe)
                        if fnmatch.fnmatchcase(cmd_exe, target): found = "exe"
                        if len(cmd) > 1 and cmd_exe.startswith("python"):
                            nonoption = 1 # atleast skip over '-u' unbuffered
                            while nonoption < len(cmd) and cmd[nonoption].startswith("-"): nonoption += 1
                            cmd_arg = os.path.basename(cmd[nonoption])
                            if DEBUG_KILLALL: logg.debug("cmd.arg '%s'", cmd_arg)
                            if fnmatch.fnmatchcase(cmd_arg, target): found = "arg"
                            if cmd_exe.startswith("coverage") or cmd_arg.startswith("coverage"):
                                x = cmd.index("--")
                                if x > 0 and x+1 < len(cmd):
                                    cmd_run = os.path.basename(cmd[x+1])
                                    if DEBUG_KILLALL: logg.debug("cmd.run '%s'", cmd_run)
                                    if fnmatch.fnmatchcase(cmd_run, target): found = "run"
                        if found:
                            if DEBUG_KILLALL: logg.debug("%s found %s %s", found, pid, [c for c in cmd])
                            if pid != os.getpid():
                                logg.debug(" kill -%s %s # %s", sig, pid, target)
                                os.kill(pid, sig)
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        logg.error("kill -%s %s >> %s", sig, pid, e)
        return True
    def force_ipv4(self) -> None:
        """ only ipv4 localhost in /etc/hosts """
        logg.debug("checking hosts sysconf for '::1 localhost'")
        lines: List[str] = []
        sysconf_hosts = os_path(self._root, _etc_hosts)
        with open(sysconf_hosts) as f:
            for line in f:
                if "::1" in line:
                    newline = re.sub("\\slocalhost\\s", " ", line)
                    if line != newline:
                        logg.info("%s: '%s' => '%s'", _etc_hosts, line.rstrip(), newline.rstrip())
                        line = newline
                lines.append(line)
        with open(sysconf_hosts, "w") as f:
            for line in lines:
                f.write(line)
    def force_ipv6(self) -> None:
        """ only ipv4 localhost in /etc/hosts """
        logg.debug("checking hosts sysconf for '127.0.0.1 localhost'")
        lines: List[str] = []
        sysconf_hosts = os_path(self._root, _etc_hosts)
        with open(sysconf_hosts) as f:
            for line in f:
                if "127.0.0.1" in line:
                    newline = re.sub("\\slocalhost\\s", " ", line)
                    if line != newline:
                        logg.info("%s: '%s' => '%s'", _etc_hosts, line.rstrip(), newline.rstrip())
                        line = newline
                lines.append(line)
        with open(sysconf_hosts, "w") as f:
            for line in lines:
                f.write(line)
    def help_list(self, show_all: Optional[int] = None) -> Dict[str, str]:
        show_all = self._show_all if show_all is None else show_all
        help_docs: Dict[str, str] = {}
        for name in dir(self):
            method = getattr(self, name)
            doctext = getattr(method, "__doc__")
            if not doctext:
                continue
            if " -- " in doctext or " --- " in doctext:
                firstword = doctext.strip().split(" ", 1)[0]
                help_docs[firstword] = doctext
            elif show_all and not name.startswith("_") and callable(method):
                internal = "__" + name
                help_docs[internal] = internal + " = " + doctext
        return help_docs
    def help_modules(self, *args: str) -> List[str]:
        """help [command] -- show this help
        """
        lines: List[str] = []
        okay = True
        prog = os.path.basename(sys.argv[0])
        if not args:
            help_docs = self.help_list()
            lines.append("%s command [options]..." % prog)
            lines.append("")
            lines.append("Commands:")
            for name in sorted(help_docs):
                doc = help_docs[name]
                firstline = doc.split("\n")[0]
                lines.append(" " + firstline.strip())
        else:
            help_docs = self.help_list(show_all = 1)
            for arg in args:
                if arg not in help_docs:
                    print("error: no such command '%s'" % arg)
                    okay = False
                else:
                    doc = help_docs[arg]
                    doc_text = doc.replace("\n", "\n\n", 1).strip()
                    lines.append("%s %s" % (prog, doc_text))
        if not okay:
            self.help_modules()
            self.error |= NOT_OK
            return []
        return lines
    def systemd_version(self) -> str:
        """ the version line for systemd compatibility """
        return "systemd %s\n  - via systemctl.py %s" % (self._systemd_version, __version__)
    def systemd_features(self) -> str:
        """ the info line for systemd features """
        features1 = "-PAM -AUDIT -SELINUX -IMA -APPARMOR -SMACK"
        features2 = " +SYSVINIT -UTMP -LIBCRYPTSETUP -GCRYPT -GNUTLS"
        features3 = " -ACL -XZ -LZ4 -SECCOMP -BLKID -ELFUTILS -KMOD -IDN"
        return features1+features2+features3
    def version_info(self) -> List[str]:
        """ version -- show systemd version details and features """
        return [self.systemd_version(), self.systemd_features()]
    def test_float(self) -> float:
        """ return 'Unknown result type' """
        return 0. # "Unknown result type"

def print_begin(argv: List[str], args: List[str]) -> None:
    script = os.path.realpath(argv[0])
    system = USER_MODE and " --user" or " --system"
    init = INIT_MODE and " --init" or ""
    logg.info("EXEC BEGIN %s %s%s%s", script, " ".join(args), system, init)
    if ROOT and not is_good_root(ROOT):
        logg.warning("begin: the --root=x should have atleast three levels /tmp/test_123/root")
        logg.warning("begin: but --root=%s ", ROOT)

def print_begin2(args: List[str]) -> None:
    logg.debug("======= systemctl.py %s", " ".join(args))

def is_not_ok(result: bool) -> int:
    if DEBUG_PRINTRESULT:
        logg.log(HINT, "EXEC END %s", result)
    if result is False:
        return NOT_OK
    return 0

def print_str(result: Optional[str]) -> None:
    if result is None:
        if DEBUG_PRINTRESULT:
            logg.debug("    END %s", result)
        return
    print(result)
    if DEBUG_PRINTRESULT:
        result1 = result.split("\n")[0][:-20]
        if result == result1:
            logg.log(HINT, "EXEC END '%s'", result)
        else:
            logg.log(HINT, "EXEC END '%s...'", result1)
            logg.debug("    END '%s'", result)
def print_str_list(result: Union[None, List[str]]) -> None:
    if result is None:
        if DEBUG_PRINTRESULT:
            logg.debug("    END %s", result)
        return
    shown = 0
    for element in result:
        print(element)
        shown += 1
    if DEBUG_PRINTRESULT:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)
def print_str_list_list(result: Union[List[Tuple[str]], List[Tuple[str, str]], List[Tuple[str, str, str]]]) -> None:
    shown = 0
    for element in result:
        print("\t".join([str(elem) for elem in element]))
        shown += 1
    if DEBUG_PRINTRESULT:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)
def print_str_dict(result: Union[None, Dict[str, str]]) -> None:
    if result is None:
        if DEBUG_PRINTRESULT:
            logg.debug("    END %s", result)
        return
    shown = 0
    for key in sorted(result.keys()):
        element = result[key]
        print("%s=%s" % (key, element))
        shown += 1
    if DEBUG_PRINTRESULT:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)

def runcommand(command: str, *modules: str) -> int:
    systemctl = Systemctl()
    if FORCE_IPV4:
        systemctl.force_ipv4()
    elif FORCE_IPV6:
        systemctl.force_ipv6()
    exitcode = 0
    if command in ["help"]:
        print_str_list(systemctl.help_modules(*modules))
    elif command in ["cat"]:
        print_str(systemctl.cat_modules(*modules))
    elif command in ["clean"]:
        exitcode = is_not_ok(systemctl.clean_modules(*modules))
    elif command in ["command"]:
        print_str_list(systemctl.command_of_unit(*modules))
    elif command in ["daemon-reload"]:
        exitcode = is_not_ok(systemctl.daemon_reload_target())
    elif command in ["default"]:
        exitcode = is_not_ok(systemctl.default_system())
    elif command in ["default-services"]:
        print_str_list(systemctl.default_services_modules(*modules))
    elif command in ["disable"]:
        exitcode = is_not_ok(systemctl.disable_modules(*modules))
    elif command in ["enable"]:
        exitcode = is_not_ok(systemctl.enable_modules(*modules))
    elif command in ["environment"]:
        print_str_dict(systemctl.environment_of_unit(*modules))
    elif command in ["get-default"]:
        print_str(systemctl.get_default_target())
    elif command in ["get-preset"]:
        print_str(systemctl.units.get_preset_of_unit(*modules))
    elif command in ["halt"]:
        exitcode = is_not_ok(systemctl.halt_target())
    elif command in ["init"]:
        logg.fatal(" -- replace 'init' by 'start --init --now' !!!")
        exitcode = EXIT_FAILURE
    elif command in ["is-active"]:
        print_str_list(systemctl.is_active_modules(*modules))
    elif command in ["is-enabled"]:
        print_str_list(systemctl.is_enabled_modules(*modules))
    elif command in ["is-failed"]:
        print_str_list(systemctl.is_failed_modules(*modules))
    elif command in ["is-system-running"]:
        print_str(systemctl.is_system_running_info())
    elif command in ["kill"]:
        exitcode = is_not_ok(systemctl.kill_modules(*modules))
    elif command in ["list-start-dependencies"]:
        print_str_list_list(systemctl.list_start_dependencies_modules(*modules))
    elif command in ["list-dependencies"]:
        print_str_list(systemctl.list_dependencies_modules(*modules))
    elif command in ["list-unit-files"]:
        print_str_list_list(systemctl.list_unit_files_modules(*modules))
    elif command in ["list-units"]:
        print_str_list_list(systemctl.list_units_modules(*modules))
    elif command in ["listen"]:
        exitcode = is_not_ok(systemctl.listen_modules(*modules))
    elif command in ["log", "logs"]:
        exitcode = is_not_ok(systemctl.log_modules(*modules))
    elif command in ["mask"]:
        exitcode = is_not_ok(systemctl.mask_modules(*modules))
    elif command in ["preset"]:
        exitcode = is_not_ok(systemctl.preset_modules(*modules))
    elif command in ["preset-all"]:
        exitcode = is_not_ok(systemctl.preset_all_modules())
    elif command in ["reap-zombies"]:
        print_str(systemctl.reap_zombies_target())
    elif command in ["reload"]:
        exitcode = is_not_ok(systemctl.reload_modules(*modules))
    elif command in ["reload-or-restart"]:
        exitcode = is_not_ok(systemctl.reload_or_restart_modules(*modules))
    elif command in ["reload-or-try-restart"]:
        exitcode = is_not_ok(systemctl.reload_or_try_restart_modules(*modules))
    elif command in ["reset-failed"]:
        exitcode = is_not_ok(systemctl.reset_failed_modules(*modules))
    elif command in ["restart"]:
        exitcode = is_not_ok(systemctl.restart_modules(*modules))
    elif command in ["set-default"]:
        print_str(systemctl.set_default_modules(*modules))
    elif command in ["show"]:
        print_str_list(systemctl.show_modules(*modules))
    elif command in ["show-environment"]:
        print_str_list(systemctl.system_exec_env())
    elif command in ["start"]:
        exitcode = is_not_ok(systemctl.start_modules(*modules))
    elif command in ["status"]:
        print_str(systemctl.status_modules(*modules))
    elif command in ["stop"]:
        exitcode = is_not_ok(systemctl.stop_modules(*modules))
    elif command in ["try-restart"]:
        exitcode = is_not_ok(systemctl.try_restart_modules(*modules))
    elif command in ["unmask"]:
        exitcode = is_not_ok(systemctl.unmask_modules(*modules))
    elif command in ["version"]:
        print_str_list(systemctl.version_info())
    elif command in ["__cat_unit"]:
        print_str(systemctl.cat_unit(*modules))
    elif command in ["__get_active_unit"]:
        print_str(systemctl.get_active_unit(*modules))
    elif command in ["__get_description"]:
        print_str(systemctl.units.get_description(*modules))
    elif command in ["__get_status_file"]:
        print_str(systemctl.get_status_file(modules[0]))
    elif command in ["__get_pid_file"]:
        print_str(systemctl.get_pid_file(modules[0]))
    elif command in ["__disable_unit"]:
        exitcode = is_not_ok(systemctl.disable_unit(*modules))
    elif command in ["__enable_unit"]:
        exitcode = is_not_ok(systemctl.enable_unit(*modules))
    elif command in ["__is_enabled_unit"]:
        exitcode = is_not_ok(systemctl.is_enabled_unit(*modules))
    elif command in ["__killall"]:
        exitcode = is_not_ok(systemctl.killall(*modules))
    elif command in ["__kill_unit"]:
        exitcode = is_not_ok(systemctl.kill_unit(*modules))
    elif command in ["__load_preset_files"]:
        print_str_list(systemctl.units.load_preset_files(*modules))
    elif command in ["__mask_unit"]:
        exitcode = is_not_ok(systemctl.mask_unit(*modules))
    elif command in ["__read_env_file"]:
        print_str_list_list(list(systemctl.units.read_env_file(*modules)))
    elif command in ["__reload_unit"]:
        exitcode = is_not_ok(systemctl.reload_unit(*modules))
    elif command in ["__reload_or_restart_unit"]:
        exitcode = is_not_ok(systemctl.reload_or_restart_unit(*modules))
    elif command in ["__reload_or_try_restart_unit"]:
        exitcode = is_not_ok(systemctl.reload_or_try_restart_unit(*modules))
    elif command in ["__reset_failed_unit"]:
        exitcode = is_not_ok(systemctl.reset_failed_unit(*modules))
    elif command in ["__restart_unit"]:
        exitcode = is_not_ok(systemctl.restart_unit(*modules))
    elif command in ["__start_unit"]:
        exitcode = is_not_ok(systemctl.start_unit(*modules))
    elif command in ["__stop_unit"]:
        exitcode = is_not_ok(systemctl.stop_unit(*modules))
    elif command in ["__try_restart_unit"]:
        exitcode = is_not_ok(systemctl.try_restart_unit(*modules))
    elif command in ["__test_start_unit"]:
        systemctl.test_start_unit(*modules)
    elif command in ["__unmask_unit"]:
        exitcode = is_not_ok(systemctl.unmask_unit(*modules))
    elif command in ["__show_unit_items"]:
        print_str_list_list(list(systemctl.show_unit_items(*modules)))
    else:
        logg.error("Unknown operation %s", command)
        return EXIT_FAILURE
    #
    exitcode |= systemctl.error
    return exitcode

def main() -> int:
    # pylint: disable=global-statement
    global EXTRA_VARS, DO_FORCE, DO_FULL, LOG_LINES, NO_PAGER, NO_RELOAD, NO_LEGEND, NO_ASK_PASSWORD
    global DO_NOW, PRESET_MODE, DO_QUIET, ROOT, SHOW_ALL, ONLY_STATE, ONLY_TYPE, ONLY_PROPERTY, ONLY_WHAT
    global MAXTIMEOUT, INIT_MODE, EXIT_MODE, USER_MODE, FORCE_IPV4, FORCE_IPV6
    import optparse # pylint: disable=deprecated-module
    _o = optparse.OptionParser("%prog [options] command [name...]", description=__doc__.strip(),
                               epilog="use 'help' command for more information")
    _o.add_option("--version", action="store_true",
                  help="Show package version")
    _o.add_option("--system", action="store_true", default=False,
                  help="Connect to system manager (default)") # overrides --user
    _o.add_option("--user", action="store_true", default=USER_MODE,
                  help="Connect to user service manager")
    # _o.add_option("-H", "--host", metavar="[USER@]HOST",
    #     help="Operate on remote host*")
    # _o.add_option("-M", "--machine", metavar="CONTAINER",
    #     help="Operate on local container*")
    _o.add_option("-t", "--type", metavar="TYPE", action="append", dest="only_type", default=ONLY_TYPE,
                  help="List units of a particual type")
    _o.add_option("--state", metavar="STATE", action="append", dest="only_state", default=ONLY_STATE,
                  help="List units with particular LOAD or SUB or ACTIVE state")
    _o.add_option("-p", "--property", metavar="NAME", action="append", dest="only_property", default=ONLY_PROPERTY,
                  help="Show only properties by this name")
    _o.add_option("--what", metavar="TYPE", action="append", dest="only_what", default=ONLY_WHAT,
                  help="Defines the service directories to be cleaned (configuration, state, cache, logs, runtime)")
    _o.add_option("-a", "--all", action="count", dest="show_all", default=SHOW_ALL,
                  help="Show all loaded units/properties, including dead empty ones. To list all units installed on the system, use the 'list-unit-files' command instead")
    _o.add_option("-l", "--full", action="store_true", default=DO_FULL,
                  help="Don't ellipsize unit names on output (never ellipsized)")
    _o.add_option("--reverse", action="store_true",
                  help="Show reverse dependencies with 'list-dependencies' (ignored)")
    _o.add_option("--job-mode", metavar="MODE",
                  help="Specify how to deal with already queued jobs, when queuing a new job (ignored)")
    _o.add_option("--show-types", action="store_true",
                  help="When showing sockets, explicitly show their type (ignored)")
    _o.add_option("-i", "--ignore-inhibitors", action="store_true",
                  help="When shutting down or sleeping, ignore inhibitors (ignored)")
    _o.add_option("--kill-who", metavar="WHO",
                  help="Who to send signal to (ignored)")
    _o.add_option("-s", "--signal", metavar="SIG",
                  help="Which signal to send (ignored)")
    _o.add_option("--now", action="count", default=DO_NOW,
                  help="Start or stop unit in addition to enabling or disabling it")
    _o.add_option("-q", "--quiet", action="store_true", default=DO_QUIET,
                  help="Suppress output")
    _o.add_option("--no-block", action="store_true", default=False,
                  help="Do not wait until operation finished (ignored)")
    _o.add_option("--no-legend", action="store_true", default=NO_LEGEND,
                  help="Do not print a legend (column headers and hints)")
    _o.add_option("--no-wall", action="store_true", default=False,
                  help="Don't send wall message before halt/power-off/reboot (ignored)")
    _o.add_option("--no-reload", action="store_true", default=NO_RELOAD,
                  help="Don't reload daemon after en-/dis-abling unit files")
    _o.add_option("--no-ask-password", action="store_true", default=NO_ASK_PASSWORD,
                  help="Do not ask for system passwords")
    # _o.add_option("--global", action="store_true", dest="globally", default=_globally,
    #    help="Enable/disable unit files globally") # for all user logins
    # _o.add_option("--runtime", action="store_true",
    #     help="Enable unit files only temporarily until next reboot")
    _o.add_option("-f", "--force", action="store_true", default=DO_FORCE,
                  help="When enabling unit files, override existing symblinks / When shutting down, execute action immediately")
    _o.add_option("--preset-mode", metavar="TYPE", default=PRESET_MODE,
                  help="Apply only enable, only disable, or all presets [%default]")
    _o.add_option("--root", metavar="PATH", default=ROOT,
                  help="Enable unit files in the specified root directory (used for alternative root prefix)")
    _o.add_option("-n", "--lines", metavar="NUM",
                  help="Number of journal entries to show")
    _o.add_option("-o", "--output", metavar="CAT",
                  help="change journal output mode [short, ..., cat] (ignored)")
    _o.add_option("--plain", action="store_true",
                  help="Print unit dependencies as a list instead of a tree (ignored)")
    _o.add_option("--no-pager", action="store_true",
                  help="Do not pipe output into pager (mostly ignored)")
    _o.add_option("--no-warn", action="store_true",
                  help="Do not generate certain warnings (ignored)")
    #
    _o.add_option("--maxtimeout", metavar="SEC", default=MAXTIMEOUT,
                  help="..override max timeout [%default]")
    _o.add_option("-c", "--config", metavar="NAME=VAL", action="append", default=[],
                  help="..override internal variables (INITLOOPSLEEP,SYSINIT_TARGET) {%default}")
    _o.add_option("-e", "--extra-vars", "--environment", metavar="NAME=VAL", action="append", default=[],
                  help="..override settings in the syntax of 'Environment='")
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="..increase debugging information level")
    _o.add_option("-4", "--ipv4", action="store_true", default=FORCE_IPV4,
                  help="..only keep ipv4 localhost in /etc/hosts")
    _o.add_option("-6", "--ipv6", action="store_true", default=FORCE_IPV6,
                  help="..only keep ipv6 localhost in /etc/hosts")
    _o.add_option("-0", "--exit", action="count", default=0,
                  help="..exit init-process when no procs left (or -00 no services (start --now))")
    _o.add_option("-1", "--init", action="count", default=0,
                  help="..keep running as init-process (default if PID 1)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = max(0, logging.FATAL - 10 * opt.verbose))
    logg.setLevel(max(0, logging.ERROR - 10 * opt.verbose))
    #
    EXTRA_VARS = opt.extra_vars
    DO_FORCE = opt.force
    DO_FULL = opt.full
    LOG_LINES = opt.lines
    NO_PAGER = opt.no_pager
    NO_RELOAD = opt.no_reload
    NO_LEGEND = opt.no_legend
    NO_ASK_PASSWORD = opt.no_ask_password
    DO_NOW = int(opt.now)
    PRESET_MODE = opt.preset_mode
    DO_QUIET = opt.quiet
    ROOT = opt.root
    SHOW_ALL = int(opt.show_all)
    ONLY_STATE = opt.only_state
    ONLY_TYPE = opt.only_type
    ONLY_PROPERTY = opt.only_property
    ONLY_WHAT = opt.only_what
    MAXTIMEOUT = to_int(opt.maxtimeout)
    FORCE_IPV4 = opt.ipv4
    FORCE_IPV6 = opt.ipv6
    # being PID 1 (or 0) in a container will imply --init
    pid1 = os.getpid()
    INIT_MODE = int(opt.init) or [1, 0].count(pid1)
    EXIT_MODE = int(opt.exit)
    USER_MODE = opt.user
    if opt.system:
        USER_MODE = False # override --user
    elif os.geteuid() and [1, 0].count(pid1):
        USER_MODE = True # implicitly for service container
    #
    for setting in opt.config:
        nam, val = setting, "1"
        if "=" in setting:
            nam, val = setting.split("=", 1)
        elif nam.startswith("no-") or nam.startswith("NO-"):
            nam, val = nam[3:], "0"
        elif nam.startswith("No") or nam.startswith("NO"):
            nam, val = nam[2:], "0"
        if nam in globals():
            old = globals()[nam]
            if old is False or old is True:
                logg.debug("yes %s=%s", nam, val)
                globals()[nam] = (val in ("true", "True", "TRUE", "yes", "y", "Y", "YES", "1"))
                logg.debug("... DO_FULL=%s", DO_FULL)
            elif isinstance(old, float):
                logg.debug("num %s=%s", nam, val)
                globals()[nam] = float(val)
                logg.debug("... YIELD=%s", YIELD)
            elif isinstance(old, int):
                logg.debug("int %s=%s", nam, val)
                globals()[nam] = int(val)
                logg.debug("... INITLOOPSLEEP=%s", INITLOOPSLEEP)
            elif isinstance(old, stringtypes):
                logg.debug("str %s=%s", nam, val)
                globals()[nam] = val.strip()
                logg.debug("... SYSINIT_TARGET=%s", SYSINIT_TARGET)
            elif isinstance(old, list):
                logg.debug("str %s+=[%s]", nam, val)
                globals()[nam] += val.strip().split(",")
                logg.debug("... EXTRA_VARS=%s", EXTRA_VARS)
            else:
                logg.warning("(ignored) unknown target type -c '%s' : %s", nam, type(old))
        else:
            logg.warning("(ignored) unknown target config -c '%s' : no such variable", nam)
    #
    systemctl_debug_log = os_path(ROOT, expand_path(SYSTEMCTL_DEBUG_LOG, not USER_MODE))
    systemctl_extra_log = os_path(ROOT, expand_path(SYSTEMCTL_EXTRA_LOG, not USER_MODE))
    if os.access(systemctl_extra_log, os.W_OK):
        loggfile = logging.FileHandler(systemctl_extra_log)
        loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logg.addHandler(loggfile)
        logg.setLevel(max(0, logging.INFO - 10 * opt.verbose))
    if os.access(systemctl_debug_log, os.W_OK):
        loggfile = logging.FileHandler(systemctl_debug_log)
        loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logg.addHandler(loggfile)
        logg.setLevel(logging.DEBUG)
    #
    print_begin(sys.argv, args)
    #
    if opt.version:
        args = ["version"]
    if not args:
        if INIT_MODE:
            args = ["default"]
        else:
            args = ["list-units"]
    print_begin2(args)
    command = args[0]
    modules = args[1:]
    try:
        modules.remove("service")
    except ValueError:
        pass
    return runcommand(command, *modules)

if __name__ == "__main__":
    sys.exit(main())
