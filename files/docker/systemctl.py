#! /usr/bin/python2
# generated from systemctl3.py - do not change

from __future__ import print_function

__copyright__ = "(C) 2016-2020 Guido U. Draheim, licensed under the EUPL"
__version__ = "1.6.4521"

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


import logging
logg = logging.getLogger("systemctl")

from types import GeneratorType
import re
import fnmatch
import shlex
import collections
import errno
import os
import sys
import signal
import time
import socket
import datetime
import string
import fcntl
import select
import hashlib
import pwd
import grp
import threading

if sys.version[0] == '3':
    basestring = str
    xrange = range

DebugSortedAfter = False
DebugStatusFile = False
DebugBootTime = False
DebugInitLoop = False
DebugKillAll = False
DebugLockFile = False
DebugExpandVars = False
DebugPrintResult = False
DebugSocketFile = True
DebugIgnoredServices = False
IgnoreSyntaxWarnings = ""
IgnoreExecWarnings = ""
IgnoreWarnings = ""
TestSocketListen = False
TestSocketAccept = False
ActiveWhileStarting = True

HINT = (logging.DEBUG + logging.INFO) // 2
NOTE = (logging.WARNING + logging.INFO) // 2
DONE = (logging.WARNING + logging.ERROR) // 2
logging.addLevelName(HINT, "HINT")
logging.addLevelName(NOTE, "NOTE")
logging.addLevelName(DONE, "DONE")


def dbg_(msg, note=None):
    if note is None:
        logg.debug("%s", msg)
    else:
        logg.debug("%s %s", msg, note)
def debug_(msg, note=None):
    if note is None:
        logg.debug("%s", msg)
    else:
        logg.debug("%s %s", msg, note)
def hint_(msg, note=None):
    if note is None:
        logg.log(HINT, "%s", msg)
    else:
        logg.log(HINT, "%s %s", msg, note)
def info_(msg, note=None):
    if note is None:
        logg.info("%s", msg)
    else:
        logg.info("%s %s", msg, note)
def note_(msg, note=None):
    if note is None:
        logg.log(NOTE, "%s", msg)
    else:
        logg.log(NOTE, "%s %s", msg, note)
def warn_(msg, note=None):
    if note is None:
        logg.warning("%s", msg)
    else:
        logg.warning("%s %s", msg, note)
def warning_(msg, note=None):
    if note is None:
        logg.warning("%s", msg)
    else:
        logg.warning("%s %s", msg, note)
def done_(msg, note=None):
    if note is None:
        logg.log(DONE, "%s", msg)
    else:
        logg.log(DONE, "%s %s", msg, note)
def error_(msg, note=None):
    if note is None:
        logg.error("%s", msg)
    else:
        logg.error("%s %s", msg, note)


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
_unit_type = None
_unit_state = None
_unit_property = None
_what_kind = ""
_show_all = False
_user_mode = False

# common default paths
_system_folder1 = "/etc/systemd/system"
_system_folder2 = "/run/systemd/system"
_system_folder3 = "/var/run/systemd/system"
_system_folder4 = "/usr/local/lib/systemd/system"
_system_folder5 = "/usr/lib/systemd/system"
_system_folder6 = "/lib/systemd/system"
_system_folderX = None
_user_folder1 = "{XDG_CONFIG_HOME}/systemd/user"
_user_folder2 = "/etc/systemd/user"
_user_folder3 = "{XDG_RUNTIME_DIR}/systemd/user"
_user_folder4 = "/run/systemd/user"
_user_folder5 = "/var/run/systemd/user"
_user_folder6 = "{XDG_DATA_HOME}/systemd/user"
_user_folder7 = "/usr/local/lib/systemd/user"
_user_folder8 = "/usr/lib/systemd/user"
_user_folder9 = "/lib/systemd/user"
_user_folderX = None
_init_folder1 = "/etc/init.d"
_init_folder2 = "/run/init.d"
_init_folder3 = "/var/run/init.d"
_init_folderX = None
_preset_folder1 = "/etc/systemd/system-preset"
_preset_folder2 = "/run/systemd/system-preset"
_preset_folder3 = "/var/run/systemd/system-preset"
_preset_folder4 = "/usr/local/lib/systemd/system-preset"
_preset_folder5 = "/usr/lib/systemd/system-preset"
_preset_folder6 = "/lib/systemd/system-preset"
_preset_folderX = None

# standard paths
_dev_null = "/dev/null"
_dev_zero = "/dev/zero"
_etc_hosts = "/etc/hosts"
_rc3_boot_folder = "/etc/rc3.d"
_rc3_init_folder = "/etc/init.d/rc3.d"
_rc5_boot_folder = "/etc/rc5.d"
_rc5_init_folder = "/etc/init.d/rc5.d"

# default values
SystemCompatibilityVersion = 219
SysInitTarget = "sysinit.target"
SysInitWait = 5  # max for target
MinimumYield = 0.5
MinimumTimeoutStartSec = 4
MinimumTimeoutStopSec = 4
DefaultTimeoutStartSec = 90   # official value
DefaultTimeoutStopSec = 90    # official value
DefaultTimeoutAbortSec = 3600  # officially it none (usually larget than StopSec)
DefaultMaximumTimeout = 200   # overrides all other
DefaultRestartSec = 0.1       # official value of 100ms
DefaultStartLimitIntervalSec = 10  # official value
DefaultStartLimitBurst = 5        # official value
InitLoopSleep = 5
TestLockSleep = 1
MaxLockWait = 0  # equals DefaultMaximumTimeout
DefaultPath = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ResetLocale = ["LANG", "LANGUAGE", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", "LC_COLLATE", "LC_MONETARY",
               "LC_MESSAGES", "LC_PAPER", "LC_NAME", "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT",
               "LC_IDENTIFICATION", "LC_ALL"]
LocaleConf="/etc/locale.conf"
DefaultListenBacklog=2

ExitWhenNoMoreServices = False
ExitWhenNoMoreProcs = False
DefaultUnit = os.environ.get("SYSTEMD_DEFAULT_UNIT", "default.target")  # systemd.exe --unit=default.target
DefaultTarget = os.environ.get("SYSTEMD_DEFAULT_TARGET", "multi-user.target")  # DefaultUnit fallback
# LogLevel = os.environ.get("SYSTEMD_LOG_LEVEL", "info") # systemd.exe --log-level
# LogTarget = os.environ.get("SYSTEMD_LOG_TARGET", "journal-or-kmsg") # systemd.exe --log-target
# LogLocation = os.environ.get("SYSTEMD_LOG_LOCATION", "no") # systemd.exe --log-location
# ShowStatus = os.environ.get("SYSTEMD_SHOW_STATUS", "auto") # systemd.exe --show-status
DefaultStandardInput=os.environ.get("SYSTEMD_STANDARD_INPUT", "null")
DefaultStandardOutput=os.environ.get("SYSTEMD_STANDARD_OUTPUT", "journal")  # systemd.exe --default-standard-output
DefaultStandardError=os.environ.get("SYSTEMD_STANDARD_ERROR", "inherit")  # systemd.exe --default-standard-error

ExecSpawn = False
ExecRedirectLogs = True
ExecIgnoreErrors = False
RemoveLockFile = False
ForceLockFile = False
BootTimeMinPID = 0
BootTimeMaxPID = -9
KillChildrenMaxDepth = 100
ExpandVarsMaxDepth = 20
ExpandVarsKeepName = True
RestartOnFailure = True

DefaultTail = "/usr/bin/tail"
DefaultPager = "/usr/bin/less"
DefaultCat = "/usr/bin/cat"
DefaultProcDir = "/proc"

# The systemd default was NOTIFY_SOCKET="/var/run/systemd/notify"
NotifySocketFolder = "{VARRUN}/systemd"  # alias /run/systemd
JournalLogFolder = "{VARLOG}/journal"

SystemctlDebugLog = "{VARLOG}/systemctl.debug.log"
SystemctlExtraLog = "{VARLOG}/systemctl.log"

CacheDeps=False
CacheAlias=True
DepsMaxDepth=9
CacheDepsFile="${XDG_CONFIG_HOME}/systemd/systemctl.deps.cache"
CacheAliasFile="${XDG_CONFIG_HOME}/systemd/systemctl.alias.cache"
CacheSysinitFile="${XDG_CONFIG_HOME}/systemd/systemctl.sysinit.cache"
IgnoredServicesFile="${XDG_CONFIG_HOME}/systemd/systemctl.services.ignore"
_ignored_services = """
[centos]
netconsole
network
[opensuse]
raw
pppoe
rpmconf*
postfix*
purge-kernels.service
after-local.service
[ubuntu]
mount*
umount*
ondemand
[systemd]
dbus*
systemd-*
[kernel]
network*
kdump*
dm-event.*
[boot]
boot.*
*.local
remote-fs.target
"""

_default_targets = [ "poweroff.target", "rescue.target", "sysinit.target", "basic.target", "multi-user.target", "graphical.target", "reboot.target" ]
_feature_targets = [ "network.target", "remote-fs.target", "local-fs.target", "timers.target", "nfs-client.target" ]
_all_common_targets = [ "default.target" ] + _default_targets + _feature_targets

# inside a docker we pretend the following
_all_common_enabled = [ "default.target", "multi-user.target", "remote-fs.target" ]
_all_common_disabled = [ "graphical.target", "resue.target", "nfs-client.target" ]

target_requires = { "graphical.target": "multi-user.target", "multi-user.target": "basic.target", "basic.target": "sockets.target" }

_runlevel_mappings = {}  # the official list
_runlevel_mappings["0"] = "poweroff.target"
_runlevel_mappings["1"] = "rescue.target"
_runlevel_mappings["2"] = "multi-user.target"
_runlevel_mappings["3"] = "multi-user.target"
_runlevel_mappings["4"] = "multi-user.target"
_runlevel_mappings["5"] = "graphical.target"
_runlevel_mappings["6"] = "reboot.target"

_sysv_mappings = {}  # by rule of thumb
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
EXIT_INVALIDARGUMENT = 2
EXIT_NOTIMPLEMENTED = 3
EXIT_NOPERMISSION = 4
EXIT_NOTINSTALLED = 5
EXIT_NOTCONFIGURED = 6
EXIT_NOTRUNNING = 7
EXIT_CORRUPTED = 11
EXIT_NOTEXECUTABLE = 126
EXIT_NOTFOUND = 127
EXIT_NOTSIG = 128
EXIT_SIGHUP = 129
EXIT_SIGINT = 130
EXIT_SIGQUIT = 131
EXIT_SIGILL = 132
EXIT_SIGTRAP = 133
EXIT_SIGABRT = 134
EXIT_SIGBUS = 135
EXIT_SIGFPE = 136
EXIT_SIGKILL = 137
EXIT_SIGUSR1= 138
EXIT_SIGSEGV= 139
EXIT_SIGUSR2= 140
EXIT_SIGPIPE= 141
EXIT_SIGALRM= 143
EXIT_SIGTERM= 144
EXIT_CHDIR = 200
EXIT_EXEC = 203
EXIT_STDIN = 208
EXIT_STDOUT = 209
EXIT_GROUP = 216
EXIT_USER = 217
EXIT_STDERR = 222
EXIT_RUNTIME_DIRECTORY = 233
EXIT_CHOWN = 235
EXIT_STATE_DIRECTORY = 238
EXIT_CACHE_DIRECTORY = 239
EXIT_LOGS_DIRECTORY = 240
EXIT_CONFIGURATION_DIRECTORY = 241

EXITCODE = {}
EXITCODE[EXIT_SUCCESS] = "SUCCESS"
EXITCODE[EXIT_FAILURE] = "FAILURE"
EXITCODE[EXIT_INVALIDARGUMENT] = "INVALIDARGUMENT"
EXITCODE[EXIT_NOTIMPLEMENTED] = "NOTIMPLEMENTED"
EXITCODE[EXIT_NOPERMISSION] = "NOPERMISSION"
EXITCODE[EXIT_NOTINSTALLED] = "NOTINSTALLED"
EXITCODE[EXIT_NOTCONFIGURED] = "NOTCONFIGURED"
EXITCODE[EXIT_NOTRUNNING] = "NOTRUNNING"
EXITCODE[EXIT_CORRUPTED] = "CORRUPTED"
EXITCODE[EXIT_NOTEXECUTABLE] = "NOTEXECUTABLE"
EXITCODE[EXIT_NOTFOUND] = "NOTFOUND"
EXITCODE[EXIT_NOTSIG] = "NOTSIG"
EXITCODE[EXIT_SIGHUP] = "SIGHUP"
EXITCODE[EXIT_SIGINT] = "SIGINT"
EXITCODE[EXIT_SIGQUIT] = "SIGQUIT"
EXITCODE[EXIT_SIGILL] = "SIGILL"
EXITCODE[EXIT_SIGTRAP] = "SIGTRAP"
EXITCODE[EXIT_SIGABRT] = "SIGABRT"
EXITCODE[EXIT_SIGBUS] = "SIGBUS"
EXITCODE[EXIT_SIGFPE] = "SIGFPE"
EXITCODE[EXIT_SIGKILL] = "SIGKIKK"
EXITCODE[EXIT_SIGUSR1] = "SIGUSR1"
EXITCODE[EXIT_SIGSEGV] = "SIGSEGV"
EXITCODE[EXIT_SIGUSR2] = "SIGUSR2"
EXITCODE[EXIT_SIGPIPE] = "SIGPIPE"
EXITCODE[EXIT_SIGALRM] = "SIGALRM"
EXITCODE[EXIT_SIGTERM] = "SIGTERM"
EXITCODE[EXIT_CHDIR] = "CHDIR"
EXITCODE[EXIT_EXEC] = "EXEC"
EXITCODE[EXIT_STDIN] = "STDIN"
EXITCODE[EXIT_STDOUT] = "STDOUT"
EXITCODE[EXIT_GROUP] = "GROUP"
EXITCODE[EXIT_USER] = "USER"
EXITCODE[EXIT_STDERR] = "STDERR"
EXITCODE[EXIT_RUNTIME_DIRECTORY] = "RUNTIME_DIRECTORY"
EXITCODE[EXIT_CHOWN] = "CHOWN"
EXITCODE[EXIT_STATE_DIRECTORY] = "STATE_DIRECTORY"
EXITCODE[EXIT_CACHE_DIRECTORY] = "CACHE_DIRECTORY"
EXITCODE[EXIT_LOGS_DIRECTORY] = "LOGS_DIRECTORY"
EXITCODE[EXIT_CONFIGURATION_DIRECTORY] = "CONFIGURATION_DIRECTORY"

def boolOK(returnvalue):
    if not returnvalue:
        "NAK"
    return "OK"
def exitOK(returncode):
    if not returncode:
        return "OK"
    return exitCODE(returncode)
def exitCODE(returncode):
    if returncode in EXITCODE:
        name = EXITCODE[returncode]
        return "{returncode}/{name}".format(**locals())
    return "{returncode}".format(**locals())

def strINET(value):
    if value == socket.SOCK_DGRAM:
        return "UDP"
    if value == socket.SOCK_STREAM:
        return "TCP"
    if value == socket.SOCK_RAW:  # pragma: no cover
        return "RAW"
    if value == socket.SOCK_RDM:  # pragma: no cover
        return "RDM"
    if value == socket.SOCK_SEQPACKET:  # pragma: no cover
        return "SEQ"
    return "<?>"  # pragma: no cover

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
def shell_cmd(cmd):
    return " ".join(["'%s'" % part for part in cmd])
def to_intN(value, default=None):
    if not value:
        return default
    try:
        return int(value)
    except:
        return default
def to_int(value, default=0):
    if not value:
        return default
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
def int_mode(value):
    try: return int(value, 8)
    except: return None  # pragma: no cover
def unit_of(module):
    if "." not in module:
        return module + ".service"
    return module
def o44(part):
    if len(part) <= 44:
        return part
    return part[:10] + "..." + part[-31:]
def o77(part):
    if len(part) <= 77:
        return part
    return part[:20] + "..." + part[-54:]
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

def get_PAGER():
    PAGER = os.environ.get("PAGER", "less")
    pager = os.environ.get("SYSTEMD_PAGER", "{PAGER}").format(**locals())  # internal
    options = os.environ.get("SYSTEMD_LESS", "FRSXMK")  # see 'man timedatectl'
    if not pager:
        pager = DefaultPager
    if "less" in pager and options:
        return [ pager, "-" + options ]
    return [ pager ]

def os_getlogin():
    """ NOT using os.getlogin() """
    return pwd.getpwuid(os.geteuid()).pw_name

def get_runtime_dir():
    explicit = os.environ.get("XDG_RUNTIME_DIR", "")
    if explicit: return explicit
    user = os_getlogin()
    return "/tmp/run-{user}".format(**locals())
def get_RUN(root=False):
    tmp_var = get_TMP(root)
    if _root:
        tmp_var = _root
    if root:
        run_root = "/run".format(**locals())
        var_root = "/var/run".format(**locals())
        tmp_root = "{tmp_var}/run".format(**locals())
        for run_path in (run_root, var_root, tmp_root):
            if os.path.isdir(run_path) and os.access(run_path, os.W_OK):
                return run_path
        os.makedirs(run_path)  # "/tmp/run"
        return run_path
    else:
        uid = get_USER_ID(root)
        run_user = "/run/user/{uid}".format(**locals())
        var_user = "/var/run/user/{uid}".format(**locals())
        tmp_user = "{tmp_var}/run-{uid}".format(**locals())
        for run_path in (run_user, var_user, tmp_user):
            if os.path.isdir(run_path) and os.access(run_path, os.W_OK):
                return run_path
        os.makedirs(run_path, 0o700)  # "/tmp/run/user/{uid}"
        return run_path
def get_PID_DIR(root=False):
    if root:
        return get_RUN(root)
    else:
        return os.path.join(get_RUN(root), "run")  # compat with older systemctl.py

def get_home():
    if False:  # pragma: no cover
        explicit = os.environ.get("HOME", "")   # >> On Unix, an initial ~ (tilde) is replaced by the
        if explicit: return explicit            # environment variable HOME if it is set; otherwise
        uid = os.geteuid()                      # the current users home directory is looked up in the
        #                                       # password directory through the built-in module pwd.
        return pwd.getpwuid(uid).pw_name        # An initial ~user i looked up directly in the
    return os.path.expanduser("~")              # password directory. << from docs(os.path.expanduser)
def get_HOME(root=False):
    if root: return "/root"
    return get_home()
def get_USER_ID(root=False):
    ID = 0
    if root: return ID
    return os.geteuid()
def get_USER(root=False):
    if root: return "root"
    uid = os.geteuid()
    return pwd.getpwuid(uid).pw_name
def get_GROUP_ID(root=False):
    ID = 0
    if root: return ID
    return os.getegid()
def get_GROUP(root=False):
    if root: return "root"
    gid = os.getegid()
    return grp.getgrgid(gid).gr_name
def get_TMP(root=False):
    TMP = "/tmp"
    if root: return TMP
    return os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", TMP)))
def get_VARTMP(root=False):
    VARTMP = "/var/tmp"
    if root: return VARTMP
    return os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", VARTMP)))
def get_SHELL(root=False):
    SHELL = "/bin/sh"
    if root: return SHELL
    return os.environ.get("SHELL", SHELL)
def get_RUNTIME_DIR(root=False):
    VARRUN = "/run"
    if root: return VARRUN
    return os.environ.get("XDG_RUNTIME_DIR", get_runtime_dir())
def get_CONFIG_HOME(root=False):
    CONFIG = "/etc"
    if root: return CONFIG
    HOME = get_HOME(root)
    return os.environ.get("XDG_CONFIG_HOME", HOME + "/.config")
def get_CACHE_HOME(root=False):
    CACHE = "/var/cache"
    if root: return CACHE
    HOME = get_HOME(root)
    return os.environ.get("XDG_CACHE_HOME", HOME + "/.cache")
def get_DATA_HOME(root=False):
    SHARE = "/usr/share"
    if root: return SHARE
    HOME = get_HOME(root)
    return os.environ.get("XDG_DATA_HOME", HOME + "/.local/share")
def get_LOG_DIR(root=False):
    LOGDIR = "/var/log"
    if root: return LOGDIR
    CONFIG = get_CONFIG_HOME(root)
    return os.path.join(CONFIG, "log")
def get_VARLIB_HOME(root=False):
    VARLIB = "/var/lib"
    if root: return VARLIB
    CONFIG = get_CONFIG_HOME(root)
    return CONFIG
def expand_path(filepath, root=False):
    HOME = get_HOME(root)
    VARRUN = get_RUN(root)
    VARLOG = get_LOG_DIR(root)
    XDG_DATA_HOME=get_DATA_HOME(root)
    XDG_CONFIG_HOME=get_CONFIG_HOME(root)
    XDG_RUNTIME_DIR=get_RUNTIME_DIR(root)
    return os.path.expanduser(filepath.replace("${", "{").format(**locals()))  # internal

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
def shutil_setuid(user=None, group=None, xgroups=None):
    """ set fork-child uid/gid (returns pw-info env-settings)"""
    if group:
        gid = grp.getgrnam(group).gr_gid
        os.setgid(gid)
        dbg_("setgid {gid} for group {group}".format(**locals()))
        groups = [ gid ]
        try:
            os.setgroups(groups)
            dbg_("setgroups {groups} < ({group})".format(**locals()))
        except OSError as e:  # pragma: no cover (it will occur in non-root mode anyway)
            dbg_("setgroups {groups} < ({group}) : {e}".format(**locals()))
    if user:
        pw = pwd.getpwnam(user)
        gid = pw.pw_gid
        gname = grp.getgrgid(gid).gr_name
        if not group:
            os.setgid(gid)
            dbg_("setgid {gid} for user {user}".format(**locals()))
        groupnames = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
        groups = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
        if xgroups:
            groups += [g.gr_gid for g in grp.getgrall() if g.gr_name in xgroups and g.gr_gid not in groups]
        if not groups:
            if group:
                gid = grp.getgrnam(group).gr_gid
            groups = [ gid ]
        try:
            os.setgroups(groups)
            dbg_("setgroups {groups} > {groupnames} ".format(**locals()))
        except OSError as e:  # pragma: no cover (it will occur in non-root mode anyway)
            dbg_("setgroups {groups} > {groupnames} : {e}".format(**locals()))
        uid = pw.pw_uid
        os.setuid(uid)
        dbg_("setuid {uid} for user {user}".format(**locals()))
        home = pw.pw_dir
        shell = pw.pw_shell
        logname = pw.pw_name
        return { "USER": user, "LOGNAME": logname, "HOME": home, "SHELL": shell }
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
    if pid is None:  # pragma: no cover (is never null)
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
    proc = DefaultProcDir
    pid_status = "{proc}/{pid}/status".format(**locals())
    try:
        for line in open(pid_status):
            if line.startswith("State:"):
                return "Z" in line
    except IOError as e:
        if e.errno != errno.ENOENT:
            err = e.errno
            error_("{pid_status} ({err}): {e}".format(**locals()))
        return False
    return False

def checkprefix(cmd):
    prefix = ""
    for i, c in enumerate(cmd):
        if c in "-+!@:":
            prefix = prefix + c
        else:
            return prefix, cmd[i:]
    return prefix, ""

ExecMode = collections.namedtuple("ExecMode", ["mode", "check", "nouser", "noexpand"])
def exec_mode(cmd):
    prefix, newcmd = checkprefix(cmd)
    check = "-" not in prefix
    nouser = "+" in prefix or "!" in prefix
    noexpand = ":" in prefix
    mode = ExecMode(prefix, check, nouser, noexpand)
    return mode, newcmd

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
            self._conf[section][option] = [ value ]
        else:
            self._conf[section][option].append(value)
    def getstr(self, section, option, default=None, allow_no_value=False):
        done = self.get(section, option, strE(default), allow_no_value)
        if done is None: return strE(default)
        return done
    def get(self, section, option, default=None, allow_no_value=False):
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._conf:
            if default is not None:
                return default
            if allow_no_value:
                return None
            _sections = self.sections()
            warn_("section {section} does not exist".format(**locals()))
            warn_("  have {_sections}".format(**locals()))
            raise AttributeError("section {section} does not exist".format(**locals()))
        if option not in self._conf[section]:
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError("option {option} in {section} does not exist".format(**locals()))
        if not self._conf[section][option]:  # i.e. an empty list
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError("option {option} in {section} is None".format(**locals()))
        return self._conf[section][option][0]  # the first line in the list of configs
    def getlist(self, section, option, default=None, allow_no_value=False):
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._conf:
            if default is not None:
                return default
            if allow_no_value:
                return []
            _sections = self.sections()
            warn_("section {section} does not exist".format(**locals()))
            warn_("  have {_sections}".format(**locals()))
            raise AttributeError("section {section} does not exist".format(**locals()))
        if option not in self._conf[section]:
            if default is not None:
                return default
            if allow_no_value:
                return []
            raise AttributeError("option {option} in {section} does not exist".format(**locals()))
        return self._conf[section][option]  # returns a list, possibly empty
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
                error_("the '.include' syntax is deprecated. Use x.service.d/ drop-in files!")
                includefile = re.sub(r'^\.include[ ]*', '', line).rstrip()
                if not os.path.isfile(includefile):
                    raise Exception("tried to include file that doesn't exist: {includefile}".format(**locals()))
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
                warn_("bad ini line: {line}".format(**locals()))
                raise Exception("bad ini line")
            name, text = m.group(1), m.group(2).strip()
            if text.endswith("\\") or text.endswith("\\\n"):
                nextline = True
                text = text + "\n"
            else:
                # hint: an empty line shall reset the value-list
                self.set(section, name, text and text or None)
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
        if description:  # LSB style initscript
            self.set(Service, "ExecReload", filename + " reload")
        self.set(Service, "Type", "forking")  # not "sysv" anymore

# UnitConfParser = ConfigParser.RawConfigParser
UnitConfParser = SystemctlConfigParser

class SystemctlSocket:
    def __init__(self, conf, sock, skip=False):
        self.conf = conf
        self.sock = sock
        self.skip = skip
    def fileno(self):
        return self.sock.fileno()
    def listen(self, backlog=None):
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
    def __init__(self, data, module=None):
        self.data = data  # UnitConfParser
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
        return [ self.drop_in_files[name] for name in sorted(self.drop_in_files) ]
    def name(self):
        """ the unit id or defaults to the file name """
        name = self.module or ""
        filename = self.filename()
        if filename:
            name = os.path.basename(filename)
        return self.module or name
    def set(self, section, name, value):
        return self.data.set(section, name, value)
    def get(self, section, name, default, allow_no_value=False):
        return self.data.getstr(section, name, default, allow_no_value)
    def getlist(self, section, name, default=None, allow_no_value=False):
        return self.data.getlist(section, name, default or [], allow_no_value)
    def getbool(self, section, name, default=None):
        value = self.data.get(section, name, default or "no")
        if value:
            if value[0] in "TtYy123456789":
                return True
        return False
    def root(self):
        return self._root
    def status_file(self):
        return os_path(self._root, self.get_status_file())
    def get_status_file(self):  # -> text
        """ file where to store a status mark """
        root = self.root_mode()
        folder = get_PID_DIR(root)
        name = self.name() + ".status"
        return os.path.join(folder, name)
    def clean_status(self):
        self.status = None
        status_file = self.status_file()
        if os.path.exists(status_file):
            with open(status_file, 'w'): pass
        # ftruncate would also be done at the next end of waitlock
    def write_status(self, **status):  # -> bool(written)
        """ if a status_file is known then path is created and the
            give status is written as the only content. """
        status_file = self.status_file()
        # if not status_file: return False
        dirpath = os.path.dirname(os.path.abspath(status_file))
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        if self.status is None:
            self.status = self.read_status()
        if DebugStatusFile:  # pragma: no cover
            oldstatus = self.status.copy()
        if True:
            for key in sorted(status.keys()):
                value = status[key]
                if key.upper() == "AS": key = "ActiveState"
                if key.upper() == "SS": key = "SubState"
                if value is None:
                    try: del self.status[key]
                    except KeyError: pass
                else:
                    self.status[key] = strE(value)
        try:
            with open(status_file, "w") as f:
                if DebugStatusFile:  # pragma: no cover
                    unit = self.name()
                    dbg_("[{unit}] writing to {status_file}".format(**locals()))
                for key in sorted(self.status):
                    value = str(self.status[key])
                    if key == "MainPID" and value == "0":
                        warn_("ignore writing MainPID=0")
                        continue
                    if DebugStatusFile:  # pragma: no cover
                        old = "old"
                        if key in oldstatus and oldstatus[key] != value:
                            old = "new"
                        dbg_("[{unit}] writing {old} {key}={value}".format(**locals()))
                    content = "{key}={value}\n".format(**locals())
                    f.write(content)
        except IOError as e:
            error_("writing STATUS {status}: {e}\n\t to status file {status_file}".format(**locals()))
        return True
    def read_status(self):
        status_file = self.status_file()
        status = {}
        # if not status_file: return status
        if not os.path.isfile(status_file):
            if DebugStatusFile:  # pagma: no cover
                dbg_("no status file: {status_file}\n returning {status}".format(**locals()))
            return status
        if path_truncate_old(status_file):
            if DebugStatusFile:  # pagma: no cover
                dbg_("old status file: {status_file}\n returning {status}".format(**locals()))
            return status
        try:
            if DebugStatusFile:  # pragma: no cover
                unit = self.name()
                dbg_("[{unit}] got status file: {status_file}".format(**locals()))
            for line0 in open(status_file):
                if line0.startswith("#"):
                    continue
                line = line0.rstrip()
                if line:
                    m = re.match(r"(\w+)[:=](.*)", line)
                    if m:
                        key, value = m.group(1), m.group(2)
                        if key.strip():
                            status[key.strip()] = value.strip()
                    else:  # pragma: no cover
                        warn_("ignored '{line}'".format(**locals()))
        except:
            warn_("bad read of status file '{status_file}'".format(**locals()))
        return status
    def get_status(self, name, default=None):
        if self.status is None:
            self.status = self.read_status()
        return self.status.get(name, default)
    def set_status(self, name, value):
        if self.status is None:
            self.status = self.read_status()
        if value is None:
            try: del self.status[name]
            except KeyError: pass
        else:
            self.status[name] = value

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
    def get_preset(self, unit, nodefault=False):
        for line in self._lines:
            m = re.match(r"(enable|disable)\s+(\S+)", line)
            if m:
                status, pattern = m.group(1), m.group(2)
                if pattern.startswith("*") and nodefault:
                    continue
                if fnmatch.fnmatchcase(unit, pattern):
                    filename44 = path44(self.filename())
                    dbg_("{status} {pattern} => {unit} {filename44}".format(**locals()))
                    return status
        return None

_boottime = None
def get_boottime():
    """ detects the boot time of the container - in general the start time of PID 1 """
    global _boottime
    if _boottime is None:
        _boottime = get_boottime_from_proc()
    assert _boottime is not None
    return _boottime
def get_boottime_from_proc():
    """ detects the latest boot time by looking at the start time of available process"""
    pid_min = BootTimeMinPID or 0
    pid_max = BootTimeMaxPID
    if pid_max < 0:
        pid_max = pid_min - pid_max
    for pid in xrange(pid_min, pid_max):
        proc = DefaultProcDir
        pid_stat = "{proc}/{pid}/stat".format(**locals())
        try:
            if os.path.exists(pid_stat):
                # return os.path.getmtime(pid_stat) # did sometimes change
                return path_proc_started(pid_stat)
        except Exception as e:  # pragma: no cover
            warn_("boottime - could not access {pid_stat}: {e}".format(**locals()))
    if DebugBootTime:
        dbg_(" boottime from the oldest entry in /proc [nothing in {pid_min}..{pid_max}]".format(**locals()))
    return get_boottime_from_old_proc()
def get_boottime_from_old_proc():
    proc = DefaultProcDir
    booted = time.time()
    for pid in os.listdir(proc):
        pid_stat = "{proc}/{pid}/stat".format(**locals())
        try:
            if os.path.exists(pid_stat):
                # ctime = os.path.getmtime(pid_stat)
                ctime = path_proc_started(pid_stat)
                if ctime < booted:
                    booted = ctime
        except Exception as e:  # pragma: no cover
            warn_("could not access {pid_stat}: {e}".format(**locals()))
    return booted

# Use uptime, time process running in ticks, and current time to determine process boot time
# You can't use the modified timestamp of the status file because it isn't static.
# ... using clock ticks it is known to be a linear time on Linux
def path_proc_started(proc):
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
    if DebugBootTime:
        dbg_("  BOOT .. Proc started time:  {started_secs:.3f} ({proc})".format(**locals()))
    # this value is the start time from the host system

    # Variant 1:
    proc = DefaultProcDir
    system_uptime = "{proc}/uptime".format(**locals())
    with open(system_uptime, "rb") as file_uptime:
        data_uptime = file_uptime.readline()
    file_uptime.close()
    uptime_data = data_uptime.decode().split()
    uptime_secs = float(uptime_data[0])
    if DebugBootTime:
        dbg_("  BOOT 1. System uptime secs: {uptime_secs:.3f} ({system_uptime})".format(**locals()))

    # get time now
    now = time.time()
    started_time = now - (uptime_secs - started_secs)
    if DebugBootTime:
        date_started_time = datetime.datetime.fromtimestamp(started_time)
        dbg_("  BOOT 1. Proc has been running since: {date_started_time}".format(**locals()))

    # Variant 2:
    system_stat = "{proc}/stat".format(**locals())
    system_btime = 0.
    with open(system_stat, "rb") as f:
        for line in f:
            assert isinstance(line, bytes)
            if line.startswith(b"btime"):
                system_btime = float(line.decode().split()[1])
    f.closed
    if DebugBootTime:
        dbg_("  BOOT 2. System btime secs: {system_btime:.3f} ({system_stat})".format(**locals()))

    started_btime = system_btime + started_secs
    if DebugBootTime:
        date_started_btime = datetime.datetime.fromtimestamp(started_btime)
        dbg_("  BOOT 2. Proc has been running since: {date_started_btime}".format(**locals()))

    # return started_time
    return started_btime

def path_truncate_old(filename):
    filetime = os.path.getmtime(filename)
    boottime = get_boottime()
    if filetime >= boottime:
        if DebugBootTime:
            date_filetime = datetime.datetime.fromtimestamp(filetime)
            date_boottime = datetime.datetime.fromtimestamp(boottime)
            filename44, status44 = path44(filename), "status modified later"
            debug_("  file time: {date_filetime} ({filename44})".format(**locals()))
            debug_("  boot time: {date_boottime} ({status44})".format(**locals()))
        return False  # OK
    else:
        if DebugBootTime:
            date_filetime = datetime.datetime.fromtimestamp(filetime)
            date_boottime = datetime.datetime.fromtimestamp(boottime)
            filename44, status44 = path44(filename), "status TRUNCATED NOW"
            info_("  file time: {date_filetime} ({filename44})".format(**locals()))
            info_("  boot time: {date_boottime} ({status44})".format(**locals()))
        try:
            shutil_truncate(filename)
        except Exception as e:
            warn_("while truncating: {e}".format(**locals()))
        return True  # truncated
def path_getsize(filename):
    if filename is None:  # pragma: no cover (is never null)
        return 0
    if not os.path.isfile(filename):
        return 0
    if path_truncate_old(filename):
        return 0
    try:
        return os.path.getsize(filename)
    except Exception as e:
        warn_("while reading file size: {e}\n of {filename}".format(**locals()))
        return 0

## with waitlock(conf): self.start()
class waitlock:
    # |
    # |
    # |
    def __init__(self, conf):
        self.conf = conf  # currently unused
        self.opened = -1
    def lockfile(self):
        return self.conf.status_file()
    def __enter__(self):
        me = os.getpid()
        try:
            lockfile = self.lockfile()
            lockname = os.path.basename(lockfile)
            basedir = os.path.dirname(lockfile)
            if not os.path.isdir(basedir):
                os.makedirs(basedir)
            self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
            for attempt in xrange(int(MaxLockWait or DefaultMaximumTimeout)):
                try:
                    if DebugLockFile:  # pragma: no cover
                        dbg_("[{me}] {attempt}. trying {lockname} _______ ".format(**locals()))
                    fcntl.flock(self.opened, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    st = os.fstat(self.opened)
                    if not st.st_nlink:
                        if DebugLockFile:  # pragma: no cover
                            dbg_("[{me}] {attempt}. {lockname} got deleted, trying again".format(**locals()))
                        os.close(self.opened)
                        self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
                        continue
                    os.lseek(self.opened, 0, os.SEEK_END)
                    content = "#lock={me}\n".format(**locals())
                    os.write(self.opened, content.encode("ascii"))
                    os.lseek(self.opened, 0, os.SEEK_SET)
                    if DebugLockFile:  # pragma: no cover
                        dbg_("[{me}] {attempt}. holding lock on {lockname}".format(**locals()))
                    return True
                except IOError as e:
                    whom = "<n/a>"
                    os.lseek(self.opened, 0, os.SEEK_SET)
                    status = os.read(self.opened, 4096)
                    os.lseek(self.opened, 0, os.SEEK_SET)
                    for state in status.splitlines():
                        if state.startswith(b"#lock="):
                            whom=state[len(b"#lock="):].decode("ascii")
                    info_("[{me}] {attempt}. systemctl locked by {whom}".format(**locals()))
                    time.sleep(TestLockSleep)  # until MaxLockWait
                    continue
            error_("[{me}] not able to get the lock to {lockname}".format(**locals()))
        except Exception as e:
            exc = str(type(e))
            warn_("[{me}] oops {exc}, {e}".format(**locals()))
        # TODO# raise Exception(f"no lock for {self.unit or global}")
        return False
    def __exit__(self, type, value, traceback):
        me = os.getpid()
        try:
            remove = False
            lockfile = self.lockfile()
            if self.conf.status is None:
                if not path_getsize(lockfile):
                    remove = True
            elif not self.conf.status:  # empty dict
                remove = True
            if remove or ForceLockFile:
                os.ftruncate(self.opened, 0)
                lockfile = self.lockfile()
                info_("truncated {lockfile}".format(**locals()))
                if RemoveLockFile:  # an optional implementation
                    lockname = os.path.basename(lockfile)
                    os.unlink(lockfile)  # ino is kept allocated because opened by this process
                    dbg_("[{me}] lockfile removed for {lockname}".format(**locals()))
            fcntl.flock(self.opened, fcntl.LOCK_UN)
            os.close(self.opened)  # implies an unlock but that has happend like 6 seconds later
            self.opened = -1
        except Exception as e:
            warn_("[{me}] oops, {e}".format(**locals()))

waitpid_result = collections.namedtuple("waitpid", ["pid", "returncode", "signal" ])

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
        if pid is None:  # unknown $MAINPID
            exitcode = EXIT_CORRUPTED  # 11
            if not waitpid.returncode:
                command = shell_cmd(cmd)
                returncode = waitpid.returncode
                error_("waitpid {command} did return {returncode} => correcting as {exitcode}".format(**locals()))
            waitpid = waitpid_result(waitpid.pid, exitcode, waitpid.signal)
    return waitpid

def subprocess_waitpid(pid):
    run_pid, run_stat = os.waitpid(pid, 0)
    return waitpid_result(run_pid, os.WEXITSTATUS(run_stat), os.WTERMSIG(run_stat))
def subprocess_testpid(pid):
    run_pid, run_stat = os.waitpid(pid, os.WNOHANG)
    if run_pid:
        return waitpid_result(run_pid, os.WEXITSTATUS(run_stat), os.WTERMSIG(run_stat))
    else:
        return waitpid_result(pid, None, 0)

parse_result = collections.namedtuple("UnitName", ["fullname", "name", "prefix", "instance", "suffix", "component" ])

def parse_unit(fullname):  # -> object(prefix, instance, suffix, ...., name, component)
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
    return parse_result(fullname, name, prefix, instance, suffix, component)

def time_to_seconds(text, maximum):
    value = 0.
    for part in str(text).split(" "):
        item = part.strip()
        if item == "infinity":
            return maximum
        if item.endswith("m"):
            try: value += 60 * int(item[:-1])
            except: pass  # pragma: no cover
        if item.endswith("min"):
            try: value += 60 * int(item[:-3])
            except: pass  # pragma: no cover
        elif item.endswith("ms"):
            try: value += int(item[:-2]) / 1000.
            except: pass  # pragma: no cover
        elif item.endswith("s"):
            try: value += int(item[:-1])
            except: pass  # pragma: no cover
        elif item:
            try: value += int(item)
            except: pass  # pragma: no cover
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
            dbg_("{idA} After {idB}".format(**locals()))
            return -1
    for after in getAfter(confB):
        if after == idA:
            dbg_("{idB} After {idA}".format(**locals()))
            return 1
    for before in getBefore(confA):
        if before == idB:
            dbg_("{idA} Before {idB}".format(**locals()))
            return 1
    for before in getBefore(confB):
        if before == idA:
            dbg_("{idB} Before {idA}".format(**locals()))
            return -1
    return 0

def conf_sortedAfter(conflist, cmp=compareAfter):
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
    sortlist = [ SortTuple(0, conf) for conf in conflist]
    for check in xrange(len(sortlist)):  # maxrank = len(sortlist)
        changed = 0
        for A in xrange(len(sortlist)):
            for B in xrange(len(sortlist)):
                if A != B:
                    itemA = sortlist[A]
                    itemB = sortlist[B]
                    before = compareAfter(itemA.conf, itemB.conf)
                    if before > 0 and itemA.rank <= itemB.rank:
                        if DebugSortedAfter:  # pragma: no cover
                            nameA, nameB = itemA.conf.name(), itemB.conf.name()
                            dbg_("  {nameA:-30} before {nameB}".format(**locals()))
                        itemA.rank = itemB.rank + 1
                        changed += 1
                    if before < 0 and itemB.rank <= itemA.rank:
                        if DebugSortedAfter:  # pragma: no cover
                            nameA, nameB = itemA.conf.name(), itemB.conf.name()
                            dbg_("  {nameB:-30} before {nameA}".format(**locals()))
                        itemB.rank = itemA.rank + 1
                        changed += 1
        if not changed:
            if DebugSortedAfter:  # pragma: no cover
                allconfs = len(sortlist)
                dbg_("done in check {check} of {allconfs}".format(**locals()))
            break
            # because Requires is almost always the same as the After clauses
            # we are mostly done in round 1 as the list is in required order
    if DebugSortedAfter:
        for conf in conflist:
            dbg_(".. " + conf.name())
        for item in sortlist:
            rank, name = item.rank, item.conf.name()
            dbg_("({rank}) {name}".format(**locals()))
    sortedlist = sorted(sortlist, key=lambda item: -item.rank)
    if DebugSortedAfter:
        for item in sortedlist:
            rank, name = item.rank, item.conf.name()
            dbg_("[{rank}] {name}".format(**locals()))
    return [ item.conf for item in sortedlist ]

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
        if DebugInitLoop:  # pragma: no cover
            info_("[{me}] listen: new thread".format(**locals()))
        if not self.systemctl._sockets:
            return
        if DebugInitLoop:  # pragma: no cover
            info_("[{me}] listen: start thread".format(**locals()))
        listen = select.poll()
        for sock in self.systemctl._sockets.values():
            listen.register(sock, READ_ONLY)
            sock.listen()
            name, addr = sock.name(), sock.addr()
            dbg_("[{me}] listen: {name} :{addr}".format(**locals()))
        timestamp = time.time()
        while not self.stopped.is_set():
            try:
                sleep_sec = InitLoopSleep - (time.time() - timestamp)
                if sleep_sec < MinimumYield:
                    sleep_sec = MinimumYield
                sleeping = sleep_sec
                while sleeping > 2:
                    time.sleep(1)  # accept signals atleast every second
                    sleeping = InitLoopSleep - (time.time() - timestamp)
                    if sleeping < MinimumYield:
                        sleeping = MinimumYield
                        break
                time.sleep(sleeping)  # remainder waits less that 2 seconds
                if DebugInitLoop:  # pragma: no cover
                    dbg_("[{me}] listen: poll".format(**locals()))
                accepting = listen.poll(100)  # milliseconds
                if DebugInitLoop:  # pragma: no cover
                    amount = len(accepting)
                    dbg_("[{me}] listen: poll ({accepting})".format(**locals()))
                for sock_fileno, event in accepting:
                    for sock in self.systemctl._sockets.values():
                        if sock.fileno() == sock_fileno:
                            if not self.stopped.is_set():
                                if self.systemctl.loop.acquire():
                                    sock_name = sock.name()
                                    dbg_("[{me}] listen: accept {sock_name} :{sock_fileno}".format(**locals()))
                                    self.systemctl.do_accept_socket_from(sock.conf, sock.sock)
            except Exception as e:
                info_("[{me}] listen: interrupted - exception {e}".format(**locals()))
                raise
        for sock in self.systemctl._sockets.values():
            try:
                listen.unregister(sock)
                sock.close()
            except Exception as e:
                warn_("[{me}] listen: close socket: {e}".format(**locals()))
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
    # |
    # |
    # |
    def __init__(self):
        self.error = NOT_A_PROBLEM  # program exitcode or process returncode
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
        self._unit_property = _unit_property
        self._unit_state = _unit_state
        self._unit_type = _unit_type
        # some common constants that may be changed
        self._systemd_version = SystemCompatibilityVersion
        self._journal_log_folder = JournalLogFolder
        # and the actual internal runtime state
        self._loaded_file_sysv = {}  # /etc/init.d/name => config data
        self._loaded_file_sysd = {}  # /etc/systemd/system/name.service => config data
        self._file_for_unit_sysv = None  # name.service => /etc/init.d/name
        self._file_for_unit_sysd = None  # name.service => /etc/systemd/system/name.service
        self._alias_modules = None       # name.service => real.name.service
        self._deps_modules = None        # name.service => Dict[dep,why]
        self._sysinit_modules = None     # name.service => Dict[dep,why]
        self._ignored_modules = None     # text
        self._preset_file_list = None  # /etc/systemd/system-preset/* => file content
        self._default_target = DefaultTarget
        self._sysinit_target = None  # stores a UnitConf()
        self.doExitWhenNoMoreProcs = ExitWhenNoMoreProcs or False
        self.doExitWhenNoMoreServices = ExitWhenNoMoreServices or False
        self._user_mode = _user_mode
        self._user_getlogin = os_getlogin()
        self._log_file = {}  # init-loop
        self._log_hold = {}  # init-loop
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
    def expand_path(self, filepath):
        return expand_path(filepath, not self.user_mode())
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
            if _preset_folder1: yield _preset_folder1
            if _preset_folder2: yield _preset_folder2
            if _preset_folder3: yield _preset_folder3
            if _preset_folder4: yield _preset_folder4
            if _preset_folder5: yield _preset_folder5
            if _preset_folder6: yield _preset_folder6
            if _preset_folderX: yield _preset_folderX
    def init_folders(self):
        SYSTEMD_SYSVINIT_PATH = self.get_SYSTEMD_SYSVINIT_PATH()
        for path in SYSTEMD_SYSVINIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_SYSVINIT_PATH.endswith(":"):
            if _init_folder1: yield _init_folder1
            if _init_folder2: yield _init_folder2
            if _init_folder3: yield _init_folder3
            if _init_folderX: yield _init_folderX
    def user_folders(self):
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH()
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            if _user_folder1: yield expand_path(_user_folder1)
            if _user_folder2: yield expand_path(_user_folder2)
            if _user_folder3: yield expand_path(_user_folder3)
            if _user_folder4: yield expand_path(_user_folder4)
            if _user_folder5: yield expand_path(_user_folder5)
            if _user_folder6: yield expand_path(_user_folder6)
            if _user_folder7: yield expand_path(_user_folder7)
            if _user_folder8: yield expand_path(_user_folder8)
            if _user_folder9: yield expand_path(_user_folder9)
            if _user_folderX: yield expand_path(_user_folderX)
    def system_folders(self):
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH()
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield expand_path(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            if _system_folder1: yield _system_folder1
            if _system_folder2: yield _system_folder2
            if _system_folder3: yield _system_folder3
            if _system_folder4: yield _system_folder4
            if _system_folder5: yield _system_folder5
            if _system_folder6: yield _system_folder6
            if _system_folderX: yield _system_folderX
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
    def scan_unit_sysd_files(self, module=None):  # -> [ unit-names,... ]
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
            found = len(self._file_for_unit_sysd)
            dbg_("found {found} sysd files".format(**locals()))
        return list(self._file_for_unit_sysd.keys())
    def scan_unit_sysv_files(self, module=None):  # -> [ unit-names,... ]
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
                    service_name = name + ".service"  # simulate systemd
                    if service_name not in self._file_for_unit_sysv:
                        self._file_for_unit_sysv[service_name] = path
            found = len(self._file_for_unit_sysv)
            dbg_("found {found} sysv files".format(**locals()))
        return list(self._file_for_unit_sysv.keys())
    def unit_sysd_file(self, module=None):  # -> filename?
        """ file path for the given module (systemd) """
        # this file is scanned upon self.load_sysd_unit_conf(name) -> load_unit_conf(conf)
        self.load_sysd_units()
        if self._alias_modules:
            if module and self._alias_modules and module in self._alias_modules:
                module = self._alias_modules[module]
        if self._file_for_unit_sysd:
            if module and self._file_for_unit_sysd and module in self._file_for_unit_sysd:
                return self._file_for_unit_sysd[module]
            if module and unit_of(module) in self._file_for_unit_sysd:
                return self._file_for_unit_sysd[unit_of(module)]
        return None
    def unit_sysv_file(self, module=None):  # -> filename?
        """ file path for the given module (sysv) """
        # this file is scanned upon self.load_sysv_unit_conf(name) -> load_unit_conf(name)
        self.load_sysv_units()
        if self._file_for_unit_sysv:
            if module and module in self._file_for_unit_sysv:
                return self._file_for_unit_sysv[module]
            if module and unit_of(module) in self._file_for_unit_sysv:
                return self._file_for_unit_sysv[unit_of(module)]
        return None
    def unit_file(self, module=None):  # -> filename?
        """ file path for the given module (sysv or systemd) """
        # this is commonly used through enable/disable - to be similar to load_unit_conf(name)
        path = self.unit_sysd_file(module)  # does also check .alias_modules
        if path is not None: return path
        path = self.unit_sysv_file(module)
        if path is not None: return path
        return None
    def is_sysv_file(self, filename):
        """ for routines that have a special treatment for init.d services """
        self.unit_file()  # scan all
        assert self._file_for_unit_sysd is not None
        assert self._file_for_unit_sysv is not None
        if not filename: return None
        if filename in self._file_for_unit_sysd.values(): return False
        if filename in self._file_for_unit_sysv.values(): return True
        return None  # not True
    def is_user_conf(self, conf):
        if not conf:  # pragma: no cover (is never null)
            return False
        filename = conf.nonloaded_path or conf.filename()
        if filename and "/user/" in filename:
            return True
        return False
    def not_user_conf(self, conf):
        """ conf can not be started as user service (when --user)"""
        if conf is None:  # pragma: no cover (is never null)
            return True
        if not self.user_mode():
            filename44 = path44(conf.filename())
            dbg_("{filename44} no --user mode >> accept".format(**locals()))
            return False
        if self.is_user_conf(conf):
            filename44 = path44(conf.filename())
            dbg_("{filename44} is /user/ conf >> accept".format(**locals()))
            return False
        # to allow for 'docker run -u user' with system services
        user = self.get_User(conf)
        if user and user == self.user():
            filename44 = path44(conf.filename())
            dbg_("{filename44} with User={user} >> accept".format(**locals()))
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
    def load_sysd_template_conf(self, module):  # -> conf?
        """ read the unit template with a UnitConfParser (systemd) """
        if module and "@" in module:
            unit = parse_unit(module)
            prefix = unit.prefix
            service = "{prefix}@.service".format(**locals())
            conf = self.load_sysd_unit_conf(service)
            if conf:
                conf.module = module
            return conf
        return None
    def load_sysd_unit_conf(self, module):  # -> conf?
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
        if self._alias_modules:
            if module in self._alias_modules:
                module = self._alias_modules[module]
        conf = SystemctlConf(data, module)
        conf.masked = masked
        conf.nonloaded_path = path  # if masked
        conf.drop_in_files = drop_in_files
        conf._root = self._root
        self._loaded_file_sysd[path] = conf
        return conf
    def load_sysv_unit_conf(self, module):  # -> conf?
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
    def load_unit_conf(self, module):  # -> conf | None(not-found)
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
            warn_("{module} not loaded: {e}".format(**locals()))
        return None
    def default_unit_conf(self, module, description=None):  # -> conf
        """ a unit conf that can be printed to the user where
            attributes are empty and loaded() is False """
        data = UnitConfParser()
        data.set(Unit, "Description", description or ("NOT-FOUND " + str(module)))
        # assert(not data.loaded())
        conf = SystemctlConf(data, module)
        conf._root = self._root
        return conf
    def get_unit_conf(self, module):  # -> conf (conf | default-conf)
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
    def get_unit_section(self, module, default=Service):
        return string.capwords(self.get_unit_type(module) or default)
    def get_unit_section_from(self, conf, default=Service):
        return self.get_unit_section(conf.name(), default)
    def load_sysv_units(self):
        self.scan_unit_sysv_files()
    def load_sysd_units(self):
        self.scan_unit_sysd_files()
        self.load_alias_cache()
    def match_sysd_templates(self, modules=None, suffix=".service"):  # -> generate[ unit ]
        """ make a file glob on all known template units (systemd areas).
            It returns no modules (!!) if no modules pattern were given.
            The module string should contain an instance name already. """
        modules = to_list(modules)
        if not modules:
            return
        self.load_sysd_units()
        assert self._file_for_unit_sysd is not None
        for item in sorted(self._file_for_unit_sysd.keys()):
            if "@" not in item:
                continue
            unit = parse_unit(item)
            for module in modules:
                if "@" not in module:
                    continue
                mod_unit = parse_unit(module)
                if unit.prefix == mod_unit.prefix:
                    prefix, instance, suffix = unit.prefix, mod_unit.instance, unit.suffix
                    yield "{prefix}@{instance}.{suffix}".format(**locals())
    def match_sysd_units(self, modules=None, suffix=".service"):  # -> generate[ unit ]
        """ make a file glob on all known units (systemd areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        modules = to_list(modules)
        self.load_sysd_units()
        if self._file_for_unit_sysd:
            for item in sorted(self._file_for_unit_sysd.keys()):
                if not modules:
                    yield item
                elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                    yield item
                elif [ module for module in modules if module+suffix == item ]:
                    yield item
        if self._alias_modules:
            for item in sorted(self._alias_modules.keys()):
                if self._file_for_unit_sysd:
                    if item in self._file_for_unit_sysd: continue  # already matched
                if not modules:
                    yield item
                elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                    yield item
                elif [ module for module in modules if module+suffix == item ]:
                    yield item
    def match_sysv_units(self, modules=None, suffix=".service"):  # -> generate[ unit ]
        """ make a file glob on all known units (sysv areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        modules = to_list(modules)
        self.load_sysv_units()
        assert self._file_for_unit_sysv is not None
        for item in sorted(self._file_for_unit_sysv.keys()):
            if not modules:
                yield item
            elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                yield item
            elif [ module for module in modules if module+suffix == item ]:
                yield item
    def match_units(self, modules=None, suffix=".service"):  # -> [ units,.. ]
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
        filename = self.unit_file()  # scan all
        assert self._file_for_unit_sysd is not None
        assert self._file_for_unit_sysv is not None
        result = []
        for name, value in self._file_for_unit_sysd.items():
            result += [ (name, "SysD", value) ]
        for name, value in self._file_for_unit_sysv.items():
            result += [ (name, "SysV", value) ]
        return result
    def list_service_units(self, *modules):  # -> [ (unit,loaded+active+substate,description) ]
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
                warn_("list-units: {e}".format(**locals()))
            if self._unit_state:
                if self._unit_state not in [ result[unit], active[unit], substate[unit] ]:
                    del result[unit]
        return [ (unit, result[unit] + " " + active[unit] + " " + substate[unit], description[unit]) for unit in sorted(result) ]
    def list_units_modules(self, *modules):  # -> [ (unit,loaded,description) ]
        """ [PATTERN]... -- List loaded units.
        If one or more PATTERNs are specified, only units matching one of 
        them are shown. NOTE: This is the default command."""
        hint = "To show all installed unit files use 'systemctl list-unit-files'."
        result = self.list_service_units(*modules)
        if self._no_legend:
            return result
        found = len(result)
        msg = "{found} loaded units listed.".format(**locals())
        return result + [ ("", "", ""), (msg, "", ""), (hint, "", "") ]
    def list_service_unit_files(self, *modules):  # -> [ (unit,enabled) ]
        """ show all the service units and the enabled status"""
        dbg_("list service unit files for {modules}".format(**locals()))
        result = {}
        enabled = {}
        for unit in self.match_units(to_list(modules)):
            if _unit_type and self.get_unit_type(unit) not in _unit_type.split(","):
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
                warn_("list-units: {e}".format(**locals()))
        return [ (unit, enabled[unit]) for unit in sorted(result) if result[unit] ]
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
    def list_target_unit_files(self, *modules):  # -> [ (unit,enabled) ]
        """ show all the target units and the enabled status"""
        enabled = {}
        targets = {}
        for target, filepath in self.each_target_file():
            info_("target {filepath}".format(**locals()))
            targets[target] = filepath
            enabled[target] = "static"
        for unit in _all_common_targets:
            targets[unit] = None
            enabled[unit] = "static"
            if unit in _all_common_enabled:
                enabled[unit] = "enabled"
            if unit in _all_common_disabled:
                enabled[unit] = "disabled"
        return [ (unit, enabled[unit]) for unit in sorted(targets) ]
    def list_unit_files_modules(self, *modules):  # -> [ (unit,enabled) ]
        """[PATTERN]... -- List installed unit files
        List installed unit files and their enablement state (as reported
        by is-enabled). If one or more PATTERNs are specified, only units
        whose filename (just the last component of the path) matches one of
        them are shown. This command reacts to limitations of --type being
        --type=service or --type=target (and --now for some basics)."""
        result = []
        types = self._unit_type
        if self._now:
            basics = self.list_service_unit_basics()
            result = [ (name, sysv + " " + filename) for name, sysv, filename in basics ]
        elif types in ["target"]:
            result = self.list_target_unit_files()
        elif types in ["service"]:
            result = self.list_service_unit_files()
        elif types:
            warn_("unsupported unit --type={types}".format(**locals()))
        else:
            result = self.list_target_unit_files()
            result += self.list_service_unit_files(*modules)
        if self._no_legend:
            return result
        found = len(result)
        msg = "{found} unit files listed.".format(**locals())
        return [ ("UNIT FILE", "STATE") ] + result + [ ("", ""), (msg, "") ]
    ##
    ##
    def get_description(self, unit, default=None):
        return self.get_description_from(self.load_unit_conf(unit))
    def get_description_from(self, conf, default=None):  # -> text
        """ Unit.Description could be empty sometimes """
        if not conf: return default or ""
        description = conf.get(Unit, "Description", default or "")
        return self.expand_special(description, conf)
    def read_pid_file(self, pid_file, default=None):
        pid = default
        if not pid_file:
            return default
        if not os.path.isfile(pid_file):
            return default
        if path_truncate_old(pid_file):
            return default
        try:
            # some pid-files from applications contain multiple lines
            for line in open(pid_file):
                if line.strip():
                    pid = to_intN(line.strip())
                    break
        except Exception as e:
            warn_("bad read of pid file '{pid_file}': {e}".format(**locals()))
        return pid
    def wait_pid_file(self, pid_file, timeout=None):  # -> pid?
        """ wait some seconds for the pid file to appear and return the pid """
        timeout = int(timeout or (DefaultTimeoutStartSec/2))
        timeout = max(timeout, (MinimumTimeoutStartSec))
        dirpath = os.path.dirname(os.path.abspath(pid_file))
        for x in xrange(timeout):
            if not os.path.isdir(dirpath):
                time.sleep(1)  # until TimeoutStartSec/2
                continue
            pid = self.read_pid_file(pid_file)
            if not pid:
                time.sleep(1)  # until TimeoutStartSec/2
                continue
            if not pid_exists(pid):
                time.sleep(1)  # until TimeoutStartSec/2
                continue
            return pid
        return None
    def get_status_pid_file(self, unit):
        """ actual file path of pid file (internal) """
        conf = self.get_unit_conf(unit)
        return self.pid_file_from(conf) or conf.status_file()
    def pid_file_from(self, conf, default=""):
        """ get the specified pid file path (not a computed default) """
        pid_file = self.get_pid_file(conf) or default
        return os_path(self._root, self.expand_special(pid_file, conf))
    def get_pid_file(self, conf, default=None):
        return conf.get(Service, "PIDFile", default)
    def read_mainpid_from(self, conf, default=None):
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
                warn_("while rm {pid_file}: {e}".format(**locals()))
        self.write_status_from(conf, MainPID=None)
    def get_status_file_path(self, unit):
        """ actual file path of the status file (internal) """
        conf = self.get_unit_conf(unit)
        return self.get_status_file_from(conf)
    def get_status_file_from(self, conf):
        return conf.status_file()
    def get_StatusFile(self, conf):  # -> text
        return conf.get_status_file()
    def clean_status_from(self, conf):
        conf.clean_status()
    def write_status_from(self, conf, **status):  # -> bool(written)
        return conf.write_status(**status)
    def read_status_from(self, conf):
        return conf.read_status()
    def get_status_from(self, conf, name, default=None):
        return conf.get_status(name, default)
    def set_status_from(self, conf, name, value):
        conf.set_status(name, value)
    def set_status_code_from(self, conf, execs, run=None, dbg = None, dbgcheck = False):
        if execs in ["ExecStart", "oneshot", "idle", "simple", "forking", "notify"]:
            pref = "ExecMain"
        else:
            pref = "ExecLast"
        self.set_status_from(conf, pref+"Step", execs)
        if run is None:
            self.set_status_from(conf, pref+"PID", None)
            self.set_status_from(conf, pref+"Code", None)
            self.set_status_from(conf, pref+"Status", None)
            return
        self.set_status_from(conf, pref+"PID", str(run.pid))
        if run.returncode is not None:
            if not run.signal:
                self.set_status_from(conf, pref+"Code", "exited")
            else:
                self.set_status_from(conf, pref+"Code", "killed")
            self.set_status_from(conf, pref+"Status", str(run.returncode))
        else:
            self.set_status_from(conf, pref+"Code", "0")
            self.set_status_from(conf, pref+"Status", "0")
        if dbg:
            returncodeOK, signalEE = exitOK(run.returncode), run.signal or ""
            done = "done"
            if run.returncode and dbgcheck: done = "failed"
            dbg_("{dbg} {done} ({returncodeOK}) <-{signalEE}>".format(**locals()))
    #
    #
    def read_env_file(self, env_file):  # -> generate[ (name,value) ]
        """ EnvironmentFile=<name> is being scanned """
        if env_file.startswith("-"):
            env_file = env_file[1:]
            if not os.path.isfile(os_path(self._root, env_file)):
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
            info_("while reading {env_file}: {e}".format(**locals()))
    def read_env_part(self, env_part):  # -> generate[ (name, value) ]
        """ Environment=<name>=<value> is being scanned """
        # systemd Environment= spec says it is a space-seperated list of
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
            info_("while reading {env_part}: {e}".format(**locals()))
    def command_of_unit(self, unit):
        """ [UNIT]. -- show service settings (experimental)
            or use -p VarName to show another property than 'ExecStart' """
        conf = self.load_unit_conf(unit)
        if conf is None:
            error_("Unit {unit} could not be found.".format(**locals()))
            self.error |= NOT_FOUND
            return None
        if _unit_property:
            return conf.getlist(Service, _unit_property)
        return conf.getlist(Service, "ExecStart")
    def environment_of_unit(self, unit):
        """ [UNIT]. -- show environment parts """
        conf = self.load_unit_conf(unit)
        if conf is None:
            error_("Unit {unit} could not be found.".format(**locals()))
            self.error |= NOT_FOUND
            return None
        return self.get_env(conf)
    def extra_vars(self):
        return self._extra_vars  # from command line
    def get_env(self, conf):
        env = os.environ.copy()
        for env_part in conf.getlist(Service, "Environment", []):
            for name, value in self.read_env_part(self.expand_special(env_part, conf)):
                env[name] = value  # a '$word' is not special here (lazy expansion)
        for env_file in conf.getlist(Service, "EnvironmentFile", []):
            for name, value in self.read_env_file(self.expand_special(env_file, conf)):
                env[name] = self.expand_env(value, env)  # but nonlazy expansion here
        if DebugExpandVars:  # pragma: no cover
            extra_vars = self.extra_vars()
            dbg_("extra-vars {extra_vars}".format(**locals()))
        for extra in self.extra_vars():
            if extra.startswith("@"):
                for name, value in self.read_env_file(extra[1:]):
                    if DebugExpandVars:  # pragma: no cover
                        info_("override {name}={value}".format(**locals()))
                    env[name] = self.expand_env(value, env)
            else:
                for name, value in self.read_env_part(extra):
                    if DebugExpandVars:  # pragma: no cover
                        info_("override {name}={value}".format(**locals()))
                    env[name] = value  # a '$word' is not special here
        return env
    def expand_env(self, cmd, env):
        def get_env1(m):
            name = m.group(1)
            if name in env:
                return env[name]
            namevar = "$%s" % name
            if DebugExpandVars:  # pragma: no cover
                dbg_("can not expand {namevar}".format(**locals()))
            return (ExpandVarsKeepName and namevar or "")
        def get_env2(m):
            name = m.group(1)
            if name in env:
                return env[name]
            namevar = "${%s}" % name
            if DebugExpandVars:  # pragma: no cover
                dbg_("can not expand {namevar}".format(**locals()))
            return (ExpandVarsKeepName and namevar or "")
        #
        maxdepth = ExpandVarsMaxDepth
        expanded = re.sub("[$](\w+)", lambda m: get_env1(m), cmd.replace("\\\n", ""))
        for depth in xrange(maxdepth):
            new_text = re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), expanded)
            if new_text == expanded:
                return expanded
            expanded = new_text
        error_("shell variable expansion exceeded maxdepth {maxdepth}".format(**locals()))
        return expanded
    def expand_special(self, cmd, conf):
        """ expand %i %t and similar special vars. They are being expanded
            before any other expand_env takes place which handles shell-style
            $HOME references. """
        def xx(arg): return unit_name_unescape(arg)
        def yy(arg): return arg
        def get_confs(conf):
            confs={ "%": "%" }
            if conf is None:  # pragma: no cover (is never null)
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
            GROUP_ID = get_GROUP_ID(root)  # getegid()            # 0
            SHELL = get_SHELL(root)       # $SHELL               # "/bin/sh"
            # confs["b"] = boot_ID
            confs["C"] = os_path(self._root, CACHE)  # Cache directory root
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
            name = m.group(1)
            if name in confs:
                return confs[name]
            warn_("can not expand %{name} special".format(**locals()))
            return ""
        result = ""
        if cmd:
            result = re.sub("[%](.)", lambda m: get_conf1(m), cmd)
            if DebugExpandVars:  # pragma: no cover
                dbg_("expanded => {result}".format(**locals()))
        return result
    def exec_newcmd(self, cmd, env, conf):
        execmode, execline = exec_mode(cmd)
        newcmd = self.exec_cmd(execline, env, conf)
        return execmode, newcmd
    def exec_cmd(self, cmd, env, conf):
        """ expand ExecCmd statements including %i and $MAINPID """
        cmd2 = cmd.replace("\\\n", "")
        # according to documentation, when bar="one two" then the expansion
        # of '$bar' is ["one","two"] and '${bar}' becomes ["one two"]. We
        # tackle that by expand $bar before shlex, and the rest thereafter.
        def get_env1(m):
            name = m.group(1)
            if name in env:
                return env[name]
            dbg_("can not expand ${name}".format(**locals()))
            return ""  # empty string
        def get_env2(m):
            name = m.group(1)
            if name in env:
                return env[name]
            dbg_("can not expand ${{{name}}}".format(**locals()))
            return ""  # empty string
        cmd3 = re.sub("[$](\w+)", lambda m: get_env1(m), cmd2)
        newcmd = []
        for part in shlex.split(cmd3):
            # newcmd += [ re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), part) ]
            newcmd += [ re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), self.expand_special(part, conf)) ]
        return newcmd
    def remove_service_directories(self, conf, section=Service):
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
            dbg_("could not fully remove service directory {path}".format(**locals()))
        return ok
    def do_rm_tree(self, run_path):
        ok = True
        if os.path.isdir(run_path):
            for dirpath, dirnames, filenames in os.walk(run_path, topdown=False):
                for item in filenames:
                    filepath = os.path.join(dirpath, item)
                    try:
                        os.remove(filepath)
                    except Exception as e:  # pragma: no cover
                        dbg_("not removed file: {filepath} ({e})".format(**locals()))
                        ok = False
                for item in dirnames:
                    dir_path = os.path.join(dirpath, item)
                    try:
                        os.rmdir(dir_path)
                    except Exception as e:  # pragma: no cover
                        dbg_("not removed dir: {dir_path} ({e})".format(**locals()))
                        ok = False
            try:
                os.rmdir(run_path)
            except Exception as e:
                dbg_("not removed top dir: {run_path} ({e})".format(**locals()))
                ok = False  # pragma: no cover
        fail = ok and "done" or "fail"
        dbg_("{fail} rm_tree {run_path}".format(**locals()))
        return ok
    def get_RuntimeDirectoryPreserve(self, conf, section=Service):
        return conf.getbool(section, "RuntimeDirectoryPreserve", "no")
    def get_RuntimeDirectory(self, conf, section=Service):
        return self.expand_special(conf.get(section, "RuntimeDirectory", ""), conf)
    def get_StateDirectory(self, conf, section=Service):
        return self.expand_special(conf.get(section, "StateDirectory", ""), conf)
    def get_CacheDirectory(self, conf, section=Service):
        return self.expand_special(conf.get(section, "CacheDirectory", ""), conf)
    def get_LogsDirectory(self, conf, section=Service):
        return self.expand_special(conf.get(section, "LogsDirectory", ""), conf)
    def get_ConfigurationDirectory(self, conf, section=Service):
        return self.expand_special(conf.get(section, "ConfigurationDirectory", ""), conf)
    def get_RuntimeDirectoryMode(self, conf, section=Service):
        return conf.get(section, "RuntimeDirectoryMode", "")
    def get_StateDirectoryMode(self, conf, section=Service):
        return conf.get(section, "StateDirectoryMode", "")
    def get_CacheDirectoryMode(self, conf, section=Service):
        return conf.get(section, "CacheDirectoryMode", "")
    def get_LogsDirectoryMode(self, conf, section=Service):
        return conf.get(section, "LogsDirectoryMode", "")
    def get_ConfigurationDirectoryMode(self, conf, section=Service):
        return conf.get(section, "ConfigurationDirectoryMode", "")
    def clean_service_directories(self, conf, which=""):
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
            dbg_("RuntimeDirectory {path}".format(**locals()))
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
                                dbg_("not a symlink: {var_dirpath}".format(**locals()))
                            continue
                        dirpath = os_path(self._root, path)
                        basepath = os.path.dirname(var_dirpath)
                        if not os.path.isdir(basepath):
                            os.makedirs(basepath)
                        try:
                            os.symlink(dirpath, var_dirpath)
                        except Exception as e:
                            dbg_("var symlink {var_dirpath}\n\t{e}".format(**locals()))
        for name in nameStateDirectory.split(" "):
            if not name.strip(): continue
            DAT = get_VARLIB_HOME(root)
            path = os.path.join(DAT, name)
            dbg_("StateDirectory {path}".format(**locals()))
            self.make_service_directory(path, modeStateDirectory)
            self.chown_service_directory(path, user, group)
            envs["STATE_DIRECTORY"] = path
        for name in nameCacheDirectory.split(" "):
            if not name.strip(): continue
            CACHE = get_CACHE_HOME(root)
            path = os.path.join(CACHE, name)
            dbg_("CacheDirectory {path}".format(**locals()))
            self.make_service_directory(path, modeCacheDirectory)
            self.chown_service_directory(path, user, group)
            envs["CACHE_DIRECTORY"] = path
        for name in nameLogsDirectory.split(" "):
            if not name.strip(): continue
            LOGS = get_LOG_DIR(root)
            path = os.path.join(LOGS, name)
            dbg_("LogsDirectory {path}".format(**locals()))
            self.make_service_directory(path, modeLogsDirectory)
            self.chown_service_directory(path, user, group)
            envs["LOGS_DIRECTORY"] = path
        for name in nameConfigurationDirectory.split(" "):
            if not name.strip(): continue
            CONFIG = get_CONFIG_HOME(root)
            path = os.path.join(CONFIG, name)
            dbg_("ConfigurationDirectory {path}".format(**locals()))
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
                info_("created directory path: {dirpath}".format(**locals()))
            except Exception as e:  # pragma: no cover
                dbg_("errors directory path: {dirpath}\n\t{e}".format(**locals()))
                ok = False
            filemode = int_mode(mode)
            if filemode:
                try:
                    os.chmod(dirpath, filemode)
                except Exception as e:  # pragma: no cover
                    dbg_("errors directory path: {dirpath}\n\t{e}".format(**locals()))
                    ok = False
        else:
            dbg_("path did already exist: {dirpath}".format(**locals()))
        if not ok:
            dbg_("could not fully create service directory {path}".format(**locals()))
        return ok
    def chown_service_directory(self, path, user, group):
        # the standard defines an optimization so that if the parent
        # directory does have the correct user and group then there
        # is no other chown on files and subdirectories to be done.
        dirpath = os_path(self._root, path)
        if not os.path.isdir(dirpath):
            dbg_("chown did not find {dirpath}".format(**locals()))
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
                dbg_("do chown {dirpath}".format(**locals()))
                try:
                    ok = self.do_chown_tree(dirpath, user, group)
                    info_("changed {user}:{group} {ok}".format(**locals()))
                    return ok
                except Exception as e:
                    info_("oops {dirpath}\n\t{e}".format(**locals()))
            else:
                dbg_("untouched {dirpath}".format(**locals()))
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
                except Exception as e:  # pragma: no cover
                    dbg_("could not set {user}:{group} on {filepath}\n\t{e}".format(**locals()))
                    ok = False
            for item in dirnames:
                dir_path = os.path.join(dirpath, item)
                try:
                    os.chown(dir_path, uid, gid)
                except Exception as e:  # pragma: no cover
                    dbg_("could not set {user}:{group} on {dir_path}\n\t{e}".format(**locals()))
                    ok = False
        try:
            os.chown(path, uid, gid)
        except Exception as e:  # pragma: no cover
            dbg_("could not set {user}:{group} on {path}\n\t{e}".format(**locals()))
            ok = False
        if not ok:
            dbg_("could not chown {user}:{group} service directory {path}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        lines = _log_lines
        follow = _force
        ok = self.clean_units(units)
        return ok and found_all
    def clean_units(self, units, what=""):
        if not what:
            what = _what_kind
        ok = True
        for unit in units:
            ok = self.clean_unit(unit, what) and ok
        return ok
    def clean_unit(self, unit, what=""):
        conf = self.load_unit_conf(unit)
        if not conf: return False
        return self.clean_unit_from(conf, what)
    def clean_unit_from(self, conf, what):
        if self.is_active_from(conf):
            name = conf.name()
            warn_("can not clean active unit: {name}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        lines = _log_lines
        follow = _force
        result = self.log_units(units, lines, follow)
        if result:
            self.error = result
            return False
        return found_all
    def log_units(self, units, lines=None, follow=False):
        result = 0
        for unit in self.sortedAfter(units):
            exitcode = self.log_unit(unit, lines, follow)
            if exitcode < 0:
                return exitcode
            if exitcode > result:
                result = exitcode
        return result
    def log_unit(self, unit, lines=None, follow=False):
        conf = self.load_unit_conf(unit)
        if not conf: return -1
        return self.log_unit_from(conf, lines, follow)
    def log_unit_from(self, conf, lines=None, follow=False):
        filename = self.get_journal_log_from(conf)
        unit = conf.name()
        msg = "journalctl {unit}".format(**locals())
        if _no_pager or not os.isatty(sys.stdout.fileno()):
            show = [ DefaultCat ]
            cmd = show + [ filename ]
        else:
            pager = get_PAGER()
            cmd = pager + [ filename ]
        if follow:
            cmd = [ DefaultTail, "-n", str(lines or 10), "-F", filename ]
        elif lines:
            cmd = [ DefaultTail, "-n", str(lines or 10), filename ]
        dbg_("{msg} -> {cmd}".format(**locals()))
        return os.spawnvp(os.P_WAIT, cmd[0], cmd)  # type: ignore
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
        if workingdir:
            ignore = False
            if workingdir.startswith("-"):
                workingdir = workingdir[1:]
                ignore = True
            into = os_path(self._root, self.expand_special(workingdir, conf))
            try:
                dbg_("chdir workingdir '{into}'".format(**locals()))
                os.chdir(into)
                return None
            except Exception as e:
                if not ignore:
                    error_("chdir workingdir '{into}': {e}".format(**locals()))
                    return "{into} : {e}".format(**locals())
                else:
                    dbg_("chdir workingdir '{into}': {e}".format(**locals()))
                    return None
        return None
    NotifySocket = collections.namedtuple("NotifySocket", ["socket", "socketfile" ])
    def get_notify_socket_from(self, conf, socketfile=None, debug=False):
        """ creates a notify-socket for the (non-privileged) user """
        notify_socket_folder = expand_path(NotifySocketFolder, conf.root_mode())
        notify_folder = os_path(self._root, notify_socket_folder)
        notify_name = "notify." + str(conf.name() or "systemctl")
        notify_socket = os.path.join(notify_folder, notify_name)
        socketfile = socketfile or notify_socket
        if len(socketfile) > 100:
            # occurs during testsuite.py for ~user/test.tmp/root path
            if debug:
                path_length = len(socketfile)
                page = "why-is-socket-path-length-limited-to-a-hundred-chars"
                dbg_("https://unix.stackexchange.com/questions/367008/{page}".format(**locals()))
                dbg_("old notify socketfile ({path_length}) = {socketfile}".format(**locals()))
            notify_name44 = o44(notify_name)
            notify_name77 = o77(notify_name)
            socketfile = os.path.join(notify_folder, notify_name77)
            if len(socketfile) > 100:
                socketfile = os.path.join(notify_folder, notify_name44)
            socketfoldername = os.path.basename(NotifySocketFolder)
            uid = get_USER_ID()
            pref1 = "zz.{uid}.{socketfoldername}".format(**locals())
            pref0 = "zz.{uid}".format(**locals())
            if len(socketfile) >= 100:
                socketfile = os.path.join(get_TMP(), pref1, notify_name)
            if len(socketfile) >= 100:
                socketfile = os.path.join(get_TMP(), pref1, notify_name77)
            if len(socketfile) >= 100:  # pragma: no cover
                socketfile = os.path.join(get_TMP(), pref1, notify_name44)
            if len(socketfile) >= 100:  # pragma: no cover
                socketfile = os.path.join(get_TMP(), pref0, notify_name44)
            if len(socketfile) >= 100:  # pragma: no cover
                socketfile = os.path.join(get_TMP(), notify_name44)
            if debug:
                path_length = len(socketfile)
                info_("new notify socketfile ({path_length}) = {socketfile}".format(**locals()))
        return socketfile
    def notify_socket_from(self, conf, socketfile=None):
        socketfile = self.get_notify_socket_from(conf, socketfile, debug=DebugSocketFile)
        try:
            if not os.path.isdir(os.path.dirname(socketfile)):
                os.makedirs(os.path.dirname(socketfile))
            if os.path.exists(socketfile):
                os.unlink(socketfile)
        except Exception as e:
            warn_("error {socketfile}: {e}".format(**locals()))
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(socketfile)
        os.chmod(socketfile, 0o777)  # the service my run under some User=setting
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
                dbg_("read_notify_socket({result_len}):{result_txt}".format(**locals()))
        except socket.timeout as e:
            if timeout > 2:
                dbg_("socket.timeout {e}".format(**locals()))
        return result
    def wait_notify_socket(self, notify, timeout, pid=None, pid_file=None):
        if not os.path.exists(notify.socketfile):
            info_("no $NOTIFY_SOCKET exists")
            return {}
        #
        lapseTimeout = max(3, int(timeout / 100))
        mainpidTimeout = lapseTimeout  # Apache sends READY before MAINPID
        status = ""
        info_("wait $NOTIFY_SOCKET, timeout {timeout} (lapse {lapseTimeout})".format(**locals()))
        waiting = " ---"
        results = {}
        for attempt in xrange(int(timeout)+1):
            if pid and not self.is_active_pid(pid):
                info_("seen dead PID {pid}".format(**locals()))
                return results
            if not attempt:  # first one
                time.sleep(1)  # until TimeoutStartSec
                continue
            result = self.read_notify_socket(notify, 1)  # sleep max 1 second
            for line in result.splitlines():
                # for name, value in self.read_env_part(line)
                if "=" not in line:
                    continue
                name, value = line.split("=", 1)
                results[name] = value
                if name in ["STATUS", "ACTIVESTATE", "MAINPID", "READY"]:
                    hint="seen notify {waiting}     ".format(**locals())
                    dbg_("{hint} :{name}={value}".format(**locals()))
            if status != results.get("STATUS", ""):
                mainpidTimeout = lapseTimeout
                status = results.get("STATUS", "")
            if "READY" not in results:
                time.sleep(1)  # until TimeoutStart
                continue
            if "MAINPID" not in results and not pid_file:
                mainpidTimeout -= 1
                if mainpidTimeout > 0:
                    waiting = "%4i" % (-mainpidTimeout)
                    time.sleep(1)  # until TimeoutStart
                    continue
            break  # READY and MAINPID
        if "READY" not in results:
            info_(".... timeout while waiting for 'READY=1' status on $NOTIFY_SOCKET")
        elif "MAINPID" not in results:
            info_(".... seen 'READY=1' but no MAINPID update status on $NOTIFY_SOCKET")
        dbg_("notify = {results}".format(**locals()))
        try:
            notify.socket.close()
        except Exception as e:
            dbg_("socket.close {e}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
        init = self._now or self._init
        return self.start_units(units, init) and found_all
    def start_units(self, units, init=None):
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
            info_("init-loop start")
            sig = self.init_loop_until_stop(started_units)
            info_("init-loop {sig}".format(**locals()))
            for unit in reversed(started_units):
                self.stop_unit(unit)
        return done
    def start_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            dbg_("unit could not be loaded ({unit})".format(**locals()))
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
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
        problems = self.check_syntax_from(conf)
        errors = [ problem for problem in problems if problem.startswith("E") ]
        if errors and not self._force:
            some = len(errors)
            error_("did find {some} errors, refusing to start unit. (use --force to pass)".format(**locals()))
            return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            dbg_(" start unit {unit} => {filename44}".format(**locals()))
            return self.do_start_unit_from(conf)
    def do_start_unit_from(self, conf):
        unit = conf.name()
        if unit.endswith(".service"):
            return self.do_start_service_from(conf)
        elif unit.endswith(".socket"):
            return self.do_start_socket_from(conf)
        elif unit.endswith(".target"):
            return self.do_start_target_from(conf)
        else:
            error_("start not implemented for unit type: {unit}".format(**locals()))
            return False
    def do_start_service_from(self, conf):
        timeout = self.get_TimeoutStartSec(conf)
        doRemainAfterExit = self.get_RemainAfterExit(conf)
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.check_exec_from(conf, env, Service, "Exec")  # all...
            if not okee and _no_reload: return False
        service_directories = self.create_service_directories(conf)
        env.update(service_directories)  # atleast sshd did check for /run/sshd
        # for StopPost on failure:
        returncode = 0
        service_result = "success"
        oldstatus = self.get_status_from(conf, "ActiveState", None)
        self.set_status_code_from(conf, "starting", None)
        self.write_status_from(conf, AS="starting", SS=None)
        if True:
            if runs in [ "simple", "forking", "notify", "idle" ]:
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
            for cmd in conf.getlist(Service, "ExecStartPre", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_(" pre-start", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStartPre", run, "pre-start", exe.check)
                if run.returncode and exe.check:
                    error_("the ExecStartPre control process exited with error code")
                    active = "failed"
                    self.write_status_from(conf, AS=active )
                    if _what_kind not in ["none", "keep"]:
                        self.remove_service_directories(conf)  # cleanup that /run/sshd
                    return False
        if runs in [ "oneshot" ]:
            if oldstatus in ["active"]:
                warn_("the service was already up once")
                self.write_status_from(conf, AS=oldstatus)
                return True
            self.set_status_code_from(conf, runs, None)
            if doRemainAfterExit and ActiveWhileStarting:
                dbg_("{runs} RemainAfterExit -> AS=active".format(**locals()))
                self.write_status_from(conf, AS="active")
            for cmd in conf.getlist(Service, "ExecStart", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("{runs} start".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:  # pragma: no cover
                    os.setsid()  # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStart", run, runs+" start", exe.check)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            if doRemainAfterExit:
                active = run.returncode and "failed" or "active"
                self.write_status_from(conf, AS=active)
            else:
                active = returncode and "failed" or "dead"
                self.write_status_from(conf, AS=active)
                # Note that if this option is used without RemainAfterExit= the service will never enter
                # "active" unit state, but directly transition from "activating" to "deactivating" or "dead"
                # since no process is configured that shall run continuously. In particular this means that
                # after a service of this type ran (and which has RemainAfterExit= not set) it will not show
                # up as started afterwards, but as dead. [freedesktop.org/.../man/systemd.service.html]
        elif runs in [ "simple", "idle" ]:
            pid = self.read_mainpid_from(conf)
            if self.is_active_pid(pid):
                warn_("the service is already running on PID {pid}".format(**locals()))
                return True
            self.set_status_code_from(conf, runs, None)
            if doRemainAfterExit and ActiveWhileStarting:
                dbg_("{runs} RemainAfterExit -> AS=active".format(**locals()))
                self.write_status_from(conf, AS="active")
            cmdlist = conf.getlist(Service, "ExecStart", [])
            for idx, cmd in enumerate(cmdlist):
                dbg_("ExecStart[{idx}]: {cmd}".format(**locals()))
            for cmd in cmdlist:
                pid = self.read_mainpid_from(conf)
                env["MAINPID"] = strE(pid)
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("{runs} start".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:  # pragma: no cover
                    os.setsid()  # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                self.write_status_from(conf, MainPID=forkpid)
                info_("{runs} started PID {forkpid}".format(**locals()))
                env["MAINPID"] = strE(forkpid)
                time.sleep(MinimumYield)
                run = subprocess_testpid(forkpid)
                self.set_status_code_from(conf, "ExecStart", run, runs+" start", exe.check)
                if run.returncode is not None:
                    if run.returncode and exe.check:
                        returncode = run.returncode
                        service_result = "failed"
                        break
            if doRemainAfterExit:
                active = run.returncode and "failed" or "active"
                self.write_status_from(conf, AS=active)
            elif returncode:
                active = returncode and "failed" or "active"  # always "failed"
                self.write_status_from(conf, AS=active)
            else:
                self.write_status_from(conf, AS=None)  # active comes from PID
        elif runs in [ "notify" ]:
            # "notify" is the same as "simple" but we create a $NOTIFY_SOCKET
            # and wait for startup completion by checking the socket messages
            pid_file = self.pid_file_from(conf)
            pid = self.read_mainpid_from(conf)
            if self.is_active_pid(pid):
                error_("the service is already running on PID {pid}".format(**locals()))
                return False
            self.set_status_code_from(conf, runs, None)
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                socketfile44 = path44(notify.socketfile)
                debug_("use NOTIFY_SOCKET={socketfile44}".format(**locals()))
            if doRemainAfterExit and ActiveWhileStarting:
                dbg_("{runs} RemainAfterExit -> AS=active".format(**locals()))
                self.write_status_from(conf, AS="active")
            cmdlist = conf.getlist(Service, "ExecStart", [])
            for idx, cmd in enumerate(cmdlist):
                dbg_("ExecStart[{idx}]: {cmd}".format(**locals()))
            mainpid = None
            for cmd in cmdlist:
                mainpid = self.read_mainpid_from(conf)
                env["MAINPID"] = strE(mainpid)
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("{runs} start".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:  # pragma: no cover
                    os.setsid()  # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                # via NOTIFY # self.write_status_from(conf, MainPID=forkpid)
                info_("{runs} started PID {forkpid}".format(**locals()))
                mainpid = forkpid
                self.write_status_from(conf, MainPID=mainpid)
                env["MAINPID"] = strE(mainpid)
                time.sleep(MinimumYield)
                run = subprocess_testpid(forkpid)
                self.set_status_code_from(conf, "ExecStart", run, runs+" start", exe.check)
                if run.returncode is not None:
                    if run.returncode and exe.check:
                        returncode = run.returncode
                        service_result = "failed"
                        break
            if service_result in [ "success" ] and mainpid:
                dbg_("okay, wating on socket for {timeout}s".format(**locals()))
                results = self.wait_notify_socket(notify, timeout, mainpid, pid_file)
                if "MAINPID" in results:
                    new_pid = to_intN(results["MAINPID"])
                    if new_pid and new_pid != mainpid:
                        info_("NEW PID {new_pid} from sd_notify (was PID {mainpid})".format(**locals()))
                        self.write_status_from(conf, MainPID=new_pid)
                        mainpid = new_pid
                info_("{runs} start done {mainpid}".format(**locals()))
                pid = self.read_mainpid_from(conf)
                if pid:
                    env["MAINPID"] = strE(pid)
                else:
                    service_result = "timeout"  # "could not start service"
            if doRemainAfterExit:
                active = run.returncode and "failed" or "active"
                self.write_status_from(conf, AS=active)
            elif returncode:
                active = returncode and "failed" or "active"  # always "failed"
                self.write_status_from(conf, AS=active)
            else:
                self.write_status_from(conf, AS=None)  # active comes from PID
        elif runs in [ "forking" ]:
            pid_file = self.pid_file_from(conf)
            self.set_status_code_from(conf, runs, None)
            for cmd in conf.getlist(Service, "ExecStart", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                if not newcmd: continue
                info_("{runs} start".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:  # pragma: no cover
                    os.setsid()  # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                info_("{runs} started PID {forkpid}".format(**locals()))
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStart", run, runs+" start", exe.check)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
            if pid_file and service_result in [ "success" ]:
                pid = self.wait_pid_file(pid_file)  # application PIDFile
                info_("{runs} start done PID {pid} [{pid_file}]".format(**locals()))
                if pid:
                    env["MAINPID"] = strE(pid)
            if not pid_file:
                time.sleep(MinimumTimeoutStartSec)
                filename44 = path44(conf.filename())
                warn_("No PIDFile for forking {filename44}".format(**locals()))
                active = run.returncode and "failed" or "active"  # result "failed"
                self.write_status_from(conf, AS=active)  # have no PID and no PIDFile
            elif returncode:
                active = run.returncode and "failed" or "active"  # result "failed"
                self.write_status_from(conf, AS=active)
            else:
                self.clean_status_from(conf)  # active comes from PIDFile alone
        else:
            error_("  unsupported run type '{runs}' (not implemented)".format(**locals()))
            self.clean_status_from(conf)  # "inactive"
            return False
        # POST sequence
        if not self.is_active_from(conf):
            warn_("{runs} start not active".format(**locals()))
            # according to the systemd documentation, a failed start-sequence
            # should execute the ExecStopPost sequence allowing some cleanup.
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Service, "ExecStopPost", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("post-fail", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStopPost", run, "post-fail")
            if _what_kind not in ["none", "keep"]:
                self.remove_service_directories(conf)
            return False
        else:
            for cmd in conf.getlist(Service, "ExecStartPost", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("post-start", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStartPost", run, "post-start")
            return True
    def listen_modules(self, *modules):
        """ [UNIT]... -- listen socket units"""
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
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
            info_("init-loop start")
            sig = self.init_loop_until_stop(started_units)
            info_("init-loop {sig}".format(**locals()))
        for started in reversed(started_units):
            if False:  # pragma: no cover
                self.stop_unit(started)
        return done
    def listen_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            dbg_("unit could not be loaded ({unit})".format(**locals()))
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.listen_unit_from(conf)
    def listen_unit_from(self, conf):
        if not conf: return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            dbg_(" listen unit {unit} => {filename44}".format(**locals()))
            return self.do_listen_unit_from(conf)
    def do_listen_unit_from(self, conf):
        if conf.name().endswith(".socket"):
            return self.do_start_socket_from(conf)
        else:
            unit = conf.name()
            error_("listen not implemented for unit type: {unit}".format(**locals()))
            return False
    def do_accept_socket_from(self, conf, sock):
        unit, fileno = conf.name(), sock.fileno()
        dbg_("{unit}: accepting {fileno}".format(**locals()))
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None or TestSocketAccept:  # pragma: no cover
            if sock.type == socket.SOCK_STREAM:
                conn, addr = sock.accept()
                data = conn.recv(1024)
                dbg_("{unit}: '{data}'".format(**locals()))
                conn.send(b"ERROR: "+data.upper())
                conn.close()
                return False
            if sock.type == socket.SOCK_DGRAM:
                data, sender = sock.recvfrom(1024)
                dbg_("{unit}: '{data}'".format(**locals()))
                sock.sendto(b"ERROR: "+data.upper(), sender)
                return False
            socktype = strINET(sock.type)
            error_("can not accept socket type {socktype}".format(**locals()))
            return False
        return self.do_start_service_from(service_conf)
    def get_socket_service_from(self, conf):
        socket_unit = conf.name()
        accept = conf.getbool(Socket, "Accept", "no")
        service_type = accept and "@.service" or ".service"
        service_name = path_replace_extension(socket_unit, ".socket", service_type)
        service_unit = conf.get(Socket, "Service", service_name)
        dbg_("socket {socket_unit} -> service {service_unit}".format(**locals()))
        return service_unit
    def do_start_socket_from(self, conf):
        runs = "socket"
        timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool(Socket, "Accept", "no")
        stream = conf.get(Socket, "ListenStream", "")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None:
            dbg_("unit could not be loaded ({service_unit})".format(**locals()))
            error_("Unit {service_unit} not found.".format(**locals()))
            return False
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.check_exec_from(conf, env, Socket, "Exec")  # all...
            if not okee and _no_reload: return False
        self.set_status_code_from(conf, "starting", None)
        if True:
            for cmd in conf.getlist(Socket, "ExecStartPre", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_(" pre-start", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStartPre", run, "pre-start", exe.check)
                if run.returncode and exe.check:
                    error_("the ExecStartPre control process exited with error code")
                    active = "failed"
                    self.write_status_from(conf, AS=active)
                    return False
        # service_directories = self.create_service_directories(conf)
        # env.update(service_directories)
        listening=False
        if not accept:
            sock = self.create_socket(conf)
            if sock and TestSocketListen:
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
                info_("post-fail", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStopPost", run, "post-fail")
            return False
        else:
            for cmd in conf.getlist(Socket, "ExecStartPost", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("post-start", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStartPost", run, "post-start")
            return True
    def create_socket(self, conf):
        unit = conf.name()
        unsupported = ["ListenUSBFunction", "ListenMessageQueue", "ListenNetlink"]
        unsupported += [ "ListenSpecial", "ListenFIFO", "ListenSequentialPacket"]
        for setting in unsupported:
            if conf.get(Socket, setting, ""):
                warn_("{unit}: {setting} sockets are not implemented".format(**locals()))
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
            warn_("{unit}: abstract namespace socket not implemented ({address})".format(**locals()))
            return None
        if re.match("vsock:.*", address):
            warn_("{unit}: virtual machine socket not implemented ({address})".format(**locals()))
            return None
        error_("{unit}: unknown socket address type ({address})".format(**locals()))
        return None
    def create_unix_socket(self, conf, sockpath, dgram):
        unit = conf.name()
        sock_stream = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_UNIX, sock_stream)
        try:
            dirmode = conf.get(Socket, "DirectoryMode", "0755")
            mode = conf.get(Socket, "SocketMode", "0666")
            user = conf.get(Socket, "SocketUser", "")
            group = conf.get(Socket, "SocketGroup", "")
            symlinks = conf.getlist(Socket, "SymLinks", [])
            dirpath = os.path.dirname(sockpath)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath, int(dirmode, 8))
            if os.path.exists(sockpath):
                os.unlink(sockpath)
            sock.bind(sockpath)
            os.fchmod(sock.fileno(), int(mode, 8))
            shutil_fchown(sock.fileno(), user, group)
            if symlinks:
                warn_("{unit}: symlinks for socket not implemented [{sockpath}]".format(**locals()))
        except Exception as e:
            error_("{unit}: create socket failed [{sockpath}]: {e}".format(**locals()))
            sock.close()
            return None
        return sock
    def create_port_socket(self, conf, port, dgram):
        unit = conf.name()
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET, inet)
        try:
            sock.bind(('', int(port)))
            socktype = strINET(inet)
            addr = "*"
            info_("{unit}: bound socket at {socktype} ({addr}:{port})".format(**locals()))
        except Exception as e:
            error_("{unit}: create socket failed ({addr}:{port}): {e}".format(**locals()))
            sock.close()
            return None
        return sock
    def create_port_ipv4_socket(self, conf, addr, port, dgram):
        unit = conf.name()
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET, inet)
        try:
            sock.bind((addr, int(port)))
            socktype = strINET(inet)
            info_("{unit}: bound socket at {socktype} ({addr}:{port})".format(**locals()))
        except Exception as e:
            error_("{unit}: create socket failed ({addr}:{port}): {e}".format(**locals()))
            sock.close()
            return None
        return sock
    def create_port_ipv6_socket(self, conf, addr, port, dgram):
        unit = conf.name()
        inet = dgram and socket.SOCK_DGRAM or socket.SOCK_STREAM
        sock = socket.socket(socket.AF_INET6, inet)
        try:
            sock.bind((addr, int(port)))
            socktype = strINET(inet)
            info_("{unit}: bound socket at {socktype} ([{addr}]:{port})".format(**locals()))
        except Exception as e:
            error_("{unit}: create socket failed ({addr}:{port}): {e}".format(**locals()))
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
        if self.get_unit_type(conf.name()) not in [ "service" ]:
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
        ret = 0
        std_inp = conf.get(Service, "StandardInput", DefaultStandardInput)
        std_out = conf.get(Service, "StandardOutput", DefaultStandardOutput)
        std_err = conf.get(Service, "StandardError", DefaultStandardError)
        # msg += "\n StandardInp {std_inp}".format(**locals()) # internal
        # msg += "\n StandardOut {std_out}".format(**locals()) # internal
        # msg += "\n StandardErr {std_err}".format(**locals()) # internal
        inp, out, err = None, None, None
        try:
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
        except Exception as e:
            msg += "\n {std_inp}: {e}".format(**locals())
            ret = EXIT_STDIN
            return ret, msg
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
            msg += "\n {std_out}: {e}".format(**locals())
            ret = EXIT_STDOUT
        if out is None:
            msg += "\n fallback to StandardOutput=journal log"
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
            msg += "\n {std_err}: {e}".format(**locals())
            ret = EXIT_STDERR
        if err is None:
            msg += "\n fallback to StandardError=journal log"
            err = self.open_journal_log(conf)
        assert err is not None
        if msg:
            err.write("ERROR:")
            err.write(msg.strip())
            err.write("\n")
        if ExecRedirectLogs:
            os.dup2(inp.fileno(), sys.stdin.fileno())
            os.dup2(out.fileno(), sys.stdout.fileno())
            os.dup2(err.fileno(), sys.stderr.fileno())
        return ret, msg
    def execve_from(self, conf, cmd, env):
        """ this code is commonly run in a child process // returns exit-code"""
        runs = conf.get(Service, "Type", "simple").lower()
        # nameE, filename44 = strE(conf.name(), path44(conf.filename())
        # dbg_("{runs} process for {nameE} => {filename44}".format(**locals())) # internal
        retcode, msg = self.dup2_journal_log(conf)
        if retcode:
            cmdline44, retcode44 = o44(shell_cmd(cmd)), exitCODE(retcode)
            error_("({cmdline44}): bad logs ({retcode44}): {msg}".format(**locals()))
            if not ExecIgnoreErrors:
                sys.exit(retcode)
        #
        runuser = self.get_User(conf)
        rungroup = self.get_Group(conf)
        xgroups = self.get_SupplementaryGroups(conf)
        envs = shutil_setuid(runuser, rungroup, xgroups)
        badpath = self.chdir_workingdir(conf)  # some dirs need setuid before
        if badpath:
            cmdline44 = o44(shell_cmd(cmd))
            error_("({cmdline44}): bad workingdir: {badpath}'".format(**locals()))
            if not ExecIgnoreErrors:
                sys.exit(EXIT_CHDIR)
        env = self.extend_exec_env(env)
        env.update(envs)  # set $HOME to ~$USER
        try:
            if ExecSpawn:
                cmd_args = [ arg for arg in cmd ]  # satisfy mypy
                exitcode = os.spawnvpe(os.P_WAIT, cmd[0], cmd_args, env)
                sys.exit(exitcode)
            else:  # pragma: no cover
                os.execve(cmd[0], cmd, env)
                sys.exit(EXIT_CORRUPTED)  # pragma: no cover (can not be reached / bug like mypy#8401)
        except Exception as e:
            cmdline44 = o44(shell_cmd(cmd))
            error_("({cmdline44}): {e}".format(**locals()))
            sys.exit(EXIT_NOTEXECUTABLE)
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.stop_unit_from(conf)

    def get_TimeoutStopSec(self, conf):
        timeout = conf.get(Service, "TimeoutSec", strE(DefaultTimeoutStartSec))
        timeout = conf.get(Service, "TimeoutStopSec", timeout)
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def stop_unit_from(self, conf):
        if not conf: return False
        problems = self.check_syntax_from(conf)
        errors = [ problem for problem in problems if problem.startswith("E") ]
        if errors and not self._force:
            some = len(errors)
            error_("did find {some} errors, refusing to stop unit. (use --force to pass)".format(**locals()))
            return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            info_(" stop unit {unit} => {filename44}".format(**locals()))
            return self.do_stop_unit_from(conf)
    def do_stop_unit_from(self, conf):
        unit = conf.name()
        if unit.endswith(".service"):
            return self.do_stop_service_from(conf)
        elif unit.endswith(".socket"):
            return self.do_stop_socket_from(conf)
        elif unit.endswith(".target"):
            return self.do_stop_target_from(conf)
        else:
            error_("stop not implemented for unit type: {unit}".format(**locals()))
            return False
    def do_stop_service_from(self, conf):
        timeout = self.get_TimeoutStopSec(conf)
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.check_exec_from(conf, env, Service, "ExecStop")
            if not okee and _no_reload: return False
        service_directories = self.env_service_directories(conf)
        env.update(service_directories)
        returncode = 0
        service_result = "success"
        oldstatus = self.get_status_from(conf, "ActiveState", "")
        self.set_status_code_from(conf, "stopping", None)
        self.write_status_from(conf, AS="stopping", SS=None)
        if runs in [ "oneshot" ]:
            if oldstatus in ["inactive"]:
                warn_("the service is already down once")
                self.write_status_from(conf, AS=oldstatus)
                return True
            for cmd in conf.getlist(Service, "ExecStop", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("{runs} stop".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStop", run, runs+" stop", exe.check)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            if True:
                if returncode:
                    self.write_status_from(conf, AS="failed")
                else:
                    self.clean_status_from(conf)  # "inactive"
        # fallback Stop => Kill for ["simple","notify","forking"]
        elif not conf.getlist(Service, "ExecStop", []):
            info_("no ExecStop => systemctl kill")
            if True:
                self.set_status_code_from(conf, "KillSignal")  # only temporary
                self.do_kill_unit_from(conf)
                self.clean_pid_file_from(conf)
                self.clean_status_from(conf)  # "inactive"
        elif runs in [ "simple", "notify", "idle" ]:
            pid = 0
            for cmd in conf.getlist(Service, "ExecStop", []):
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("{runs} stop".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStop", run, runs+" stop", exe.check)
                run = must_have_failed(run, newcmd)  # TODO: a workaround for Ubuntu 16.04
                # self.write_status_from(conf, MainPID=run.pid) # no ExecStop
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = to_intN(env.get("MAINPID"))
            if pid:
                if self.wait_vanished_pid(pid, timeout):
                    self.clean_pid_file_from(conf)
                    self.clean_status_from(conf)  # "inactive"
                else:
                    self.write_status_from(conf, AS="failed")  # keep MainPID
            else:
                info_("{runs} sleep as no PID was found on Stop".format(**locals()))
                time.sleep(MinimumTimeoutStopSec)
                pid = self.read_mainpid_from(conf)
                if not pid or not pid_exists(pid) or pid_zombie(pid):
                    self.clean_pid_file_from(conf)
                self.clean_status_from(conf)  # "inactive"
        elif runs in [ "forking" ]:
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist(Service, "ExecStop", []):
                # active = self.is_active_from(conf)
                if pid_file:
                    new_pid = self.read_mainpid_from(conf)
                    if new_pid:
                        env["MAINPID"] = strE(new_pid)
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("fork stop", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStop", run, runs+" stop", exe.check)
                if run.returncode and exe.check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = to_intN(env.get("MAINPID"))
            if pid:
                if self.wait_vanished_pid(pid, timeout):
                    self.clean_pid_file_from(conf)
                else:
                    self.write_status_from(conf, AS="failed")  # keep MainPID
            else:
                info_("{runs} sleep as no PID was found on Stop".format(**locals()))
                time.sleep(MinimumTimeoutStopSec)
                pid = self.read_mainpid_from(conf)
                if not pid or not pid_exists(pid) or pid_zombie(pid):
                    self.clean_pid_file_from(conf)
            if returncode:
                self.write_status_from(conf, AS="failed")  # keep MainPID
            else:
                self.clean_status_from(conf)  # "inactive"
        else:
            error_("  unsupported run type '{runs}' (not implemented)".format(**locals()))
            self.clean_status_from(conf)  # "inactive"
            return False
        # POST sequence
        if not self.is_active_from(conf):
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Service, "ExecStopPost", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("post-stop", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStopPost", run, "post-stop")
        if _what_kind not in ["none", "keep"]:
            self.remove_service_directories(conf)
        return service_result == "success"
    def do_stop_socket_from(self, conf):
        runs = "socket"
        timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool(Socket, "Accept", "no")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None:
            dbg_("unit could not be loaded ({service_unit})".format(**locals()))
            error_("Unit {service_unit} not found.".format(**locals()))
            return False
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.check_exec_from(conf, env, Socket, "ExecStop")
            if not okee and _no_reload: return False
        self.set_status_code_from(conf, "stopping", None)
        if not accept:
            # we do not listen but have the service started right away
            done = self.do_stop_service_from(service_conf)
            service_result = done and "success" or "failed"
            status_result = done and "stopped" or "failed"
        else:
            done = self.do_stop_service_from(service_conf)
            service_result = done and "success" or "failed"
            status_result = done and "stopped" or "failed"
        self.set_status_code_from(conf, service_result, None)
        # service_directories = self.env_service_directories(conf)
        # env.update(service_directories)
        # POST sequence
        if not self.is_active_from(conf):
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist(Socket, "ExecStopPost", []):
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("post-stop", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecStop", run, "post-stop")
        if service_result in ["failed"]:
            self.write_status_from(conf, AS="failed")
        else:
            self.clean_status_from(conf)  # "inactive"
        return service_result == "success"
    def wait_vanished_pid(self, pid, timeout):
        if not pid:
            return True
        info_("wait for PID {pid} to vanish ({timeout}s)".format(**locals()))
        for x in xrange(int(timeout)):
            if not self.is_active_pid(pid):
                info_("wait for PID {pid} is done ({x}.)".format(**locals()))
                return True
            time.sleep(1)  # until TimeoutStopSec
        info_("wait for PID {pid} failed ({x}.)".format(**locals()))
        return False
    def reload_modules(self, *modules):
        """ [UNIT]... -- reload these units """
        self.wait_system()
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.reload_unit_from(conf)
    def reload_unit_from(self, conf):
        if not conf: return False
        problems = self.check_syntax_from(conf)
        errors = [ problem for problem in problems if problem.startswith("E") ]
        if errors and not self._force:
            some = len(errors)
            error_("did find {some} errors, refusing to reload unit. (use --force to pass)".format(**locals()))
            return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            info_(" reload unit {unit} => {filename44}".format(**locals()))
            return self.do_reload_unit_from(conf)
    def do_reload_unit_from(self, conf):
        unit = conf.name()
        if unit.endswith(".service"):
            return self.do_reload_service_from(conf)
        elif unit.endswith(".socket"):
            service_unit = self.get_socket_service_from(conf)
            service_conf = self.load_unit_conf(service_unit)
            if service_conf:
                return self.do_reload_service_from(service_conf)
            else:
                error_("no {service_unit} found for unit type: {unit}".format(**locals()))
                return False
        elif unit.endswith(".target"):
            return self.do_reload_target_from(conf)
        else:
            error_("reload not implemented for unit type: {unit}".format(**locals()))
            return False
    def do_reload_service_from(self, conf):
        runs = conf.get(Service, "Type", "simple").lower()
        env = self.get_env(conf)
        if not self._quiet:
            okee = self.check_exec_from(conf, env, Service, "ExecReload")
            if not okee and _no_reload: return False
        self.set_status_code_from(conf, "reloading", None)
        #
        initscript = conf.filename()
        if initscript and self.is_sysv_file(initscript):
            for cmd in [initscript]:
                newcmd = [initscript, "reload"]
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                info_("{runs} reload".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "initscript", run)
                if run.returncode:
                    self.write_status_from(conf, AS="failed", SS="initscript")
                    return False
                else:
                    self.write_status_from(conf, AS="active", SS="initscript")
                    return True
        service_directories = self.env_service_directories(conf)
        env.update(service_directories)
        if runs in [ "simple", "notify", "forking", "idle" ]:
            unit = conf.name()
            if not self.is_active_from(conf):
                info_("no reload on inactive service {unit}".format(**locals()))
                return True
            oldstatus = self.get_status_from(conf, "ActiveState", None)
            self.write_status_from(conf, AS="reloading", SS=None)
            for cmd in conf.getlist(Service, "ExecReload", []):
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
                exe, newcmd = self.exec_newcmd(cmd, env, conf)
                info_("{runs} reload".format(**locals()), shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env)  # pragma: no cover
                run = subprocess_waitpid(forkpid)
                self.set_status_code_from(conf, "ExecReload", run, "reload", exe.check)
                if run.returncode and exe.check:
                    returncodeOK = exitOK(run.returncode)
                    self.write_status_from(conf, AS="failed")
                    return False
            time.sleep(MinimumYield)
            self.write_status_from(conf, AS=oldstatus)
            return True
        elif runs in [ "oneshot" ]:
            dbg_("ignored run type '{runs}' for reload".format(**locals()))
            return True
        else:
            error_("  unsupported run type '{runs}' (not implemented)".format(**locals()))
            self.clean_status_from(conf)  # "inactive"
            return False
    def restart_modules(self, *modules):
        """ [UNIT]... -- restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.restart_unit_from(conf)
    def restart_unit_from(self, conf):
        if not conf: return False
        problems = self.check_syntax_from(conf)
        errors = [ problem for problem in problems if problem.startswith("E") ]
        if errors and not self._force:
            some = len(errors)
            error_("did find {some} errors, refusing to restart unit. (use --force to pass)".format(**locals()))
            return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            if unit.endswith(".service"):
                info_(" restart service {unit} => {filename44}".format(**locals()))
                if not self.is_active_from(conf):
                    return self.do_start_unit_from(conf)
                else:
                    return self.do_restart_unit_from(conf)
            else:
                return self.do_restart_unit_from(conf)
    def do_restart_unit_from(self, conf):
        unit = conf.name()
        info_("(restart) => stop/start {unit}".format(**locals()))
        self.do_stop_unit_from(conf)
        return self.do_start_unit_from(conf)
    def try_restart_modules(self, *modules):
        """ [UNIT]... -- try-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.try_restart_unit_from(conf)
    def try_restart_unit_from(self, conf):
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            info_(" try-restart unit {unit} => {filename44}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.reload_or_restart_unit_from(conf)
    def reload_or_restart_unit_from(self, conf):
        """ do 'reload' if specified, otherwise do 'restart' """
        if not conf: return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            info_(" reload-or-restart unit {unit} => {filename44}".format(**locals()))
            return self.do_reload_or_restart_unit_from(conf)
    def do_reload_or_restart_unit_from(self, conf):
        if not self.is_active_from(conf):
            # try: self.stop_unit_from(conf)
            # except Exception as e: pass
            return self.do_start_unit_from(conf)
        elif conf.getlist(Service, "ExecReload", []):
            info_("found service to have ExecReload -> 'reload'")
            return self.do_reload_unit_from(conf)
        else:
            info_("found service without ExecReload -> 'restart'")
            return self.do_restart_unit_from(conf)
    def reload_or_try_restart_modules(self, *modules):
        """ [UNIT]... -- reload-or-try-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.reload_or_try_restart_unit_from(conf)
    def reload_or_try_restart_unit_from(self, conf):
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            info_(" reload-or-try-restart unit {unit} => {filename44}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.kill_unit_from(conf)
    def kill_unit_from(self, conf):
        if not conf: return False
        with waitlock(conf):
            unit, filename44 = conf.name(), path44(conf.filename())
            info_(" kill unit {unit} => {filename44}".format(**locals()))
            return self.do_kill_unit_from(conf)
    def do_kill_unit_from(self, conf):
        started = time.time()
        doSendSIGKILL = self.get_SendSIGKILL(conf)
        doSendSIGHUP = self.get_SendSIGHUP(conf)
        useKillMode = self.get_KillMode(conf)
        useKillSignal = self.get_KillSignal(conf)
        kill_signal = getattr(signal, useKillSignal)
        timeout = self.get_TimeoutStopSec(conf)
        if DebugStatusFile:  # pragma: no cover
            status_file = self.get_status_file_from(conf)
            size = os.path.exists(status_file) and os.path.getsize(status_file)
            info_("STATUS {status_file} {size}".format(**locals()))
        mainpid = self.read_mainpid_from(conf)
        self.clean_status_from(conf)  # clear RemainAfterExit and TimeoutStartSec
        if not mainpid:
            filename44 = path44(conf.filename())
            if useKillMode in ["control-group"]:
                warn_("no main PID {filename44}".format(**locals()))
                warn_("and there is no control-group here")
            else:
                info_("no main PID {filename44}".format(**locals()))
            return False
        if not pid_exists(mainpid) or pid_zombie(mainpid):
            dbg_("ignoring children when mainpid is already dead")
            # because we list child processes, not processes in control-group
            return True
        pidlist = self.kill_children_pidlist_of(mainpid)  # here
        if pid_exists(mainpid):
            info_("stop kill PID {mainpid}".format(**locals()))
            self._kill_pid(mainpid, kill_signal)
        if useKillMode in ["control-group"]:
            if len(pidlist) > 1:
                info_("stop control-group PIDs {pidlist}".format(**locals()))
            for pid in pidlist:
                if pid != mainpid:
                    self._kill_pid(pid, kill_signal)
        if doSendSIGHUP:
            info_("stop SendSIGHUP to PIDs {pidlist}".format(**locals()))
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
                info_("service PIDs not stopped after {timeout}".format(**locals()))
                break
            time.sleep(1)  # until TimeoutStopSec
        if dead or not doSendSIGKILL:
            deadOK = boolOK(dead)
            info_("done kill PID {mainpid} {deadOK}".format(**locals()))
            return dead
        if useKillMode in [ "control-group", "mixed" ]:
            info_("hard kill PIDs {pidlist}".format(**locals()))
            for pid in pidlist:
                if pid != mainpid:
                    self._kill_pid(pid, signal.SIGKILL)
            time.sleep(MinimumYield)
        # useKillMode in [ "control-group", "mixed", "process" ]
        if pid_exists(mainpid):
            info_("hard kill PID {mainpid}".format(**locals()))
            self._kill_pid(mainpid, signal.SIGKILL)
            time.sleep(MinimumYield)
        dead = not pid_exists(mainpid) or pid_zombie(mainpid)
        deadOK = boolOK(dead)
        info_("done hard kill PID {mainpid} {deadOK}".format(**locals()))
        return dead
    def _kill_pid(self, pid, kill_signal=None):
        try:
            sig = kill_signal or signal.SIGTERM
            os.kill(pid, sig)
        except OSError as e:
            if e.errno == errno.ESRCH or e.errno == errno.ENOENT:
                dbg_("kill PID {pid} => No such process".format(**locals()))
                return True
            else:
                error_("kill PID {pid} => {e}".format(**locals()))
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
        units = []
        results = []
        for module in modules:
            units = self.match_units(to_list(module))
            if not units:
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                self.error |= NOT_ACTIVE
                results += [ "inactive" ]
                continue
            for unit in units:
                active = self.get_active_unit(unit)
                enabled = self.enabled_unit(unit)
                results += [ active ]
                break
        # how it should work:
        status = "active" in results
        # how 'systemctl' works:
        non_active = [ result for result in results if result != "active" ]
        if non_active:
            self.error |= NOT_ACTIVE
        if non_active:
            self.error |= NOT_OK  # status
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
            return pid  # usually a string (not null)
        return None
    def get_active_unit(self, unit):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        conf = self.load_unit_conf(unit)
        if not conf:
            warn_("Unit {unit} not found.".format(**locals()))
            return "unknown"
        else:
            return self.get_active_from(conf)
    def get_active_from(self, conf):
        unit = conf.name()
        if unit.endswith(".service"):
            return self.get_active_service_from(conf)
        elif unit.endswith(".socket"):
            service_unit = self.get_socket_service_from(conf)
            service_conf = self.load_unit_conf(service_unit)
            return self.get_active_service_from(service_conf)
        elif unit.endswith(".target"):
            return self.get_active_target_from(conf)
        else:
            debug_("is-active not implemented for unit type: {unit}".format(**locals()))
            return "unknown"  # TODO: "inactive" ?
    def get_active_service_from(self, conf):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        # used in try-restart/other commands to check if needed.
        if not conf: return "unknown"
        pid_file = self.pid_file_from(conf)
        if pid_file:  # application PIDFile
            if not os.path.exists(pid_file):
                if DebugStatusFile:  # pragma: no cover
                    unit = conf.name()
                    debug_("[{unit}] get from pid file: (does not exist) => inactive".format(**locals()))
                return "inactive"
        status_file = self.get_status_file_from(conf)
        if path_getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if DebugStatusFile:  # pragma: no cover
                    unit = conf.name()
                    info_("[{unit}] state from status file: written => {state}".format(**locals()))
                return state
        pid = self.read_mainpid_from(conf)
        result = "inactive"
        if pid:
            result = "active"
            if not pid_exists(pid) or pid_zombie(pid):
                result = "failed"
        if DebugStatusFile:  # pragma: no cover
            if pid_file:
                unit = conf.name()
                debug_("[{unit}] pid from pid file: PID {pid} => {result}".format(**locals()))
            else:  # status file
                unit = conf.name()
                debug_("[{unit}] pid from status file: PID {pid} => {result}".format(**locals()))
        return result
    def get_active_target_from(self, conf):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        return self.get_active_target(conf.name())
    def get_active_target(self, target):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        if target in self.get_active_target_list():
            status = self.is_system_running()
            if status in [ "running" ]:
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
        target_list += [ DefaultUnit ]  # upper end
        target_list += [ SysInitTarget ]  # lower end
        return target_list
    def get_substate_from(self, conf):
        """ returns 'running' 'exited' 'dead' 'failed' 'plugged' 'mounted' """
        if not conf: return None
        pid_file = self.pid_file_from(conf)
        if pid_file:
            if not os.path.exists(pid_file):
                return "dead"
        status_file = self.get_status_file_from(conf)
        if path_getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if state in [ "active" ]:
                    return self.get_status_from(conf, "SubState", "running")
                else:
                    return self.get_status_from(conf, "SubState", "dead")
        pid = self.read_mainpid_from(conf)
        if DebugStatusFile:  # pragma: no cover
            filename44 = path44(pid_file or status_file)
            debug_("pid_file {filename44} => PID {pid}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                results += [ "inactive" ]
                continue
            for unit in units:
                active = self.get_active_unit(unit)
                enabled = self.enabled_unit(unit)
                results += [ active ]
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                return False
            for unit in units:
                if not self.reset_failed_unit(unit):
                    error_("Unit {unit} could not be reset.".format(**locals()))
                    status = False
                break
        return status
    def reset_failed_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if not conf:
            warn_("Unit {unit} not found.".format(**locals()))
            return False
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.reset_failed_from(conf)
    def reset_failed_from(self, conf):
        if conf is None: return True
        if not self.is_failed_from(conf): return False
        with waitlock(conf):
            return self.do_reset_failed_from(conf)
    def do_reset_failed_from(self, conf):
        done = False
        pid_file = self.pid_file_from(conf)
        if pid_file and os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                done = True
                dbg_("done rm {pid_file}".format(**locals()))
            except Exception as e:
                error_("while rm {pid_file}: {e}".format(**locals()))
        # clean_status will truncate/remove the status file on end of waitlock
        conf.clean_status()
        if conf.write_status():
            done = True
        return done
    def status_modules(self, *modules):
        """ [UNIT]... check the status of these units.
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
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
            self.error |= NOT_OK | NOT_ACTIVE  # 3
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
        execstate = ""
        for varname in ["ExecMainPID", "ExecMainCode", "ExecMainStatus", "ExecLastPID", "ExecLastCode", "ExecLastStatus", "ExecLastStep"]:
            try:
                returncode = self.get_status_from(conf, varname, "")
                if returncode:
                    returncodeOK = exitOK(int(returncode))
                    execstate = " {varname}={returncodeOK}".format(**locals())
            except Exception as e: pass
        result += "\n    Active: {active} ({substate})".format(**locals())
        last_step = self.get_status_from(conf, "ExecLastStep", "")
        if last_step:
            inprocess = "  Process"
            if not last_step.startswith("Exec"):
                inprocess = "Last Step"
            last_code = self.get_status_from(conf, "ExecLastCode", "")
            last_pid = self.get_status_from(conf, "ExecLastPID", "")
            last_state = exitCODE(to_int(self.get_status_from(conf, "ExecMainStatus", "0")))
            if last_code in ["0", ""]: last_code = "running"
            show_pid = "PID {last_pid:6s}".format(**locals())
            if not last_pid: show_pid = "          "
            result += "\n {inprocess}: {show_pid} ({last_state}) [{last_step}] {last_code}".format(**locals())
        main_step = self.get_status_from(conf, "ExecMainStep", "")
        if main_step:
            inprocess = "  Process"
            main_code = self.get_status_from(conf, "ExecMainCode", "")
            main_pid = self.get_status_from(conf, "ExecMainPID", "")
            main_state = exitCODE(to_int(self.get_status_from(conf, "ExecMainStatus", "0")))
            if main_code in ["0", ""]: main_code = "running"
            show_pid = "PID {main_pid:6s}".format(**locals())
            if not main_pid: show_pid = "          "
            result += "\n {inprocess}: {show_pid} ({main_state}) [{main_step}] {main_code}".format(**locals())
        if active in ["active", "starting", "stopping", "reloading"]:
            pid = self.read_mainpid_from(conf)
            if pid:
                result += "\n  Main PID: {pid}".format(**locals())
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
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
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
            error_("No files found for {unit}".format(**locals()))
        except Exception as e:
            error_("Unit {unit} is not-loaded: {e}".format(**locals()))
        self.error |= NOT_OK
        return None
    ##
    ##
    def load_preset_files(self, module=None):  # -> [ preset-file-names,... ]
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
            found = len(self._preset_file_list)
            debug_("found {found} preset files".format(**locals()))
        return sorted(self._preset_file_list.keys())
    def get_preset(self, unit, default=None):
        """ [UNIT] check the *.preset of this unit (experimental)
        """
        self.load_preset_files()
        assert self._preset_file_list is not None
        for filename in sorted(self._preset_file_list.keys()):
            preset = self._preset_file_list[filename]
            status = preset.get_preset(unit, nodefault=True)
            if status:
                return status
        return default
    def get_preset_of_unit(self, unit, default=None):
        """ [UNIT] check the *.preset of this unit (experimental)
        """
        status = self.get_preset(unit)
        if status is not None:
            return status
        logg.info("Unit {unit} not found in preset files (defaults to disable)".format(**locals()))
        self.error |= NOT_FOUND
        return default
    def preset_modules(self, *modules):
        """ [UNIT]... -- set 'enabled' when in *.preset
        """
        if self.user_mode():
            warn_("preset makes no sense in --user mode")
            return True
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.preset_units(units) and found_all
    def preset_units(self, units):
        """ fails if any unit could not be changed """
        self.wait_system()
        fails = 0
        found = 0
        for unit in units:
            status = self.get_preset(unit)
            if not status: continue
            found += 1
            if status.startswith("enable"):
                if self._preset_mode == "disable": continue
                info_("preset enable {unit}".format(**locals()))
                if not self.enable_unit(unit):
                    warn_("failed to enable {unit}".format(**locals()))
                    fails += 1
            if status.startswith("disable"):
                if self._preset_mode == "enable": continue
                info_("preset disable {unit}".format(**locals()))
                if not self.disable_unit(unit):
                    warn_("failed to disable {unit}".format(**locals()))
                    fails += 1
        return not fails and not not found
    def preset_all_modules(self, *modules):
        """ 'preset' all services
        enable or disable services according to *.preset files
        """
        if self.user_mode():
            warn_("preset-all makes no sense in --user mode")
            return True
        found_all = True
        units = self.match_units()  # TODO: how to handle module arguments
        return self.preset_units(units) and found_all
    def wanted_from(self, conf, default=None):
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
    def default_enablefolder(self, wanted, basefolder=None):
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        unit_file = conf.filename()
        if unit_file is None:
            error_("Unit file {unit} not found.".format(**locals()))
            return False
        if self.is_sysv_file(unit_file):
            if self.user_mode():
                error_("Initscript {unit} not for --user mode".format(**locals()))
                return False
            return self.enable_unit_sysv(unit_file)
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.enable_unit_from(conf)
    def enable_unit_from(self, conf):
        unit = conf.name()
        wanted = self.wanted_from(conf)
        if not wanted and not self._force:
            dbg_("{unit} has no target".format(**locals()))
            return False  # "static" is-enabled
        target = wanted or self.get_default_target()
        folder = self.enablefolder(target)
        if self._root:
            folder = os_path(self._root, folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        source = conf.filename()
        if not source:  # pragma: no cover (was checked before)
            dbg_("{unit} has no real file".format(**locals()))
            return False
        symlink = os.path.join(folder, unit)
        if True:
            _f = self._force and "-f" or ""
            source44 = path44(source)
            info_("ln -s {_f} '{source44}' '{symlink}'".format(**locals()))
        try:
            if self._force and os.path.exists(symlink):
                os.remove(symlink)
            if os.path.islink(symlink):
                os.remove(symlink)
            os.symlink(source, symlink)
        except Exception as e:
            error_("Failed to enable unit: File {symlink}: {e}".format(**locals()))
            return False
        return True
    def rc3_root_folder(self):
        old_folder = os_path(self._root, _rc3_boot_folder)
        new_folder = os_path(self._root, _rc3_init_folder)
        if os.path.isdir(old_folder):  # pragma: no cover
            return old_folder
        return new_folder
    def rc5_root_folder(self):
        old_folder = os_path(self._root, _rc5_boot_folder)
        new_folder = os_path(self._root, _rc5_init_folder)
        if os.path.isdir(old_folder):  # pragma: no cover
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
        return self.disable_units(units) and found_all
    def disable_units(self, units):
        self.wait_system()
        done = True
        for unit in units:
            if not self.disable_unit(unit):
                done = False
        return done
    def disable_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            error_("Unit {unit} not found.".format(**locals()))
            return False
        unit_file = conf.filename()
        if unit_file is None:
            error_("Unit file {unit} not found.".format(**locals()))
            return False
        if self.is_sysv_file(unit_file):
            if self.user_mode():
                error_("Initscript {unit} not for --user mode".format(**locals()))
                return False
            return self.disable_unit_sysv(unit_file)
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        return self.disable_unit_from(conf)
    def disable_unit_from(self, conf):
        wanted = self.wanted_from(conf)
        if not wanted and not self._force:
            unit = conf.name()
            dbg_("{unit} has no target".format(**locals()))
            return False  # "static" is-enabled
        target = wanted or self.get_default_target()
        for folder in self.enablefolders(target):
            if self._root:
                folder = os_path(self._root, folder)
            symlink = os.path.join(folder, conf.name())
            if os.path.exists(symlink):
                try:
                    _f = self._force and "-f" or ""
                    info_("rm {_f} '{symlink}'".format(**locals()))
                    if os.path.islink(symlink) or self._force:
                        os.remove(symlink)
                except IOError as e:
                    error_("disable {symlink}: {e}".format(**locals()))
                except OSError as e:
                    error_("disable {symlink}: {e}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.is_enabled_units(units)  # and found_all
    def is_enabled_units(self, units):
        """ true if any is enabled, and a list of infos """
        result = False
        infos = []
        for unit in units:
            infos += [ self.enabled_unit(unit) ]
            if self.is_enabled(unit):
                result = True
        if not result:
            self.error |= NOT_OK
        return infos
    def is_enabled(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            error_("Unit {unit} not found.".format(**locals()))
            return False
        unit_file = conf.filename()
        if not unit_file:
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.is_sysv_file(unit_file):
            return self.is_enabled_sysv(unit_file)
        state = self.get_enabled_from(conf)
        if state in ["enabled", "static"]:
            return True
        return False  # ["disabled", "masked"]
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.is_sysv_file(unit_file):
            error_("Initscript {unit} can not be masked".format(**locals()))
            return False
        conf = self.get_unit_conf(unit)
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
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
            dbg_("ln -s {_f} {dev_null} '{target}'".format(**locals()))
        if self._force and os.path.islink(target):
            os.remove(target)
        if not os.path.exists(target):
            os.symlink(dev_null, target)
            info_("Created symlink {target} -> {dev_null}".format(**locals()))
            return True
        elif os.path.islink(target):
            dbg_("mask symlink does already exist: {target}".format(**locals()))
            return True
        else:
            error_("mask target does already exist: {target}".format(**locals()))
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
                unit_ = unit_of(module)
                error_("Unit {unit_} not found.".format(**locals()))
                self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
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
            error_("Unit {unit} not found.".format(**locals()))
            return False
        if self.is_sysv_file(unit_file):
            error_("Initscript {unit} can not be un/masked".format(**locals()))
            return False
        conf = self.get_unit_conf(unit)
        if self.not_user_conf(conf):
            error_("Unit {unit} not for --user mode".format(**locals()))
            return False
        folder = self.mask_folder()
        if self._root:
            folder = os_path(self._root, folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        if True:
            _f = self._force and "-f" or ""
            info_("rm {_f} '{target}'".format(**locals()))
        if os.path.islink(target):
            os.remove(target)
            return True
        elif not os.path.exists(target):
            dbg_("Symlink did not exist anymore: {target}".format(**locals()))
            return True
        else:
            warn_("target is not a symlink: {target}".format(**locals()))
            return True

    def list_start_dependencies_modules(self, *modules):
        """ [UNIT]... show the dependency tree (experimental)"
        """
        # for future usage
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.list_start_dependencies_units(units)
    def list_dependencies_modules(self, *modules):
        """ [UNIT]... show the dependency tree"
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.list_dependencies_units(units)  # and found_all
    def list_dependencies_units(self, units):
        result = []
        for unit in units:
            if result:
                result += [ "", "" ]
            result += self.list_dependencies_unit(unit)
        return result
    def list_dependencies_unit(self, unit):
        result = []
        for line in self.list_dependencies(unit, ""):
            result += [ line ]
        return result
    def list_dependencies(self, unit, indent=None, mark=None, loop=[]):
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
            yield "{indent}({unit}): {mark}".format(**locals())
        else:
            yield "{indent}{unit}: {mark}".format(**locals())
            for stop_recursion in [ "Conflict", "conflict", "reloaded", "Propagate" ]:
                if stop_recursion in mark:
                    return
            for dep in deps:
                if dep in loop:
                    dbg_("detected loop at {dep}".format(**locals()))
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
    def get_dependencies_unit(self, unit, styles=None):
        """ scans both systemd folders and unit conf for dependency relations """
        styles = styles or [ "Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                             ".requires", ".wants", "PropagateReloadTo", "Conflicts", ]
        conf = self.get_unit_conf(unit)
        deps = {}
        for style in styles:
            if style.startswith("."):
                deps.update(self.get_wants_unit(unit, [ style ]))
            else:
                deps.update(self.get_deps_unit(unit, [ style ]))
        return deps
    def get_wants_unit(self, unit, styles=None):
        """ scans the systemd folders for unit.service.wants subfolders """
        styles = styles or [ ".requires", ".wants" ]
        deps = {}
        for style in styles:
            if not style.startswith("."): continue
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
        return deps
    def get_deps_unit(self, unit, styles=None):
        """ scans the unit conf for Requires= or Wants= settings - can use the cache file """
        if self._deps_modules:
            if unit in self._deps_modules:
                return self._deps_modules[unit]
        dbg_("scanning Unit {unit} for Requuires".format(**locals()))
        conf = self.get_unit_conf(unit)
        return self.get_deps_from(conf, styles)
    def get_deps_from(self, conf, styles=None):
        """ scans the unit conf for Requires= or Wants= settings in the [Unit] section """
        # shall not use the cache file as it is called from cache creation in daemon-reload
        deps = {}
        styles = styles or [ "Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                             "PropagateReloadTo", "Conflicts", ]
        for style in styles:
            if style.startswith("."): continue
            for requirelist in conf.getlist(Unit, style, []):
                for required in requirelist.strip().split(" "):
                    deps[required.strip()] = style
        return deps
    def get_required_dependencies(self, unit, styles=None):
        styles = styles or [ "Requires", "Wants", "Requisite", "BindsTo",
                             ".requires", ".wants"  ]
        return self.get_dependencies_unit(unit, styles)
    def get_start_dependencies(self, unit, styles=None):  # pragma: no cover
        """ the list of services to be started as well / TODO: unused """
        styles = styles or ["Requires", "Wants", "Requisite", "BindsTo", "PartOf", "ConsistsOf",
                            ".requires", ".wants"]
        deps = {}
        unit_deps = self.get_dependencies_unit(unit)
        for dep_unit, dep_style in unit_deps.items():
            if dep_style in styles:
                if dep_unit in deps:
                    if dep_style not in deps[dep_unit]:
                        deps[dep_unit].append( dep_style)
                else:
                    deps[dep_unit] = [ dep_style ]
                next_deps = self.get_start_dependencies(dep_unit)
                for dep, styles in next_deps.items():
                    for style in styles:
                        if dep in deps:
                            if style not in deps[dep]:
                                deps[dep].append(style)
                        else:
                            deps[dep] = [ style ]
        return deps
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
                            deps[dep_unit].append( dep_style)
                    else:
                        deps[dep_unit] = [ dep_style ]
        deps_conf = []
        for dep in deps:
            if dep in unit_order:
                continue
            conf = self.get_unit_conf(dep)
            if conf.loaded():
                deps_conf.append(conf)
        for unit in unit_order:
            deps[unit] = [ "Requested" ]
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
        conflist = [ self.get_unit_conf(unit) for unit in unitlist ]
        if True:
            conflist = []
            for unit in unitlist:
                conf = self.get_unit_conf(unit)
                if conf.masked:
                    dbg_("ignoring masked unit {unit}".format(**locals()))
                    continue
                conflist.append(conf)
        sortlist = conf_sortedAfter(conflist)
        return [ item.name() for item in sortlist ]
    def sortedBefore(self, unitlist):
        """ get correct start order for the unit list (ignoring masked units) """
        conflist = [ self.get_unit_conf(unit) for unit in unitlist ]
        if True:
            conflist = []
            for unit in unitlist:
                conf = self.get_unit_conf(unit)
                if conf.masked:
                    dbg_("ignoring masked unit {unit}".format(**locals()))
                    continue
                conflist.append(conf)
        sortlist = conf_sortedAfter(reversed(conflist))
        return [ item.name() for item in reversed(sortlist) ]
    def daemon_reload_target(self):
        """ reload does will only check the service files here.
            The returncode will tell the number of warnings,
            and it is over 100 if it can not continue even
            for the relaxed systemctl.py style of execution. """
        problems = []
        aliases = {}
        unit_deps = {}
        sysinit_deps = {}
        for unit in self.match_units():
            try:
                conf = self.get_unit_conf(unit)
            except Exception as e:
                filename44 = path44(conf.filename())
                error_("{unit}: can not read unit file {filename44}\n\t{e}".format(**locals()))
                continue
            problems = self.check_syntax_from(conf)
            if CacheAlias:
                aliases.update(self.get_alias_from(conf))
            if CacheDeps:
                found = self.get_deps_from(conf)
                if found:
                    unit_deps[unit] = found
        if CacheDeps:
            sysinit_deps = self.get_sysinit_deps(SysInitTarget)
        if sysinit_deps:
            some_sysinit = len(sysinit_deps) - 1  # do not count sysinit.target itself
            info_(" found {some_sysinit} sysinit.target deps".format(**locals()))
            self.write_sysinit_cache(sysinit_deps)
        if unit_deps:
            some_unit = len(unit_deps)
            info_(" found {some_unit} dependencies for units".format(**locals()))
            self.write_deps_cache(unit_deps)
        if aliases:
            some_given = len(aliases)
            info_(" found {some_given} alias units".format(**locals()))
            self.write_alias_cache(aliases)
        if problems:
            errors = [ problem for problem in problems if problem.startswith("E") ]
            if errors:
                some = len(errors)
                more = len(problems)
                error_("* found {some} errors in {more} problems in unit definitions. (use -vvvv to see more)".format(**locals()))
            else:
                some = len(problems)
                info_(" * found {some} problems in unit definitions. (may be ignored - use -vvvv to see more)".format(**locals()))
        return True  # errors
    def get_alias_from(self, conf):
        result = {}
        for defs in conf.getlist("Install", "Alias"):
            for unit_def in defs.split(" "):
                unit = unit_def.strip()
                if not unit: continue
                name = conf.name()
                result[unit] = name
        return result
    def write_alias_cache(self, aliases):
        filename = os_path(self._root, self.expand_path(CacheAliasFile))
        try:
            with open(filename, "w") as f:
                for unit in sorted(aliases):
                    name = aliases[unit]
                    f.write("{unit} {name}\n".format(**locals()))
            debug_("written aliases to {filename}".format(**locals()))
            return True
        except Exception as e:
            warning_("while writing {filename}: {e}".format(**locals()))
        return False
    def read_alias_cache(self):
        filename = os_path(self._root, self.expand_path(CacheAliasFile))
        if os.path.exists(filename):
            try:
                result = {}
                text = open(filename).read()
                for line in text.splitlines():
                    if line.startswith("#"): continue
                    unit, name = line.split(" ", 1)
                    result[unit] = name
                return result
            except Exception as e:
                warning_("while reading {filename}: {e}".format(**locals()))
        return None
    def load_alias_cache(self):
        if self._alias_modules is None:
            self._alias_modules = self.read_alias_cache()
    def write_deps_cache(self, deps):
        filename = os_path(self._root, self.expand_path(CacheDepsFile))
        try:
            with open(filename, "w") as f:
                for unit in sorted(deps):
                    sets = deps[unit]
                    for name in sorted(sets):
                        requires = sets[name]
                        f.write("{unit} {requires} {name}\n".format(**locals()))
            debug_("written unit deps to {filename}".format(**locals()))
            return True
        except Exception as e:
            warning_("while writing {filename}: {e}".format(**locals()))
        return False
    def read_deps_cache(self):
        filename = os_path(self._root, self.expand_path(CacheDepsFile))
        if os.path.exists(filename):
            try:
                result = {}
                text = open(filename).read()
                for line in text.splitlines():
                    if line.startswith("#"): continue
                    unit, requires, name = line.split(" ", 2)
                    if unit not in result:
                        result[unit] = {}
                    result[unit][name] = requires
                return result
            except Exception as e:
                warning_("while reading {filename}: {e}".format(**locals()))
        return None
    def load_deps_cache(self):
        if self._deps_modules is None:
            self._deps_modules = self.read_deps_cache()
    def get_sysinit_deps(self, unit):
        result = {}
        deps = self.get_wants_unit(unit)
        result[unit] = deps
        newresults = {}
        for depth in xrange(DepsMaxDepth):
            newresults = {}
            for name, deps in result.items():
                for dep in deps:
                    units = self.get_wants_unit(dep)
                    if dep not in result:
                        newresults[dep] = units
                    # dbg_("wants for {dep} -> {units}".format(**locals())) # internal
            if not newresults:
                break
            result.update(newresults)
        result_units = list(result)
        dbg_("found sysinit deps = {result_units} # after {depth} rounds".format(**locals()))
        if len(result) == 1:
            if not result[unit]:
                return {}
        return result
    def write_sysinit_cache(self, deps):
        filename = os_path(self._root, self.expand_path(CacheSysinitFile))
        try:
            with open(filename, "w") as f:
                for unit in sorted(deps):
                    sets = deps[unit]
                    for name in sorted(sets):
                        requires = sets[name]
                        f.write("{unit} {requires} {name}\n".format(**locals()))
                    if not sets:
                        f.write("{unit} .required\n".format(**locals()))
            debug_("written sysinit deps to {filename}".format(**locals()))
            return True
        except Exception as e:
            warning_("while writing {filename}: {e}".format(**locals()))
        return False
    def read_sysinit_cache(self):
        filename = os_path(self._root, self.expand_path(CacheSysinitFile))
        if os.path.exists(filename):
            try:
                result = {}
                text = open(filename).read()
                for line in text.splitlines():
                    if line.startswith("#"): continue
                    unit, requires, name = line.split(" ", 2)
                    if unit not in result:
                        result[unit] = {}
                    result[unit][name] = requires
                return result
            except Exception as e:
                warning_("while reading {filename}: {e}".format(**locals()))
        return None
    def load_sysinit_cache(self):
        if self._sysinit_modules is None:
            self._sysinit_modules = self.read_sysinit_cache()
    def load_sysinit_modules(self, unit=None):
        unit = unit or SysInitTarget
        if self._sysinit_modules is None:
            self._sysinit_modules = self.get_sysinit_deps(unit)
    def check_syntax_from(self, conf):
        filename = conf.filename()
        warnings = []
        if filename and filename.endswith(".service"):
            warnings += self.check_service_syntax(conf, Service)
        if filename and filename.endswith(".socket"):
            warnings += self.check_socket_syntax(conf, Socket)
        badwarnings = []
        for problem in warnings:
            for ignore in IgnoreSyntaxWarnings.split(","):
                if ignore and problem.startswith(ignore):
                    continue
            for ignore in IgnoreWarnings.split(","):
                if ignore and problem.startswith(ignore):
                    continue
            badwarnings.append(problem)
        return badwarnings
    def check_socket_syntax(self, conf, section=Service):
        unit = conf.name()
        if not conf.data.has_section(section):
            definition = section.lower()
            error_("  {unit}: found a .{definition} file without a [{section}] section".format(**locals()))
            debug_("  {unit}:  (E01) which does render the unit definition pretty useless".format(**locals()))
            return ["E01"]
        warnings = []
        warnings += self.check_exec_unknown_settings(conf, section)
        warnings += self.check_environment_file_settings(conf, section)
        return warnings
    def check_service_syntax(self, conf, section=Service):
        unit = conf.name()
        if not conf.data.has_section(section):
            definition = section.lower()
            error_("  {unit}: found a .{definition} file without a [{section}] section".format(**locals()))
            debug_("  {unit}:  (E00) which does render the unit definition pretty useless".format(**locals()))
            return ["E00"]
        warnings = []
        warnings += self.check_service_type_settings(conf, section)
        warnings += self.check_service_mainpid_settings(conf, section)
        warnings += self.check_exec_format_settings(conf, section)
        warnings += self.check_exec_unknown_settings(conf, section)
        warnings += self.check_environment_file_settings(conf, section)
        return warnings
    def check_environment_file_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        for env_file in conf.getlist(section, "EnvironmentFile", []):
            skipping, filename = checkprefix(env_file)
            if not os.path.isfile(os_path(self._root, filename)):
                if not skipping:
                    error_("  {unit}: {section} did not find mandatory environment file: {filename}".format(**locals()))
                    debug_("  {unit}:  (E77) the environment variable expansions will probably fail.".format(**locals()))
                    warnings += ["E77"]
                else:
                    info_("   {unit}: {section} did not find optional environment file: {filename}".format(**locals()))
                    debug_("  {unit}:  (W77) the environment variable expansions must not depend on it.".format(**locals()))
                    warnings += ["W77"]
        return warnings
    def check_service_type_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        haveType = conf.get(section, "Type", "simple")
        if haveType not in [ "simple", "forking", "notify", "oneshot", "dbus", "idle"]:
            error_("  {unit}: Failed to parse service type, ignoring: {haveType}".format(**locals()))
            debug_("  {unit}:  (W01) systemctl can only handle simple|forking|notify|oneshot/idle (no dbus)".format(**locals()))
            warnings += ["W01"]
        return warnings
    def check_service_mainpid_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        haveType = conf.get(section, "Type", "simple")
        havePIDFile = conf.get(section, "PIDFile", "")
        if haveType in ["notify"]:
            if not havePIDFile:
                info_("   {unit}: {section} type={haveType} does not provide a {section} PIDFile.".format(**locals()))
                debug_("  {unit}:  (W11) this will make systemctl to wait for MAINPID (expect timeout problems)".format(**locals()))
                warnings += ["W11"]
        if haveType in ["forking"]:
            if not havePIDFile:
                warning_("{unit}: {section} type={haveType} does not provide a {section} PIDFile.".format(**locals()))
                debug_("  {unit}:  (W12) this will not allow sending signals to the MainPID (expect restart problems)".format(**locals()))
                warnings += ["W12"]
        return warnings
    def check_exec_format_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        haveType = conf.get(section, "Type", "simple")
        haveExecStart = conf.getlist(section, "ExecStart", [])
        haveExecStop = conf.getlist(section, "ExecStop", [])
        haveExecReload = conf.getlist(section, "ExecReload", [])
        usedExecStart = []
        usedExecStop = []
        usedExecReload = []
        for line in haveExecStart:
            execmode, execline = exec_mode(line)
            if not execline.startswith("/"):
                if execmode.check:
                    error_("  {unit}: {section} Executable path is not absolute.".format(**locals()))
                else:
                    warning_("{unit}: {section} Executable path is not absolute.".format(**locals()))
                debug_("  {unit}:  (W21) ignoring {execline}".format(**locals()))
                warnings += ["W21"]
            usedExecStart.append(line)
        for line in haveExecStop:
            execmode, execline = exec_mode(line)
            if not execline.startswith("/"):
                if execmode.check:
                    error_("  {unit}: {section} Executable path is not absolute.".format(**locals()))
                else:
                    warning_("{unit}: {section} Executable path is not absolute.".format(**locals()))
                debug_("  {unit}:  (W22) ignoring {execline}".format(**locals()))
                warnings += ["W22"]
            usedExecStop.append(execline)
        for line in haveExecReload:
            execmode, execline = exec_mode(line)
            if not execline.startswith("/"):
                if execmode.check:
                    error_("  {unit}: {section} Executable path is not absolute.".format(**locals()))
                else:
                    warning_("{unit}: {section} Executable path is not absolute.".format(**locals()))
                debug_("  {unit}:  (W23) ignoring {execline}".format(**locals()))
                warnings += ["W23"]
            usedExecReload.append(execline)
        if haveType in ["simple", "notify", "forking", "idle"]:
            if not usedExecStart and not usedExecStop:
                error_("  {unit}: {section} lacks both ExecStart and ExecStop= setting. Refusing.".format(**locals()))
                debug_("  {unit}:  (E31) without start/stop the {section} type={haveType} is just useless.".format(**locals()))
                warnings += ["E31"]
            elif not usedExecStart and haveType != "oneshot":
                error_("  {unit}: {section} has no ExecStart= setting, which is only allowed for Type=oneshot services. Refusing.".format(**locals()))
                debug_("  {unit}:  (E32) without a MainPID the {section} type={haveType} can not control anything.".format(**locals()))
                warnings += ["E32"]
        if len(usedExecStart) > 1 and haveType != "oneshot":
            error_("  {unit}: There may be only one {section} ExecStart statement (unless for 'oneshot' services).".format(**locals()))
            debug_("  {unit}:  (W41) You should use ExecStartPre / ExecStartPost to add additional commands.".format(**locals()))
            warnings += ["W41"]
        if len(usedExecStop) > 1 and haveType != "oneshot":
            info_("   {unit}: There should be only one {section} ExecStop statement (unless for 'oneshot' services)".format(**locals()))
            debug_("  {unit}:  (W42) You can use ExecStopPost to add additional commands (also executed on failed Start).".format(**locals()))
            warnings += ["W42"]
        if len(usedExecReload) > 1:
            info_("   {unit}: There should be only one {section} ExecReload statement.".format(**locals()))
            debug_("  {unit}:  (W43) Use ' ; ' for multiple commands (ExecReloadPost or ExedReloadPre do not exist)".format(**locals()))
            warnings += ["W43"]
        if len(usedExecReload) > 0 and "/bin/kill " in usedExecReload[0]:
            warning_("{unit}: The use of /bin/kill is not recommended for {section} ExecReload as it is asychronous.".format(**locals()))
            debug_("  {unit}:  (W44) That means all the dependencies will perform the reload simultanously / out of order.".format(**locals()))
            warnings += ["W44"]
        return warnings
    def check_exec_unknown_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        if conf.getlist(Service, "ExecRestart", []):  # pragma: no cover
            error_("  {unit}: there no such thing as a {section} ExecRestart (ignored)".format(**locals()))
            debug_("  {unit}:  (W51) might be a bit unexpected but no.".format(**locals()))
            warnings += ["W51"]
        if conf.getlist(Service, "ExecRestartPre", []):  # pragma: no cover
            error_("  {unit}: there no such thing as a {section} ExecRestartPre (ignored)".format(**locals()))
            debug_("  {unit}:  (W52) might be a bit unexpected but no.".format(**locals()))
            warnings += ["W52"]
        if conf.getlist(Service, "ExecRestartPost", []):  # pragma: no cover
            error_("  {unit}: there no such thing as a {section} ExecRestartPost (ignored)".format(**locals()))
            debug_("  {unit}:  (W53) might be a bit unexpected but no.".format(**locals()))
            warnings += ["W53"]
        if conf.getlist(Service, "ExecReloadPre", []):  # pragma: no cover
            error_("  {unit}: there no such thing as a {section} ExecReloadPre (ignored)".format(**locals()))
            debug_("  {unit}:  (W54) might be a bit unexpected but no.".format(**locals()))
            warnings += ["W54"]
        if conf.getlist(Service, "ExecReloadPost", []):  # pragma: no cover
            error_("  {unit}: there no such thing as a {section} ExecReloadPost (ignored)".format(**locals()))
            debug_("  {unit}:  (W55) might be a bit unexpected but no.".format(**locals()))
            warnings += ["W55"]
        if conf.getlist(Service, "ExecStopPre", []):  # pragma: no cover
            error_("  {unit}: there no such thing as a {section} ExecStopPre (ignored)".format(**locals()))
            debug_("  {unit}:  (W56) might be a bit unexpected but no.".format(**locals()))
            warnings += ["W56"]
        return warnings
    def check_exec_type_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        haveType = conf.get(section, "Type", "simple")
        havePIDFile = conf.get(section, "PIDFile", "")
        if haveType in ["notify", "forking"] and not havePIDFile:
            info_("   {unit}: {section} type={haveType} does not provide a {section} PIDFile.".format(**locals()))
            warnings += [ "W19"]
            doGuessMainPID = conf.getbool(section, "GuessMainPID", "no")
            if doGuessMainPID and haveType in ["forking"]:
                warn_("{unit}: {section} type={haveType} without PIDFile can not be fixed with GuessMainPID.".format(**locals()))
                warnings += [ "W09" ]
        if haveType in ["oneshot"]:
            doRemainAfterExit = self.get_RemainAfterExit(conf)
            if not doRemainAfterExit:
                warn_("{unit}: {section} type={haveType} requires RemainAfterExit=yes to be 'active' after start.".format(**locals()))
                warnings += [ "W39" ]
        return warnings
    def check_exec_path_settings(self, conf, env, section=Service, exectype=""):
        warnings = []
        unit = conf.name()
        for execs in [ "ExecStartPre", "ExecStart", "ExecStartPost", "ExecStop", "ExecStopPost", "ExecReload" ]:
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
                    error_("  {unit}: Exec is not an absolute path:  {execs}={cmd}".format(**locals()))
                    warnings += ["E29"]
                if not os.path.isfile(exe):
                    error_("  {unit}: Exec command does not exist: ({execs}) {exe}".format(**locals()))
                    if mode.check:
                        warnings += ["E49"]
                    else:
                        warnings += ["W49"]
                    newexe1 = os.path.join("/usr/bin", exe)
                    newexe2 = os.path.join("/bin", exe)
                    indent = " " * len(execs)
                    if os.path.exists(newexe1):
                        error_("  {unit}: but this does exist: {indent}  {newexe1}".format(**locals()))
                    elif os.path.exists(newexe2):
                        error_("  {unit}: but this does exist: {indent}      {newexe2}".format(**locals()))
        return warnings
    def check_user_group_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        users = [ conf.get(section, "User", ""), conf.get(section, "SocketUser", "") ]
        groups = [ conf.get(section, "Group", ""), conf.get(section, "SocketGroup", "") ] + conf.getlist(section, "SupplementaryGroups")
        for user in users:
            if user:
                try: pwd.getpwnam(user)
                except Exception as e:
                    info = getattr(e, "__doc__", "")
                    error_("  {unit}: User does not exist: {user} ({info})".format(**locals()))
                    warnings += ["E91"]
        for group in groups:
            if group:
                try: grp.getgrnam(group)
                except Exception as e:
                    info = getattr(e, "__doc__", "")
                    error_("  {unit}: Group does not exist: {group} ({info})".format(**locals()))
                    warnings += ["E92"]
        return warnings
    def check_directory_settings(self, conf, section=Service):
        warnings = []
        unit = conf.name()
        for setting in ("RootDirectory", "RootImage", "BindPaths", "BindReadOnlyPaths",
                        "ReadWritePaths", "ReadOnlyPaths", "TemporaryFileSystem"):
            setting_value = conf.get(section, setting, "")
            if setting_value:
                info_("   {unit}: {section} private directory remounts ignored: {setting}={setting_value}".format(**locals()))
                warnings += ["W61"]
        for setting in ("PrivateTmp", "PrivateDevices", "PrivateNetwork", "PrivateUsers", "DynamicUser",
                        "ProtectSystem", "ProjectHome", "ProtectHostname", "PrivateMounts", "MountAPIVFS"):
            setting_yes = conf.getbool(section, setting, "no")
            if setting_yes:
                info_("   {unit}: {section} private directory option is ignored: {setting}=yes".format(**locals()))
                warnings += ["W62"]
        return warnings
    def check_exec_from(self, conf, env, section=Service, exectype=""):
        if conf is None:
            return []  # pragma: no cover (is never null)
        badwarnings = self.check_exec_service_from(conf, env, section, exectype)
        return not badwarnings # okee
    def check_exec_service_from(self, conf, env, section=Service, exectype=""):
        if conf is None:
            return []  # pragma: no cover (is never null)
        if not conf.data.has_section(section):
            return []  # pragma: no cover (ignored here)
        warnings = []
        unit = conf.name()
        if self.is_sysv_file(conf.filename()):
            return []  # we don't care about that
        badtypes = self.check_exec_type_settings(conf, section)
        badpaths = self.check_exec_path_settings(conf, env, section, exectype)
        badusers = self.check_user_group_settings(conf, section)
        baddirs = self.check_directory_settings(conf, section)
        warnings = badtypes + badpaths + badusers + baddirs
        badwarnings = []
        for problem in warnings:
            for ignore in IgnoreExecWarnings.split(","):
                if ignore and problem.startswith(ignore):
                    continue
            for ignore in IgnoreWarnings.split(","):
                if ignore and problem.startswith(ignore):
                    continue
            badwarnings.append(problem)
        errors = [ problem for problem in badwarnings if problem.startswith("E") ]
        if not errors:
            return [] # only warnings - no errors
        if True:
            error_("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            abspath = [ problem for problem in badpaths if problem.startswith("E2") ]
            notexists = [ problem for problem in badpaths if problem.startswith("E4") ]
            if abspath:
                some = len(abspath)
                error_("  Note, {some} executable paths were not absolute but they must always be by definition.".format(**locals()))
                time.sleep(1)
            if notexists:
                some = len(notexists)
                error_("  Oops, {some} executable paths were not found in the current environment. Refusing.".format(**locals()))
                time.sleep(1)
            if badusers:
                some = len(badusers)
                error_("  Oops, {some} user names or group names were not found. Refusing.".format(**locals()))
                time.sleep(1)
            if baddirs:
                some = len(baddirs)
                info_("   Note, {some} private directory settings are ignored. The application should not depend on it.".format(**locals()))
                time.sleep(1)
            error_("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return badwarnings
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
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                units += [ module ]
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.show_units(units) + notfound  # and found_all
    def show_units(self, units):
        unit_property = self._unit_property
        dbg_("show --property={unit_property}".format(**locals()))
        result = []
        for unit in units:
            if result: result += [ "" ]
            for var, value in self.show_unit_items(unit):
                if unit_property:
                    if unit_property != var:
                        continue
                else:
                    if not value and not self._show_all:
                        continue
                result += [ "{var}={value}".format(**locals()) ]
        return result
    def show_unit_items(self, unit):
        info_("try read unit {unit}".format(**locals()))
        conf = self.get_unit_conf(unit)
        for entry in self.each_unit_items(unit, conf):
            yield entry
    def each_unit_items(self, unit, conf):
        loaded = conf.loaded()
        if not loaded:
            loaded = "not-loaded"
            if "NOT-FOUND" in self.get_description_from(conf):
                loaded = "not-found"
        names = { unit: 1, conf.name(): 1 }
        yield "Id", conf.name()
        yield "Names", " ".join(sorted(names.keys()))
        yield "Description", self.get_description_from(conf)  # conf.get(Unit, "Description")
        yield "PIDFile", self.get_pid_file(conf)  # not self.pid_file_from w/o default location
        yield "PIDFilePath", self.pid_file_from(conf)
        yield "MainPID", strE(self.active_pid_from(conf))            # status["MainPID"] or PIDFile-read
        yield "SubState", self.get_substate_from(conf) or "unknown"  # status["SubState"] or notify-result
        yield "ActiveState", self.get_active_from(conf) or "unknown"  # status["ActiveState"]
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
        for item in ["ExecMainPID", "ExecMainCode", "ExecMainStatus", "ExecMainStep"]:
            result = self.get_status_from(conf, item, "")
            if result:
                yield item, result
        for item in ["ExecLastPID", "ExecLastCode", "ExecLastStatus", "ExecLastStep"]:
            result = self.get_status_from(conf, item, "")
            if result:
                yield item, result
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
    def ignore_modules(self, *modules):
        """ [UNIT]... append ignore-pattern to mask pre-enabled services
            Use --force to append the pattern as text instead of matching
            them with existing units in the system. That allows for them
            to have fnmatch */? wildcards and a gitignore-style !-inverse.
        """
        found_all = True
        units = []
        for module in modules:
            if _force:
                units += to_list(module)
                continue
            prefix = ""
            if module.startswith("!"):
                prefix = "!"
                module = module[1:]
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ prefix + unit ]
        if not found_all and not _force:
            error_("Use --force to append the pattern as text (to be evaluated later)")
            self.error |= NOT_OK
            return False
        result = self.ignore_units(units)
        return result
    def ignore_units(self, units):
        filename = os_path(self._root, self.expand_path(IgnoredServicesFile))
        try:
            if os.path.exists(filename):
                text = open(filename, "rb").read()
                if text and not text.endswith(b"\n"):
                    text += b"\n"
            else:
                text = b""
            for unit in units:
                text += unit.encode("utf-8")
                text += b"\n"
            dirpath = os.path.dirname(filename)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
            with open(filename, "wb") as f:
                f.write(text)
            # dbg_("written {text}".format(**locals()))  # (internal)
            # dbg__("after adding {units}".format(**locals()))  # (internal)
            return True
        except Exception as e:
            error_("while append to {filename}: {e}".format(**locals()))
            return False
    def read_ignored_modules(self):
        filename = os_path(self._root, self.expand_path(IgnoredServicesFile))
        try:
            if os.path.exists(filename):
                content = open(filename, "r").read()
                return content
        except Exception as e:
            warning_("while reading {filename}: {e}")
        return ""
    def load_ignored_modules(self):
        if self._ignored_modules is None:
            self._ignored_modules = self.read_ignored_modules()
    def get_ignored_services(self):
        igno = _ignored_services
        filename = os_path(self._root, IgnoredServicesFile)
        if os.path.exists(filename):
            try:
                text_data = open(filename, "rb").read()
                igno_text = text_data.decode("utf-8")
                if not igno_text.endswith("\n"):
                    igno_text += "\n"
                igno += "[{filename}]\n".format(**locals())
                igno += igno_text
            except Exception as e:
                error_("while reading from {filename}: {e}".format(**locals()))
        return igno
    def ignored_unit(self, unit, ignored):
        if self._show_all:
            return []
        return self._ignored_unit(unit, ignored)
    def _ignored_unit(self, unit, ignored):
        is_ignored = False
        because_of = []
        in_section = "[...]"
        self.load_sysinit_modules()
        if self._sysinit_modules:
            if unit in self._sysinit_modules:
                is_ignored = True
                because_of.append("sysinit.target")
        self.load_ignored_modules()
        for igno in (ignored, self._ignored_modules):
            if not igno: continue
            for line in igno.splitlines():
                if not line.strip():
                    continue
                if line.startswith("["):
                    in_section = line.strip()
                ignore = line.strip()
                if ignore.startswith("!"):
                    ignore = ignore[1:].strip()
                    if fnmatch.fnmatchcase(unit, ignore):
                        is_ignored = False
                        because_of.append("!" + in_section)
                    if fnmatch.fnmatchcase(unit, ignore+".service"):
                        is_ignored = False
                        because_of.append("!" + in_section)
                else:
                    if fnmatch.fnmatchcase(unit, ignore):
                        is_ignored = True
                        because_of.append(in_section)
                    if fnmatch.fnmatchcase(unit, ignore+".service"):
                        is_ignored = True
                        because_of.append(in_section)
        if DebugIgnoredServices:
            if is_ignored:
                dbg_("Unit {unit} ignored because of {because_of}".format(**locals()))
            elif because_of:
                dbg_("Unit {unit} allowed because of {because_of}".format(**locals()))
        if is_ignored:
            return because_of
        return []
    def default_services_modules(self, *modules):
        """ -- show the default services (started by 'default')
            This is used internally to know the list of service to be started in the 'get-default'
            target runlevel when the container is started through default initialisation. It will
            ignore a number of services - use '--all' to show all services as systemd would do.
        """
        results = []
        targets = modules or [ self.get_default_target() ]
        for target in targets:
            units = self.target_default_services(target)
            unitlist = " ".join(units)
            dbg_(" {unitlist} # {target}".format(**locals()))
            for unit in units:
                if unit not in results:
                    results.append(unit)
        return results
    def target_default_services(self, target=None, sysv="S"):
        """ get the default services for a target - this will ignore a number of services,
            use '--all' see the original list as systemd would see them.
        """
        if self._show_all:
            igno = ""
        else:
            igno = self.get_ignored_services()
        if DebugIgnoredServices:
            dbg_("ignored services filter for default.target:\n\t{igno}".format(**locals()))
        default_target = target or self.get_default_target()
        return self.enabled_target_services(default_target, sysv, igno)
    def enabled_target_services(self, target, sysv="S", igno=""):
        result = []
        units = self._enabled_target_services(target, sysv)
        if self._show_all:
            return units
        for unit in units:
            ignored = self._ignored_unit(unit, igno)
            if ignored:
                dbg_("Unit {unit} ignored in {ignored} for target services".format(**locals()))
            else:
                result.append(unit)
        return result
    def _enabled_target_services(self, target, sysv="S"):
        units = []
        if self.user_mode():
            targetlist = self.get_target_list(target)
            dbg_("check for {target} user services : {targetlist}".format(**locals()))
            for targets in targetlist:
                for unit in self._enabled_target_user_local_units(targets, ".target"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._required_target_units(targets, ".socket"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._enabled_target_user_local_units(targets, ".socket"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._required_target_units(targets, ".service"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._enabled_target_user_local_units(targets, ".service"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._enabled_target_user_system_units(targets, ".service"):
                    if unit not in units:
                        units.append(unit)
        else:
            targetlist = self.get_target_list(target)
            dbg_("check for {target} system services: {targetlist}".format(**locals()))
            for targets in targetlist:
                for unit in self._enabled_target_configured_system_units(targets, ".target"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._required_target_units(targets, ".socket"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._enabled_target_installed_system_units(targets, ".socket"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._required_target_units(targets, ".service"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._enabled_target_installed_system_units(targets, ".service"):
                    if unit not in units:
                        units.append(unit)
            for targets in targetlist:
                for unit in self._enabled_target_sysv_units(targets, sysv):
                    if unit not in units:
                        units.append(unit)
        return units
    def _enabled_target_user_local_units(self, target, unit_kind=".service"):
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
                    if unit.endswith(unit_kind):
                        units.append(unit)
        return units
    def _enabled_target_user_system_units(self, target, unit_kind=".service"):
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
                    if unit.endswith(unit_kind):
                        conf = self.load_unit_conf(unit)
                        if conf is None:
                            pass
                        elif self.not_user_conf(conf):
                            pass
                        else:
                            units.append(unit)
        return units
    def _enabled_target_installed_system_units(self, target, unit_type=".service"):
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
                    if unit.endswith(unit_type):
                        units.append(unit)
        return units
    def _enabled_target_configured_system_units(self, target, unit_type=".service"):
        units = []
        if True:
            folder = self.default_enablefolder(target)
            if self._root:
                folder = os_path(self._root, folder)
            if os.path.isdir(folder):
                for unit in sorted(os.listdir(folder)):
                    path = os.path.join(folder, unit)
                    if os.path.isdir(path): continue
                    if unit.endswith(unit_type):
                        units.append(unit)
        return units
    def _enabled_target_sysv_units(self, target, sysv="S"):
        units = []
        folders = []
        if target in [ "multi-user.target", DefaultUnit ]:
            folders += [ self.rc3_root_folder() ]
        if target in [ "graphical.target" ]:
            folders += [ self.rc5_root_folder() ]
        for folder in folders:
            if not os.path.isdir(folder):
                warn_("non-existant {folder}".format(**locals()))
                continue
            for unit in sorted(os.listdir(folder)):
                path = os.path.join(folder, unit)
                if os.path.isdir(path): continue
                m = re.match(sysv+r"\d\d(.*)", unit)
                if m:
                    service = m.group(1)
                    unit = service + ".service"
                    units.append(unit)
        return units
    def required_target_units(self, target, unit_type, igno=""):
        units = self._required_target_units(target, unit_type)
        if self._show_all:
            return units
        result = []
        for unit in units:
            ignored = self._ignored_unit(unit, igno)
            if ignored:
                dbg_("Unit {unit} ignored in {ignored} for required target units".format(**locals()))
            else:
                result.append(unit)
        return result
    def _required_target_units(self, target, unit_type):
        units = []
        deps = self.get_required_dependencies(target)
        for unit in sorted(deps):
            if unit.endswith(unit_type):
                if unit not in units:
                    units.append(unit)
        return units
    def get_target_conf(self, module):  # -> conf (conf | default-conf)
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
        targets = [ target ]
        conf = self.get_target_conf(module)
        requires = conf.get(Unit, "Requires", "")
        while requires in target_requires:
            targets = [ requires ] + targets
            requires = target_requires[requires]
        dbg_("the {module} requires {targets}".format(**locals()))
        return targets
    def default_target(self, *modules):
        """ -- start units for default system level
            This will go through the enabled services in the default 'multi-user.target'.
            However some services are ignored as being known to be installation garbage
            from unintended services. Use '--all' so start all of the installed services
            and with '--all --force' even those services that are otherwise wrong. 
            /// SPECIAL: with --now or --init the init-loop is run and afterwards
                a system_halt is performed with the enabled services to be stopped."""
        return self.default_system()
    def default_system(self, arg=True):
        self.sysinit_status(SubState="initializing")
        info_("system default requested - {arg}".format(**locals()))
        init = self._now or self._init
        return self.start_system_default(init=init)
    def start_system_default(self, init=False):
        """ detect the default.target services and start them.
            When --init is given then the init-loop is run and
            the services are stopped again by 'systemctl halt'."""
        target = self.get_default_target()
        services = self.start_target_system(target, init)
        info_("{target} system is up".format(**locals()))
        if init:
            info_("init-loop start")
            sig = self.init_loop_until_stop(services)
            info_("init-loop {sig}".format(**locals()))
            self.stop_system_default()
        return not not services
    def start_target_system(self, target, init=False):
        services = self.target_default_services(target, "S")
        self.sysinit_status(SubState="starting")
        self.start_units(services)
        return services
    def do_start_target_from(self, conf):
        target = conf.name()
        # services = self.start_target_system(target)
        services = self.target_default_services(target, "S")
        units = [service for service in services if not self.is_running_unit(service)]
        dbg_("start {target} is starting {units} from {services}".format(**locals()))
        return self.start_units(units)
    def stop_system_default(self):
        """ detect the default.target services and stop them.
            This is commonly run through 'systemctl halt' or
            at the end of a 'systemctl --init default' loop."""
        target = self.get_default_target()
        services = self.stop_target_system(target)
        info_("{target} system is down".format(**locals()))
        return not not services
    def stop_target_system(self, target):
        services = self.target_default_services(target, "K")
        self.sysinit_status(SubState="stopping")
        self.stop_units(services)
        return services
    def do_stop_target_from(self, conf):
        target = conf.name()
        # services = self.stop_target_system(target)
        services = self.target_default_services(target, "K")
        units = [service for service in services if self.is_running_unit(service)]
        dbg_("stop {target} is stopping {units} from {services}".format(**locals()))
        return self.stop_units(units)
    def do_reload_target_from(self, conf):
        target = conf.name()
        return self.reload_target_system(target)
    def reload_target_system(self, target):
        services = self.target_default_services(target, "S")
        units = [service for service in services if self.is_running_unit(service)]
        return self.reload_units(units)
    def halt_target(self, *modules):
        """ -- stop units from default system level """
        return self.halt_system()
    def halt_system(self, arg=True):
        """ -- stop units from default system level """
        info_("system halt requested - {arg}".format(**locals()))
        done = self.stop_system_default()
        try:
            os.kill(1, signal.SIGQUIT)  # exit init-loop on no_more_procs
        except Exception as e:
            warn_("SIGQUIT to init-loop on PID-1: {e}".format(**locals()))
        return done
    def get_targets_folder(self):
        return os_path(self._root, self.mask_folder())
    def get_default_target_file(self):
        targets_folder = self.get_targets_folder()
        return os.path.join(targets_folder, DefaultUnit)
    def get_default_target(self, default_target=None):
        """ get current default run-level"""
        current = default_target or self._default_target
        default_target_file = self.get_default_target_file()
        if os.path.islink(default_target_file):
            current = os.path.basename(os.readlink(default_target_file))
        return current
    def set_default_modules(self, *modules):
        """ set current default run-level"""
        if not modules:
            dbg_(".. no runlevel given")
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
                self.error |= NOT_OK | NOT_ACTIVE  # 3
                msg = "No such runlevel {module}".format(**locals())
                continue
            #
            if os.path.islink(default_target_file):
                os.unlink(default_target_file)
            if not os.path.isdir(os.path.dirname(default_target_file)):
                os.makedirs(os.path.dirname(default_target_file))
            os.symlink(targetfile, default_target_file)
            dbg_("Created symlink from {default_target_file} -> {targetfile}".format(**locals()))
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
                dbg_("init default --now --all => no_more_procs")
                self.doExitWhenNoMoreProcs = True
            return self.start_system_default(init=True)
        #
        # otherwise quit when all the init-services have died
        self.doExitWhenNoMoreServices = True
        if self._now or self._show_all:
            dbg_("init services --now --all => no_more_procs")
            self.doExitWhenNoMoreProcs = True
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                unit_ = unit_of(module)
                error_("Unit {unit_} could not be found.".format(**locals()))
                found_all = False
                continue
            for unit in matched:
                ignored = self.ignored_unit(unit, _ignored_services)
                if ignored and not self._force:
                    warn_("Unit {unit} ignored in {ignored} (use --force to pass)".format(**locals()))
                    continue
                if unit not in units:
                    units += [ unit ]
        modulelist, unitlist = " ".join(modules), " ".join(units)
        info_("init {modulelist} -> start {unitlist}".format(**locals()))
        done = self.start_units(units, init=True)
        info_("-- init is done")
        return done  # and found_all
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
                error_("can not open {unit} log: {log_path}\n\t{e}".format(**locals()))
    def read_log_files(self, units):
        BUFSIZE=8192
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
                    os.write(1, content)
                    try: os.fsync(1)
                    except: pass
    def stop_log_files(self, units):
        for unit in units:
            try:
                if unit in self._log_file:
                    if self._log_file[unit]:
                        os.close(self._log_file[unit])
            except Exception as e:
                error_("can not close log: {unit}\n\t{e}".format(**locals()))
        self._log_file = {}
        self._log_hold = {}

    def get_StartLimitBurst(self, conf):
        defaults = DefaultStartLimitBurst
        return to_int(conf.get(Service, "StartLimitBurst", strE(defaults)), defaults)  # 5
    def get_StartLimitIntervalSec(self, conf, maximum=None):
        maximum = maximum or 999
        defaults = DefaultStartLimitIntervalSec
        interval = conf.get(Service, "StartLimitIntervalSec", strE(defaults))  # 10s
        return time_to_seconds(interval, maximum)
    def get_RestartSec(self, conf, maximum=None):
        maximum = maximum or DefaultStartLimitIntervalSec
        delay = conf.get(Service, "RestartSec", strE(DefaultRestartSec))
        return time_to_seconds(delay, maximum)
    def restart_failed_units(self, units, maximum=None):
        """ This function will retart failed units.
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
                    dbg_("[{me}] [{unit}] Current NoCheck (Restart={restartPolicy})".format(**locals()))
                    continue
                restartSec = self.get_RestartSec(conf)
                if restartSec == 0:
                    minSleep = 1
                    if minSleep < InitLoopSleep:
                        oldSleep = InitLoopSleep
                        warn_("[{me}] [{unit}] set InitLoopSleep from {oldSleep}s to {minSleep} (caused by RestartSec=0!)".format(**locals()))
                        InitLoopSleep = minSleep
                elif restartSec > 0.9 and restartSec < InitLoopSleep:
                    restartSleep = int(restartSec + 0.2)
                    if restartSleep < InitLoopSleep:
                        oldSleep = InitLoopSleep
                        warn_("[{me}] [{unit}] set InitLoopSleep from {oldSleep}s to {restartSleep} (caused by RestartSec={restartSec:.3f}s)".format(**locals()))
                        InitLoopSleep = restartSleep
                isUnitState = self.get_active_from(conf)
                isUnitFailed = isUnitState in ["failed"]
                dbg_("[{me}] [{unit}] Current Status: {isUnitState} ({isUnitFailed})".format(**locals()))
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
                        restarted_ = len(restarted)
                        dbg_("[{me}] [{unit}] Current limitSecs={limitSecs}s limitBurst={limitBurst}x (restarted {restarted_}x)".format(**locals()))
                        oldest = 0.
                        interval = 0.
                        if len(restarted) >= limitBurst:
                            history = [ "%.3fs" % (t - now) for t in restarted ]
                            dbg_("[{me}] [{unit}] restarted {history}".format(**locals()))
                            while len(restarted):
                                oldest = restarted[0]
                                interval = time.time() - oldest
                                if interval > limitSecs:
                                    restarted = restarted[1:]
                                    continue
                                break
                            self._restarted_unit[unit] = restarted
                            history = [ "%.3fs" % (t - now) for t in restarted ]
                            dbg_("[{me}] [{unit}] ratelimit {history}".format(**locals()))
                            # all values in restarted have a time below limitSecs
                        if len(restarted) >= limitBurst:
                            info_("[{me}] [{unit}] Blocking Restart - oldest {oldest} is {interval} ago (allowed {limitSecs})".format(**locals()))
                            self.write_status_from(conf, AS="failed", SS="restart-limit")
                            unit = ""  # dropped out
                            continue
                    except Exception as e:
                        error_("[{unit}] burst exception {e}".format(**locals()))
                if unit:  # not dropped out
                    if unit not in self._restart_failed_units:
                        self._restart_failed_units[unit] = now + restartSec
                        restarting = self._restart_failed_units[unit] - now
                        dbg_("[{me}] [{unit}] restart scheduled in {restarting:+.3f}s".format(**locals()))
            except Exception as e:
                error_("[{me}] [{unit}] An error ocurred while restart checking: {e}".format(**locals()))
        if not self._restart_failed_units:
            self.error |= NOT_OK
            return []
        # NOTE: this function is only called from InitLoop when "running"
        # let's check if any of the restart_units has its restartSec expired
        now = time.time()
        restart_done = []
        checkinglist = [ "%+.3fs" % (t - now) for t in self._restart_failed_units.values() ]
        dbg_("[{me}] Restart checking  {checkinglist}".format(**locals()))
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
                dbg_("[{me}] [{unit}] Restart Status: {isUnitState} ({isUnitFailed})".format(**locals()))
                if isUnitFailed:
                    dbg_("[{me}] [{unit}] --- restarting failed unit...".format(**locals()))
                    self.restart_unit(unit)
                    dbg_("[{me}] [{unit}] --- has been restarted.".format(**locals()))
                    if unit in self._restarted_unit:
                        self._restarted_unit[unit].append(time.time())
            except Exception as e:
                error_("[{me}] [{unit}] An error ocurred while restarting: {e}".format(**locals()))
        for unit in restart_done:
            if unit in self._restart_failed_units:
                del self._restart_failed_units[unit]
        remaininglist = [ "%+.3fs" % (t - now) for t in self._restart_failed_units.values() ]
        dbg_("[{me}] Restart remaining {remaininglist}".format(**locals()))
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
        #
        self.start_log_files(units)
        dbg_("start listen")
        listen = SystemctlListenThread(self)
        dbg_("starts listen")
        listen.start()
        dbg_("started listen")
        self.sysinit_status(ActiveState="active", SubState="running")
        timestamp = time.time()
        result = None
        while True:
            try:
                if DebugInitLoop:  # pragma: no cover
                    sleeps = InitLoopSleep
                    dbg_("DONE InitLoop (sleep {sleeps}s)".format(**locals()))
                sleep_sec = InitLoopSleep - (time.time() - timestamp)
                if sleep_sec < MinimumYield:
                    sleep_sec = MinimumYield
                sleeping = sleep_sec
                while sleeping > 2:
                    time.sleep(1)  # accept signals atleast every second
                    sleeping = InitLoopSleep - (time.time() - timestamp)
                    if sleeping < MinimumYield:
                        sleeping = MinimumYield
                        break
                time.sleep(sleeping)  # remainder waits less that 2 seconds
                timestamp = time.time()
                self.loop.acquire()
                if DebugInitLoop:  # pragma: no cover
                    dbg_("NEXT InitLoop (after {sleep_sec}s)".format(**locals()))
                self.read_log_files(units)
                if DebugInitLoop:  # pragma: no cover
                    dbg_("reap zombies - check current processes")
                running = self.reap_zombies()
                if DebugInitLoop:  # pragma: no cover
                    dbg_("reap zombies - init-loop found {running} running procs".format(**locals()))
                if self.doExitWhenNoMoreServices:
                    active = False
                    for unit in units:
                        conf = self.load_unit_conf(unit)
                        if not conf: continue
                        if self.is_active_from(conf):
                            active = True
                    if not active:
                        info_("no more services - exit init-loop")
                        break
                if self.doExitWhenNoMoreProcs:
                    if not running:
                        info_("no more procs - exit init-loop")
                        break
                if RestartOnFailure:
                    self.restart_failed_units(units)
                self.loop.release()
            except KeyboardInterrupt as e:
                if e.args and e.args[0] == "SIGQUIT":
                    # the original systemd puts a coredump on that signal.
                    info_("SIGQUIT - switch to no more procs check")
                    self.doExitWhenNoMoreProcs = True
                    continue
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                info_("interrupted - exit init-loop")
                result = str(e) or "STOPPED"
                break
            except Exception as e:
                info_("interrupted - exception {e}".format(**locals()))
                raise
        self.sysinit_status(ActiveState=None, SubState="degraded")
        try: self.loop.release()
        except: pass
        listen.stop()
        listen.join(2)
        self.read_log_files(units)
        self.read_log_files(units)
        self.stop_log_files(units)
        dbg_("done - init loop")
        return result
    def reap_zombies_target(self):
        """ -- check to reap children (internal) """
        running = self.reap_zombies()
        return "remaining {running} process".format(**locals())
    def reap_zombies(self):
        """ check to reap children """
        proc = DefaultProcDir
        selfpid = os.getpid()
        running = 0
        for pid_entry in os.listdir(proc):
            pid = to_intN(pid_entry)
            if pid is None:
                continue
            if pid == selfpid:
                continue
            pid_status = "{proc}/{pid}/status".format(**locals())
            if os.path.isfile(pid_status):
                zombie = False
                ppid = -1
                try:
                    for line in open(pid_status):
                        m = re.match(r"State:\s*Z.*", line)
                        if m: zombie = True
                        m = re.match(r"PPid:\s*(\d+)", line)
                        if m: ppid = int(m.group(1))
                except IOError as e:
                    warn_("{pid_status} : {e}".format(**locals()))
                    continue
                if zombie and ppid == os.getpid():
                    info_("reap zombie {pid}".format(**locals()))
                    try: os.waitpid(pid, os.WNOHANG)
                    except OSError as e:
                        strerror = e.strerror
                        warn_("reap zombie {pid}: {strerror}".format(**locals()))
            if os.path.isfile(pid_status):
                if pid > 1:
                    running += 1
        return running  # except PID 0 and PID 1
    def sysinit_status(self, **status):
        conf = self.sysinit_target_conf()
        self.write_status_from(conf, **status)
    def sysinit_target_conf(self):
        if not self._sysinit_target:
            self._sysinit_target = self.default_unit_conf(SysInitTarget, "System Initialization")
        assert self._sysinit_target is not None
        return self._sysinit_target
    def is_system_running(self):
        conf = self.sysinit_target_conf()
        if not self.is_running_unit_from(conf):
            time.sleep(MinimumYield)
        if not self.is_running_unit_from(conf):
            return "offline"
        status = self.read_status_from(conf)
        return status.get("SubState", "unknown")
    def is_system_running_info(self):
        """ -- return status while running 'default' services """
        state = self.is_system_running()
        if state not in [ "running" ]:
            self.error |= NOT_OK  # 1
        if self._quiet:
            return None
        return state
    def wait_system(self, target=None):
        target = target or SysInitTarget
        for attempt in xrange(int(SysInitWait)):
            state = self.is_system_running()
            if "init" in state:
                if target in [ SysInitTarget, "basic.target" ]:
                    info_("system not initialized - wait {target}".format(**locals()))
                    time.sleep(1)
                    continue
            if "start" in state or "stop" in state:
                if target in [ "basic.target" ]:
                    info_("system not running - wait {target}".format(**locals()))
                    time.sleep(1)
                    continue
            if "running" not in state:
                info_("system is {state}".format(**locals()))
            break
    def is_running_unit_from(self, conf):
        status_file = self.get_status_file_from(conf)
        return path_getsize(status_file) > 0
    def is_running_unit(self, unit):
        conf = self.get_unit_conf(unit)
        return self.is_running_unit_from(conf)
    def kill_children_pidlist_of(self, mainpid):
        if not mainpid:
            return []
        proc = DefaultProcDir
        pidlist = [ mainpid ]
        pids = [ mainpid ]
        ppid_of = {}
        for depth in xrange(KillChildrenMaxDepth):
            for pid_entry in os.listdir(proc):
                pid = to_intN(pid_entry)
                if pid is None:
                    continue
                if pid not in ppid_of:
                    pid_status = "{proc}/{pid}/status".format(**locals())
                    if os.path.isfile(pid_status):
                        try:
                            for line in open(pid_status):
                                if line.startswith("PPid:"):
                                    ppid_text = line[len("PPid:"):].strip()
                                    ppid = int(ppid_text)
                                    ppid_of[pid] = ppid
                                    break
                        except IOError as e:
                            warn_("{pid_status} : {e}".format(**locals()))
                            continue
                ppid = ppid_of.get(pid, 0)
                if ppid and ppid in pidlist:
                    if ppid not in pids:
                        pids += [ pid ]
                    if pid not in pids:
                        pids += [ pid ]
            if len(pids) <= len(pidlist):
                break
            pidlist = pids[:]
            continue
        debug_(".... mainpid {mainpid} to pid list {pidlist}".format(**locals()))
        return pids
    def killall(self, *targets):
        """ --- explicitly kill processes (internal) """
        proc = DefaultProcDir
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
                else:  # pragma: no cover
                    error_("unsupported {target}".format(**locals()))
                continue
            for pid_entry in os.listdir(proc):
                pid = to_intN(pid_entry)
                if pid:
                    try:
                        cmdline = "{proc}/{pid}/cmdline".format(**locals())
                        cmd = open(cmdline).read().split("\0")
                        if DebugKillAll:  # pragma: no cover
                            dbg_("cmdline {cmd}".format(**locals()))
                        found = None
                        cmd_exe = os.path.basename(cmd[0])
                        if DebugKillAll:  # pragma: no cover
                            dbg_("cmd.exe '{cmd_exe}'".format(**locals()))
                        if fnmatch.fnmatchcase(cmd_exe, target): found = "exe"
                        if len(cmd) > 1 and cmd_exe.startswith("python"):
                            X = 1
                            while cmd[X].startswith("-"): X += 1  # atleast '-u' unbuffered
                            cmd_arg = os.path.basename(cmd[X])
                            if DebugKillAll:  # pragma: no cover
                                dbg_("cmd.arg '{cmd_arg}'".format(**locals()))
                            if fnmatch.fnmatchcase(cmd_arg, target):
                                found = "arg"
                            if cmd_exe.startswith("coverage") or cmd_arg.startswith("coverage"):
                                x = cmd.index("--")
                                if x > 0 and x+1 < len(cmd):
                                    cmd_run = os.path.basename(cmd[x+1])
                                    if DebugKillAll:  # pragma: no cover
                                        dbg_("cmd.run '{cmd_run}'".format(**locals()))
                                    if fnmatch.fnmatchcase(cmd_run, target):
                                        found = "run"
                        if found:
                            if DebugKillAll:  # pragma: no cover
                                dbg_("{found} found {pid} {cmd}".format(**locals()))
                            if pid != os.getpid():
                                dbg_(" kill -{sig} {pid} # {target}".format(**locals()))
                                os.kill(pid, sig)
                    except Exception as e:
                        error_("kill -{sig} {pid} : {e}".format(**locals()))
        return True
    def force_ipv4(self, *args):
        """ only ipv4 localhost in /etc/hosts """
        dbg_("checking hosts sysconf for '::1 localhost'")
        lines = []
        sysconf_hosts = os_path(self._root, _etc_hosts)
        for line in open(sysconf_hosts):
            if "::1" in line:
                newline = re.sub("\\slocalhost\\s", " ", line)
                if line != newline:
                    hosts44 = path44(sysconf_hosts)
                    line44, newline44 = o44(line.rstrip()), o44(newline.rstrip())
                    info_("{hosts44}: '{line44}' => '{newline44}'".format(**locals()))
                    line = newline
            lines.append(line)
        f = open(sysconf_hosts, "w")
        for line in lines:
            f.write(line)
        f.close()
    def force_ipv6(self, *args):
        """ only ipv4 localhost in /etc/hosts """
        dbg_("checking hosts sysconf for '127.0.0.1 localhost'")
        lines = []
        sysconf_hosts = os_path(self._root, _etc_hosts)
        for line in open(sysconf_hosts):
            if "127.0.0.1" in line:
                newline = re.sub("\\slocalhost\\s", " ", line)
                if line != newline:
                    hosts44 = path44(sysconf_hosts)
                    line44, newline44 = o44(line.rstrip()), o44(newline.rstrip())
                    info_("{hosts44}: '{line44}' => '{newline44}'".format(**locals()))
                    line = newline
            lines.append(line)
        f = open(sysconf_hosts, "w")
        for line in lines:
            f.write(line)
        f.close()
    def help_overview(self):
        lines = []
        prog = os.path.basename(sys.argv[0])
        argz = {}
        for name in dir(self):
            arg = None
            if name.endswith("_target"):
                arg = name[:-len("_target")].replace("_", "-")
            if name.endswith("_of_unit"):
                arg = name[:-len("_of_unit")].replace("_", "-")
            if name.endswith("_info"):
                arg = name[:-len("_info")].replace("_", "-")
            if name.endswith("_modules"):
                arg = name[:-len("_modules")].replace("_", "-")
            if arg:
                argz[arg] = name
        lines.append("%s command [options]..." % prog)
        lines.append("")
        lines.append("Commands:")
        for arg in sorted(argz):
            name = argz[arg]
            func = getattr(self, name)
            if not callable(func):
                continue
            doc = "..."
            doctext = getattr(func, "__doc__")
            if doctext:
                doc = doctext
            elif not self._show_all:
                continue  # pragma: no cover
            firstline = doc.split("\n")[0]
            doc_text = firstline.strip()
            if "--" not in firstline:
                doc_text = "-- " + doc_text
            if "(internal)" in firstline or "(experimental)" in firstline:
                if not self._show_all:
                    continue
            lines.append(" %s %s" % (arg, firstline.strip()))
        return lines
    def help_modules(self, *args):
        """[command] -- show this help
        """
        lines = []
        prog = os.path.basename(sys.argv[0])
        if not args:
            return self.help_overview()
        for arg in args:
            arg = arg.replace("-", "_")
            func1 = getattr(self.__class__, arg+"_modules", None)
            func2 = getattr(self.__class__, arg+"_info", None)
            func3 = getattr(self.__class__, arg+"_of_unit", None)
            func4 = getattr(self.__class__, arg+"_target", None)
            func5 = None
            if arg.startswith("__"):
                func5 = getattr(self.__class__, arg[2:], None)
            func = func1 or func2 or func3 or func4 or func5
            if func is None:
                print("error: no such command '%s'" % arg)
                self.error |= NOT_OK
                continue
            if not callable(func):
                continue
            doc_text = "..."
            doc = getattr(func, "__doc__", None)
            if doc:
                doc_text = doc.replace("\n", "\n\n", 1).strip()
                if "--" not in doc_text:
                    doc_text = "-- " + doc_text
            else:
                func_name = arg  # FIXME
                dbg_("__doc__ of {func_name} is none".format(**locals()))
                if not self._show_all: continue
            lines.append("%s %s %s" % (prog, arg, doc_text))
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
        return [ self.systemd_version(), self.systemd_features() ]

def debug_result_(msg):
    if DebugPrintResult:  # pragma: no cover
        logg.debug("%s", msg)
def hint_result_(msg):
    if DebugPrintResult:  # pragma: no cover
        logg.info("%s", msg)
def note_result_(msg):
    if DebugPrintResult:  # pragma: no cover
        logg.warning("%s", msg)

def print_begin(argv, args):
    script = os.path.realpath(argv[0])
    command = " ".join(args)
    system = _user_mode and " --user" or " --system"
    init = _init and " --init" or ""
    info_("EXEC BEGIN {script} {command}{system}{init}".format(**locals()))
    if _root and not is_good_root(_root):
        root44 = path44(_root)
        warn_("the --root={root44} should have alteast three levels /tmp/test_123/root")

def print_begin2(args):
    dbg_("======= systemctl.py " + " ".join(args))

def is_not_ok(result):
    hint_result_("EXEC END {result}")
    if result is False:
        return NOT_OK
    return 0

def print_str(result):
    if result is None:
        debug_result_("    END {result}")
        return
    print(result)
    result1 = result.split("\n")[0][:-20]
    if result == result1:
        hint_result_("EXEC END '{result}'".format(**locals()))
    else:
        hint_result_("EXEC END '{result1}...'".format(**locals()))
        debug_result_("    END '{result}'".format(**locals()))
def print_str_list(result):
    if result is None:
        debug_result_("    END {result}")
        return
    shown = 0
    for element in result:
        print(element)
        shown += 1
    hint_result_("EXEC END {shown} items".format(**locals()))
    debug_result_("    END {result}".format(**locals()))
def print_str_list_list(result):
    shown = 0
    for element in result:
        print("\t".join([ str(elem) for elem in element] ))
        shown += 1
    hint_result_("EXEC END {shown} items".format(**locals()))
    debug_result_("    END {result}".format(**locals()))
def print_str_dict(result):
    if result is None:
        debug_result_("    END {result}")
        return
    shown = 0
    for key in sorted(result.keys()):
        element = result[key]
        print("%s=%s" % (key, element))
        shown += 1
    hint_result_("EXEC END {shown} items".format(**locals()))
    debug_result_("    END {result}".format(**locals()))

def config_globals(settings):
    for setting in settings:
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
                dbg_("yes {nam}={val}".format(**locals()))
                globals()[nam] = (val in ("true", "True", "TRUE", "yes", "y", "Y", "YES", "1"))
                v_show_all = _show_all
                dbg_("... _show_all={v_show_all}".format(**locals()))
            elif isinstance(old, float):
                dbg_("num {nam}={val}".format(**locals()))
                globals()[nam] = float(val)
                vMinimumYield = MinimumYield
                dbg_("... MinimumYield={vMinimumYield}".format(**locals()))
            elif isinstance(old, int):
                dbg_("int {nam}={val}".format(**locals()))
                globals()[nam] = int(val)
                vInitLoopSleep = InitLoopSleep
                dbg_("... InitLoopSleep={vInitLoopSleep}".format(**locals()))
            elif isinstance(old, basestring):
                dbg_("str {nam}={val}".format(**locals()))
                globals()[nam] = val.strip()
                vSysInitTarget = SysInitTarget
                dbg_("... SysInitTarget={vSysInitTarget}".format(**locals()))
            else:
                nam_type = type(old)
                warn_("(ignored) unknown target type -c '{nam}' : {nam_type}".format(**locals()))
        else:
            warn_("(ignored) unknown target config -c '{nam}' : no such variable".format(**locals()))

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
        exitcode = is_not_ok(systemctl.default_target())
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
    elif command in ["ignore"]:
        exitcode = is_not_ok(systemctl.ignore_modules(*modules))
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
        print_str(systemctl.get_status_file_path(*modules))
    elif command in ["__get_status_pid_file", "__get_pid_file"]:
        print_str(systemctl.get_status_pid_file(*modules))
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
        error_("Unknown operation "+command)
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
                  help="Connect to system manager (default)")  # overrides --user
    _o.add_option("--user", action="store_true", default=_user_mode,
                  help="Connect to user service manager")
    # _o.add_option("-H", "--host", metavar="[USER@]HOST",
    #     help="Operate on remote host*")
    # _o.add_option("-M", "--machine", metavar="CONTAINER",
    #     help="Operate on local container*")
    _o.add_option("-t", "--type", metavar="TYPE", dest="unit_type", default=_unit_type,
                  help="List units of a particual type")
    _o.add_option("--state", metavar="STATE", default=_unit_state,
                  help="List units with particular LOAD or SUB or ACTIVE state")
    _o.add_option("-p", "--property", metavar="NAME", dest="unit_property", default=_unit_property,
                  help="Show only properties by this name")
    _o.add_option("--what", metavar="TYPE", dest="what_kind", default=_what_kind,
                  help="Defines the service directories to be cleaned (configuration, state, cache, logs, runtime)")
    _o.add_option("-a", "--all", action="store_true", dest="show_all", default=_show_all,
                  help="Show all loaded units/properties, including dead empty ones. To list all units installed on the system, use the 'list-unit-files' command instead")
    _o.add_option("-l", "--full", action="store_true", default=_full,
                  help="Don't ellipsize unit names on output (never ellipsized)")
    _o.add_option("--reverse", action="store_true",
                  help="Show reverse dependencies with 'list-dependencies' (ignored)")
    _o.add_option("--job-mode", metavar="MODE",
                  help="Specifiy how to deal with already queued jobs, when queuing a new job (ignored)")
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
    logging.basicConfig(level=max(0, logging.FATAL - 10 * opt.verbose))
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
    _unit_state = opt.state
    _unit_type = opt.unit_type
    _unit_property = opt.unit_property
    _what_kind = opt.what_kind
    # being PID 1 (or 0) in a container will imply --init
    _pid = os.getpid()
    _init = opt.init or _pid in [ 1, 0 ]
    _user_mode = opt.user
    if os.geteuid() and _pid in [ 1, 0 ]:
        _user_mode = True
    if opt.system:
        _user_mode = False  # override --user
    #
    config_globals(opt.config)
    #
    systemctl_debug_log = os_path(_root, expand_path(SystemctlDebugLog, not _user_mode))
    systemctl_extra_log = os_path(_root, expand_path(SystemctlExtraLog, not _user_mode))
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
        args = [ "version" ]
    if not args:
        if _init:
            args = [ "default" ]
        else:
            args = [ "list-units" ]
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
