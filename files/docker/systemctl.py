#! /usr/bin/python2
# generated from systemctl3.py - do not change
from __future__ import print_function
import threading
import grp
import pwd
import hashlib
import select
import fcntl
import string
import datetime
import socket
import time
import signal
import sys
import os
import errno
import collections
import shlex
import fnmatch
import re
from types import GeneratorType

__copyright__ = "(C) 2016-2024 Guido U. Draheim, licensed under the EUPL"
__version__ = "1.5.8066"

# |
# |
# |
# |
# |
# |
# |
# |
# |
# |
# |
# |
# |

import logging
logg = logging.getLogger("systemctl")


if sys.version[0] == '3':
    basestring = str
    xrange = range

DEBUG_AFTER = False
DEBUG_STATUS = False
DEBUG_BOOTTIME = False
DEBUG_INITLOOP = False
DEBUG_KILLALL = False
DEBUG_FLOCK = False
DebugPrintResult = False
TestListen = False
TestAccept = False

HINT = (logging.DEBUG + logging.INFO) // 2
NOTE = (logging.WARNING + logging.INFO) // 2
DONE = (logging.WARNING + logging.ERROR) // 2
logging.addLevelName(HINT, "HINT")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(DONE, "DONE")

def logg_debug_flock(format, *args):
    if DEBUG_FLOCK:
        logg.debug(format, *args) # pragma: no cover
def logg_debug_after(format, *args):
    if DEBUG_AFTER:
        logg.debug(format, *args) # pragma: no cover

NOT_A_PROBLEM = 0   # FOUND_OK
NOT_OK = 1          # FOUND_ERROR
NOT_ACTIVE = 2      # FOUND_INACTIVE
NOT_FOUND = 4       # FOUND_UNKNOWN

# defaults for options
_extra_vars = []
_force = False
_full = False
_log_lines = 0
_no_pager = False
_now = False
_no_reload = False
_no_legend = False
_no_ask_password = False
_preset_mode = "all"
_quiet = False
_root = ""
_show_all = False
_user_mode = False
_only_what = []
_only_type = []
_only_state = []
_only_property = []

# common default paths
_system_folders = [
    "/etc/systemd/system",
    "/run/systemd/system",
    "/var/run/systemd/system",
    "/usr/local/lib/systemd/system",
    "/usr/lib/systemd/system",
    "/lib/systemd/system",
]
_user_folders = [
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
_init_folders = [
    "/etc/init.d",
    "/run/init.d",
    "/var/run/init.d",
]
_preset_folders = [
    "/etc/systemd/system-preset",
    "/run/systemd/system-preset",
    "/var/run/systemd/system-preset",
    "/usr/local/lib/systemd/system-preset",
    "/usr/lib/systemd/system-preset",
    "/lib/systemd/system-preset",
]

# standard paths
_dev_null = "/dev/null"
_dev_zero = "/dev/zero"
_etc_hosts = "/etc/hosts"
_rc3_boot_folder = "/etc/rc3.d"
_rc3_init_folder = "/etc/init.d/rc3.d"
_rc5_boot_folder = "/etc/rc5.d"
_rc5_init_folder = "/etc/init.d/rc5.d"
_proc_pid_stat = "/proc/{pid}/stat"
_proc_pid_status = "/proc/{pid}/status"
_proc_pid_cmdline= "/proc/{pid}/cmdline"
_proc_pid_dir = "/proc"
_proc_sys_uptime = "/proc/uptime"
_proc_sys_stat = "/proc/stat"

# default values
SystemCompatibilityVersion = 219
SysInitTarget = "sysinit.target"
SysInitWait = 5 # max for target
MinimumYield = 0.5
MinimumTimeoutStartSec = 4
MinimumTimeoutStopSec = 4
DefaultTimeoutStartSec = 90   # official value
DefaultTimeoutStopSec = 90    # official value
DefaultTimeoutAbortSec = 3600 # officially it none (usually larget than StopSec)
DefaultMaximumTimeout = 200   # overrides all other
DefaultRestartSec = 0.1       # official value of 100ms
DefaultStartLimitIntervalSec = 10 # official value
DefaultStartLimitBurst = 5        # official value
InitLoopSleep = 5
MaxLockWait = 0 # equals DefaultMaximumTimeout
DefaultPath = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ResetLocale = ["LANG", "LANGUAGE", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", "LC_COLLATE", "LC_MONETARY",
               "LC_MESSAGES", "LC_PAPER", "LC_NAME", "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT",
               "LC_IDENTIFICATION", "LC_ALL"]
LocaleConf="/etc/locale.conf"
DefaultListenBacklog=2

ExitWhenNoMoreServices = False
ExitWhenNoMoreProcs = False
DefaultUnit = os.environ.get("SYSTEMD_DEFAULT_UNIT", "default.target") # systemd.exe --unit=default.target
DefaultTarget = os.environ.get("SYSTEMD_DEFAULT_TARGET", "multi-user.target") # DefaultUnit fallback
# LogLevel = os.environ.get("SYSTEMD_LOG_LEVEL", "info") # systemd.exe --log-level
# LogTarget = os.environ.get("SYSTEMD_LOG_TARGET", "journal-or-kmsg") # systemd.exe --log-target
# LogLocation = os.environ.get("SYSTEMD_LOG_LOCATION", "no") # systemd.exe --log-location
# ShowStatus = os.environ.get("SYSTEMD_SHOW_STATUS", "auto") # systemd.exe --show-status
DefaultStandardInput=os.environ.get("SYSTEMD_STANDARD_INPUT", "null")
DefaultStandardOutput=os.environ.get("SYSTEMD_STANDARD_OUTPUT", "journal") # systemd.exe --default-standard-output
DefaultStandardError=os.environ.get("SYSTEMD_STANDARD_ERROR", "inherit") # systemd.exe --default-standard-error

EXEC_SPAWN = False
EXEC_DUP2 = True
REMOVE_LOCK_FILE = False
BOOT_PID_MIN = 0
BOOT_PID_MAX = -9
PROC_MAX_DEPTH = 100
EXPAND_VARS_MAXDEPTH = 20
EXPAND_KEEP_VARS = True
RESTART_FAILED_UNITS = True
ACTIVE_IF_ENABLED=False

TAIL_CMDS = ["/bin/tail", "/usr/bin/tail", "/usr/local/bin/tail"]
LESS_CMDS = ["/bin/less", "/usr/bin/less", "/usr/local/bin/less"]
CAT_CMDS = ["/bin/cat", "/usr/bin/cat", "/usr/local/bin/cat"]

# The systemd default was NOTIFY_SOCKET="/var/run/systemd/notify"
_notify_socket_folder = "{RUN}/systemd" # alias /run/systemd
_journal_log_folder = "{LOG}/journal"

SYSTEMCTL_DEBUG_LOG = "{LOG}/systemctl.debug.log"
SYSTEMCTL_EXTRA_LOG = "{LOG}/systemctl.log"

_default_targets = ["poweroff.target", "rescue.target", "sysinit.target", "basic.target", "multi-user.target", "graphical.target", "reboot.target"]
_feature_targets = ["network.target", "remote-fs.target", "local-fs.target", "timers.target", "nfs-client.target"]
_all_common_targets = ["default.target"] + _default_targets + _feature_targets

# inside a docker we pretend the following
_all_common_enabled = ["default.target", "multi-user.target", "remote-fs.target"]
_all_common_disabled = ["graphical.target", "resue.target", "nfs-client.target"]

target_requires = {"graphical.target": "multi-user.target", "multi-user.target": "basic.target", "basic.target": "sockets.target"}

_runlevel_mappings = {} # the official list
_runlevel_mappings["0"] = "poweroff.target"
_runlevel_mappings["1"] = "rescue.target"
_runlevel_mappings["2"] = "multi-user.target"
_runlevel_mappings["3"] = "multi-user.target"
_runlevel_mappings["4"] = "multi-user.target"
_runlevel_mappings["5"] = "graphical.target"
_runlevel_mappings["6"] = "reboot.target"

_sysv_mappings = {} # by rule of thumb
_sysv_mappings["$local_fs"] = "local-fs.target"
_sysv_mappings["$network"] = "network.target"
_sysv_mappings["$remote_fs"] = "remote-fs.target"
_sysv_mappings["$timer"] = "timers.target"


# sections from conf
Unit = "Unit"
Service = "Service"
Socket = "Socket"
Install = "Install"

# https://tldp.org/LDP/abs/html/exitcodes.html
# https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

def strINET(value):
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

def strYes(value):
    if value is True:
        return "yes"
    if not value:
        return "no"
    return str(value)
def strE(part):
    if not part:
        return ""
    return str(part)
def strQ(part):
    if part is None:
        return ""
    if isinstance(part, int):
        return str(part)
    return "'%s'" % part
def shell_cmd(cmd):
    return " ".join([strQ(part) for part in cmd])
def to_intN(value, default = None):
    if not value:
        return default
    try:
        return int(value)
    except:
        return default
def to_int(value, default = 0):
    try:
        return int(value)
    except:
        return default
def to_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return str(value or "").split(",")
def commalist(value):
    return list(_commalist(value))
def _commalist(value):
    for val in value:
        if not val:
            continue
        for elem in val.strip().split(","):
            yield elem
def int_mode(value):
    try: return int(value, 8)
    except: return None # pragma: no cover
def unit_of(module):
    if "." not in module:
        return module + ".service"
    return module
def o22(part):
    if isinstance(part, basestring):
        if len(part) <= 22:
            return part
        return part[:5] + "..." + part[-14:]
    return part # pragma: no cover (is always str)
def o44(part):
    if isinstance(part, basestring):
        if len(part) <= 44:
            return part
        return part[:10] + "..." + part[-31:]
    return part # pragma: no cover (is always str)
def o77(part):
    if isinstance(part, basestring):
        if len(part) <= 77:
            return part
        return part[:20] + "..." + part[-54:]
    return part # pragma: no cover (is always str)
def path44(filename):
    if not filename:
        return "<none>"
    x = filename.find("/", 8)
    if len(filename) <= 40:
        if "/" not in filename:
            return ".../" + filename
    elif len(filename) <= 44:
        return filename
    if 0 < x and x < 14:
        out = filename[:x+1]
        out += "..."
    else:
        out = filename[:10]
        out += "..."
    remain = len(filename) - len(out)
    y = filename.find("/", remain)
    if 0 < y and y < remain+5:
        out += filename[y:]
    else:
        out += filename[remain:]
    return out

def unit_name_escape(text):
    # https://www.freedesktop.org/software/systemd/man/systemd.unit.html#id-1.6
    esc = re.sub("([^a-z-AZ.-/])", lambda m: "\\x%02x" % ord(m.group(1)[0]), text)
    return esc.replace("/", "-")
def unit_name_unescape(text):
    esc = text.replace("-", "/")
    return re.sub("\\\\x(..)", lambda m: "%c" % chr(int(m.group(1), 16)), esc)

def is_good_root(root):
    if not root:
        return True
    return root.strip(os.path.sep).count(os.path.sep) > 1
def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    if is_good_root(root) and path.startswith(root):
        return path
    while path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(root, path)
def path_replace_extension(path, old, new):
    if path.endswith(old):
        path = path[:-len(old)]
    return path + new
def get_exist_path(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def get_PAGER():
    PAGER = os.environ.get("PAGER", "less")
    pager = os.environ.get("SYSTEMD_PAGER", "{PAGER}").format(**locals())
    options = os.environ.get("SYSTEMD_LESS", "FRSXMK") # see 'man timedatectl'
    if not pager: pager = "cat"
    if "less" in pager and options:
        return [pager, "-" + options]
    return [pager]

def os_getlogin():
    """ NOT using os.getlogin() """
    return pwd.getpwuid(os.geteuid()).pw_name

def get_runtime_dir():
    explicit = os.environ.get("XDG_RUNTIME_DIR", "")
    if explicit: return explicit
    user = os_getlogin()
    return "/tmp/run-"+user
def get_RUN(root = False):
    tmp_var = get_TMP(root)
    if _root:
        tmp_var = _root
    if root:
        for p in ("/run", "/var/run", "{tmp_var}/run"):
            path = p.format(**locals())
            if os.path.isdir(path) and os.access(path, os.W_OK):
                return path
        os.makedirs(path) # "/tmp/run"
        return path
    else:
        uid = get_USER_ID(root)
        for p in ("/run/user/{uid}", "/var/run/user/{uid}", "{tmp_var}/run-{uid}"):
            path = p.format(**locals())
            if os.path.isdir(path) and os.access(path, os.W_OK):
                return path
        os.makedirs(path, 0o700) # "/tmp/run/user/{uid}"
        return path
def get_PID_DIR(root = False):
    if root:
        return get_RUN(root)
    else:
        return os.path.join(get_RUN(root), "run") # compat with older systemctl.py

def get_home():
    if False: # pragma: no cover
        explicit = os.environ.get("HOME", "")   # >> On Unix, an initial ~ (tilde) is replaced by the
        if explicit: return explicit            # environment variable HOME if it is set; otherwise
        uid = os.geteuid()                      # the current users home directory is looked up in the
        #                                       # password directory through the built-in module pwd.
        return pwd.getpwuid(uid).pw_name        # An initial ~user i looked up directly in the
    return os.path.expanduser("~")              # password directory. << from docs(os.path.expanduser)
def get_HOME(root = False):
    if root: return "/root"
    return get_home()
def get_USER_ID(root = False):
    ID = 0
    if root: return ID
    return os.geteuid()
def get_USER(root = False):
    if root: return "root"
    uid = os.geteuid()
    return pwd.getpwuid(uid).pw_name
def get_GROUP_ID(root = False):
    ID = 0
    if root: return ID
    return os.getegid()
def get_GROUP(root = False):
    if root: return "root"
    gid = os.getegid()
    return grp.getgrgid(gid).gr_name
def get_TMP(root = False):
    TMP = "/tmp"
    if root: return TMP
    return os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", TMP)))
def get_VARTMP(root = False):
    VARTMP = "/var/tmp"
    if root: return VARTMP
    return os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", VARTMP)))
def get_SHELL(root = False):
    SHELL = "/bin/sh"
    if root: return SHELL
    return os.environ.get("SHELL", SHELL)
def get_RUNTIME_DIR(root = False):
    RUN = "/run"
    if root: return RUN
    return os.environ.get("XDG_RUNTIME_DIR", get_runtime_dir())
def get_CONFIG_HOME(root = False):
    CONFIG = "/etc"
    if root: return CONFIG
    HOME = get_HOME(root)
    return os.environ.get("XDG_CONFIG_HOME", HOME + "/.config")
def get_CACHE_HOME(root = False):
    CACHE = "/var/cache"
    if root: return CACHE
    HOME = get_HOME(root)
    return os.environ.get("XDG_CACHE_HOME", HOME + "/.cache")
def get_DATA_HOME(root = False):
    SHARE = "/usr/share"
    if root: return SHARE
    HOME = get_HOME(root)
    return os.environ.get("XDG_DATA_HOME", HOME + "/.local/share")
def get_LOG_DIR(root = False):
    LOGDIR = "/var/log"
    if root: return LOGDIR
    CONFIG = get_CONFIG_HOME(root)
    return os.path.join(CONFIG, "log")
def get_VARLIB_HOME(root = False):
    VARLIB = "/var/lib"
    if root: return VARLIB
    CONFIG = get_CONFIG_HOME(root)
    return CONFIG
def expand_path(path, root = False):
    HOME = get_HOME(root)
    RUN = get_RUN(root)
    LOG = get_LOG_DIR(root)
    XDG_DATA_HOME=get_DATA_HOME(root)
    XDG_CONFIG_HOME=get_CONFIG_HOME(root)
    XDG_RUNTIME_DIR=get_RUNTIME_DIR(root)
    return os.path.expanduser(path.replace("${", "{").format(**locals()))

def shutil_chown(path, user, group):
    if user or group:
        uid, gid = -1, -1
        if user:
            uid = pwd.getpwnam(user).pw_uid
            gid = pwd.getpwnam(user).pw_gid
        if group:
            gid = grp.getgrnam(group).gr_gid
        os.chown(path, uid, gid)
def shutil_fchown(fileno, user, group):
    if user or group:
        uid, gid = -1, -1
        if user:
            uid = pwd.getpwnam(user).pw_uid
            gid = pwd.getpwnam(user).pw_gid
        if group:
            gid = grp.getgrnam(group).gr_gid
        os.fchown(fileno, uid, gid)
def shutil_setuid(user = None, group = None, xgroups = None):
    """ set fork-child uid/gid (returns pw-info env-settings)"""
    if group:
        gid = grp.getgrnam(group).gr_gid
        os.setgid(gid)
        logg.debug("setgid %s for %s", gid, strQ(group))
        groups = [gid]
        try:
            os.setgroups(groups)
            logg.debug("setgroups %s < (%s)", groups, group)
        except OSError as e: # pragma: no cover (it will occur in non-root mode anyway)
            logg.debug("setgroups %s < (%s) : %s", groups, group, e)
    if user:
        pw = pwd.getpwnam(user)
        gid = pw.pw_gid
        gname = grp.getgrgid(gid).gr_name
        if not group:
            os.setgid(gid)
            logg.debug("setgid %s for user %s", gid, strQ(user))
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
            logg.debug("setgroups %s > %s : %s", groups, groupnames, e)
        uid = pw.pw_uid
        os.setuid(uid)
        logg.debug("setuid %s for user %s", uid, strQ(user))
        home = pw.pw_dir
        shell = pw.pw_shell
        logname = pw.pw_name
        return {"USER": user, "LOGNAME": logname, "HOME": home, "SHELL": shell}
    return {}

def shutil_truncate(filename):
    """ truncates the file (or creates a new empty file)"""
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    f.write("")
    f.close()

# http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    if pid is None: # pragma: no cover (is never null)
        return False
    return _pid_exists(int(pid))
def _pid_exists(pid):
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
def pid_zombie(pid):
    """ may be a pid exists but it is only a zombie """
    if pid is None:
        return False
    return _pid_zombie(int(pid))
def _pid_zombie(pid):
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
        for line in open(check):
            if line.startswith("State:"):
                return "Z" in line
    except IOError as e:
        if e.errno != errno.ENOENT:
            logg.error("%s (%s): %s", check, e.errno, e)
        return False
    return False

def checkprefix(cmd):
    prefix = ""
    for i, c in enumerate(cmd):
        if c in "-+!@:":
            prefix = prefix + c
        else:
            newcmd = cmd[i:]
            return prefix, newcmd
    return prefix, ""

ExecMode = collections.namedtuple("ExecMode", ["mode", "check", "nouser", "noexpand", "argv0"])
def exec_path(cmd):
    """ Hint: exec_path values are usually not moved by --root (while load_path are)"""
    prefix, newcmd = checkprefix(cmd)
    check = "-" not in prefix
    nouser = "+" in prefix or "!" in prefix
    noexpand = ":" in prefix
    argv0 = "@" in prefix
    mode = ExecMode(prefix, check, nouser, noexpand, argv0)
    return mode, newcmd
LoadMode = collections.namedtuple("LoadMode", ["mode", "check"])
def load_path(ref):
    """ Hint: load_path values are usually moved by --root (while exec_path are not)"""
    prefix, filename = "", ref
    while filename.startswith("-"):
        prefix = prefix + filename[0]
        filename = filename[1:]
    check = "-" not in prefix
    mode = LoadMode(prefix, check)
    return mode, filename

# https://github.com/phusion/baseimage-docker/blob/rel-0.9.16/image/bin/my_init
def ignore_signals_and_raise_keyboard_interrupt(signame):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    raise KeyboardInterrupt(signame)

_default_dict_type = collections.OrderedDict
_default_conf_type = collections.OrderedDict

class SystemctlConfData:
    """ A *.service files has a structure similar to an *.ini file so
        that data is structured in sections and values. Actually the
        values are lists - the raw data is in .getlist(). Otherwise
        .get() will return the first line that was encountered. """
    # |
    # |
    # |
    # |
    # |
    # |
    def __init__(self, defaults=None, dict_type=None, conf_type=None, allow_no_value=False):
        self._defaults = defaults or {}
        self._conf_type = conf_type or _default_conf_type
        self._dict_type = dict_type or _default_dict_type
        self._allow_no_value = allow_no_value
        self._conf = self._conf_type()
        self._files = []
    def defaults(self):
        return self._defaults
    def sections(self):
        return list(self._conf.keys())
    def add_section(self, section):
        if section not in self._conf:
            self._conf[section] = self._dict_type()
    def has_section(self, section):
        return section in self._conf
    def has_option(self, section, option):
        if section not in self._conf:
            return False
        return option in self._conf[section]
    def set(self, section, option, value):
        if section not in self._conf:
            self._conf[section] = self._dict_type()
        if value is None:
            self._conf[section][option] = []
        elif option not in self._conf[section]:
            self._conf[section][option] = [value]
        else:
            self._conf[section][option].append(value)
    def getstr(self, section, option, default = None, allow_no_value = False):
        done = self.get(section, option, strE(default), allow_no_value)
        if done is None: return strE(default)
        return done
    def get(self, section, option, default = None, allow_no_value = False):
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._conf:
            if default is not None:
                return default
            if allow_no_value:
                return None
            logg.warning("section {} does not exist".format(section))
            logg.warning("  have {}".format(self.sections()))
            raise AttributeError("section {} does not exist".format(section))
        if option not in self._conf[section]:
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError("option {} in {} does not exist".format(option, section))
        if not self._conf[section][option]: # i.e. an empty list
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError("option {} in {} is None".format(option, section))
        return self._conf[section][option][0] # the first line in the list of configs
    def getlist(self, section, option, default = None, allow_no_value = False):
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._conf:
            if default is not None:
                return default
            if allow_no_value:
                return []
            logg.warning("section {} does not exist".format(section))
            logg.warning("  have {}".format(self.sections()))
            raise AttributeError("section {} does not exist".format(section))
        if option not in self._conf[section]:
            if default is not None:
                return default
            if allow_no_value:
                return []
            raise AttributeError("option {} in {} does not exist".format(option, section))
        return self._conf[section][option] # returns a list, possibly empty
    def filenames(self):
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
    def read(self, filename):
        return self.read_sysd(filename)
    def read_sysd(self, filename):
        initscript = False
        initinfo = False
        section = "GLOBAL"
        nextline = False
        name, text = "", ""
        if os.path.isfile(filename):
            self._files.append(filename)
        for orig_line in open(filename):
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
                    raise Exception("tried to include file that doesn't exist: %s" % includefile)
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
                raise Exception("bad ini line")
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
    def read_sysv(self, filename):
        """ an LSB header is scanned and converted to (almost)
            equivalent settings of a SystemD ini-style input """
        initscript = False
        initinfo = False
        section = "GLOBAL"
        if os.path.isfile(filename):
            self._files.append(filename)
        for orig_line in open(filename):
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
    def systemd_sysv_generator(self, filename):
        """ see systemd-sysv-generator(8) """
        self.set(Unit, "SourcePath", filename)
        description = self.get("init.d", "Description", "")
        if description:
            self.set(Unit, "Description", description)
        check = self.get("init.d", "Required-Start", "")
        if check:
            for item in check.split(" "):
                if item.strip() in _sysv_mappings:
                    self.set(Unit, "Requires", _sysv_mappings[item.strip()])
        provides = self.get("init.d", "Provides", "")
        if provides:
            self.set(Install, "Alias", provides)
        # if already in multi-user.target then start it there.
        runlevels = self.getstr("init.d", "Default-Start", "3 5")
        for item in runlevels.split(" "):
            if item.strip() in _runlevel_mappings:
                self.set(Install, "WantedBy", _runlevel_mappings[item.strip()])
        self.set(Service, "Restart", "no")
        self.set(Service, "TimeoutSec", strE(DefaultMaximumTimeout))
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
    def __init__(self, conf, sock, skip = False):
        self.conf = conf
        self.sock = sock
        self.skip = skip
    def fileno(self):
        return self.sock.fileno()
    def listen(self, backlog = None):
        if backlog is None:
            backlog = DefaultListenBacklog
        dgram = (self.sock.type == socket.SOCK_DGRAM)
        if not dgram and not self.skip:
            self.sock.listen(backlog)
    def name(self):
        return self.conf.name()
    def addr(self):
        stream = self.conf.get(Socket, "ListenStream", "")
        dgram = self.conf.get(Socket, "ListenDatagram", "")
        return stream or dgram
    def close(self):
        self.sock.close()

class SystemctlConf:
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    def __init__(self, data, module = None):
        self.data = data # UnitConfParser
        self.env = {}
        self.status = None
        self.masked = None
        self.module = module
        self.nonloaded_path = ""
        self.drop_in_files = {}
        self._root = _root
        self._user_mode = _user_mode
    def root_mode(self):
        return not self._user_mode
    def loaded(self):
        files = self.data.filenames()
        if self.masked:
            return "masked"
        if len(files):
            return "loaded"
        return ""
    def filename(self):
        """ returns the last filename that was parsed """
        files = self.data.filenames()
        if files:
            return files[0]
        return None
    def overrides(self):
        """ drop-in files are loaded alphabetically by name, not by full path """
        return [self.drop_in_files[name] for name in sorted(self.drop_in_files)]
    def name(self):
        """ the unit id or defaults to the file name """
        name = self.module or ""
        filename = self.filename()
        if filename:
            name = os.path.basename(filename)
        return self.module or name
    def set(self, section, name, value):
        return self.data.set(section, name, value)
    def get(self, section, name, default, allow_no_value = False):
        return self.data.getstr(section, name, default, allow_no_value)
    def getlist(self, section, name, default = None, allow_no_value = False):
        return self.data.getlist(section, name, default or [], allow_no_value)
    def getbool(self, section, name, default = None):
        value = self.data.get(section, name, default or "no")
        if value:
            if value[0] in "TtYy123456789":
                return True
        return False

class PresetFile:
    # |
    # |
    def __init__(self):
        self._files = []
        self._lines = []
    def filename(self):
        """ returns the last filename that was parsed """
        if self._files:
            return self._files[-1]
        return None
    def read(self, filename):
        self._files.append(filename)
        for line in open(filename):
            self._lines.append(line.strip())
        return self
    def get_preset(self, unit):
        for line in self._lines:
            m = re.match(r"(enable|disable)\s+(\S+)", line)
            if m:
                status, pattern = m.group(1), m.group(2)
                if fnmatch.fnmatchcase(unit, pattern):
                    logg.debug("%s %s => %s %s", status, pattern, unit, strQ(self.filename()))
                    return status
        return None

## with waitlock(conf): self.start()
class waitlock:
    # |
    # |
    # |
    def __init__(self, conf):
        self.conf = conf # currently unused
        self.opened = -1
        self.lockfolder = expand_path(_notify_socket_folder, conf.root_mode())
        try:
            folder = self.lockfolder
            if not os.path.isdir(folder):
                os.makedirs(folder)
        except Exception as e:
            logg.warning("oops, %s", e)
    def lockfile(self):
        unit = ""
        if self.conf:
            unit = self.conf.name()
        return os.path.join(self.lockfolder, str(unit or "global") + ".lock")
    def __enter__(self):
        try:
            lockfile = self.lockfile()
            lockname = os.path.basename(lockfile)
            self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
            for attempt in xrange(int(MaxLockWait or DefaultMaximumTimeout)):
                try:
                    logg_debug_flock("[%s] %s. trying %s _______ ", os.getpid(), attempt, lockname)
                    fcntl.flock(self.opened, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    st = os.fstat(self.opened)
                    if not st.st_nlink:
                        logg_debug_flock("[%s] %s. %s got deleted, trying again", os.getpid(), attempt, lockname)
                        os.close(self.opened)
                        self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
                        continue
                    content = "{ 'systemctl': %s, 'lock': '%s' }\n" % (os.getpid(), lockname)
                    os.write(self.opened, content.encode("utf-8"))
                    logg_debug_flock("[%s] %s. holding lock on %s", os.getpid(), attempt, lockname)
                    return True
                except IOError as e:
                    whom = os.read(self.opened, 4096)
                    os.lseek(self.opened, 0, os.SEEK_SET)
                    logg.info("[%s] %s. systemctl locked by %s", os.getpid(), attempt, whom.rstrip())
                    time.sleep(1) # until MaxLockWait
                    continue
            logg.error("[%s] not able to get the lock to %s", os.getpid(), lockname)
        except Exception as e:
            logg.warning("[%s] oops %s, %s", os.getpid(), str(type(e)), e)
        # TODO# raise Exception("no lock for %s", self.unit or "global")
        return False
    def __exit__(self, type, value, traceback):
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
        except Exception as e:
            logg.warning("oops, %s", e)

SystemctlWaitPID = collections.namedtuple("SystemctlWaitPID", ["pid", "returncode", "signal"])

def must_have_failed(waitpid, cmd):
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

def subprocess_waitpid(pid):
    run_pid, run_stat = os.waitpid(pid, 0)
    return SystemctlWaitPID(run_pid, os.WEXITSTATUS(run_stat), os.WTERMSIG(run_stat))
def subprocess_testpid(pid):
    run_pid, run_stat = os.waitpid(pid, os.WNOHANG)
    if run_pid:
        return SystemctlWaitPID(run_pid, os.WEXITSTATUS(run_stat), os.WTERMSIG(run_stat))
    else:
        return SystemctlWaitPID(pid, None, 0)

SystemctlUnitName = collections.namedtuple("SystemctlUnitName", ["fullname", "name", "prefix", "instance", "suffix", "component"])

def parse_unit(fullname): # -> object(prefix, instance, suffix, ...., name, component)
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

def time_to_seconds(text, maximum):
    value = 0.
    for part in str(text).split(" "):
        item = part.strip()
        if item == "infinity":
            return maximum
        if item.endswith("m"):
            try: value += 60 * int(item[:-1])
            except: pass # pragma: no cover
        if item.endswith("min"):
            try: value += 60 * int(item[:-3])
            except: pass # pragma: no cover
        elif item.endswith("ms"):
            try: value += int(item[:-2]) / 1000.
            except: pass # pragma: no cover
        elif item.endswith("s"):
            try: value += int(item[:-1])
            except: pass # pragma: no cover
        elif item:
            try: value += int(item)
            except: pass # pragma: no cover
    if value > maximum:
        return maximum
    if not value and text.strip() == "0":
        return 0.
    if not value:
        return 1.
    return value
def seconds_to_time(seconds):
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

def getBefore(conf):
    result = []
    beforelist = conf.getlist(Unit, "Before", [])
    for befores in beforelist:
        for before in befores.split(" "):
            name = before.strip()
            if name and name not in result:
                result.append(name)
    return result

def getAfter(conf):
    result = []
    afterlist = conf.getlist(Unit, "After", [])
    for afters in afterlist:
        for after in afters.split(" "):
            name = after.strip()
            if name and name not in result:
                result.append(name)
    return result

def compareAfter(confA, confB):
    idA = confA.name()
    idB = confB.name()
    for after in getAfter(confA):
        if after == idB:
            logg.debug("%s After %s", idA, idB)
            return -1
    for after in getAfter(confB):
        if after == idA:
            logg.debug("%s After %s", idB, idA)
            return 1
    for before in getBefore(confA):
        if before == idB:
            logg.debug("%s Before %s", idA, idB)
            return 1
    for before in getBefore(confB):
        if before == idA:
            logg.debug("%s Before %s", idB, idA)
            return -1
    return 0

def conf_sortedAfter(conflist, cmp = compareAfter):
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
        def __init__(self, rank, conf):
            self.rank = rank
            self.conf = conf
    sortlist = [SortTuple(0, conf) for conf in conflist]
    for check in xrange(len(sortlist)): # maxrank = len(sortlist)
        changed = 0
        for A in xrange(len(sortlist)):
            for B in xrange(len(sortlist)):
                if A != B:
                    itemA = sortlist[A]
                    itemB = sortlist[B]
                    before = compareAfter(itemA.conf, itemB.conf)
                    if before > 0 and itemA.rank <= itemB.rank:
                        logg_debug_after("  %-30s before %s", itemA.conf.name(), itemB.conf.name())
                        itemA.rank = itemB.rank + 1
                        changed += 1
                    if before < 0 and itemB.rank <= itemA.rank:
                        logg_debug_after("  %-30s before %s", itemB.conf.name(), itemA.conf.name())
                        itemB.rank = itemA.rank + 1
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

class SystemctlListenThread(threading.Thread):
    def __init__(self, systemctl):
        threading.Thread.__init__(self, name="listen")
        self.systemctl = systemctl
        self.stopped = threading.Event()
    def stop(self):
        self.stopped.set()
    def run(self):
        READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
        READ_WRITE = READ_ONLY | select.POLLOUT
        me = os.getpid()
        if DEBUG_INITLOOP: # pragma: no cover
            logg.info("[%s] listen: new thread", me)
        if not self.systemctl._sockets:
            return
        if DEBUG_INITLOOP: # pragma: no cover
            logg.info("[%s] listen: start thread", me)
        listen = select.poll()
        for sock in self.systemctl._sockets.values():
            listen.register(sock, READ_ONLY)
            sock.listen()
            logg.debug("[%s] listen: %s :%s", me, sock.name(), sock.addr())
        timestamp = time.time()
        while not self.stopped.is_set():
            try:
                sleep_sec = InitLoopSleep - (time.time() - timestamp)
                if sleep_sec < MinimumYield:
                    sleep_sec = MinimumYield
                sleeping = sleep_sec
                while sleeping > 2:
                    time.sleep(1) # accept signals atleast every second
                    sleeping = InitLoopSleep - (time.time() - timestamp)
                    if sleeping < MinimumYield:
                        sleeping = MinimumYield
                        break
                time.sleep(sleeping) # remainder waits less that 2 seconds
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[%s] listen: poll", me)
                accepting = listen.poll(100) # milliseconds
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("[%s] listen: poll (%s)", me, len(accepting))
                for sock_fileno, event in accepting:
                    for sock in self.systemctl._sockets.values():
                        if sock.fileno() == sock_fileno:
                            if not self.stopped.is_set():
                                if self.systemctl.loop.acquire():
                                    logg.debug("[%s] listen: accept %s :%s", me, sock.name(), sock_fileno)
                                    self.systemctl.do_accept_socket_from(sock.conf, sock.sock)
            except Exception as e:
                logg.info("[%s] listen: interrupted - exception %s", me, e)
                raise
        for sock in self.systemctl._sockets.values():
            try:
                listen.unregister(sock)
                sock.close()
            except Exception as e:
                logg.warning("[%s] listen: close socket: %s", me, e)
        return

class Systemctl:
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    # |
    def __init__(self):
        self.error = NOT_A_PROBLEM # program exitcode or process returncode
        # from command line options or the defaults
        self._extra_vars = _extra_vars
        self._force = _force
        self._full = _full
        self._init = _init
        self._no_ask_password = _no_ask_password
        self._no_legend = _no_legend
        self._now = _now
        self._preset_mode = _preset_mode
        self._quiet = _quiet
        self._root = _root
        self._show_all = _show_all
        self._only_what = commalist(_only_what) or [""]
        self._only_property = commalist(_only_property)
        self._only_state = commalist(_only_state)
        self._only_type = commalist(_only_type)
        # some common constants that may be changed
        self._systemd_version = SystemCompatibilityVersion
        self._journal_log_folder = _journal_log_folder
        # and the actual internal runtime state
        self._loaded_file_sysv = {} # /etc/init.d/name => config data
        self._loaded_file_sysd = {} # /etc/systemd/system/name.service => config data
        self._file_for_unit_sysv = None # name.service => /etc/init.d/name
        self._file_for_unit_sysd = None # name.service => /etc/systemd/system/name.service
        self._preset_file_list = None # /etc/systemd/system-preset/* => file content
        self._default_target = DefaultTarget
        self._sysinit_target = None # stores a UnitConf()
        self.doExitWhenNoMoreProcs = ExitWhenNoMoreProcs or False
        self.doExitWhenNoMoreServices = ExitWhenNoMoreServices or False
        self._user_mode = _user_mode
        self._user_getlogin = os_getlogin()
        self._log_file = {} # init-loop
        self._log_hold = {} # init-loop
        self._boottime = None # cache self.get_boottime()
        self._SYSTEMD_UNIT_PATH = None
        self._SYSTEMD_SYSVINIT_PATH = None
        self._SYSTEMD_PRESET_PATH = None
        self._restarted_unit = {}
        self._restart_failed_units = {}
        self._sockets = {}
        self.loop = threading.Lock()
    def user(self):
        return self._user_getlogin
    def user_mode(self):
        return self._user_mode
    def user_folder(self):
        for folder in self.user_folders():
            if folder: return folder
        raise Exception("did not find any systemd/user folder")
    def system_folder(self):
        for folder in self.system_folders():
            if folder: return folder
        raise Exception("did not find any systemd/system folder")
    def preset_folders(self):
        SYSTEMD_PRESET_PATH = self.get_SYSTEMD_PRESET_PATH()
        for path in SYSTEMD_PRESET_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_PRESET_PATH.endswith(":"):
            for p in _preset_folders:
                yield expand_path(p.strip())
    def init_folders(self):
        SYSTEMD_SYSVINIT_PATH = self.get_SYSTEMD_SYSVINIT_PATH()
        for path in SYSTEMD_SYSVINIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_SYSVINIT_PATH.endswith(":"):
            for p in _init_folders:
                yield expand_path(p.strip())
    def user_folders(self):
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH()
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            for p in _user_folders:
                yield expand_path(p.strip())
    def system_folders(self):
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH()
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            for p in _system_folders:
                yield expand_path(p.strip())
    def get_SYSTEMD_UNIT_PATH(self):
        if self._SYSTEMD_UNIT_PATH is None:
            self._SYSTEMD_UNIT_PATH = os.environ.get("SYSTEMD_UNIT_PATH", ":")
        assert self._SYSTEMD_UNIT_PATH is not None
        return self._SYSTEMD_UNIT_PATH
    def get_SYSTEMD_SYSVINIT_PATH(self):
        if self._SYSTEMD_SYSVINIT_PATH is None:
            self._SYSTEMD_SYSVINIT_PATH = os.environ.get("SYSTEMD_SYSVINIT_PATH", ":")
        assert self._SYSTEMD_SYSVINIT_PATH is not None
        return self._SYSTEMD_SYSVINIT_PATH
    def get_SYSTEMD_PRESET_PATH(self):
        if self._SYSTEMD_PRESET_PATH is None:
            self._SYSTEMD_PRESET_PATH = os.environ.get("SYSTEMD_PRESET_PATH", ":")
        assert self._SYSTEMD_PRESET_PATH is not None
        return self._SYSTEMD_PRESET_PATH
    def sysd_folders(self):
        """ if --user then these folders are preferred """
        if self.user_mode():
            for folder in self.user_folders():
                yield folder
        if True:
            for folder in self.system_folders():
                yield folder
    def scan_unit_sysd_files(self, module = None): # -> [ unit-names,... ]
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
    def scan_unit_sysv_files(self, module = None): # -> [ unit-names,... ]
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
    def unit_sysd_file(self, module = None): # -> filename?
        """ file path for the given module (systemd) """
        self.scan_unit_sysd_files()
        assert self._file_for_unit_sysd is not None
        if module and module in self._file_for_unit_sysd:
            return self._file_for_unit_sysd[module]
        if module and unit_of(module) in self._file_for_unit_sysd:
            return self._file_for_unit_sysd[unit_of(module)]
        return None
    def unit_sysv_file(self, module = None): # -> filename?
        """ file path for the given module (sysv) """
        self.scan_unit_sysv_files()
        assert self._file_for_unit_sysv is not None
        if module and module in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[module]
        if module and unit_of(module) in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[unit_of(module)]
        return None
    def unit_file(self, module = None): # -> filename?
        """ file path for the given module (sysv or systemd) """
        path = self.unit_sysd_file(module)
        if path is not None: return path
        path = self.unit_sysv_file(module)
        if path is not None: return path
        return None
    def is_sysv_file(self, filename):
        """ for routines that have a special treatment for init.d services """
        self.unit_file() # scan all
        assert self._file_for_unit_sysd is not None
        assert self._file_for_unit_sysv is not None
        if not filename: return None
        if filename in self._file_for_unit_sysd.values(): return False
        if filename in self._file_for_unit_sysv.values(): return True
        return None # not True
    def is_user_conf(self, conf):
        if not conf: # pragma: no cover (is never null)
            return False
        filename = conf.nonloaded_path or conf.filename()
        if filename and "/user/" in filename:
            return True
        return False
    def not_user_conf(self, conf):
        """ conf can not be started as user service (when --user)"""
        if conf is None: # pragma: no cover (is never null)
            return True
        if not self.user_mode():
            logg.debug("%s no --user mode >> accept", strQ(conf.filename()))
            return False
        if self.is_user_conf(conf):
            logg.debug("%s is /user/ conf >> accept", strQ(conf.filename()))
            return False
        # to allow for 'docker run -u user' with system services
        user = self.get_User(conf)
        if user and user == self.user():
            logg.debug("%s with User=%s >> accept", strQ(conf.filename()), user)
            return False
        return True
    def find_drop_in_files(self, unit):
        """ search for some.service.d/extra.conf files """
        result = {}
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
    def load_sysd_template_conf(self, module): # -> conf?
        """ read the unit template with a UnitConfParser (systemd) """
        if module and "@" in module:
            unit = parse_unit(module)
            service = "%s@.service" % unit.prefix
            conf = self.load_sysd_unit_conf(service)
            if conf:
                conf.module = module
            return conf
        return None
    def load_sysd_unit_conf(self, module): # -> conf?
        """ read the unit file with a UnitConfParser (systemd) """
        path = self.unit_sysd_file(module)
        if not path: return None
        assert self._loaded_file_sysd is not None
        if path in self._loaded_file_sysd:
            return self._loaded_file_sysd[path]
        masked = None
        if os.path.islink(path) and os.readlink(path).startswith("/dev"):
            masked = os.readlink(path)
        drop_in_files = {}
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
        conf._root = self._root
        self._loaded_file_sysd[path] = conf
        return conf
    def load_sysv_unit_conf(self, module): # -> conf?
        """ read the unit file with a UnitConfParser (sysv) """
        path = self.unit_sysv_file(module)
        if not path: return None
        assert self._loaded_file_sysv is not None
        if path in self._loaded_file_sysv:
            return self._loaded_file_sysv[path]
        data = UnitConfParser()
        data.read_sysv(path)
        conf = SystemctlConf(data, module)
        conf._root = self._root
        self._loaded_file_sysv[path] = conf
        return conf
    def load_unit_conf(self, module): # -> conf | None(not-found)
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
        except Exception as e:
            logg.warning("%s not loaded: %s", module, e)
        return None
    def default_unit_conf(self, module, description = None): # -> conf
        """ a unit conf that can be printed to the user where
            attributes are empty and loaded() is False """
        data = UnitConfParser()
        data.set(Unit, "Description", description or ("NOT-FOUND " + str(module)))
        # assert(not data.loaded())
        conf = SystemctlConf(data, module)
        conf._root = self._root
        return conf
    def get_unit_conf(self, module): # -> conf (conf | default-conf)
        """ accept that a unit does not exist
            and return a unit conf that says 'not-loaded' """
        conf = self.load_unit_conf(module)
        if conf is not None:
            return conf
        return self.default_unit_conf(module)
    def get_unit_type(self, module):
        name, ext = os.path.splitext(module)
        if ext in [".service", ".socket", ".target"]:
            return ext[1:]
        return None
    def get_unit_section(self, module, default = Service):
        return string.capwords(self.get_unit_type(module) or default)
    def get_unit_section_from(self, conf, default = Service):
        return self.get_unit_section(conf.name(), default)
    def match_sysd_templates(self, modules = None, suffix=".service"): # -> generate[ unit ]
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
    def match_sysd_units(self, modules = None, suffix=".service"): # -> generate[ unit ]
        """ make a file glob on all known units (systemd areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
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
    def match_sysv_units(self, modules = None, suffix=".service"): # -> generate[ unit ]
        """ make a file glob on all known units (sysv areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
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
    def match_units(self, modules = None, suffix=".service"): # -> [ units,.. ]
        """ Helper for about any command with multiple units which can
            actually be glob patterns on their respective unit name.
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        found = []
        for unit in self.match_sysd_units(modules, suffix):
            if unit not in found:
                found.append(unit)
        for unit in self.match_sysd_templates(modules, suffix):
            if unit not in found:
                found.append(unit)
        for unit in self.match_sysv_units(modules, suffix):
            if unit not in found:
                found.append(unit)
        return found
    def list_service_unit_basics(self):
        """ show all the basic loading state of services """
        filename = self.unit_file() # scan all
        assert self._file_for_unit_sysd is not None
        assert self._file_for_unit_sysv is not None
        result = []
        for name, value in self._file_for_unit_sysd.items():
            result += [(name, "SysD", value)]
        for name, value in self._file_for_unit_sysv.items():
            result += [(name, "SysV", value)]
        return result
    def list_service_units(self, *modules): # -> [ (unit,loaded+active+substate,description) ]
        """ show all the service units """
        result = {}
        active = {}
        substate = {}
        description = {}
        for unit in self.match_units(to_list(modules)):
            result[unit] = "not-found"
            active[unit] = "inactive"
            substate[unit] = "dead"
            description[unit] = ""
            try:
                conf = self.get_unit_conf(unit)
                result[unit] = "loaded"
                description[unit] = self.get_description_from(conf)
                active[unit] = self.get_active_from(conf)
                substate[unit] = self.get_substate_from(conf) or "unknown"
            except Exception as e:
                logg.warning("list-units: %s", e)
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
    def list_units_modules(self, *modules): # -> [ (unit,loaded,description) ]
        """ [PATTERN]... -- List loaded units.
        If one or more PATTERNs are specified, only units matching one of
        them are shown. NOTE: This is the default command."""
        hint = "To show all installed unit files use 'systemctl list-unit-files'."
        result = self.list_service_units(*modules)
        if self._no_legend:
            return result
        found = "%s loaded units listed." % len(result)
        return result + [("", "", ""), (found, "", ""), (hint, "", "")]
    def list_service_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """ show all the service units and the enabled status"""
        logg.debug("list service unit files for %s", modules)
        result = {}
        enabled = {}
        for unit in self.match_units(to_list(modules)):
            if self._only_type and self.get_unit_type(unit) not in self._only_type:
                continue
            result[unit] = None
            enabled[unit] = ""
            try:
                conf = self.get_unit_conf(unit)
                if self.not_user_conf(conf):
                    result[unit] = None
                    continue
                result[unit] = conf
                enabled[unit] = self.enabled_from(conf)
            except Exception as e:
                logg.warning("list-units: %s", e)
        return [(unit, enabled[unit]) for unit in sorted(result) if result[unit]]
    def each_target_file(self):
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
    def list_target_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """ show all the target units and the enabled status"""
        enabled = {}
        targets = {}
        for target, filepath in self.each_target_file():
            logg.info("target %s", filepath)
            targets[target] = filepath
            enabled[target] = "static"
        for unit in _all_common_targets:
            targets[unit] = None
            enabled[unit] = "static"
            if unit in _all_common_enabled:
                enabled[unit] = "enabled"
            if unit in _all_common_disabled:
                enabled[unit] = "disabled"
        return [(unit, enabled[unit]) for unit in sorted(targets)]
    def list_unit_files_modules(self, *modules): # -> [ (unit,enabled) ]
        """[PATTERN]... -- List installed unit files
        List installed unit files and their enablement state (as reported
        by is-enabled). If one or more PATTERNs are specified, only units
        whose filename (just the last component of the path) matches one of
        them are shown. This command reacts to limitations of --type being
        --type=service or --type=target (and --now for some basics)."""
        result = []
        if self._now:
            basics = self.list_service_unit_basics()
            result = [(name, sysv + " " + filename) for name, sysv, filename in basics]
        elif self._only_type: 
            if "target" in self._only_type:
                result = self.list_target_unit_files()
            if "service" in self._only_type:
                result = self.list_service_unit_files()
        else:
            result = self.list_target_unit_files()
            result += self.list_service_unit_files(*modules)
        if self._no_legend:
            return result
        found = "%s unit files listed." % len(result)
        return [("UNIT FILE", "STATE")] + result + [("", ""), (found, "")]
    ##
    ##
    def get_description(self, unit, default = None):
        return self.get_description_from(self.load_unit_conf(unit))
    def get_description_from(self, conf, default = None): # -> text
        """ Unit.Description could be empty sometimes """
        if not conf: return default or ""
        description = conf.get(Unit, "Description", default or "")
        return self.expand_special(description, conf)
    def read_pid_file(self, pid_file, default = None):
        pid = default
        if not pid_file:
            return default
        if not os.path.isfile(pid_file):
            return default
        if self.truncate_old(pid_file):
            return default
        try:
            # some pid-files from applications contain multiple lines
            for line in open(pid_file):
                if line.strip():
                    pid = to_intN(line.strip())
                    break
        except Exception as e:
            logg.warning("bad read of pid file '%s': %s", pid_file, e)
        return pid
    def wait_pid_file(self, pid_file, timeout = None): # -> pid?
        """ wait some seconds for the pid file to appear and return the pid """
        timeout = int(timeout or (DefaultTimeoutStartSec/2))
        timeout = max(timeout, (MinimumTimeoutStartSec))
        dirpath = os.path.dirname(os.path.abspath(pid_file))
        for x in xrange(timeout):
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
    def get_status_pid_file(self, unit):
        """ actual file path of pid file (internal) """
        conf = self.get_unit_conf(unit)
        return self.pid_file_from(conf) or self.get_status_file_from(conf)
    def pid_file_from(self, conf, default = ""):
        """ get the specified pid file path (not a computed default) """
        pid_file = self.get_pid_file(conf) or default
        return os_path(self._root, self.expand_special(pid_file, conf))
    def get_pid_file(self, conf, default = None):
        return conf.get(Service, "PIDFile", default)
    def read_mainpid_from(self, conf, default = None):
        """ MAINPID is either the PIDFile content written from the application
            or it is the value in the status file written by this systemctl.py code """
        pid_file = self.pid_file_from(conf)
        if pid_file:
            return self.read_pid_file(pid_file, default)
        status = self.read_status_from(conf)
        if "MainPID" in status:
            return to_intN(status["MainPID"], default)
        return default
    def clean_pid_file_from(self, conf):
        pid_file = self.pid_file_from(conf)
        if pid_file and os.path.isfile(pid_file):
            try:
                os.remove(pid_file)
            except OSError as e:
                logg.warning("while rm %s: %s", pid_file, e)
        self.write_status_from(conf, MainPID=None)
    def get_status_file(self, unit): # for testing
        conf = self.get_unit_conf(unit)
        return self.get_status_file_from(conf)
    def get_status_file_from(self, conf, default = None):
        status_file = self.get_StatusFile(conf)
        # this not a real setting, but do the expand_special anyway
        return os_path(self._root, self.expand_special(status_file, conf))
    def get_StatusFile(self, conf, default = None): # -> text
        """ file where to store a status mark """
        status_file = conf.get(Service, "StatusFile", default)
        if status_file:
            return status_file
        root = conf.root_mode()
        folder = get_PID_DIR(root)
        name = "%s.status" % conf.name()
        return os.path.join(folder, name)
    def clean_status_from(self, conf):
        status_file = self.get_status_file_from(conf)
        if os.path.exists(status_file):
            os.remove(status_file)
        conf.status = {}
    def write_status_from(self, conf, **status): # -> bool(written)
        """ if a status_file is known then path is created and the
            give status is written as the only content. """
        status_file = self.get_status_file_from(conf)
        # if not status_file: return False
        dirpath = os.path.dirname(os.path.abspath(status_file))
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        if conf.status is None:
            conf.status = self.read_status_from(conf)
        if True:
            for key in sorted(status.keys()):
                value = status[key]
                if key.upper() == "AS": key = "ActiveState"
                if key.upper() == "EXIT": key = "ExecMainCode"
                if value is None:
                    try: del conf.status[key]
                    except KeyError: pass
                else:
                    conf.status[key] = strE(value)
        try:
            with open(status_file, "w") as f:
                for key in sorted(conf.status):
                    value = conf.status[key]
                    if key == "MainPID" and str(value) == "0":
                        logg.warning("ignore writing MainPID=0")
                        continue
                    content = "{}={}\n".format(key, str(value))
                    logg.debug("writing to %s\n\t%s", status_file, content.strip())
                    f.write(content)
        except IOError as e:
            logg.error("writing STATUS %s: %s\n\t to status file %s", status, e, status_file)
        return True
    def read_status_from(self, conf):
        status_file = self.get_status_file_from(conf)
        status = {}
        # if not status_file: return status
        if not os.path.isfile(status_file):
            if DEBUG_STATUS: logg.debug("no status file: %s\n returning %s", status_file, status)
            return status
        if self.truncate_old(status_file):
            if DEBUG_STATUS: logg.debug("old status file: %s\n returning %s", status_file, status)
            return status
        try:
            if DEBUG_STATUS: logg.debug("reading %s", status_file)
            for line in open(status_file):
                if line.strip():
                    m = re.match(r"(\w+)[:=](.*)", line)
                    if m:
                        key, value = m.group(1), m.group(2)
                        if key.strip():
                            status[key.strip()] = value.strip()
                    else:  # pragma: no cover
                        logg.warning("ignored %s", line.strip())
        except:
            logg.warning("bad read of status file '%s'", status_file)
        return status
    def get_status_from(self, conf, name, default = None):
        if conf.status is None:
            conf.status = self.read_status_from(conf)
        return conf.status.get(name, default)
    def set_status_from(self, conf, name, value):
        if conf.status is None:
            conf.status = self.read_status_from(conf)
        if value is None:
            try: del conf.status[name]
            except KeyError: pass
        else:
            conf.status[name] = value
    #
    def get_boottime(self):
        """ detects the boot time of the container - in general the start time of PID 1 """
        if self._boottime is None:
            self._boottime = self.get_boottime_from_proc()
        assert self._boottime is not None
        return self._boottime
    def get_boottime_from_proc(self):
        """ detects the latest boot time by looking at the start time of available process"""
        pid1 = BOOT_PID_MIN or 0
        pid_max = BOOT_PID_MAX
        if pid_max < 0:
            pid_max = pid1 - pid_max
        for pid in xrange(pid1, pid_max):
            proc = _proc_pid_stat.format(**locals())
            try:
                if os.path.exists(proc):
                    # return os.path.getmtime(proc) # did sometimes change
                    return self.path_proc_started(proc)
            except Exception as e: # pragma: no cover
                logg.warning("boottime - could not access %s: %s", proc, e)
        if DEBUG_BOOTTIME:
            logg.debug(" boottime from the oldest entry in /proc [nothing in %s..%s]", pid1, pid_max)
        return self.get_boottime_from_old_proc()
    def get_boottime_from_old_proc(self):
        booted = time.time()
        for pid in os.listdir(_proc_pid_dir):
            proc = _proc_pid_stat.format(**locals())
            try:
                if os.path.exists(proc):
                    # ctime = os.path.getmtime(proc)
                    ctime = self.path_proc_started(proc)
                    if ctime < booted:
                        booted = ctime
            except Exception as e: # pragma: no cover
                logg.warning("could not access %s: %s", proc, e)
        return booted

    # Use uptime, time process running in ticks, and current time to determine process boot time
    # You can't use the modified timestamp of the status file because it isn't static.
    # ... using clock ticks it is known to be a linear time on Linux
    def path_proc_started(self, proc):
        # get time process started after boot in clock ticks
        with open(proc) as file_stat:
            data_stat = file_stat.readline()
        file_stat.close()
        stat_data = data_stat.split()
        started_ticks = stat_data[21]
        # man proc(5): "(22) starttime = The time the process started after system boot."
        #    ".. the value is expressed in clock ticks (divide by sysconf(_SC_CLK_TCK))."
        # NOTE: for containers the start time is related to the boot time of host system.

        clkTickInt = os.sysconf_names['SC_CLK_TCK']
        clockTicksPerSec = os.sysconf(clkTickInt)
        started_secs = float(started_ticks) / clockTicksPerSec
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
            logg.debug("  BOOT 1. Proc has been running since: %s" % (datetime.datetime.fromtimestamp(started_time)))

        # Variant 2:
        system_stat = _proc_sys_stat
        system_btime = 0.
        with open(system_stat, "rb") as f:
            for line in f:
                assert isinstance(line, bytes)
                if line.startswith(b"btime"):
                    system_btime = float(line.decode().split()[1])
        f.closed
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 2. System btime secs: %.3f (%s)", system_btime, system_stat)

        started_btime = system_btime + started_secs
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 2. Proc has been running since: %s" % (datetime.datetime.fromtimestamp(started_btime)))

        # return started_time
        return started_btime

    def get_filetime(self, filename):
        return os.path.getmtime(filename)
    def truncate_old(self, filename):
        filetime = self.get_filetime(filename)
        boottime = self.get_boottime()
        if filetime >= boottime:
            if DEBUG_BOOTTIME:
                logg.debug("  file time: %s (%s)", datetime.datetime.fromtimestamp(filetime), o22(filename))
                logg.debug("  boot time: %s (%s)", datetime.datetime.fromtimestamp(boottime), "status modified later")
            return False # OK
        if DEBUG_BOOTTIME:
            logg.info("  file time: %s (%s)", datetime.datetime.fromtimestamp(filetime), o22(filename))
            logg.info("  boot time: %s (%s)", datetime.datetime.fromtimestamp(boottime), "status TRUNCATED NOW")
        try:
            shutil_truncate(filename)
        except Exception as e:
            logg.warning("while truncating: %s", e)
        return True # truncated
    def getsize(self, filename):
        if filename is None: # pragma: no cover (is never null)
            return 0
        if not os.path.isfile(filename):
            return 0
        if self.truncate_old(filename):
            return 0
        try:
            return os.path.getsize(filename)
        except Exception as e:
            logg.warning("while reading file size: %s\n of %s", e, filename)
            return 0
    #
    def read_env_file(self, env_file): # -> generate[ (name,value) ]
        """ EnvironmentFile=<name> is being scanned """
        mode, env_file = load_path(env_file)
        real_file = os_path(self._root, env_file)
        if not os.path.exists(real_file):
            if mode.check:
                logg.error("file does not exist: %s", real_file)
            else:
                logg.debug("file does not exist: %s", real_file)
            return
        try:
            for real_line in open(os_path(self._root, env_file)):
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
        except Exception as e:
            logg.info("while reading %s: %s", env_file, e)
    def read_env_part(self, env_part): # -> generate[ (name, value) ]
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
        except Exception as e:
            logg.info("while reading %s: %s", env_part, e)
    def command_of_unit(self, unit):
        """ [UNIT]. -- show service settings (experimental)
            or use -p VarName to show another property than 'ExecStart' """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s could not be found.", unit)
            self.error |= NOT_FOUND
            return None
        if self._only_property:
            found = []
            for prop in self._only_property:
                found += conf.getlist(Service, prop)
            return found
        return conf.getlist(Service, "ExecStart")
    def environment_of_unit(self, unit):
        """ [UNIT]. -- show environment parts """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s could not be found.", unit)
            self.error |= NOT_FOUND
            return None
        return self.get_env(conf)
    def extra_vars(self):
        return self._extra_vars # from command line
    def get_env(self, conf):
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
    def expand_env(self, cmd, env):
        def get_env1(m):
            name = m.group(1)
            if name in env:
                return env[name]
            namevar = "$%s" % name
            logg.debug("can not expand %s", namevar)
            return (EXPAND_KEEP_VARS and namevar or "")
        def get_env2(m):
            name = m.group(1)
            if name in env:
                return env[name]
            namevar = "${%s}" % name
            logg.debug("can not expand %s", namevar)
            return (EXPAND_KEEP_VARS and namevar or "")
        #
        maxdepth = EXPAND_VARS_MAXDEPTH
        expanded = re.sub(r"[$](\w+)", lambda m: get_env1(m), cmd.replace("\\\n", ""))
        for depth in xrange(maxdepth):
            new_text = re.sub(r"[$][{](\w+)[}]", lambda m: get_env2(m), expanded)
            if new_text == expanded:
                return expanded
            expanded = new_text
        logg.error("shell variable expansion exceeded maxdepth %s", maxdepth)
        return expanded
    def expand_special(self, cmd, conf):
        """ expand %i %t and similar special vars. They are being expanded
            before any other expand_env takes place which handles shell-style
            $HOME references. """
        def xx(arg): return unit_name_unescape(arg)
        def yy(arg): return arg
        def get_confs(conf):
            confs={"%": "%"}
            if conf is None: # pragma: no cover (is never null)
                return confs
            unit = parse_unit(conf.name())
            #
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
            confs["F"] = strE(conf.filename())      # EXTRA
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
        def get_conf1(m):
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
    def exec_newcmd(self, cmd, env, conf):
        mode, exe = exec_path(cmd)
        if mode.noexpand:
            newcmd = self.split_cmd(exe)
        else:
            newcmd = self.expand_cmd(exe, env, conf)
        if mode.argv0:
            if len(newcmd) > 1:
                del newcmd[1] # TODO: keep but allow execve calls to pick it up
        return mode, newcmd
    def split_cmd(self, cmd):
        cmd2 = cmd.replace("\\\n", "")
        newcmd = []
        for part in shlex.split(cmd2):
            newcmd += [part]
        return newcmd
    def expand_cmd(self, cmd, env, conf):
        """ expand ExecCmd statements including %i and $MAINPID """
        cmd2 = cmd.replace("\\\n", "")
        # according to documentation, when bar="one two" then the expansion
        # of '$bar' is ["one","two"] and '${bar}' becomes ["one two"]. We
        # tackle that by expand $bar before shlex, and the rest thereafter.
        def get_env1(m):
            name = m.group(1)
            if name in env:
                return env[name]
            logg.debug("can not expand $%s", name)
            return ""  # empty string
        def get_env2(m):
            name = m.group(1)
            if name in env:
                return env[name]
            logg.debug("can not expand $%s}}", name)
            return ""  # empty string
        cmd3 = re.sub(r"[$](\w+)", lambda m: get_env1(m), cmd2)
        newcmd = []
        for part in shlex.split(cmd3):
            part2 = self.expand_special(part, conf)
            newcmd += [re.sub(r"[$][{](\w+)[}]", lambda m: get_env2(m), part2)] # type: ignore[arg-type]
        return newcmd
    def remove_service_directories(self, conf, section = Service):
        # |
        ok = True
        nameRuntimeDirectory = self.get_RuntimeDirectory(conf, section)
        keepRuntimeDirectory = self.get_RuntimeDirectoryPreserve(conf, section)
        if not keepRuntimeDirectory:
            root = conf.root_mode()
            for name in nameRuntimeDirectory.split(" "):
                if not name.strip(): continue
                RUN = get_RUNTIME_DIR(root)
                path = os.path.join(RUN, name)
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
                if RUN == "/run":
                    for var_run in ("/var/run", "/tmp/run"):
                        if os.path.isdir(var_run):
                            var_path = os.path.join(var_run, name)
                            var_dirpath = os_path(self._root, var_path)
                            self.do_rm_tree(var_dirpath)
        if not ok:
            logg.debug("could not fully remove service directory %s", path)
        return ok
    def do_rm_tree(self, path):
        ok = True
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for item in filenames:
                    filepath = os.path.join(dirpath, item)
                    try:
                        os.remove(filepath)
                    except Exception as e: # pragma: no cover
                        logg.debug("not removed file: %s (%s)", filepath, e)
                        ok = False
                for item in dirnames:
                    dir_path = os.path.join(dirpath, item)
                    try:
                        os.rmdir(dir_path)
                    except Exception as e: # pragma: no cover
                        logg.debug("not removed dir: %s (%s)", dir_path, e)
                        ok = False
            try:
                os.rmdir(path)
            except Exception as e:
                logg.debug("not removed top dir: %s (%s)", path, e)
                ok = False # pragma: no cover
        logg.debug("%s rm_tree %s", ok and "done" or "fail", path)
        return ok
    def get_RuntimeDirectoryPreserve(self, conf, section = Service):
        return conf.getbool(section, "RuntimeDirectoryPreserve", "no")
    def get_RuntimeDirectory(self, conf, section = Service):
        return self.expand_special(conf.get(section, "RuntimeDirectory", ""), conf)
    def get_StateDirectory(self, conf, section = Service):
        return self.expand_special(conf.get(section, "StateDirectory", ""), conf)
    def get_CacheDirectory(self, conf, section = Service):
        return self.expand_special(conf.get(section, "CacheDirectory", ""), conf)
    def get_LogsDirectory(self, conf, section = Service):
        return self.expand_special(conf.get(section, "LogsDirectory", ""), conf)
    def get_ConfigurationDirectory(self, conf, section = Service):
        return self.expand_special(conf.get(section, "ConfigurationDirectory", ""), conf)
    def get_RuntimeDirectoryMode(self, conf, section = Service):
        return conf.get(section, "RuntimeDirectoryMode", "")
    def get_StateDirectoryMode(self, conf, section = Service):
        return conf.get(section, "StateDirectoryMode", "")
    def get_CacheDirectoryMode(self, conf, section = Service):
        return conf.get(section, "CacheDirectoryMode", "")
    def get_LogsDirectoryMode(self, conf, section = Service):
        return conf.get(section, "LogsDirectoryMode", "")
    def get_ConfigurationDirectoryMode(self, conf, section = Service):
        return conf.get(section, "ConfigurationDirectoryMode", "")
    def clean_service_directories(self, conf, which = ""):
        ok = True
        section = self.get_unit_section_from(conf)
        nameRuntimeDirectory = self.get_RuntimeDirectory(conf, section)
        nameStateDirectory = self.get_StateDirectory(conf, section)
        nameCacheDirectory = self.get_CacheDirectory(conf, section)
        nameLogsDirectory = self.get_LogsDirectory(conf, section)
        nameConfigurationDirectory = self.get_ConfigurationDirectory(conf, section)
        root = conf.root_mode()
        for name in nameRuntimeDirectory.split(" "):
            if not name.strip(): continue
            RUN = get_RUNTIME_DIR(root)
            path = os.path.join(RUN, name)
            if which in ["all", "runtime", ""]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
                if RUN == "/run":
                    for var_run in ("/var/run", "/tmp/run"):
                        var_path = os.path.join(var_run, name)
                        var_dirpath = os_path(self._root, var_path)
                        self.do_rm_tree(var_dirpath)
        for name in nameStateDirectory.split(" "):
            if not name.strip(): continue
            DAT = get_VARLIB_HOME(root)
            path = os.path.join(DAT, name)
            if which in ["all", "state"]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        for name in nameCacheDirectory.split(" "):
            if not name.strip(): continue
            CACHE = get_CACHE_HOME(root)
            path = os.path.join(CACHE, name)
            if which in ["all", "cache", ""]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        for name in nameLogsDirectory.split(" "):
            if not name.strip(): continue
            LOGS = get_LOG_DIR(root)
            path = os.path.join(LOGS, name)
            if which in ["all", "logs"]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        for name in nameConfigurationDirectory.split(" "):
            if not name.strip(): continue
            CONFIG = get_CONFIG_HOME(root)
            path = os.path.join(CONFIG, name)
            if which in ["all", "configuration", ""]:
                dirpath = os_path(self._root, path)
                ok = self.do_rm_tree(dirpath) and ok
        return ok
    def env_service_directories(self, conf):
        envs = {}
        section = self.get_unit_section_from(conf)
        nameRuntimeDirectory = self.get_RuntimeDirectory(conf, section)
        nameStateDirectory = self.get_StateDirectory(conf, section)
        nameCacheDirectory = self.get_CacheDirectory(conf, section)
        nameLogsDirectory = self.get_LogsDirectory(conf, section)
        nameConfigurationDirectory = self.get_ConfigurationDirectory(conf, section)
        root = conf.root_mode()
        for name in nameRuntimeDirectory.split(" "):
            if not name.strip(): continue
            RUN = get_RUNTIME_DIR(root)
            path = os.path.join(RUN, name)
            envs["RUNTIME_DIRECTORY"] = path
        for name in nameStateDirectory.split(" "):
            if not name.strip(): continue
            DAT = get_VARLIB_HOME(root)
            path = os.path.join(DAT, name)
            envs["STATE_DIRECTORY"] = path
        for name in nameCacheDirectory.split(" "):
            if not name.strip(): continue
            CACHE = get_CACHE_HOME(root)
            path = os.path.join(CACHE, name)
            envs["CACHE_DIRECTORY"] = path
        for name in nameLogsDirectory.split(" "):
            if not name.strip(): continue
            LOGS = get_LOG_DIR(root)
            path = os.path.join(LOGS, name)
            envs["LOGS_DIRECTORY"] = path
        for name in nameConfigurationDirectory.split(" "):
            if not name.strip(): continue
            CONFIG = get_CONFIG_HOME(root)
            path = os.path.join(CONFIG, name)
            envs["CONFIGURATION_DIRECTORY"] = path
        return envs
    def create_service_directories(self, conf):
        envs = {}
        section = self.get_unit_section_from(conf)
        nameRuntimeDirectory = self.get_RuntimeDirectory(conf, section)
        modeRuntimeDirectory = self.get_RuntimeDirectoryMode(conf, section)
        nameStateDirectory = self.get_StateDirectory(conf, section)
        modeStateDirectory = self.get_StateDirectoryMode(conf, section)
        nameCacheDirectory = self.get_CacheDirectory(conf, section)
        modeCacheDirectory = self.get_CacheDirectoryMode(conf, section)
        nameLogsDirectory = self.get_LogsDirectory(conf, section)
        modeLogsDirectory = self.get_LogsDirectoryMode(conf, section)
        nameConfigurationDirectory = self.get_ConfigurationDirectory(conf, section)
        modeConfigurationDirectory = self.get_ConfigurationDirectoryMode(conf, section)
        root = conf.root_mode()
        user = self.get_User(conf)
        group = self.get_Group(conf)
        for name in nameRuntimeDirectory.split(" "):
            if not name.strip(): continue
            RUN = get_RUNTIME_DIR(root)
            path = os.path.join(RUN, name)
            logg.debug("RuntimeDirectory %s", path)
            self.make_service_directory(path, modeRuntimeDirectory)
            self.chown_service_directory(path, user, group)
            envs["RUNTIME_DIRECTORY"] = path
            if RUN == "/run":
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
                        except Exception as e:
                            logg.debug("var symlink %s\n\t%s", var_dirpath, e)
        for name in nameStateDirectory.split(" "):
            if not name.strip(): continue
            DAT = get_VARLIB_HOME(root)
            path = os.path.join(DAT, name)
            logg.debug("StateDirectory %s", path)
            self.make_service_directory(path, modeStateDirectory)
            self.chown_service_directory(path, user, group)
            envs["STATE_DIRECTORY"] = path
        for name in nameCacheDirectory.split(" "):
            if not name.strip(): continue
            CACHE = get_CACHE_HOME(root)
            path = os.path.join(CACHE, name)
            logg.debug("CacheDirectory %s", path)
            self.make_service_directory(path, modeCacheDirectory)
            self.chown_service_directory(path, user, group)
            envs["CACHE_DIRECTORY"] = path
        for name in nameLogsDirectory.split(" "):
            if not name.strip(): continue
            LOGS = get_LOG_DIR(root)
            path = os.path.join(LOGS, name)
            logg.debug("LogsDirectory %s", path)
            self.make_service_directory(path, modeLogsDirectory)
            self.chown_service_directory(path, user, group)
            envs["LOGS_DIRECTORY"] = path
        for name in nameConfigurationDirectory.split(" "):
            if not name.strip(): continue
            CONFIG = get_CONFIG_HOME(root)
            path = os.path.join(CONFIG, name)
            logg.debug("ConfigurationDirectory %s", path)
            self.make_service_directory(path, modeConfigurationDirectory)
            # not done according the standard
            # self.chown_service_directory(path, user, group)
            envs["CONFIGURATION_DIRECTORY"] = path
        return envs
    def make_service_directory(self, path, mode):
        ok = True
        dirpath = os_path(self._root, path)
        if not os.path.isdir(dirpath):
            try:
                os.makedirs(dirpath)
                logg.info("created directory path: %s", dirpath)
            except Exception as e: # pragma: no cover
                logg.debug("errors directory path: %s\n\t%s", dirpath, e)
                ok = False
            filemode = int_mode(mode)
            if filemode:
                try:
                    os.chmod(dirpath, filemode)
                except Exception as e: # pragma: no cover
                    logg.debug("errors directory path: %s\n\t%s", dirpath, e)
                    ok = False
        else:
            logg.debug("path did already exist: %s", dirpath)
        if not ok:
            logg.debug("could not fully create service directory %s", path)
        return ok
    def chown_service_directory(self, path, user, group):
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
                except Exception as e:
                    logg.info("oops %s\n\t%s", dirpath, e)
            else:
                logg.debug("untouched %s", dirpath)
        return True
    def do_chown_tree(self, path, user, group):
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
                except Exception as e: # pragma: no cover
                    logg.debug("could not set %s:%s on %s\n\t%s", user, group, filepath, e)
                    ok = False
            for item in dirnames:
                dir_path = os.path.join(dirpath, item)
                try:
                    os.chown(dir_path, uid, gid)
                except Exception as e: # pragma: no cover
                    logg.debug("could not set %s:%s on %s\n\t%s", user, group, dir_path, e)
                    ok = False
        try:
            os.chown(path, uid, gid)
        except Exception as e: # pragma: no cover
            logg.debug("could not set %s:%s on %s\n\t%s", user, group, path, e)
            ok = False
        if not ok:
            logg.debug("could not chown %s:%s service directory %s", user, group, path)
        return ok
    def clean_modules(self, *modules):
        """ [UNIT]... -- remove the state directories
        /// it recognizes --what=all or any of configuration, state, cache, logs, runtime
            while an empty value (the default) removes cache and runtime directories"""
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        lines = _log_lines
        follow = _force
        ok = self.clean_units(units)
        return ok and found_all
    def clean_units(self, units, what = ""):
        if not what:
            what = self._only_what[0]
        ok = True
        for unit in units:
            ok = self.clean_unit(unit, what) and ok
        return ok
    def clean_unit(self, unit, what = ""):
        conf = self.load_unit_conf(unit)
        if not conf: return False
        return self.clean_unit_from(conf, what)
    def clean_unit_from(self, conf, what):
        if self.is_active_from(conf):
            logg.warning("can not clean active unit: %s", conf.name())
            return False
        return self.clean_service_directories(conf, what)
    def log_modules(self, *modules):
        """ [UNIT]... -- start 'less' on the log files for the services
        /// use '-f' to follow and '-n lines' to limit output using 'tail',
            using '--no-pager' just does a full 'cat'"""
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        lines = _log_lines
        follow = _force
        result = self.log_units(units, lines, follow)
        if result:
            self.error = result
            return False
        return found_all
    def log_units(self, units, lines = None, follow = False):
        result = 0
        for unit in self.sortedAfter(units):
            exitcode = self.log_unit(unit, lines, follow)
            if exitcode < 0:
                return exitcode
            if exitcode > result:
                result = exitcode
        return result
    def log_unit(self, unit, lines = None, follow = False):
        conf = self.load_unit_conf(unit)
        if not conf: return -1
        return self.log_unit_from(conf, lines, follow)
    def log_unit_from(self, conf, lines = None, follow = False):
        cmd_args = []
        log_path = self.get_journal_log_from(conf)
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
        elif _no_pager:
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
    def get_journal_log_from(self, conf):
        return os_path(self._root, self.get_journal_log(conf))
    def get_journal_log(self, conf):
        """ /var/log/zzz.service.log or /var/log/default.unit.log """
        filename = os.path.basename(strE(conf.filename()))
        unitname = (conf.name() or "default")+".unit"
        name = filename or unitname
        log_folder = expand_path(self._journal_log_folder, conf.root_mode())
        log_file = name.replace(os.path.sep, ".") + ".log"
        if log_file.startswith("."):
            log_file = "dot."+log_file
        return os.path.join(log_folder, log_file)
    def open_journal_log(self, conf):
        log_file = self.get_journal_log_from(conf)
        log_folder = os.path.dirname(log_file)
        if not os.path.isdir(log_folder):
            os.makedirs(log_folder)
        return open(os.path.join(log_file), "a")
    def get_WorkingDirectory(self, conf):
        return conf.get(Service, "WorkingDirectory", "")
    def chdir_workingdir(self, conf):
        """ if specified then change the working directory """
        # the original systemd will start in '/' even if User= is given
        if self._root:
            os.chdir(self._root)
        workingdir = self.get_WorkingDirectory(conf)
        mode, workingdir = load_path(workingdir)
        if workingdir:
            into = os_path(self._root, self.expand_special(workingdir, conf))
            try:
                logg.debug("chdir workingdir '%s'", into)
                os.chdir(into)
                return False
            except Exception as e:
                if mode.check:
                    logg.error("chdir workingdir '%s': %s", into, e)
                    return into
                else:
                    logg.debug("chdir workingdir '%s': %s", into, e)
                    return None
        return None
    NotifySocket = collections.namedtuple("NotifySocket", ["socket", "socketfile"])
    def get_notify_socket_from(self, conf, socketfile = None, debug = False):
        """ creates a notify-socket for the (non-privileged) user """
        notify_socket_folder = expand_path(_notify_socket_folder, conf.root_mode())
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
            pref = "zz.%i.%s" % (get_USER_ID(), o22(os.path.basename(notify_socket_folder)))
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
    def notify_socket_from(self, conf, socketfile = None):
        socketfile = self.get_notify_socket_from(conf, socketfile, debug=True)
        try:
            if not os.path.isdir(os.path.dirname(socketfile)):
                os.makedirs(os.path.dirname(socketfile))
            if os.path.exists(socketfile):
                os.unlink(socketfile)
        except Exception as e:
            logg.warning("error %s: %s", socketfile, e)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(socketfile)
        os.chmod(socketfile, 0o777) # the service my run under some User=setting
        return Systemctl.NotifySocket(sock, socketfile)
    def read_notify_socket(self, notify, timeout):
        notify.socket.settimeout(timeout or DefaultMaximumTimeout)
        result = ""
        try:
            result, client_address = notify.socket.recvfrom(4096)
            assert isinstance(result, bytes)
            if result:
                result = result.decode("utf-8")
                result_txt = result.replace("\n", "|")
                result_len = len(result)
                logg.debug("read_notify_socket(%s):%s", result_len, result_txt)
        except socket.timeout as e:
            if timeout > 2:
                logg.debug("socket.timeout %s", e)
        return result
    def wait_notify_socket(self, notify, timeout, pid = None, pid_file = None):
        if not os.path.exists(notify.socketfile):
            logg.info("no $NOTIFY_SOCKET exists")
            return {}
        #
        lapseTimeout = max(3, int(timeout / 100))
        mainpidTimeout = lapseTimeout # Apache sends READY before MAINPID
        status = ""
        logg.info("wait $NOTIFY_SOCKET, timeout %s (lapse %s)", timeout, lapseTimeout)
        waiting = " ---"
        results = {}
        for attempt in xrange(int(timeout)+1):
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
                mainpidTimeout = lapseTimeout
                status = results.get("STATUS", "")
            if "READY" not in results:
                time.sleep(1) # until TimeoutStart
                continue
            if "MAINPID" not in results and not pid_file:
                mainpidTimeout -= 1
                if mainpidTimeout > 0:
                    waiting = "%4i" % (-mainpidTimeout)
                    time.sleep(1) # until TimeoutStart
                    continue
            break # READY and MAINPID
        if "READY" not in results:
            logg.info(".... timeout while waiting for 'READY=1' status on $NOTIFY_SOCKET")
        elif "MAINPID" not in results:
            logg.info(".... seen 'READY=1' but no MAINPID update status on $NOTIFY_SOCKET")
        logg.debug("notify = %s", results)
        try:
            notify.socket.close()
        except Exception as e:
            logg.debug("socket.close %s", e)
        return results
    def start_modules(self, *modules):
        """ [UNIT]... -- start these units
        /// SPECIAL: with --now or --init it will
            run the init-loop and stop the units afterwards """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        init = self._now or self._init
        return self.start_units(units, init) and found_all
    def start_units(self, units, init = None):
        """ fails if any unit does not start
        /// SPECIAL: may run the init-loop and
            stop the named units afterwards """
        self.wait_system()
        done = True
        started_units = []
        for unit in self.sortedAfter(units):
            started_units.append(unit)
            if not self.start_unit(unit):
                done = False
        if init:
            logg.info("init-loop start")
            sig = self.init_loop_until_stop(started_units)
            logg.info("init-loop %s", sig)
            for unit in reversed(started_units):
                self.stop_unit(unit)
        return done
    def start_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.debug("unit could not be loaded (%s)", unit)
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.start_unit_from(conf)
    def get_TimeoutStartSec(self, conf):
        timeout = conf.get(Service, "TimeoutSec", strE(DefaultTimeoutStartSec))
        timeout = conf.get(Service, "TimeoutStartSec", timeout)
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def get_SocketTimeoutSec(self, conf):
        timeout = conf.get(Socket, "TimeoutSec", strE(DefaultTimeoutStartSec))
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def get_RemainAfterExit(self, conf):
        return conf.getbool(Service, "RemainAfterExit", "no")
    def start_unit_from(self, conf):
        if not conf: return False
        if self.syntax_check(conf) > 100: return False
        with waitlock(conf):
            logg.debug(" start unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_start_unit_from(conf)
    def do_start_unit_from(self, conf):
        if conf.name().endswith(".service"):
            return self.do_start_service_from(conf)
        elif conf.name().endswith(".socket"):
            return self.do_start_socket_from(conf)
        elif conf.name().endswith(".target"):
            return self.do_start_target_from(conf)
        else:
            logg.error("start not implemented for unit type: %s", conf.name())
            return False
    def do_start_service_from(self, conf):
        timeout = self.get_TimeoutStartSec(conf)
        doRemainAfterExit = self.get_RemainAfterExit(conf)
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.exec_check_unit(conf, env, Service, "Exec") # all...
            if not okee and _no_reload: return False
        service_directories = self.create_service_directories(conf)
        env.update(service_directories) # atleast sshd did check for /run/sshd
        # for StopPost on failure:
        returncode = 0
        service_result = "success"
        if True:
            if runs in ["simple", "exec", "forking", "notify", "idle"]:
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
            for cmd in conf.getlist(Service, "ExecStartPre", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
            status_file = self.get_status_file_from(conf)
            if self.get_status_from(conf, "ActiveState", "unknown") == "active":
                logg.warning("the service was already up once")
                return True
            for cmd in conf.getlist(Service, "ExecStart", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
            if True:
                self.set_status_from(conf, "ExecMainCode", strE(returncode))
                active = returncode and "failed" or "active"
                self.write_status_from(conf, AS=active)
        elif runs in ["simple", "exec", "idle"]:
            status_file = self.get_status_file_from(conf)
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
                env["MAINPID"] = strE(pid)
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                self.write_status_from(conf, MainPID=forkpid)
                logg.info("%s started PID %s", runs, forkpid)
                env["MAINPID"] = strE(forkpid)
                time.sleep(MinimumYield)
                run = subprocess_testpid(forkpid)
                if run.returncode is not None:
                    logg.info("%s stopped PID %s (%s) <-%s>", runs, run.pid,
                              run.returncode or "OK", run.signal or "")
                    if doRemainAfterExit:
                        self.set_status_from(conf, "ExecMainCode", strE(run.returncode))
                        active = run.returncode and "failed" or "active"
                        self.write_status_from(conf, AS=active)
                    if run.returncode and exe.check:
                        service_result = "failed"
                        break
        elif runs in ["notify"]:
            # "notify" is the same as "simple" but we create a $NOTIFY_SOCKET
            # and wait for startup completion by checking the socket messages
            pid_file = self.pid_file_from(conf)
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
                env["MAINPID"] = strE(mainpid)
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                # via NOTIFY # self.write_status_from(conf, MainPID=forkpid)
                logg.info("%s started PID %s", runs, forkpid)
                mainpid = forkpid
                self.write_status_from(conf, MainPID=mainpid)
                env["MAINPID"] = strE(mainpid)
                time.sleep(MinimumYield)
                run = subprocess_testpid(forkpid)
                if run.returncode is not None:
                    logg.info("%s stopped PID %s (%s) <-%s>", runs, run.pid,
                              run.returncode or "OK", run.signal or "")
                    if doRemainAfterExit:
                        self.set_status_from(conf, "ExecMainCode", strE(run.returncode))
                        active = run.returncode and "failed" or "active"
                        self.write_status_from(conf, AS=active)
                    if run.returncode and exe.check:
                        service_result = "failed"
                        break
            if service_result in ["success"] and mainpid:
                logg.debug("okay, waiting on socket for %ss", timeout)
                results = self.wait_notify_socket(notify, timeout, mainpid, pid_file)
                if "MAINPID" in results:
                    new_pid = to_intN(results["MAINPID"])
                    if new_pid and new_pid != mainpid:
                        logg.info("NEW PID %s from sd_notify (was PID %s)", new_pid, mainpid)
                        self.write_status_from(conf, MainPID=new_pid)
                        mainpid = new_pid
                logg.info("%s start done %s", runs, mainpid)
                pid = self.read_mainpid_from(conf)
                if pid:
                    env["MAINPID"] = strE(pid)
                else:
                    service_result = "timeout" # "could not start service"
        elif runs in ["forking"]:
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist(Service, "ExecStart", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
                    env["MAINPID"] = strE(pid)
            if not pid_file:
                time.sleep(MinimumTimeoutStartSec)
                logg.warning("No PIDFile for forking %s", strQ(conf.filename()))
                status_file = self.get_status_file_from(conf)
                self.set_status_from(conf, "ExecMainCode", strE(returncode))
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
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("post-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-start done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
            return True
    def listen_modules(self, *modules):
        """ [UNIT]... -- listen socket units"""
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.listen_units(units) and found_all
    def listen_units(self, units):
        """ fails if any socket does not start """
        self.wait_system()
        done = True
        started_units = []
        active_units = []
        for unit in self.sortedAfter(units):
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
    def listen_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.debug("unit could not be loaded (%s)", unit)
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.listen_unit_from(conf)
    def listen_unit_from(self, conf):
        if not conf: return False
        with waitlock(conf):
            logg.debug(" listen unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_listen_unit_from(conf)
    def do_listen_unit_from(self, conf):
        if conf.name().endswith(".socket"):
            return self.do_start_socket_from(conf)
        else:
            logg.error("listen not implemented for unit type: %s", conf.name())
            return False
    def do_accept_socket_from(self, conf, sock):
        logg.debug("%s: accepting %s", conf.name(), sock.fileno())
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None or TestAccept:  # pragma: no cover
            if sock.type == socket.SOCK_STREAM:
                conn, addr = sock.accept()
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
            logg.error("can not accept socket type %s", strINET(sock.type))
            return False
        return self.do_start_service_from(service_conf)
    def get_socket_service_from(self, conf):
        socket_unit = conf.name()
        accept = conf.getbool(Socket, "Accept", "no")
        service_type = accept and "@.service" or ".service"
        service_name = path_replace_extension(socket_unit, ".socket", service_type)
        service_unit = conf.get(Socket, Service, service_name)
        logg.debug("socket %s -> service %s", socket_unit, service_unit)
        return service_unit
    def do_start_socket_from(self, conf):
        runs = "socket"
        timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool(Socket, "Accept", "no")
        stream = conf.get(Socket, "ListenStream", "")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None:
            logg.debug("unit could not be loaded (%s)", service_unit)
            logg.error("Unit %s not found.", service_unit)
            return False
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.exec_check_unit(conf, env, Socket, "Exec") # all...
            if not okee and _no_reload: return False
        if True:
            for cmd in conf.getlist(Socket, "ExecStartPre", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
                    return False
        # service_directories = self.create_service_directories(conf)
        # env.update(service_directories)
        listening=False
        if not accept:
            sock = self.create_socket(conf)
            if sock and TestListen:
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
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("post-fail %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-fail done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
            return False
        else:
            for cmd in conf.getlist(Socket, "ExecStartPost", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("post-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-start done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
            return True
    def create_socket(self, conf):
        unsupported = ["ListenUSBFunction", "ListenMessageQueue", "ListenNetlink"]
        unsupported += ["ListenSpecial", "ListenFIFO", "ListenSequentialPacket"]
        for item in unsupported:
            if conf.get(Socket, item, ""):
                logg.warning("%s: %s sockets are not implemented", conf.name(), item)
                self.error |= NOT_OK
                return None
        vListenDatagram = conf.get(Socket, "ListenDatagram", "")
        vListenStream = conf.get(Socket, "ListenStream", "")
        address = vListenStream or vListenDatagram
        m = re.match(r"(/.*)", address)
        if m:
            path = m.group(1)
            sock = self.create_unix_socket(conf, path, not vListenStream)
            self.set_status_from(conf, "path", path)
            return sock
        m = re.match(r"(\d+[.]\d*[.]\d*[.]\d+):(\d+)", address)
        if m:
            addr, port = m.group(1), m.group(2)
            sock = self.create_port_ipv4_socket(conf, addr, port, not vListenStream)
            self.set_status_from(conf, "port", port)
            self.set_status_from(conf, "addr", addr)
            return sock
        m = re.match(r"\[([0-9a-fA-F:]*)\]:(\d+)", address)
        if m:
            addr, port = m.group(1), m.group(2)
            sock = self.create_port_ipv6_socket(conf, addr, port, not vListenStream)
            self.set_status_from(conf, "port", port)
            self.set_status_from(conf, "addr", addr)
            return sock
        m = re.match(r"(\d+)$", address)
        if m:
            port = m.group(1)
            sock = self.create_port_socket(conf, port, not vListenStream)
            self.set_status_from(conf, "port", port)
            return sock
        if re.match("@.*", address):
            logg.warning("%s: abstract namespace socket not implemented (%s)", conf.name(), address)
            return None
        if re.match("vsock:.*", address):
            logg.warning("%s: virtual machine socket not implemented (%s)", conf.name(), address)
            return None
        logg.error("%s: unknown socket address type (%s)", conf.name(), address)
        return None
    def create_unix_socket(self, conf, path, dgram):
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
        except Exception as e:
            logg.error("%s: create socket failed [%s]: %s", conf.name(), path, e)
            sock.close()
            return None
        return sock
    def create_port_socket(self, conf, port, dgram):
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET, inet)
        try:
            sock.bind(('', int(port)))
            logg.info("%s: bound socket at %s %s:%s", conf.name(), strINET(inet), "*", port)
        except Exception as e:
            logg.error("%s: create socket failed (%s:%s): %s", conf.name(), "*", port, e)
            sock.close()
            return None
        return sock
    def create_port_ipv4_socket(self, conf, addr, port, dgram):
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET, inet)
        try:
            sock.bind((addr, int(port)))
            logg.info("%s: bound socket at %s %s:%s", conf.name(), strINET(inet), addr, port)
        except Exception as e:
            logg.error("%s: create socket failed (%s:%s): %s", conf.name(), addr, port, e)
            sock.close()
            return None
        return sock
    def create_port_ipv6_socket(self, conf, addr, port, dgram):
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET6, inet)
        try:
            sock.bind((addr, int(port)))
            logg.info("%s: bound socket at %s [%s]:%s", conf.name(), strINET(inet), addr, port)
        except Exception as e:
            logg.error("%s: create socket failed ([%s]:%s): %s", conf.name(), addr, port, e)
            sock.close()
            return None
        return sock
    def extend_exec_env(self, env):
        env = env.copy()
        # implant DefaultPath into $PATH
        path = env.get("PATH", DefaultPath)
        parts = path.split(os.pathsep)
        for part in DefaultPath.split(os.pathsep):
            if part and part not in parts:
                parts.append(part)
        env["PATH"] = str(os.pathsep).join(parts)
        # reset locale to system default
        for name in ResetLocale:
            if name in env:
                del env[name]
        locale = {}
        path = env.get("LOCALE_CONF", LocaleConf)
        parts = path.split(os.pathsep)
        for part in parts:
            if os.path.isfile(part):
                for var, val in self.read_env_file("-"+part):
                    locale[var] = val
                    env[var] = val
        if "LANG" not in locale:
            env["LANG"] = locale.get("LANGUAGE", locale.get("LC_CTYPE", "C"))
        return env
    def expand_list(self, group_lines, conf):
        result = []
        for line in group_lines:
            for item in line.split():
                if item:
                    result.append(self.expand_special(item, conf))
        return result
    def get_User(self, conf):
        return self.expand_special(conf.get(Service, "User", ""), conf)
    def get_Group(self, conf):
        return self.expand_special(conf.get(Service, "Group", ""), conf)
    def get_SupplementaryGroups(self, conf):
        return self.expand_list(conf.getlist(Service, "SupplementaryGroups", []), conf)
    def skip_journal_log(self, conf):
        if self.get_unit_type(conf.name()) not in ["service"]:
            return True
        std_out = conf.get(Service, "StandardOutput", DefaultStandardOutput)
        std_err = conf.get(Service, "StandardError", DefaultStandardError)
        out, err = False, False
        if std_out in ["null"]: out = True
        if std_out.startswith("file:"): out = True
        if std_err in ["inherit"]: std_err = std_out
        if std_err in ["null"]: err = True
        if std_err.startswith("file:"): err = True
        if std_err.startswith("append:"): err = True
        return out and err
    def dup2_journal_log(self, conf):
        msg = ""
        std_inp = conf.get(Service, "StandardInput", DefaultStandardInput)
        std_out = conf.get(Service, "StandardOutput", DefaultStandardOutput)
        std_err = conf.get(Service, "StandardError", DefaultStandardError)
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
        except Exception as e:
            msg += "\n%s: %s" % (fname, e)
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
        except Exception as e:
            msg += "\n%s: %s" % (fname, e)
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
    def execve_from(self, conf, cmd, env):
        """ this code is commonly run in a child process // returns exit-code"""
        # |
        runs = conf.get(Service, "Type", "simple").lower()
        # logg.debug("%s process for %s => %s", runs, strE(conf.name()), strQ(conf.filename()))
        self.dup2_journal_log(conf)
        cmd_args = []
        #
        runuser = self.get_User(conf)
        rungroup = self.get_Group(conf)
        xgroups = self.get_SupplementaryGroups(conf)
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
        except Exception as e:
            logg.error("(%s): %s", shell_cmd(cmd), e)
            sys.exit(1)
    def test_start_unit(self, unit):
        """ helper function to test the code that is normally forked off """
        conf = self.load_unit_conf(unit)
        if not conf: return None
        env = self.get_env(conf)
        for cmd in conf.getlist(Service, "ExecStart", []):
            exe, newcmd = self.exec_newcmd(cmd, env, conf)
            self.execve_from(conf, newcmd, env)
        return None
    def stop_modules(self, *modules):
        """ [UNIT]... -- stop these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.stop_units(units) and found_all
    def stop_units(self, units):
        """ fails if any unit fails to stop """
        self.wait_system()
        done = True
        for unit in self.sortedBefore(units):
            if not self.stop_unit(unit):
                done = False
        return done
    def stop_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.stop_unit_from(conf)

    def get_TimeoutStopSec(self, conf):
        timeout = conf.get(Service, "TimeoutSec", strE(DefaultTimeoutStartSec))
        timeout = conf.get(Service, "TimeoutStopSec", timeout)
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def stop_unit_from(self, conf):
        if not conf: return False
        if self.syntax_check(conf) > 100: return False
        with waitlock(conf):
            logg.info(" stop unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_stop_unit_from(conf)
    def do_stop_unit_from(self, conf):
        if conf.name().endswith(".service"):
            return self.do_stop_service_from(conf)
        elif conf.name().endswith(".socket"):
            return self.do_stop_socket_from(conf)
        elif conf.name().endswith(".target"):
            return self.do_stop_target_from(conf)
        else:
            logg.error("stop not implemented for unit type: %s", conf.name())
            return False
    def do_stop_service_from(self, conf):
        # |
        timeout = self.get_TimeoutStopSec(conf)
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.exec_check_unit(conf, env, Service, "ExecStop")
            if not okee and _no_reload: return False
        service_directories = self.env_service_directories(conf)
        env.update(service_directories)
        returncode = 0
        service_result = "success"
        if runs in ["oneshot"]:
            status_file = self.get_status_file_from(conf)
            if self.get_status_from(conf, "ActiveState", "unknown") == "inactive":
                logg.warning("the service is already down once")
                return True
            for cmd in conf.getlist(Service, "ExecStop", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            if True:
                if returncode:
                    self.set_status_from(conf, "ExecStopCode", strE(returncode))
                    self.write_status_from(conf, AS="failed")
                else:
                    self.clean_status_from(conf) # "inactive"
        # fallback Stop => Kill for ["simple","notify","forking"]
        elif not conf.getlist(Service, "ExecStop", []):
            logg.info("no ExecStop => systemctl kill")
            if True:
                self.do_kill_unit_from(conf)
                self.clean_pid_file_from(conf)
                self.clean_status_from(conf) # "inactive"
        elif runs in ["simple", "exec", "notify", "idle"]:
            status_file = self.get_status_file_from(conf)
            size = os.path.exists(status_file) and os.path.getsize(status_file)
            logg.info("STATUS %s %s", status_file, size)
            pid = 0
            for cmd in conf.getlist(Service, "ExecStop", []):
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
            pid = to_intN(env.get("MAINPID"))
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
            status_file = self.get_status_file_from(conf)
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist(Service, "ExecStop", []):
                # active = self.is_active_from(conf)
                if pid_file:
                    new_pid = self.read_mainpid_from(conf)
                    if new_pid:
                        env["MAINPID"] = strE(new_pid)
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("fork stop %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = to_intN(env.get("MAINPID"))
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
                    self.set_status_from(conf, "ExecStopCode", strE(returncode))
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
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
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
    def do_stop_socket_from(self, conf):
        runs = "socket"
        timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool(Socket, "Accept", "no")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None:
            logg.debug("unit could not be loaded (%s)", service_unit)
            logg.error("Unit %s not found.", service_unit)
            return False
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.exec_check_unit(conf, env, Socket, "ExecStop")
            if not okee and _no_reload: return False
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
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("post-stop %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-stop done (%s) <-%s>",
                           run.returncode or "OK", run.signal or "")
        return service_result == "success"
    def wait_vanished_pid(self, pid, timeout):
        if not pid:
            return True
        if not self.is_active_pid(pid):
            return True
        logg.info("wait for PID %s to vanish (%ss)", pid, timeout)
        for x in xrange(int(timeout)):
            time.sleep(1) # until TimeoutStopSec
            if not self.is_active_pid(pid):
                logg.info("wait for PID %s is done (%s.)", pid, x)
                return True
        logg.info("wait for PID %s failed (%s.)", pid, timeout)
        return False
    def reload_modules(self, *modules):
        """ [UNIT]... -- reload these units """
        self.wait_system()
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.reload_units(units) and found_all
    def reload_units(self, units):
        """ fails if any unit fails to reload """
        self.wait_system()
        done = True
        for unit in self.sortedAfter(units):
            if not self.reload_unit(unit):
                done = False
        return done
    def reload_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reload_unit_from(conf)
    def reload_unit_from(self, conf):
        if not conf: return False
        if self.syntax_check(conf) > 100: return False
        with waitlock(conf):
            logg.info(" reload unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_reload_unit_from(conf)
    def do_reload_unit_from(self, conf):
        if conf.name().endswith(".service"):
            return self.do_reload_service_from(conf)
        elif conf.name().endswith(".socket"):
            service_unit = self.get_socket_service_from(conf)
            service_conf = self.load_unit_conf(service_unit)
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
    def do_reload_service_from(self, conf):
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.exec_check_unit(conf, env, Service, "ExecReload")
            if not okee and _no_reload: return False
        initscript = conf.filename()
        if self.is_sysv_file(initscript):
            status_file = self.get_status_file_from(conf)
            if initscript:
                newcmd = [initscript, "reload"]
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                logg.info("%s reload %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: nocover
                run = subprocess_waitpid(forkpid)
                self.set_status_from(conf, "ExecReloadCode", run.returncode)
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
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                logg.info("%s reload %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and exe.check:
                    logg.error("Job for %s failed because the control process exited with error code. (%s)",
                               conf.name(), run.returncode)
                    return False
            time.sleep(MinimumYield)
            return True
        elif runs in ["oneshot"]:
            logg.debug("ignored run type '%s' for reload", runs)
            return True
        else:
            logg.error("unsupported run type '%s'", runs)
            return False
    def restart_modules(self, *modules):
        """ [UNIT]... -- restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.restart_units(units) and found_all
    def restart_units(self, units):
        """ fails if any unit fails to restart """
        self.wait_system()
        done = True
        for unit in self.sortedAfter(units):
            if not self.restart_unit(unit):
                done = False
        return done
    def restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.restart_unit_from(conf)
    def restart_unit_from(self, conf):
        if not conf: return False
        if self.syntax_check(conf) > 100: return False
        with waitlock(conf):
            if conf.name().endswith(".service"):
                logg.info(" restart service %s => %s", conf.name(), strQ(conf.filename()))
                if not self.is_active_from(conf):
                    return self.do_start_unit_from(conf)
                else:
                    return self.do_restart_unit_from(conf)
            else:
                return self.do_restart_unit_from(conf)
    def do_restart_unit_from(self, conf):
        logg.info("(restart) => stop/start %s", conf.name())
        self.do_stop_unit_from(conf)
        return self.do_start_unit_from(conf)
    def try_restart_modules(self, *modules):
        """ [UNIT]... -- try-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.try_restart_units(units) and found_all
    def try_restart_units(self, units):
        """ fails if any module fails to try-restart """
        self.wait_system()
        done = True
        for unit in self.sortedAfter(units):
            if not self.try_restart_unit(unit):
                done = False
        return done
    def try_restart_unit(self, unit):
        """ only do 'restart' if 'active' """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        with waitlock(conf):
            logg.info(" try-restart unit %s => %s", conf.name(), strQ(conf.filename()))
            if self.is_active_from(conf):
                return self.do_restart_unit_from(conf)
        return True
    def reload_or_restart_modules(self, *modules):
        """ [UNIT]... -- reload-or-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.reload_or_restart_units(units) and found_all
    def reload_or_restart_units(self, units):
        """ fails if any unit does not reload-or-restart """
        self.wait_system()
        done = True
        for unit in self.sortedAfter(units):
            if not self.reload_or_restart_unit(unit):
                done = False
        return done
    def reload_or_restart_unit(self, unit):
        """ do 'reload' if specified, otherwise do 'restart' """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reload_or_restart_unit_from(conf)
    def reload_or_restart_unit_from(self, conf):
        """ do 'reload' if specified, otherwise do 'restart' """
        if not conf: return False
        with waitlock(conf):
            logg.info(" reload-or-restart unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_reload_or_restart_unit_from(conf)
    def do_reload_or_restart_unit_from(self, conf):
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
    def reload_or_try_restart_modules(self, *modules):
        """ [UNIT]... -- reload-or-try-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.reload_or_try_restart_units(units) and found_all
    def reload_or_try_restart_units(self, units):
        """ fails if any unit fails to reload-or-try-restart """
        self.wait_system()
        done = True
        for unit in self.sortedAfter(units):
            if not self.reload_or_try_restart_unit(unit):
                done = False
        return done
    def reload_or_try_restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reload_or_try_restart_unit_from(conf)
    def reload_or_try_restart_unit_from(self, conf):
        with waitlock(conf):
            logg.info(" reload-or-try-restart unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_reload_or_try_restart_unit_from(conf)
    def do_reload_or_try_restart_unit_from(self, conf):
        if conf.getlist(Service, "ExecReload", []):
            return self.do_reload_unit_from(conf)
        elif not self.is_active_from(conf):
            return True
        else:
            return self.do_restart_unit_from(conf)
    def kill_modules(self, *modules):
        """ [UNIT]... -- kill these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.kill_units(units) and found_all
    def kill_units(self, units):
        """ fails if any unit could not be killed """
        self.wait_system()
        done = True
        for unit in self.sortedBefore(units):
            if not self.kill_unit(unit):
                done = False
        return done
    def kill_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.kill_unit_from(conf)
    def kill_unit_from(self, conf):
        if not conf: return False
        with waitlock(conf):
            logg.info(" kill unit %s => %s", conf.name(), strQ(conf.filename()))
            return self.do_kill_unit_from(conf)
    def do_kill_unit_from(self, conf):
        started = time.time()
        doSendSIGKILL = self.get_SendSIGKILL(conf)
        doSendSIGHUP = self.get_SendSIGHUP(conf)
        useKillMode = self.get_KillMode(conf)
        useKillSignal = self.get_KillSignal(conf)
        kill_signal = getattr(signal, useKillSignal)
        timeout = self.get_TimeoutStopSec(conf)
        status_file = self.get_status_file_from(conf)
        size = os.path.exists(status_file) and os.path.getsize(status_file)
        logg.info("STATUS %s %s", status_file, size)
        mainpid = self.read_mainpid_from(conf)
        self.clean_status_from(conf) # clear RemainAfterExit and TimeoutStartSec
        if not mainpid:
            if useKillMode in ["control-group"]:
                logg.warning("no main PID %s", strQ(conf.filename()))
                logg.warning("and there is no control-group here")
            else:
                logg.info("no main PID %s", strQ(conf.filename()))
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
            if time.time() > started + timeout:
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
            time.sleep(MinimumYield)
        # useKillMode in [ "control-group", "mixed", "process" ]
        if pid_exists(mainpid):
            logg.info("hard kill PID %s", mainpid)
            self._kill_pid(mainpid, signal.SIGKILL)
            time.sleep(MinimumYield)
        dead = not pid_exists(mainpid) or pid_zombie(mainpid)
        logg.info("done hard kill PID %s %s", mainpid, dead and "OK")
        return dead
    def _kill_pid(self, pid, kill_signal = None):
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
    def is_active_modules(self, *modules):
        """ [UNIT].. -- check if these units are in active state
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
        # |
        units = []
        results = []
        for module in modules:
            units = self.match_units(to_list(module))
            if not units:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                self.error |= NOT_ACTIVE
                results += ["inactive"]
                continue
            for unit in units:
                active = self.get_active_unit(unit)
                enabled = self.enabled_unit(unit)
                if enabled != "enabled" and ACTIVE_IF_ENABLED:
                    active = "inactive" # "unknown"
                results += [active]
                break
        # how it should work:
        status = "active" in results
        # how 'systemctl' works:
        non_active = [result for result in results if result != "active"]
        if non_active:
            self.error |= NOT_ACTIVE
        if non_active:
            self.error |= NOT_OK # status
        if _quiet:
            return []
        return results
    def is_active_from(self, conf):
        """ used in try-restart/other commands to check if needed. """
        if not conf: return False
        return self.get_active_from(conf) == "active"
    def active_pid_from(self, conf):
        if not conf: return False
        pid = self.read_mainpid_from(conf)
        return self.is_active_pid(pid)
    def is_active_pid(self, pid):
        """ returns pid if the pid is still an active process """
        if pid and pid_exists(pid) and not pid_zombie(pid):
            return pid # usually a string (not null)
        return None
    def get_active_unit(self, unit):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        conf = self.load_unit_conf(unit)
        if not conf:
            logg.warning("Unit %s not found.", unit)
            return "unknown"
        else:
            return self.get_active_from(conf)
    def get_active_from(self, conf):
        if conf.name().endswith(".service"):
            return self.get_active_service_from(conf)
        elif conf.name().endswith(".socket"):
            service_unit = self.get_socket_service_from(conf)
            service_conf = self.load_unit_conf(service_unit)
            return self.get_active_service_from(service_conf)
        elif conf.name().endswith(".target"):
            return self.get_active_target_from(conf)
        else:
            logg.debug("is-active not implemented for unit type: %s", conf.name())
            return "unknown" # TODO: "inactive" ?
    def get_active_service_from(self, conf):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        # used in try-restart/other commands to check if needed.
        if not conf: return "unknown"
        pid_file = self.pid_file_from(conf)
        if pid_file: # application PIDFile
            if not os.path.exists(pid_file):
                return "inactive"
        status_file = self.get_status_file_from(conf)
        if self.getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if DEBUG_STATUS:
                    logg.info("get_status_from %s => %s", conf.name(), state)
                return state
        pid = self.read_mainpid_from(conf)
        if DEBUG_STATUS:
            logg.debug("pid_file '%s' => PID %s", pid_file or status_file, strE(pid))
        if pid:
            if not pid_exists(pid) or pid_zombie(pid):
                return "failed"
            return "active"
        else:
            return "inactive"
    def get_active_target_from(self, conf):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        return self.get_active_target(conf.name())
    def get_active_target(self, target):
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
                conf = self.load_unit_conf(service)
                if conf:
                    state = self.get_active_from(conf)
                    if state in ["failed"]:
                        result = state
                    elif state not in ["active"]:
                        result = state
            return result
    def get_active_target_list(self):
        current_target = self.get_default_target()
        target_list = self.get_target_list(current_target)
        target_list += [DefaultUnit] # upper end
        target_list += [SysInitTarget] # lower end
        return target_list
    def get_substate_from(self, conf):
        """ returns 'running' 'exited' 'dead' 'failed' 'plugged' 'mounted' """
        if not conf: return None
        pid_file = self.pid_file_from(conf)
        if pid_file:
            if not os.path.exists(pid_file):
                return "dead"
        status_file = self.get_status_file_from(conf)
        if self.getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if state in ["active"]:
                    return self.get_status_from(conf, "SubState", "running")
                else:
                    return self.get_status_from(conf, "SubState", "dead")
        pid = self.read_mainpid_from(conf)
        if DEBUG_STATUS:
            logg.debug("pid_file '%s' => PID %s", pid_file or status_file, strE(pid))
        if pid:
            if not pid_exists(pid) or pid_zombie(pid):
                return "failed"
            return "running"
        else:
            return "dead"
    def is_failed_modules(self, *modules):
        """ [UNIT]... -- check if these units are in failes state
        implements True if any is-active = True """
        units = []
        results = []
        for module in modules:
            units = self.match_units(to_list(module))
            if not units:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                results += ["inactive"]
                continue
            for unit in units:
                active = self.get_active_unit(unit)
                enabled = self.enabled_unit(unit)
                if enabled != "enabled" and ACTIVE_IF_ENABLED:
                    active = "inactive"
                results += [active]
                break
        if "failed" in results:
            self.error = 0
        else:
            self.error |= NOT_OK
        if _quiet:
            return []
        return results
    def is_failed_from(self, conf):
        if conf is None: return True
        return self.get_active_from(conf) == "failed"
    def reset_failed_modules(self, *modules):
        """ [UNIT]... -- Reset failed state for all, one, or more units """
        units = []
        status = True
        for module in modules:
            units = self.match_units(to_list(module))
            if not units:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                return False
            for unit in units:
                if not self.reset_failed_unit(unit):
                    logg.error("Unit %s could not be reset.", unit_of(module))
                    status = False
                break
        return status
    def reset_failed_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if not conf:
            logg.warning("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.reset_failed_from(conf)
    def reset_failed_from(self, conf):
        if conf is None: return True
        if not self.is_failed_from(conf): return False
        done = False
        status_file = self.get_status_file_from(conf)
        if status_file and os.path.exists(status_file):
            try:
                os.remove(status_file)
                done = True
                logg.debug("done rm %s", status_file)
            except Exception as e:
                logg.error("while rm %s: %s", status_file, e)
        pid_file = self.pid_file_from(conf)
        if pid_file and os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                done = True
                logg.debug("done rm %s", pid_file)
            except Exception as e:
                logg.error("while rm %s: %s", pid_file, e)
        return done
    def status_modules(self, *modules):
        """ [UNIT]... check the status of these units.
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        result = self.status_units(units)
        # if not found_all:
        #     self.error |= NOT_OK | NOT_ACTIVE # 3
        #     # same as (dead) # original behaviour
        return result
    def status_units(self, units):
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
    def status_unit(self, unit):
        conf = self.get_unit_conf(unit)
        result = "%s - %s" % (unit, self.get_description_from(conf))
        loaded = conf.loaded()
        if loaded:
            filename = str(conf.filename())
            enabled = self.enabled_from(conf)
            result += "\n    Loaded: {loaded} ({filename}, {enabled})".format(**locals())
            for path in conf.overrides():
                result += "\n    Drop-In: {path}".format(**locals())
        else:
            result += "\n    Loaded: failed"
            return 3, result
        active = self.get_active_from(conf)
        substate = self.get_substate_from(conf)
        result += "\n    Active: {} ({})".format(active, substate)
        if active == "active":
            return 0, result
        else:
            return 3, result
    def cat_modules(self, *modules):
        """ [UNIT]... show the *.system file for these"
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        result = self.cat_units(units)
        if not found_all:
            self.error |= NOT_OK
        return result
    def cat_units(self, units):
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
    def cat_unit(self, unit):
        try:
            unit_file = self.unit_file(unit)
            if unit_file:
                return open(unit_file).read()
            logg.error("No files found for %s", unit)
        except Exception as e:
            print("Unit {} is not-loaded: {}".format(unit, e))
        self.error |= NOT_OK
        return None
    ##
    ##
    def load_preset_files(self, module = None): # -> [ preset-file-names,... ]
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
        return sorted(self._preset_file_list.keys())
    def get_preset_of_unit(self, unit):
        """ [UNIT] check the *.preset of this unit
        """
        self.load_preset_files()
        assert self._preset_file_list is not None
        for filename in sorted(self._preset_file_list.keys()):
            preset = self._preset_file_list[filename]
            status = preset.get_preset(unit)
            if status:
                return status
        return None
    def preset_modules(self, *modules):
        """ [UNIT]... -- set 'enabled' when in *.preset
        """
        if self.user_mode():
            logg.warning("preset makes no sense in --user mode")
            return True
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.preset_units(units) and found_all
    def preset_units(self, units):
        """ fails if any unit could not be changed """
        self.wait_system()
        fails = 0
        found = 0
        for unit in units:
            status = self.get_preset_of_unit(unit)
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
        return not fails and not not found
    def preset_all_modules(self, *modules):
        """ 'preset' all services
        enable or disable services according to *.preset files
        """
        if self.user_mode():
            logg.warning("preset-all makes no sense in --user mode")
            return True
        found_all = True
        units = self.match_units() # TODO: how to handle module arguments
        return self.preset_units(units) and found_all
    def wanted_from(self, conf, default = None):
        if not conf: return default
        return conf.get(Install, "WantedBy", default, True)
    def enablefolders(self, wanted):
        if self.user_mode():
            for folder in self.user_folders():
                yield self.default_enablefolder(wanted, folder)
        if True:
            for folder in self.system_folders():
                yield self.default_enablefolder(wanted, folder)
    def enablefolder(self, wanted):
        if self.user_mode():
            user_folder = self.user_folder()
            return self.default_enablefolder(wanted, user_folder)
        else:
            return self.default_enablefolder(wanted)
    def default_enablefolder(self, wanted, basefolder = None):
        basefolder = basefolder or self.system_folder()
        if not wanted:
            return wanted
        if not wanted.endswith(".wants"):
            wanted = wanted + ".wants"
        return os.path.join(basefolder, wanted)
    def enable_modules(self, *modules):
        """ [UNIT]... -- enable these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                logg.info("matched %s", unit)  # ++
                if unit not in units:
                    units += [unit]
        return self.enable_units(units) and found_all
    def enable_units(self, units):
        self.wait_system()
        done = True
        for unit in units:
            if not self.enable_unit(unit):
                done = False
            elif self._now:
                self.start_unit(unit)
        return done
    def enable_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        unit_file = conf.filename()
        if unit_file is None:
            logg.error("Unit file %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            if self.user_mode():
                logg.error("Initscript %s not for --user mode", unit)
                return False
            return self.enable_unit_sysv(unit_file)
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.enable_unit_from(conf)
    def enable_unit_from(self, conf):
        wanted = self.wanted_from(conf)
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
        if True:
            _f = self._force and "-f" or ""
            logg.info("ln -s {_f} '{source}' '{symlink}'".format(**locals()))
        if self._force and os.path.islink(symlink):
            os.remove(target)
        if not os.path.islink(symlink):
            os.symlink(source, symlink)
        return True
    def rc3_root_folder(self):
        old_folder = os_path(self._root, _rc3_boot_folder)
        new_folder = os_path(self._root, _rc3_init_folder)
        if os.path.isdir(old_folder): # pragma: no cover
            return old_folder
        return new_folder
    def rc5_root_folder(self):
        old_folder = os_path(self._root, _rc5_boot_folder)
        new_folder = os_path(self._root, _rc5_init_folder)
        if os.path.isdir(old_folder): # pragma: no cover
            return old_folder
        return new_folder
    def enable_unit_sysv(self, unit_file):
        # a "multi-user.target"/rc3 is also started in /rc5
        rc3 = self._enable_unit_sysv(unit_file, self.rc3_root_folder())
        rc5 = self._enable_unit_sysv(unit_file, self.rc5_root_folder())
        return rc3 and rc5
    def _enable_unit_sysv(self, unit_file, rc_folder):
        name = os.path.basename(unit_file)
        nameS = "S50"+name
        nameK = "K50"+name
        if not os.path.isdir(rc_folder):
            os.makedirs(rc_folder)
        # do not double existing entries
        for found in os.listdir(rc_folder):
            m = re.match(r"S\d\d(.*)", found)
            if m and m.group(1) == name:
                nameS = found
            m = re.match(r"K\d\d(.*)", found)
            if m and m.group(1) == name:
                nameK = found
        target = os.path.join(rc_folder, nameS)
        if not os.path.exists(target):
            os.symlink(unit_file, target)
        target = os.path.join(rc_folder, nameK)
        if not os.path.exists(target):
            os.symlink(unit_file, target)
        return True
    def disable_modules(self, *modules):
        """ [UNIT]... -- disable these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.disable_units(units) and found_all
    def disable_units(self, units):
        self.wait_system()
        done = True
        for unit in units:
            if not self.disable_unit(unit):
                done = False
            elif self._now:
                self.stop_unit(unit)
        return done
    def disable_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        unit_file = conf.filename()
        if unit_file is None:
            logg.error("Unit file %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            if self.user_mode():
                logg.error("Initscript %s not for --user mode", unit)
                return False
            return self.disable_unit_sysv(unit_file)
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.disable_unit_from(conf)
    def disable_unit_from(self, conf):
        wanted = self.wanted_from(conf)
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
                    logg.info("rm {_f} '{symlink}'".format(**locals()))
                    if os.path.islink(symlink) or self._force:
                        os.remove(symlink)
                except IOError as e:
                    logg.error("disable %s: %s", symlink, e)
                except OSError as e:
                    logg.error("disable %s: %s", symlink, e)
        return True
    def disable_unit_sysv(self, unit_file):
        rc3 = self._disable_unit_sysv(unit_file, self.rc3_root_folder())
        rc5 = self._disable_unit_sysv(unit_file, self.rc5_root_folder())
        return rc3 and rc5
    def _disable_unit_sysv(self, unit_file, rc_folder):
        # a "multi-user.target"/rc3 is also started in /rc5
        name = os.path.basename(unit_file)
        nameS = "S50"+name
        nameK = "K50"+name
        # do not forget the existing entries
        for found in os.listdir(rc_folder):
            m = re.match(r"S\d\d(.*)", found)
            if m and m.group(1) == name:
                nameS = found
            m = re.match(r"K\d\d(.*)", found)
            if m and m.group(1) == name:
                nameK = found
        target = os.path.join(rc_folder, nameS)
        if os.path.exists(target):
            os.unlink(target)
        target = os.path.join(rc_folder, nameK)
        if os.path.exists(target):
            os.unlink(target)
        return True
    def is_enabled_sysv(self, unit_file):
        name = os.path.basename(unit_file)
        target = os.path.join(self.rc3_root_folder(), "S50%s" % name)
        if os.path.exists(target):
            return True
        return False
    def is_enabled_modules(self, *modules):
        """ [UNIT]... -- check if these units are enabled
        returns True if any of them is enabled."""
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.is_enabled_units(units) # and found_all
    def is_enabled_units(self, units):
        """ true if any is enabled, and a list of infos """
        result = False
        infos = []
        for unit in units:
            infos += [self.enabled_unit(unit)]
            if self.is_enabled(unit):
                result = True
        if not result:
            self.error |= NOT_OK
        return infos
    def is_enabled(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s not found.", unit)
            return False
        unit_file = conf.filename()
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            return self.is_enabled_sysv(unit_file)
        state = self.get_enabled_from(conf)
        if state in ["enabled", "static"]:
            return True
        return False # ["disabled", "masked"]
    def enabled_unit(self, unit):
        conf = self.get_unit_conf(unit)
        return self.enabled_from(conf)
    def enabled_from(self, conf):
        unit_file = strE(conf.filename())
        if self.is_sysv_file(unit_file):
            state = self.is_enabled_sysv(unit_file)
            if state:
                return "enabled"
            return "disabled"
        return self.get_enabled_from(conf)
    def get_enabled_from(self, conf):
        if conf.masked:
            return "masked"
        wanted = self.wanted_from(conf)
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
    def mask_modules(self, *modules):
        """ [UNIT]... -- mask non-startable units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.mask_units(units) and found_all
    def mask_units(self, units):
        self.wait_system()
        done = True
        for unit in units:
            if not self.mask_unit(unit):
                done = False
        return done
    def mask_unit(self, unit):
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            logg.error("Initscript %s can not be masked", unit)
            return False
        conf = self.get_unit_conf(unit)
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        folder = self.mask_folder()
        if self._root:
            folder = os_path(self._root, folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        dev_null = _dev_null
        if True:
            _f = self._force and "-f" or ""
            logg.debug("ln -s {_f} {dev_null} '{target}'".format(**locals()))
        if self._force and os.path.islink(target):
            os.remove(target)
        if not os.path.exists(target):
            os.symlink(dev_null, target)
            logg.info("Created symlink {target} -> {dev_null}".format(**locals()))
            return True
        elif os.path.islink(target):
            logg.debug("mask symlink does already exist: %s", target)
            return True
        else:
            logg.error("mask target does already exist: %s", target)
            return False
    def mask_folder(self):
        for folder in self.mask_folders():
            if folder: return folder
        raise Exception("did not find any systemd/system folder")
    def mask_folders(self):
        if self.user_mode():
            for folder in self.user_folders():
                yield folder
        if True:
            for folder in self.system_folders():
                yield folder
    def unmask_modules(self, *modules):
        """ [UNIT]... -- unmask non-startable units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s not found.", unit_of(module))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.unmask_units(units) and found_all
    def unmask_units(self, units):
        self.wait_system()
        done = True
        for unit in units:
            if not self.unmask_unit(unit):
                done = False
        return done
    def unmask_unit(self, unit):
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            logg.error("Initscript %s can not be un/masked", unit)
            return False
        conf = self.get_unit_conf(unit)
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        folder = self.mask_folder()
        if self._root:
            folder = os_path(self._root, folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        if True:
            _f = self._force and "-f" or ""
            logg.info("rm {_f} '{target}'".format(**locals()))
        if os.path.islink(target):
            os.remove(target)
            return True
        elif not os.path.exists(target):
            logg.debug("Symlink did not exist anymore: %s", target)
            return True
        else:
            logg.warning("target is not a symlink: %s", target)
            return True
    def list_dependencies_modules(self, *modules):
        """ [UNIT]... show the dependency tree"
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.list_dependencies_units(units) # and found_all
    def list_dependencies_units(self, units):
        result = []
        for unit in units:
            if result:
                result += ["", ""]
            result += self.list_dependencies_unit(unit)
        return result
    def list_dependencies_unit(self, unit):
        result = []
        for line in self.list_dependencies(unit, ""):
            result += [line]
        return result
    def list_dependencies(self, unit, indent = None, mark = None, loop = []):
        mapping = {}
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
        conf = self.get_unit_conf(unit)
        if not conf.loaded():
            if not self._show_all:
                return
            yield "%s(%s): %s" % (indent, unit, mark)
        else:
            yield "%s%s: %s" % (indent, unit, mark)
            for stop_recursion in ["Conflict", "conflict", "reloaded", "Propagate"]:
                if stop_recursion in mark:
                    return
            for dep in deps:
                if dep in loop:
                    logg.debug("detected loop at %s", dep)
                    continue
                new_loop = loop + list(deps.keys())
                new_indent = indent + "| "
                new_mark = deps[dep]
                if not self._show_all:
                    if new_mark not in restrict:
                        continue
                if new_mark in mapping:
                    new_mark = mapping[new_mark]
                restrict = ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants"]
                for line in self.list_dependencies(dep, new_indent, new_mark, new_loop):
                    yield line
    def get_dependencies_unit(self, unit, styles = None):
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants", "PropagateReloadTo", "Conflicts", ]
        conf = self.get_unit_conf(unit)
        deps = {}
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
    def get_required_dependencies(self, unit, styles = None):
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo",
                            ".requires", ".wants"]
        return self.get_dependencies_unit(unit, styles)
    def get_start_dependencies(self, unit, styles = None): # pragma: no cover
        """ the list of services to be started as well / TODO: unused """
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants"]
        deps = {}
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
    def list_start_dependencies_modules(self, *modules):
        """ [UNIT]... show the dependency tree (experimental)"
        """
        return self.list_start_dependencies_units(list(modules))
    def list_start_dependencies_units(self, units):
        unit_order = []
        deps = {}
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
        deps_conf = []
        for dep in deps:
            if dep in unit_order:
                continue
            conf = self.get_unit_conf(dep)
            if conf.loaded():
                deps_conf.append(conf)
        for unit in unit_order:
            deps[unit] = ["Requested"]
            conf = self.get_unit_conf(unit)
            if conf.loaded():
                deps_conf.append(conf)
        result = []
        sortlist = conf_sortedAfter(deps_conf, cmp=compareAfter)
        for item in sortlist:
            line = (item.name(), "(%s)" % (" ".join(deps[item.name()])))
            result.append(line)
        return result
    def sortedAfter(self, unitlist):
        """ get correct start order for the unit list (ignoring masked units) """
        conflist = [self.get_unit_conf(unit) for unit in unitlist]
        if True:
            conflist = []
            for unit in unitlist:
                conf = self.get_unit_conf(unit)
                if conf.masked:
                    logg.debug("ignoring masked unit %s", unit)
                    continue
                conflist.append(conf)
        sortlist = conf_sortedAfter(conflist)
        return [item.name() for item in sortlist]
    def sortedBefore(self, unitlist):
        """ get correct start order for the unit list (ignoring masked units) """
        conflist = [self.get_unit_conf(unit) for unit in unitlist]
        if True:
            conflist = []
            for unit in unitlist:
                conf = self.get_unit_conf(unit)
                if conf.masked:
                    logg.debug("ignoring masked unit %s", unit)
                    continue
                conflist.append(conf)
        sortlist = conf_sortedAfter(reversed(conflist))
        return [item.name() for item in reversed(sortlist)]
    def daemon_reload_target(self):
        """ reload does will only check the service files here.
            The returncode will tell the number of warnings,
            and it is over 100 if it can not continue even
            for the relaxed systemctl.py style of execution. """
        errors = 0
        for unit in self.match_units():
            try:
                conf = self.get_unit_conf(unit)
            except Exception as e:
                logg.error("%s: can not read unit file %s\n\t%s",
                           unit, strQ(conf.filename()), e)
                continue
            errors += self.syntax_check(conf)
        if errors:
            logg.warning(" (%s) found %s problems", errors, errors % 100)
        return True # errors
    def syntax_check(self, conf):
        filename = conf.filename()
        if filename and filename.endswith(".service"):
            return self.syntax_check_service(conf)
        return 0
    def syntax_check_service(self, conf, section = Service):
        unit = conf.name()
        if not conf.data.has_section(Service):
            logg.error(" %s: a .service file without [Service] section", unit)
            return 101
        errors = 0
        haveType = conf.get(section, "Type", "simple")
        haveExecStart = conf.getlist(section, "ExecStart", [])
        haveExecStop = conf.getlist(section, "ExecStop", [])
        haveExecReload = conf.getlist(section, "ExecReload", [])
        usedExecStart = []
        usedExecStop = []
        usedExecReload = []
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
    def exec_check_unit(self, conf, env, section = Service, exectype = ""):
        if conf is None: # pragma: no cover (is never null)
            return True
        if not conf.data.has_section(section):
            return True  # pragma: no cover
        haveType = conf.get(section, "Type", "simple")
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
                mode, newcmd = self.exec_newcmd(cmd, env, conf)
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
                except Exception as e:
                    logg.error(" %s: User does not exist: %s (%s)", unit, user, getattr(e, "__doc__", ""))
                    badusers += 1
        for group in groups:
            if group:
                try: grp.getgrnam(self.expand_special(group, conf))
                except Exception as e:
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
        if True:
            filename = strE(conf.filename())
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
    def show_modules(self, *modules):
        """ [PATTERN]... -- Show properties of one or more units
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
        notfound = []
        units = []
        found_all = True
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                units += [module]
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        return self.show_units(units) + notfound # and found_all
    def show_units(self, units):
        logg.debug("show --property=%s", ",".join(self._only_property))
        result = []
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
    def show_unit_items(self, unit):
        """ [UNIT]... -- show properties of a unit.
        """
        logg.info("try read unit %s", unit)
        conf = self.get_unit_conf(unit)
        for entry in self.each_unit_items(unit, conf):
            yield entry
    def each_unit_items(self, unit, conf):
        loaded = conf.loaded()
        if not loaded:
            loaded = "not-loaded"
            if "NOT-FOUND" in self.get_description_from(conf):
                loaded = "not-found"
        names = {unit: 1, conf.name(): 1}
        yield "Id", conf.name()
        yield "Names", " ".join(sorted(names.keys()))
        yield "Description", self.get_description_from(conf) # conf.get(Unit, "Description")
        yield "PIDFile", self.get_pid_file(conf) # not self.pid_file_from w/o default location
        yield "PIDFilePath", self.pid_file_from(conf)
        yield "MainPID", strE(self.active_pid_from(conf))            # status["MainPID"] or PIDFile-read
        yield "SubState", self.get_substate_from(conf) or "unknown"  # status["SubState"] or notify-result
        yield "ActiveState", self.get_active_from(conf) or "unknown" # status["ActiveState"]
        yield "LoadState", loaded
        yield "UnitFileState", self.enabled_from(conf)
        yield "StatusFile", self.get_StatusFile(conf)
        yield "StatusFilePath", self.get_status_file_from(conf)
        yield "JournalFile", self.get_journal_log(conf)
        yield "JournalFilePath", self.get_journal_log_from(conf)
        yield "NotifySocket", self.get_notify_socket_from(conf)
        yield "User", self.get_User(conf) or ""
        yield "Group", self.get_Group(conf) or ""
        yield "SupplementaryGroups", " ".join(self.get_SupplementaryGroups(conf))
        yield "TimeoutStartUSec", seconds_to_time(self.get_TimeoutStartSec(conf))
        yield "TimeoutStopUSec", seconds_to_time(self.get_TimeoutStopSec(conf))
        yield "NeedDaemonReload", "no"
        yield "SendSIGKILL", strYes(self.get_SendSIGKILL(conf))
        yield "SendSIGHUP", strYes(self.get_SendSIGHUP(conf))
        yield "KillMode", strE(self.get_KillMode(conf))
        yield "KillSignal", strE(self.get_KillSignal(conf))
        yield "StartLimitBurst", strE(self.get_StartLimitBurst(conf))
        yield "StartLimitIntervalSec", seconds_to_time(self.get_StartLimitIntervalSec(conf))
        yield "RestartSec", seconds_to_time(self.get_RestartSec(conf))
        yield "RemainAfterExit", strYes(self.get_RemainAfterExit(conf))
        yield "WorkingDirectory", strE(self.get_WorkingDirectory(conf))
        env_parts = []
        for env_part in conf.getlist(Service, "Environment", []):
            env_parts.append(self.expand_special(env_part, conf))
        if env_parts:
            yield "Environment", " ".join(env_parts)
        env_files = []
        for env_file in conf.getlist(Service, "EnvironmentFile", []):
            env_files.append(self.expand_special(env_file, conf))
        if env_files:
            yield "EnvironmentFile", " ".join(env_files)
    def get_SendSIGKILL(self, conf):
        return conf.getbool(Service, "SendSIGKILL", "yes")
    def get_SendSIGHUP(self, conf):
        return conf.getbool(Service, "SendSIGHUP", "no")
    def get_KillMode(self, conf):
        return conf.get(Service, "KillMode", "control-group")
    def get_KillSignal(self, conf):
        return conf.get(Service, "KillSignal", "SIGTERM")
    #
    igno_centos = ["netconsole", "network"]
    igno_opensuse = ["raw", "pppoe", "*.local", "boot.*", "rpmconf*", "postfix*"]
    igno_ubuntu = ["mount*", "umount*", "ondemand", "*.local"]
    igno_always = ["network*", "dbus*", "systemd-*", "kdump*", "kmod*"]
    igno_always += ["purge-kernels.service", "after-local.service", "dm-event.*"] # as on opensuse
    igno_targets = ["remote-fs.target"]
    def _ignored_unit(self, unit, ignore_list):
        for ignore in ignore_list:
            if fnmatch.fnmatchcase(unit, ignore):
                return True # ignore
            if fnmatch.fnmatchcase(unit, ignore+".service"):
                return True # ignore
        return False
    def default_services_modules(self, *modules):
        """ show the default services
            This is used internally to know the list of service to be started in the 'get-default'
            target runlevel when the container is started through default initialisation. It will
            ignore a number of services - use '--all' to show a longer list of services and
            use '--all --force' if not even a minimal filter shall be used.
        """
        results = []
        targets = modules or [self.get_default_target()]
        for target in targets:
            units = self.target_default_services(target)
            logg.debug(" %s # %s", " ".join(units), target)
            for unit in units:
                if unit not in results:
                    results.append(unit)
        return results
    def target_default_services(self, target = None, sysv = "S"):
        """ get the default services for a target - this will ignore a number of services,
            use '--all' and --force' to get more services.
        """
        igno = self.igno_centos + self.igno_opensuse + self.igno_ubuntu + self.igno_always
        if self._show_all:
            igno = self.igno_always
            if self._force:
                igno = []
        logg.debug("ignored services filter for default.target:\n\t%s", igno)
        default_target = target or self.get_default_target()
        return self.enabled_target_services(default_target, sysv, igno)
    def enabled_target_services(self, target, sysv = "S", igno = []):
        units = []
        if self.user_mode():
            targetlist = self.get_target_list(target)
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
            targetlist = self.get_target_list(target)
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
    def enabled_target_user_local_units(self, target, unit_kind = ".service", igno = []):
        units = []
        for basefolder in self.user_folders():
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
    def enabled_target_user_system_units(self, target, unit_kind = ".service", igno = []):
        units = []
        for basefolder in self.system_folders():
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
                        conf = self.load_unit_conf(unit)
                        if conf is None:
                            pass
                        elif self.not_user_conf(conf):
                            pass
                        else:
                            units.append(unit)
        return units
    def enabled_target_installed_system_units(self, target, unit_type = ".service", igno = []):
        units = []
        for basefolder in self.system_folders():
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
    def enabled_target_configured_system_units(self, target, unit_type = ".service", igno = []):
        units = []
        if True:
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
    def enabled_target_sysv_units(self, target, sysv = "S", igno = []):
        units = []
        folders = []
        if target in ["multi-user.target", DefaultUnit]:
            folders += [self.rc3_root_folder()]
        if target in ["graphical.target"]:
            folders += [self.rc5_root_folder()]
        for folder in folders:
            if not os.path.isdir(folder):
                logg.warning("non-existent %s", folder)
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
    def required_target_units(self, target, unit_type, igno):
        units = []
        deps = self.get_required_dependencies(target)
        for unit in sorted(deps):
            if self._ignored_unit(unit, igno):
                continue # ignore
            if unit.endswith(unit_type):
                if unit not in units:
                    units.append(unit)
        return units
    def get_target_conf(self, module): # -> conf (conf | default-conf)
        """ accept that a unit does not exist
            and return a unit conf that says 'not-loaded' """
        conf = self.load_unit_conf(module)
        if conf is not None:
            return conf
        target_conf = self.default_unit_conf(module)
        if module in target_requires:
            target_conf.set(Unit, "Requires", target_requires[module])
        return target_conf
    def get_target_list(self, module):
        """ the Requires= in target units are only accepted if known """
        target = module
        if "." not in target: target += ".target"
        targets = [target]
        conf = self.get_target_conf(module)
        requires = conf.get(Unit, "Requires", "")
        while requires in target_requires:
            targets = [requires] + targets
            requires = target_requires[requires]
        logg.debug("the %s requires %s", module, targets)
        return targets
    def default_system(self, arg = True):
        """ start units for default system level
            This will go through the enabled services in the default 'multi-user.target'.
            However some services are ignored as being known to be installation garbage
            from unintended services. Use '--all' so start all of the installed services
            and with '--all --force' even those services that are otherwise wrong.
            /// SPECIAL: with --now or --init the init-loop is run and afterwards
                a system_halt is performed with the enabled services to be stopped."""
        self.sysinit_status(SubState = "initializing")
        logg.info("system default requested - %s", arg)
        init = self._now or self._init
        return self.start_system_default(init = init)
    def start_system_default(self, init = False):
        """ detect the default.target services and start them.
            When --init is given then the init-loop is run and
            the services are stopped again by 'systemctl halt'."""
        target = self.get_default_target()
        services = self.start_target_system(target, init)
        logg.info("%s system is up", target)
        if init:
            logg.info("init-loop start")
            sig = self.init_loop_until_stop(services)
            logg.info("init-loop %s", sig)
            self.stop_system_default()
        return not not services
    def start_target_system(self, target, init = False):
        services = self.target_default_services(target, "S")
        self.sysinit_status(SubState = "starting")
        self.start_units(services)
        return services
    def do_start_target_from(self, conf):
        target = conf.name()
        # services = self.start_target_system(target)
        services = self.target_default_services(target, "S")
        units = [service for service in services if not self.is_running_unit(service)]
        logg.debug("start %s is starting %s from %s", target, units, services)
        return self.start_units(units)
    def stop_system_default(self):
        """ detect the default.target services and stop them.
            This is commonly run through 'systemctl halt' or
            at the end of a 'systemctl --init default' loop."""
        target = self.get_default_target()
        services = self.stop_target_system(target)
        logg.info("%s system is down", target)
        return not not services
    def stop_target_system(self, target):
        services = self.target_default_services(target, "K")
        self.sysinit_status(SubState = "stopping")
        self.stop_units(services)
        return services
    def do_stop_target_from(self, conf):
        target = conf.name()
        # services = self.stop_target_system(target)
        services = self.target_default_services(target, "K")
        units = [service for service in services if self.is_running_unit(service)]
        logg.debug("stop %s is stopping %s from %s", target, units, services)
        return self.stop_units(units)
    def do_reload_target_from(self, conf):
        target = conf.name()
        return self.reload_target_system(target)
    def reload_target_system(self, target):
        services = self.target_default_services(target, "S")
        units = [service for service in services if self.is_running_unit(service)]
        return self.reload_units(units)
    def halt_target(self, arg = True):
        """ stop units from default system level """
        logg.info("system halt requested - %s", arg)
        done = self.stop_system_default()
        try:
            os.kill(1, signal.SIGQUIT) # exit init-loop on no_more_procs
        except Exception as e:
            logg.warning("SIGQUIT to init-loop on PID-1: %s", e)
        return done
    def system_get_default(self):
        """ get current default run-level"""
        return self.get_default_target()
    def get_targets_folder(self):
        return os_path(self._root, self.mask_folder())
    def get_default_target_file(self):
        targets_folder = self.get_targets_folder()
        return os.path.join(targets_folder, DefaultUnit)
    def get_default_target(self, default_target = None):
        """ get current default run-level"""
        current = default_target or self._default_target
        default_target_file = self.get_default_target_file()
        if os.path.islink(default_target_file):
            current = os.path.basename(os.readlink(default_target_file))
        return current
    def set_default_modules(self, *modules):
        """ set current default run-level"""
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
            for targetname, targetpath in self.each_target_file():
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
    def init_modules(self, *modules):
        """ [UNIT*] -- init loop: '--init default' or '--init start UNIT*'
        The systemctl init service will start the enabled 'default' services,
        and then wait for any  zombies to be reaped. When a SIGINT is received
        then a clean shutdown of the enabled services is ensured. A Control-C in
        in interactive mode will also run 'stop' on all the enabled services. //
        When a UNIT name is given then only that one is started instead of the
        services in the 'default.target'. Using 'init UNIT' is better than
        '--init start UNIT' because the UNIT is also stopped cleanly even when
        it was never enabled in the system.
        /// SPECIAL: when using --now then only the init-loop is started,
        with the reap-zombies function and waiting for an interrupt.
        (and no unit is started/stoppped wether given or not).
        """
        if self._now:
            result = self.init_loop_until_stop([])
            return not not result
        if not modules:
            # like 'systemctl --init default'
            if self._now or self._show_all:
                logg.debug("init default --now --all => no_more_procs")
                self.doExitWhenNoMoreProcs = True
            return self.start_system_default(init = True)
        #
        # otherwise quit when all the init-services have died
        self.doExitWhenNoMoreServices = True
        if self._now or self._show_all:
            logg.debug("init services --now --all => no_more_procs")
            self.doExitWhenNoMoreProcs = True
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [unit]
        logg.info("init %s -> start %s", ",".join(modules), ",".join(units))
        done = self.start_units(units, init = True)
        logg.info("-- init is done")
        return done # and found_all
    def start_log_files(self, units):
        self._log_file = {}
        self._log_hold = {}
        for unit in units:
            conf = self.load_unit_conf(unit)
            if not conf: continue
            if self.skip_journal_log(conf): continue
            log_path = self.get_journal_log_from(conf)
            try:
                opened = os.open(log_path, os.O_RDONLY | os.O_NONBLOCK)
                self._log_file[unit] = opened
                self._log_hold[unit] = b""
            except Exception as e:
                logg.error("can not open %s log: %s\n\t%s", unit, log_path, e)
    def read_log_files(self, units):
        self.print_log_files(units)
    def print_log_files(self, units, stdout = 1):
        BUFSIZE=8192
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
                        except Exception: 
                            pass
                        printed += 1
                    except BlockingIOError:
                        pass
        return printed
    def stop_log_files(self, units):
        for unit in units:
            try:
                if unit in self._log_file:
                    if self._log_file[unit]:
                        os.close(self._log_file[unit])
            except Exception as e:
                logg.error("can not close log: %s\n\t%s", unit, e)
        self._log_file = {}
        self._log_hold = {}

    def get_StartLimitBurst(self, conf):
        defaults = DefaultStartLimitBurst
        return to_int(conf.get(Service, "StartLimitBurst", strE(defaults)), defaults) # 5
    def get_StartLimitIntervalSec(self, conf, maximum = None):
        maximum = maximum or 999
        defaults = DefaultStartLimitIntervalSec
        interval = conf.get(Service, "StartLimitIntervalSec", strE(defaults)) # 10s
        return time_to_seconds(interval, maximum)
    def get_RestartSec(self, conf, maximum = None):
        maximum = maximum or DefaultStartLimitIntervalSec
        delay = conf.get(Service, "RestartSec", strE(DefaultRestartSec))
        return time_to_seconds(delay, maximum)
    def restart_failed_units(self, units, maximum = None):
        """ This function will restart failed units.
        /
        NOTE that with standard settings the LimitBurst implementation has no effect. If
        the InitLoopSleep is ticking at the Default of 5sec and the LimitBurst Default
        is 5x within a Default 10secs time frame then within those 10sec only 2 loop
        rounds have come here checking for possible restarts. You can directly shorten
        the interval ('-c InitLoopSleep=1') or have it indirectly shorter from the
        service descriptor's RestartSec ("RestartSec=2s").
        """
        global InitLoopSleep
        me = os.getpid()
        maximum = maximum or DefaultStartLimitIntervalSec
        restartDelay = MinimumYield
        for unit in units:
            now = time.time()
            try:
                conf = self.load_unit_conf(unit)
                if not conf: continue
                restartPolicy = conf.get(Service, "Restart", "no")
                if restartPolicy in ["no", "on-success"]:
                    logg.debug("[%s] [%s] Current NoCheck (Restart=%s)", me, unit, restartPolicy)
                    continue
                restartSec = self.get_RestartSec(conf)
                if restartSec == 0:
                    if InitLoopSleep > 1:
                        logg.warning("[%s] set InitLoopSleep from %ss to 1 (caused by RestartSec=0!)",
                                     unit, InitLoopSleep)
                        InitLoopSleep = 1
                elif restartSec > 0.9 and restartSec < InitLoopSleep:
                    restartSleep = int(restartSec + 0.2)
                    if restartSleep < InitLoopSleep:
                        logg.warning("[%s] set InitLoopSleep from %ss to %s (caused by RestartSec=%.3fs)",
                                     unit, InitLoopSleep, restartSleep, restartSec)
                        InitLoopSleep = restartSleep
                isUnitState = self.get_active_from(conf)
                isUnitFailed = isUnitState in ["failed"]
                logg.debug("[%s] [%s] Current Status: %s (%s)", me, unit, isUnitState, isUnitFailed)
                if not isUnitFailed:
                    if unit in self._restart_failed_units:
                        del self._restart_failed_units[unit]
                    continue
                limitBurst = self.get_StartLimitBurst(conf)
                limitSecs = self.get_StartLimitIntervalSec(conf)
                if limitBurst > 1 and limitSecs >= 1:
                    try:
                        if unit not in self._restarted_unit:
                            self._restarted_unit[unit] = []
                            # we want to register restarts from now on
                        restarted = self._restarted_unit[unit]
                        logg.debug("[%s] [%s] Current limitSecs=%ss limitBurst=%sx (restarted %sx)",
                                   me, unit, limitSecs, limitBurst, len(restarted))
                        oldest = 0.
                        interval = 0.
                        if len(restarted) >= limitBurst:
                            logg.debug("[%s] [%s] restarted %s",
                                       me, unit, ["%.3fs" % (t - now) for t in restarted])
                            while len(restarted):
                                oldest = restarted[0]
                                interval = time.time() - oldest
                                if interval > limitSecs:
                                    restarted = restarted[1:]
                                    continue
                                break
                            self._restarted_unit[unit] = restarted
                            logg.debug("[%s] [%s] ratelimit %s",
                                       me, unit, ["%.3fs" % (t - now) for t in restarted])
                            # all values in restarted have a time below limitSecs
                        if len(restarted) >= limitBurst:
                            logg.info("[%s] [%s] Blocking Restart - oldest %s is %s ago (allowed %s)",
                                      me, unit, oldest, interval, limitSecs)
                            self.write_status_from(conf, AS="error")
                            unit = "" # dropped out
                            continue
                    except Exception as e:
                        logg.error("[%s] burst exception %s", unit, e)
                if unit: # not dropped out
                    if unit not in self._restart_failed_units:
                        self._restart_failed_units[unit] = now + restartSec
                        logg.debug("[%s] [%s] restart scheduled in %+.3fs",
                                   me, unit, (self._restart_failed_units[unit] - now))
            except Exception as e:
                logg.error("[%s] [%s] An error occurred while restart checking: %s", me, unit, e)
        if not self._restart_failed_units:
            self.error |= NOT_OK
            return []
        # NOTE: this function is only called from InitLoop when "running"
        # let's check if any of the restart_units has its restartSec expired
        now = time.time()
        restart_done = []
        logg.debug("[%s] Restart checking  %s",
                   me, ["%+.3fs" % (t - now) for t in self._restart_failed_units.values()])
        for unit in sorted(self._restart_failed_units):
            restartAt = self._restart_failed_units[unit]
            if restartAt > now:
                continue
            restart_done.append(unit)
            try:
                conf = self.load_unit_conf(unit)
                if not conf: continue
                isUnitState = self.get_active_from(conf)
                isUnitFailed = isUnitState in ["failed"]
                logg.debug("[%s] [%s] Restart Status: %s (%s)", me, unit, isUnitState, isUnitFailed)
                if isUnitFailed:
                    logg.debug("[%s] [%s] --- restarting failed unit...", me, unit)
                    self.restart_unit(unit)
                    logg.debug("[%s] [%s] --- has been restarted.", me, unit)
                    if unit in self._restarted_unit:
                        self._restarted_unit[unit].append(time.time())
            except Exception as e:
                logg.error("[%s] [%s] An error occurred while restarting: %s", me, unit, e)
        for unit in restart_done:
            if unit in self._restart_failed_units:
                del self._restart_failed_units[unit]
        logg.debug("[%s] Restart remaining %s",
                   me, ["%+.3fs" % (t - now) for t in self._restart_failed_units.values()])
        return restart_done

    def init_loop_until_stop(self, units):
        """ this is the init-loop - it checks for any zombies to be reaped and
            waits for an interrupt. When a SIGTERM /SIGINT /Control-C signal
            is received then the signal name is returned. Any other signal will
            just raise an Exception like one would normally expect. As a special
            the 'systemctl halt' emits SIGQUIT which puts it into no_more_procs mode."""
        signal.signal(signal.SIGQUIT, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGQUIT"))
        signal.signal(signal.SIGINT, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGINT"))
        signal.signal(signal.SIGTERM, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGTERM"))
        result = None
        #
        self.start_log_files(units)
        logg.debug("start listen")
        listen = SystemctlListenThread(self)
        logg.debug("starts listen")
        listen.start()
        logg.debug("started listen")
        self.sysinit_status(ActiveState = "active", SubState = "running")
        timestamp = time.time()
        while True:
            try:
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("DONE InitLoop (sleep %ss)", InitLoopSleep)
                sleep_sec = InitLoopSleep - (time.time() - timestamp)
                if sleep_sec < MinimumYield:
                    sleep_sec = MinimumYield
                sleeping = sleep_sec
                while sleeping > 2:
                    time.sleep(1) # accept signals atleast every second
                    sleeping = InitLoopSleep - (time.time() - timestamp)
                    if sleeping < MinimumYield:
                        sleeping = MinimumYield
                        break
                time.sleep(sleeping) # remainder waits less that 2 seconds
                timestamp = time.time()
                self.loop.acquire()
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("NEXT InitLoop (after %ss)", sleep_sec)
                self.read_log_files(units)
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("reap zombies - check current processes")
                running = self.reap_zombies()
                if DEBUG_INITLOOP: # pragma: no cover
                    logg.debug("reap zombies - init-loop found %s running procs", running)
                if self.doExitWhenNoMoreServices:
                    active = False
                    for unit in units:
                        conf = self.load_unit_conf(unit)
                        if not conf: continue
                        if self.is_active_from(conf):
                            active = True
                    if not active:
                        logg.info("no more services - exit init-loop")
                        break
                if self.doExitWhenNoMoreProcs:
                    if not running:
                        logg.info("no more procs - exit init-loop")
                        break
                if RESTART_FAILED_UNITS:
                    self.restart_failed_units(units)
                self.loop.release()
            except KeyboardInterrupt as e:
                if e.args and e.args[0] == "SIGQUIT":
                    # the original systemd puts a coredump on that signal.
                    logg.info("SIGQUIT - switch to no more procs check")
                    self.doExitWhenNoMoreProcs = True
                    continue
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                logg.info("interrupted - exit init-loop")
                result = str(e) or "STOPPED"
                break
            except Exception as e:
                logg.info("interrupted - exception %s", e)
                raise
        self.sysinit_status(ActiveState = None, SubState = "degraded")
        try: self.loop.release()
        except: pass
        listen.stop()
        listen.join(2)
        self.read_log_files(units)
        self.read_log_files(units)
        self.stop_log_files(units)
        logg.debug("done - init loop")
        return result
    def reap_zombies_target(self):
        """ -- check to reap children (internal) """
        running = self.reap_zombies()
        return "remaining {running} process".format(**locals())
    def reap_zombies(self):
        """ check to reap children """
        selfpid = os.getpid()
        running = 0
        for pid_entry in os.listdir(_proc_pid_dir):
            pid = to_intN(pid_entry)
            if pid is None:
                continue
            if pid == selfpid:
                continue
            proc_status = _proc_pid_status.format(**locals())
            if os.path.isfile(proc_status):
                zombie = False
                ppid = -1
                try:
                    for line in open(proc_status):
                        m = re.match(r"State:\s*Z.*", line)
                        if m: zombie = True
                        m = re.match(r"PPid:\s*(\d+)", line)
                        if m: ppid = int(m.group(1))
                except IOError as e:
                    logg.warning("%s : %s", proc_status, e)
                    continue
                if zombie and ppid == os.getpid():
                    logg.info("reap zombie %s", pid)
                    try: os.waitpid(pid, os.WNOHANG)
                    except OSError as e:
                        logg.warning("reap zombie %s: %s", e.strerror)
            if os.path.isfile(proc_status):
                if pid > 1:
                    running += 1
        return running # except PID 0 and PID 1
    def sysinit_status(self, **status):
        conf = self.sysinit_target()
        self.write_status_from(conf, **status)
    def sysinit_target(self):
        if not self._sysinit_target:
            self._sysinit_target = self.default_unit_conf(SysInitTarget, "System Initialization")
        assert self._sysinit_target is not None
        return self._sysinit_target
    def is_system_running(self):
        conf = self.sysinit_target()
        if not self.is_running_unit_from(conf):
            time.sleep(MinimumYield)
        if not self.is_running_unit_from(conf):
            return "offline"
        status = self.read_status_from(conf)
        return status.get("SubState", "unknown")
    def is_system_running_info(self):
        state = self.is_system_running()
        if state not in ["running"]:
            self.error |= NOT_OK # 1
        if self._quiet:
            return None
        return state
    def wait_system(self, target = None):
        target = target or SysInitTarget
        for attempt in xrange(int(SysInitWait)):
            state = self.is_system_running()
            if "init" in state:
                if target in [SysInitTarget, "basic.target"]:
                    logg.info("system not initialized - wait %s", target)
                    time.sleep(1)
                    continue
            if "start" in state or "stop" in state:
                if target in ["basic.target"]:
                    logg.info("system not running - wait %s", target)
                    time.sleep(1)
                    continue
            if "running" not in state:
                logg.info("system is %s", state)
            break
    def is_running_unit_from(self, conf):
        status_file = self.get_status_file_from(conf)
        pid_file = self.pid_file_from(conf)
        return self.getsize(status_file) > 0 or self.getsize(pid_file) > 0
    def is_running_unit(self, unit):
        conf = self.get_unit_conf(unit)
        return self.is_running_unit_from(conf)
    def pidlist_of(self, pid):
        if not pid:
            return []
        pidlist = [pid]
        pids = [pid]
        for depth in xrange(PROC_MAX_DEPTH):
            for pid_entry in os.listdir(_proc_pid_dir):
                pid = to_intN(pid_entry)
                if pid is None:
                    continue
                proc_status = _proc_pid_status.format(**locals())
                if os.path.isfile(proc_status):
                    try:
                        for line in open(proc_status):
                            if line.startswith("PPid:"):
                                ppid_text = line[len("PPid:"):].strip()
                                try: ppid = int(ppid_text)
                                except: continue
                                if ppid in pidlist and pid not in pids:
                                    pids += [pid]
                    except IOError as e:
                        logg.warning("%s : %s", proc_status, e)
                        continue
            if len(pids) != len(pidlist):
                pidlist = pids[:]
                continue
        return pids
    def echo(self, *targets):
        line = " ".join(*targets)
        logg.info(" == echo == %s", line)
        return line
    def killall(self, *targets):
        mapping = {}
        mapping[":3"] = signal.SIGQUIT
        mapping[":QUIT"] = signal.SIGQUIT
        mapping[":6"] = signal.SIGABRT
        mapping[":ABRT"] = signal.SIGABRT
        mapping[":9"] = signal.SIGKILL
        mapping[":KILL"] = signal.SIGKILL
        sig = signal.SIGTERM
        for target in targets:
            if target.startswith(":"):
                if target in mapping:
                    sig = mapping[target]
                else: # pragma: no cover
                    logg.error("unsupported %s", target)
                continue
            for pid_entry in os.listdir(_proc_pid_dir):
                pid = to_intN(pid_entry)
                if pid:
                    try:
                        cmdline = _proc_pid_cmdline.format(**locals())
                        cmd = open(cmdline).read().split("\0")
                        if DEBUG_KILLALL: logg.debug("cmdline %s", cmd)
                        found = None
                        cmd_exe = os.path.basename(cmd[0])
                        if DEBUG_KILLALL: logg.debug("cmd.exe '%s'", cmd_exe)
                        if fnmatch.fnmatchcase(cmd_exe, target): found = "exe"
                        if len(cmd) > 1 and cmd_exe.startswith("python"):
                            X = 1
                            while cmd[X].startswith("-"): X += 1 # atleast '-u' unbuffered
                            cmd_arg = os.path.basename(cmd[X])
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
                    except Exception as e:
                        logg.error("kill -%s %s : %s", sig, pid, e)
        return True
    def force_ipv4(self, *args):
        """ only ipv4 localhost in /etc/hosts """
        logg.debug("checking hosts sysconf for '::1 localhost'")
        lines = []
        sysconf_hosts = os_path(self._root, _etc_hosts)
        for line in open(sysconf_hosts):
            if "::1" in line:
                newline = re.sub("\\slocalhost\\s", " ", line)
                if line != newline:
                    logg.info("%s: '%s' => '%s'", _etc_hosts, line.rstrip(), newline.rstrip())
                    line = newline
            lines.append(line)
        f = open(sysconf_hosts, "w")
        for line in lines:
            f.write(line)
        f.close()
    def force_ipv6(self, *args):
        """ only ipv4 localhost in /etc/hosts """
        logg.debug("checking hosts sysconf for '127.0.0.1 localhost'")
        lines = []
        sysconf_hosts = os_path(self._root, _etc_hosts)
        for line in open(sysconf_hosts):
            if "127.0.0.1" in line:
                newline = re.sub("\\slocalhost\\s", " ", line)
                if line != newline:
                    logg.info("%s: '%s' => '%s'", _etc_hosts, line.rstrip(), newline.rstrip())
                    line = newline
            lines.append(line)
        f = open(sysconf_hosts, "w")
        for line in lines:
            f.write(line)
        f.close()
    def help_modules(self, *args):
        """[command] -- show this help
        """
        lines = []
        okay = True
        prog = os.path.basename(sys.argv[0])
        if not args:
            argz = {}
            for name in dir(self):
                arg = None
                if name.startswith("system_"):
                    arg = name[len("system_"):].replace("_", "-")
                if name.startswith("show_"):
                    arg = name[len("show_"):].replace("_", "-")
                if name.endswith("_of_unit"):
                    arg = name[:-len("_of_unit")].replace("_", "-")
                if name.endswith("_modules"):
                    arg = name[:-len("_modules")].replace("_", "-")
                if arg:
                    argz[arg] = name
            lines.append("%s command [options]..." % prog)
            lines.append("")
            lines.append("Commands:")
            for arg in sorted(argz):
                name = argz[arg]
                method = getattr(self, name)
                doc = "..."
                doctext = getattr(method, "__doc__")
                if doctext:
                    doc = doctext
                elif not self._show_all:
                    continue # pragma: no cover
                firstline = doc.split("\n")[0]
                doc_text = firstline.strip()
                if "--" not in firstline:
                    doc_text = "-- " + doc_text
                lines.append(" %s %s" % (arg, firstline.strip()))
            return lines
        for arg in args:
            arg = arg.replace("-", "_")
            func1 = getattr(self.__class__, arg+"_modules", None)
            func2 = getattr(self.__class__, arg+"_of_unit", None)
            func3 = getattr(self.__class__, "show_"+arg, None)
            func4 = getattr(self.__class__, "system_"+arg, None)
            func5 = None
            if arg.startswith("__"):
                func5 = getattr(self.__class__, arg[2:], None)
            func = func1 or func2 or func3 or func4 or func5
            if func is None:
                print("error: no such command '%s'" % arg)
                okay = False
            else:
                doc_text = "..."
                doc = getattr(func, "__doc__", "")
                if doc:
                    doc_text = doc.replace("\n", "\n\n", 1).strip()
                    if "--" not in doc_text:
                        doc_text = "-- " + doc_text
                else:
                    func_name = arg # FIXME
                    logg.debug("__doc__ of %s is none", func_name)
                    if not self._show_all: continue
                lines.append("%s %s %s" % (prog, arg, doc_text))
        if not okay:
            self.help_modules()
            self.error |= NOT_OK
            return []
        return lines
    def systemd_version(self):
        """ the version line for systemd compatibility """
        return "systemd %s\n  - via systemctl.py %s" % (self._systemd_version, __version__)
    def systemd_features(self):
        """ the info line for systemd features """
        features1 = "-PAM -AUDIT -SELINUX -IMA -APPARMOR -SMACK"
        features2 = " +SYSVINIT -UTMP -LIBCRYPTSETUP -GCRYPT -GNUTLS"
        features3 = " -ACL -XZ -LZ4 -SECCOMP -BLKID -ELFUTILS -KMOD -IDN"
        return features1+features2+features3
    def version_info(self):
        return [self.systemd_version(), self.systemd_features()]
    def test_float(self):
        return 0. # "Unknown result type"

def print_begin(argv, args):
    script = os.path.realpath(argv[0])
    system = _user_mode and " --user" or " --system"
    init = _init and " --init" or ""
    logg.info("EXEC BEGIN %s %s%s%s", script, " ".join(args), system, init)
    if _root and not is_good_root(_root):
        root44 = path44(_root)
        logg.warning("the --root=%s should have atleast three levels /tmp/test_123/root", root44)

def print_begin2(args):
    logg.debug("======= systemctl.py %s", " ".join(args))

def is_not_ok(result):
    if DebugPrintResult:
        logg.log(HINT, "EXEC END %s", result)
    if result is False:
        return NOT_OK
    return 0

def print_str(result):
    if result is None:
        if DebugPrintResult:
            logg.debug("    END %s", result)
        return
    print(result)
    if DebugPrintResult:
        result1 = result.split("\n")[0][:-20]
        if result == result1:
            logg.log(HINT, "EXEC END '%s'", result)
        else:
            logg.log(HINT, "EXEC END '%s...'", result1)
            logg.debug("    END '%s'", result)
def print_str_list(result):
    if result is None:
        if DebugPrintResult:
            logg.debug("    END %s", result)
        return
    shown = 0
    for element in result:
        print(element)
        shown += 1
    if DebugPrintResult:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)
def print_str_list_list(result):
    shown = 0
    for element in result:
        print("\t".join([str(elem) for elem in element]))
        shown += 1
    if DebugPrintResult:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)
def print_str_dict(result):
    if result is None:
        if DebugPrintResult:
            logg.debug("    END %s", result)
        return
    shown = 0
    for key in sorted(result.keys()):
        element = result[key]
        print("%s=%s" % (key, element))
        shown += 1
    if DebugPrintResult:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)
def print_str_dict_dict(result):
    if result is None:
        if DebugPrintResult:
            logg.debug("    END %s", result)
        return
    shown = 0
    for key in sorted(result):
        element = result[key]
        for name in sorted(element):
            value = element[name]
            print("%s [%s] %s" % (key, value, name))
        shown += 1
    if DebugPrintResult:
        logg.log(HINT, "EXEC END %i items", shown)
        logg.debug("    END %s", result)

def run(command, *modules):
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
        print_str(systemctl.get_preset_of_unit(*modules))
    elif command in ["halt"]:
        exitcode = is_not_ok(systemctl.halt_target())
    elif command in ["init"]:
        exitcode = is_not_ok(systemctl.init_modules(*modules))
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
        print_str(systemctl.get_description(*modules))
    elif command in ["__get_status_file"]:
        print_str(systemctl.get_status_file(modules[0]))
    elif command in ["__get_status_pid_file", "__get_pid_file"]:
        print_str(systemctl.get_status_pid_file(modules[0]))
    elif command in ["__disable_unit"]:
        exitcode = is_not_ok(systemctl.disable_unit(*modules))
    elif command in ["__enable_unit"]:
        exitcode = is_not_ok(systemctl.enable_unit(*modules))
    elif command in ["__is_enabled"]:
        exitcode = is_not_ok(systemctl.is_enabled(*modules))
    elif command in ["__killall"]:
        exitcode = is_not_ok(systemctl.killall(*modules))
    elif command in ["__kill_unit"]:
        exitcode = is_not_ok(systemctl.kill_unit(*modules))
    elif command in ["__load_preset_files"]:
        print_str_list(systemctl.load_preset_files(*modules))
    elif command in ["__mask_unit"]:
        exitcode = is_not_ok(systemctl.mask_unit(*modules))
    elif command in ["__read_env_file"]:
        print_str_list_list(list(systemctl.read_env_file(*modules)))
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

if __name__ == "__main__":
    import optparse
    _o = optparse.OptionParser("%prog [options] command [name...]",
                               epilog="use 'help' command for more information")
    _o.add_option("--version", action="store_true",
                  help="Show package version")
    _o.add_option("--system", action="store_true", default=False,
                  help="Connect to system manager (default)") # overrides --user
    _o.add_option("--user", action="store_true", default=_user_mode,
                  help="Connect to user service manager")
    # _o.add_option("-H", "--host", metavar="[USER@]HOST",
    #     help="Operate on remote host*")
    # _o.add_option("-M", "--machine", metavar="CONTAINER",
    #     help="Operate on local container*")
    _o.add_option("-t", "--type", metavar="TYPE", action="append", dest="only_type", default=_only_type,
                  help="List units of a particual type")
    _o.add_option("--state", metavar="STATE", action="append", dest="only_state", default=_only_state,
                  help="List units with particular LOAD or SUB or ACTIVE state")
    _o.add_option("-p", "--property", metavar="NAME", action="append", dest="only_property", default=_only_property,
                  help="Show only properties by this name")
    _o.add_option("--what", metavar="TYPE", action="append", dest="only_what", default=_only_what,
                  help="Defines the service directories to be cleaned (configuration, state, cache, logs, runtime)")
    _o.add_option("-a", "--all", action="store_true", dest="show_all", default=_show_all,
                  help="Show all loaded units/properties, including dead empty ones. To list all units installed on the system, use the 'list-unit-files' command instead")
    _o.add_option("-l", "--full", action="store_true", default=_full,
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
    _o.add_option("--now", action="store_true", default=_now,
                  help="Start or stop unit in addition to enabling or disabling it")
    _o.add_option("-q", "--quiet", action="store_true", default=_quiet,
                  help="Suppress output")
    _o.add_option("--no-block", action="store_true", default=False,
                  help="Do not wait until operation finished (ignored)")
    _o.add_option("--no-legend", action="store_true", default=_no_legend,
                  help="Do not print a legend (column headers and hints)")
    _o.add_option("--no-wall", action="store_true", default=False,
                  help="Don't send wall message before halt/power-off/reboot (ignored)")
    _o.add_option("--no-reload", action="store_true", default=_no_reload,
                  help="Don't reload daemon after en-/dis-abling unit files")
    _o.add_option("--no-ask-password", action="store_true", default=_no_ask_password,
                  help="Do not ask for system passwords")
    # _o.add_option("--global", action="store_true", dest="globally", default=_globally,
    #    help="Enable/disable unit files globally") # for all user logins
    # _o.add_option("--runtime", action="store_true",
    #     help="Enable unit files only temporarily until next reboot")
    _o.add_option("-f", "--force", action="store_true", default=_force,
                  help="When enabling unit files, override existing symblinks / When shutting down, execute action immediately")
    _o.add_option("--preset-mode", metavar="TYPE", default=_preset_mode,
                  help="Apply only enable, only disable, or all presets [%default]")
    _o.add_option("--root", metavar="PATH", default=_root,
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
    _o.add_option("-c", "--config", metavar="NAME=VAL", action="append", default=[],
                  help="..override internal variables (InitLoopSleep,SysInitTarget) {%default}")
    _o.add_option("-e", "--extra-vars", "--environment", metavar="NAME=VAL", action="append", default=[],
                  help="..override settings in the syntax of 'Environment='")
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="..increase debugging information level")
    _o.add_option("-4", "--ipv4", action="store_true", default=False,
                  help="..only keep ipv4 localhost in /etc/hosts")
    _o.add_option("-6", "--ipv6", action="store_true", default=False,
                  help="..only keep ipv6 localhost in /etc/hosts")
    _o.add_option("-1", "--init", action="store_true", default=False,
                  help="..keep running as init-process (default if PID 1)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = max(0, logging.FATAL - 10 * opt.verbose))
    logg.setLevel(max(0, logging.ERROR - 10 * opt.verbose))
    #
    _extra_vars = opt.extra_vars
    _force = opt.force
    _full = opt.full
    _log_lines = opt.lines
    _no_pager = opt.no_pager
    _no_reload = opt.no_reload
    _no_legend = opt.no_legend
    _no_ask_password = opt.no_ask_password
    _now = opt.now
    _preset_mode = opt.preset_mode
    _quiet = opt.quiet
    _root = opt.root
    _show_all = opt.show_all
    _only_state = opt.only_state
    _only_type = opt.only_type
    _only_property = opt.only_property
    _only_what = opt.only_what
    # being PID 1 (or 0) in a container will imply --init
    _pid = os.getpid()
    _init = opt.init or _pid in [1, 0]
    _user_mode = opt.user
    if os.geteuid() and _pid in [1, 0]:
        _user_mode = True
    if opt.system:
        _user_mode = False # override --user
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
                logg.debug("... _show_all=%s", _show_all)
            elif isinstance(old, float):
                logg.debug("num %s=%s", nam, val)
                globals()[nam] = float(val)
                logg.debug("... MinimumYield=%s", MinimumYield)
            elif isinstance(old, int):
                logg.debug("int %s=%s", nam, val)
                globals()[nam] = int(val)
                logg.debug("... InitLoopSleep=%s", InitLoopSleep)
            elif isinstance(old, basestring):
                logg.debug("str %s=%s", nam, val)
                globals()[nam] = val.strip()
                logg.debug("... SysInitTarget=%s", SysInitTarget)
            elif isinstance(old, list):
                logg.debug("str %s+=[%s]", nam, val)
                globals()[nam] += val.strip().split(",")
                logg.debug("... _extra_vars=%s", _extra_vars)
            else:
                logg.warning("(ignored) unknown target type -c '%s' : %s", nam, type(old))
        else:
            logg.warning("(ignored) unknown target config -c '%s' : no such variable", nam)
    #
    systemctl_debug_log = os_path(_root, expand_path(SYSTEMCTL_DEBUG_LOG, not _user_mode))
    systemctl_extra_log = os_path(_root, expand_path(SYSTEMCTL_EXTRA_LOG, not _user_mode))
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
    systemctl = Systemctl()
    if opt.version:
        args = ["version"]
    if not args:
        if _init:
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
    if opt.ipv4:
        systemctl.force_ipv4()
    elif opt.ipv6:
        systemctl.force_ipv6()
    sys.exit(run(command, *modules))
