#! /usr/bin/python3
## type hints are provided in 'types/systemctl3.pyi'

from __future__ import print_function

__copyright__ = "(C) 2016-2019 Guido U. Draheim, licensed under the EUPL"
__version__ = "1.5.3420"

import logging
logg = logging.getLogger("systemctl")

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
import fcntl

if sys.version[0] == '3':
    basestring = str
    xrange = range

DEBUG_AFTER = False
DEBUG_STATUS = False
DEBUG_BOOTTIME = True
DEBUG_INITLOOP = False
DEBUG_KILLALL = False

NOT_A_PROBLEM = 0   # FOUND_OK
NOT_OK = 1          # FOUND_ERROR
NOT_ACTIVE = 2      # FOUND_INACTIVE
NOT_FOUND = 4       # FOUND_UNKNOWN

# defaults for options
_extra_vars = []
_force = False
_full = False
_now = False
_no_legend = False
_no_ask_password = False
_preset_mode = "all"
_quiet = False
_root = ""
_unit_type = None
_unit_state = None
_unit_property = None
_show_all = False
_user_mode = False

# common default paths
_system_folder1 = "/etc/systemd/system"
_system_folder2 = "/var/run/systemd/system"
_system_folder3 = "/usr/lib/systemd/system"
_system_folder4 = "/lib/systemd/system"
_system_folder9 = None
_user_folder1 = "~/.config/systemd/user"
_user_folder2 = "/etc/systemd/user"
_user_folder3 = "~.local/share/systemd/user"
_user_folder4 = "/usr/lib/systemd/user"
_user_folder9 = None
_init_folder1 = "/etc/init.d"
_init_folder2 = "/var/run/init.d"
_init_folder9 = None
_preset_folder1 = "/etc/systemd/system-preset"
_preset_folder2 = "/var/run/systemd/system-preset"
_preset_folder3 = "/usr/lib/systemd/system-preset"
_preset_folder4 = "/lib/systemd/system-preset"
_preset_folder9 = None

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

ExitWhenNoMoreServices = False
ExitWhenNoMoreProcs = False
DefaultUnit = os.environ.get("SYSTEMD_DEFAULT_UNIT", "default.target") # systemd.exe --unit=default.target
DefaultTarget = os.environ.get("SYSTEMD_DEFAULT_TARGET", "multi-user.target") # DefaultUnit fallback
# LogLevel = os.environ.get("SYSTEMD_LOG_LEVEL", "info") # systemd.exe --log-level
# LogTarget = os.environ.get("SYSTEMD_LOG_TARGET", "journal-or-kmsg") # systemd.exe --log-target
# LogLocation = os.environ.get("SYSTEMD_LOG_LOCATION", "no") # systemd.exe --log-location
# ShowStatus = os.environ.get("SYSTEMD_SHOW_STATUS", "auto") # systemd.exe --show-status
# DefaultStandardOutput=os.environ.get("SYSTEMD_STANDARD_OUTPUT", "journal") # systemd.exe --default-standard-output
# DefaultStandardError=os.environ.get("SYSTEMD_STANDARD_ERROR", "inherit") # systemd.exe --default-standard-error

EXEC_SPAWN = False
REMOVE_LOCK_FILE = False
BOOT_PID_MIN = 0
BOOT_PID_MAX = -9
PROC_MAX_DEPTH = 100
EXPAND_VARS_MAXDEPTH = 20
EXPAND_KEEP_VARS = True
RESTART_FAILED_UNITS = True

# The systemd default is NOTIFY_SOCKET="/var/run/systemd/notify"
_notify_socket_folder = "/var/run/systemd" # alias /run/systemd
_pid_file_folder = "/var/run"
_journal_log_folder = "/var/log/journal"

SYSTEMCTL_DEBUG_LOG = "/var/log/systemctl.debug.log"
SYSTEMCTL_EXTRA_LOG = "/var/log/systemctl.log"

_default_targets = [ "poweroff.target", "rescue.target", "sysinit.target", "basic.target", "multi-user.target", "graphical.target", "reboot.target" ]
_feature_targets = [ "network.target", "remote-fs.target", "local-fs.target", "timers.target", "nfs-client.target" ]
_all_common_targets = [ "default.target" ] + _default_targets + _feature_targets

# inside a docker we pretend the following
_all_common_enabled = [ "default.target", "multi-user.target", "remote-fs.target" ]
_all_common_disabled = [ "graphical.target", "resue.target", "nfs-client.target" ]

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
def unit_of(module):
    if "." not in module:
        return module + ".service"
    return module
def o22(part):
    if isinstance(part, basestring):
        if len(part) <= 22:
            return part
        return part[:5] + "..." + part[-14:]
    return part
def o99(part, shorter=0):
    if isinstance(part, basestring):
        if len(part) <= 99:
            return part
        return part[:20] + "-.-" + part[-(75-shorter):]
    return part

def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(root, path)
def path_replace_extension(path, old, new):
    if path.endswith(old):
        path = path[:-len(old)]
    return path + new

def os_getlogin():
    """ NOT using os.getlogin() """
    import pwd
    return pwd.getpwuid(os.geteuid()).pw_name

def get_runtime_dir():
    explicit = os.environ.get("XDG_RUNTIME_DIR", "")
    if explicit: return explicit
    user = os_getlogin()
    return "/tmp/run-"+user

def get_home():
    explicit = os.environ.get("HOME", "")
    if explicit: return explicit
    return os.path.expanduser("~")

def _var_path(path):
    """ assumes that the path starts with /var - when in 
        user mode it shall be moved to /run/user/1001/run/
        or as a fallback path to /tmp/run-{user}/ so that
        you may find /var/log in /tmp/run-{user}/log .."""
    if path.startswith("/var"): 
        runtime = get_runtime_dir() # $XDG_RUNTIME_DIR
        if not os.path.isdir(runtime):
            os.makedirs(runtime)
            os.chmod(runtime, 0o700)
        return re.sub("^(/var)?", get_runtime_dir(), path)
    return path


def shutil_setuid(user = None, group = None, xgroups = None):
    """ set fork-child uid/gid (returns pw-info env-settings)"""
    if group:
        import grp
        gid = grp.getgrnam(group).gr_gid
        os.setgid(gid)
        logg.debug("setgid %s '%s'", gid, group)
    if user:
        import pwd
        import grp
        pw = pwd.getpwnam(user)
        gid = pw.pw_gid
        gname = grp.getgrgid(gid).gr_name
        if not group:
            os.setgid(gid)
            logg.debug("setgid %s", gid)
        groups = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
        if xgroups:
            groups += [g.gr_gid for g in grp.getgrall() if g.gr_name in xgroups and g.gr_gid not in groups]
        if groups:
            os.setgroups(groups)
        uid = pw.pw_uid
        os.setuid(uid)
        logg.debug("setuid %s '%s'", uid, user)
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
    if pid is None:
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
    check = "/proc/%s/status" % pid
    try:
        for line in open(check):
            if line.startswith("State:"):
                return "Z" in line
    except IOError as e:
        if e.errno != errno.ENOENT:
            logg.error("%s (%s): %s", check, e.errno, e)
        return False
    return False

def checkstatus(cmd):
    if cmd.startswith("-"):
        return False, cmd[1:]
    else:
        return True, cmd

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
        self.set("Unit", "SourcePath", filename)
        description = self.get("init.d", "Description", "")
        if description:
            self.set("Unit", "Description", description)
        check = self.get("init.d", "Required-Start","")
        if check:
            for item in check.split(" "):
                if item.strip() in _sysv_mappings:
                    self.set("Unit", "Requires", _sysv_mappings[item.strip()])
        provides = self.get("init.d", "Provides", "")
        if provides:
            self.set("Install", "Alias", provides)
        # if already in multi-user.target then start it there.
        runlevels = self.getstr("init.d", "Default-Start","3 5")
        for item in runlevels.split(" "):
            if item.strip() in _runlevel_mappings:
                self.set("Install", "WantedBy", _runlevel_mappings[item.strip()])
        self.set("Service", "Restart", "no")
        self.set("Service", "TimeoutSec", strE(DefaultMaximumTimeout))
        self.set("Service", "KillMode", "process")
        self.set("Service", "GuessMainPID", "no")
        # self.set("Service", "RemainAfterExit", "yes")
        # self.set("Service", "SuccessExitStatus", "5 6")
        self.set("Service", "ExecStart", filename + " start")
        self.set("Service", "ExecStop", filename + " stop")
        if description: # LSB style initscript
            self.set("Service", "ExecReload", filename + " reload")
        self.set("Service", "Type", "forking") # not "sysv" anymore

# UnitConfParser = ConfigParser.RawConfigParser
UnitConfParser = SystemctlConfigParser

class SystemctlConf:
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
    def os_path_var(self, path):
        if self._user_mode:
            return os_path(self._root, _var_path(path))
        return os_path(self._root, path)
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
    def __init__(self, conf):
        self.conf = conf # currently unused
        self.opened = -1
        self.lockfolder = conf.os_path_var(_notify_socket_folder)
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
                    logg.debug("[%s] %s. trying %s _______ ", os.getpid(), attempt, lockname)
                    fcntl.flock(self.opened, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    st = os.fstat(self.opened)
                    if not st.st_nlink:
                        logg.debug("[%s] %s. %s got deleted, trying again", os.getpid(), attempt, lockname)
                        os.close(self.opened)
                        self.opened = os.open(lockfile, os.O_RDWR | os.O_CREAT, 0o600)
                        continue
                    content = "{ 'systemctl': %s, 'lock': '%s' }\n" % (os.getpid(), lockname)
                    os.write(self.opened, content.encode("utf-8"))
                    logg.debug("[%s] %s. holding lock on %s", os.getpid(), attempt, lockname)
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
        #TODO# raise Exception("no lock for %s", self.unit or "global")
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
        if pid is None: # unknown $MAINPID
            if not waitpid.returncode:
                logg.error("waitpid %s did return %s => correcting as 11", cmd, waitpid.returncode)
            waitpid = waitpid_result(waitpid.pid, 11, waitpid.signal)
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

parse_result = collections.namedtuple("UnitName", ["name", "prefix", "instance", "suffix", "component" ])

def parse_unit(name): # -> object(prefix, instance, suffix, ...., name, component)
    unit_name, suffix = name, ""
    has_suffix = name.rfind(".")
    if has_suffix > 0: 
        unit_name = name[:has_suffix]
        suffix = name[has_suffix+1:]
    prefix, instance = unit_name, ""
    has_instance = unit_name.find("@")
    if has_instance > 0:
        prefix = unit_name[:has_instance]
        instance = unit_name[has_instance+1:]
    component = ""
    has_component = prefix.rfind("-")
    if has_component > 0: 
        component = prefix[has_component+1:]
    return parse_result(name, prefix, instance, suffix, component)

def time_to_seconds(text, maximum = None):
    if maximum is None:
        maximum = DefaultMaximumTimeout
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
    beforelist = conf.getlist("Unit", "Before", [])
    for befores in beforelist:
        for before in befores.split(" "):
            name = before.strip()
            if name and name not in result:
                result.append(name)
    return result

def getAfter(conf):
    result = []
    afterlist = conf.getlist("Unit", "After", [])
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
    sortlist = [ SortTuple(0, conf) for conf in conflist]
    for check in xrange(len(sortlist)): # maxrank = len(sortlist)
        changed = 0
        for A in xrange(len(sortlist)):
            for B in xrange(len(sortlist)):
                if A != B:
                    itemA = sortlist[A]
                    itemB = sortlist[B]
                    before = compareAfter(itemA.conf, itemB.conf)
                    if before > 0 and itemA.rank <= itemB.rank:
                        if DEBUG_AFTER: # pragma: no cover
                            logg.info("  %-30s before %s", itemA.conf.name(), itemB.conf.name())
                        itemA.rank = itemB.rank + 1
                        changed += 1
                    if before < 0 and itemB.rank <= itemA.rank:
                        if DEBUG_AFTER: # pragma: no cover
                            logg.info("  %-30s before %s", itemB.conf.name(), itemA.conf.name())
                        itemB.rank = itemA.rank + 1
                        changed += 1
        if not changed:
            if DEBUG_AFTER: # pragma: no cover
                logg.info("done in check %s of %s", check, len(sortlist))
            break
            # because Requires is almost always the same as the After clauses
            # we are mostly done in round 1 as the list is in required order
    for conf in conflist:
        if DEBUG_AFTER: # pragma: no cover
            logg.debug(".. %s", conf.name())
    for item in sortlist:
        if DEBUG_AFTER: # pragma: no cover
            logg.info("(%s) %s", item.rank, item.conf.name())
    sortedlist = sorted(sortlist, key = lambda item: -item.rank)
    for item in sortedlist:
        if DEBUG_AFTER: # pragma: no cover
            logg.info("[%s] %s", item.rank, item.conf.name())
    return [ item.conf for item in sortedlist ]

class Systemctl:
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
        self._unit_property = _unit_property
        self._unit_state = _unit_state
        self._unit_type = _unit_type
        # some common constants that may be changed
        self._systemd_version = SystemCompatibilityVersion
        self._pid_file_folder = _pid_file_folder 
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
            if path.strip(): yield os.path.expanduser(path.strip())
        if SYSTEMD_PRESET_PATH.endswith(":"):
            if _preset_folder1: yield _preset_folder1
            if _preset_folder2: yield _preset_folder2
            if _preset_folder3: yield _preset_folder3
            if _preset_folder4: yield _preset_folder4
            if _preset_folder9: yield _preset_folder9
    def init_folders(self):
        SYSTEMD_SYSVINIT_PATH = self.get_SYSTEMD_SYSVINIT_PATH()
        for path in SYSTEMD_SYSVINIT_PATH.split(":"):
            if path.strip(): yield os.path.expanduser(path.strip())
        if SYSTEMD_SYSVINIT_PATH.endswith(":"):
            if _init_folder1: yield _init_folder1
            if _init_folder2: yield _init_folder2
            if _init_folder9: yield _init_folder9
    def user_folders(self):
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH()
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield os.path.expanduser(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            if _user_folder1: yield os.path.expanduser(_user_folder1)
            if _user_folder2: yield os.path.expanduser(_user_folder2)
            if _user_folder3: yield os.path.expanduser(_user_folder3)
            if _user_folder4: yield os.path.expanduser(_user_folder4)
            if _user_folder9: yield os.path.expanduser(_user_folder9)
    def system_folders(self):
        SYSTEMD_UNIT_PATH = self.get_SYSTEMD_UNIT_PATH()
        for path in SYSTEMD_UNIT_PATH.split(":"):
            if path.strip(): yield os.path.expanduser(path.strip())
        if SYSTEMD_UNIT_PATH.endswith(":"):
            if _system_folder1: yield _system_folder1
            if _system_folder2: yield _system_folder2
            if _system_folder3: yield _system_folder3
            if _system_folder4: yield _system_folder4
            if _system_folder9: yield _system_folder9
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
        if not conf:
            return False # no such conf >> ignored
        filename = conf.nonloaded_path or conf.filename()
        if filename and "/user/" in filename:
            return True
        return False
    def not_user_conf(self, conf):
        """ conf can not be started as user service (when --user)"""
        if not conf:
            return True # no such conf >> ignored
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
            return self.load_sysd_unit_conf(service)
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
        data.set("Unit", "Description", description or ("NOT-FOUND " + str(module)))
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
        if module.endswith(".service"):
            return "service"
        if module.endswith(".socket"):
            return "socket"
        if module.endswith(".target"):
            return "target"
        return None
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
            if not modules:
                yield item
            elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                yield item
            elif [ module for module in modules if module+suffix == item ]:
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
            elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                yield item
            elif [ module for module in modules if module+suffix == item ]:
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
            result += [ (name, "SysD", value) ]
        for name, value in self._file_for_unit_sysv.items():
            result += [ (name, "SysV", value) ]
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
            if self._unit_state:
                if self._unit_state not in [ result[unit], active[unit], substate[unit] ]:
                    del result[unit]
        return [ (unit, result[unit] + " " + active[unit] + " " + substate[unit], description[unit]) for unit in sorted(result) ]
    def show_list_units(self, *modules): # -> [ (unit,loaded,description) ]
        """ [PATTERN]... -- List loaded units.
        If one or more PATTERNs are specified, only units matching one of 
        them are shown. NOTE: This is the default command."""
        hint = "To show all installed unit files use 'systemctl list-unit-files'."
        result = self.list_service_units(*modules)
        if self._no_legend:
            return result
        found = "%s loaded units listed." % len(result)
        return result + [ ("", "", ""), (found, "", ""), (hint, "", "") ]
    def list_service_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """ show all the service units and the enabled status"""
        logg.debug("list service unit files for %s", modules)
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
                logg.warning("list-units: %s", e)
        return [ (unit, enabled[unit]) for unit in sorted(result) if result[unit] ]
    def each_target_file(self):
        folders = self.system_folders()
        if self.user_mode():
            folders = self.user_folders()
        for folder in folders:
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
        return [ (unit, enabled[unit]) for unit in sorted(targets) ]
    def show_list_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """[PATTERN]... -- List installed unit files
        List installed unit files and their enablement state (as reported
        by is-enabled). If one or more PATTERNs are specified, only units
        whose filename (just the last component of the path) matches one of
        them are shown. This command reacts to limitations of --type being
        --type=service or --type=target (and --now for some basics)."""
        result = []
        if self._now:
            basics = self.list_service_unit_basics()
            result = [ (name, sysv + " " + filename) for name, sysv, filename in basics ]
        elif self._unit_type == "target":
            result = self.list_target_unit_files()
        elif self._unit_type == "service":
            result = self.list_service_unit_files()
        elif self._unit_type:
            logg.warning("unsupported unit --type=%s", self._unit_type)
        else:
            result = self.list_target_unit_files()
            result += self.list_service_unit_files(*modules)
        if self._no_legend:
            return result
        found = "%s unit files listed." % len(result)
        return [ ("UNIT FILE", "STATE") ] + result + [ ("", ""), (found, "") ]
    ##
    ##
    def get_description(self, unit, default = None):
        return self.get_description_from(self.load_unit_conf(unit))
    def get_description_from(self, conf, default = None): # -> text
        """ Unit.Description could be empty sometimes """
        if not conf: return default or ""
        description = conf.get("Unit", "Description", default or "")
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
    def test_pid_file(self, unit): # -> text
        """ support for the testsuite.py """
        conf = self.get_unit_conf(unit)
        return self.pid_file_from(conf) or self.status_file_from(conf)
    def pid_file_from(self, conf, default = ""):
        """ get the specified pid file path (not a computed default) """
        pid_file = conf.get("Service", "PIDFile", default)
        return self.expand_special(pid_file, conf)
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
        return self.status_file_from(conf)
    def status_file_from(self, conf, default = None):
        if default is None:
           default = self.default_status_file(conf)
        if conf is None: return default
        status_file = conf.get("Service", "StatusFile", default)
        # this not a real setting, but do the expand_special anyway
        return self.expand_special(status_file, conf)
    def default_status_file(self, conf): # -> text
        """ default file pattern where to store a status mark """
        folder = conf.os_path_var(self._pid_file_folder)
        name = "%s.status" % conf.name()
        return os.path.join(folder, name)
    def clean_status_from(self, conf):
        status_file = self.status_file_from(conf)
        if os.path.exists(status_file):
            os.remove(status_file)
        conf.status = {}
    def write_status_from(self, conf, **status): # -> bool(written)
        """ if a status_file is known then path is created and the
            give status is written as the only content. """
        status_file = self.status_file_from(conf)
        if not status_file: 
            logg.debug("status %s but no status_file", conf.name())
            return False
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
    def read_status_from(self, conf, defaults = None):
        status_file = self.status_file_from(conf)
        status = {}
        if defaults is not None:
           for key in defaults.keys():
               status[key] = defaults[key]
        elif isinstance(defaults, basestring):
           status["ActiveState"] = defaults
        if not status_file:
            if DEBUG_STATUS: logg.debug("no status file. returning %s", status)
            return status
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
                    else: #pragma: no cover
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
            proc = "/proc/%s/stat" % pid
            try:
                if os.path.exists(proc):
                    # return os.path.getmtime(proc) # did sometimes change
                    return self.path_proc_started(proc)
            except Exception as e: # pragma: no cover
                logg.warning("could not access %s: %s", proc, e)
        if DEBUG_BOOTTIME:
            logg.debug(" boottime from the oldest entry in /proc [nothing in %s..%s]", pid1, pid_max)
        booted = time.time()
        for name in os.listdir("/proc"):
            proc = "/proc/%s/stat" % name
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
    def get_proc_started(self, pid):
        proc = "/proc/%s/status" % pid
        return self.path_proc_started(proc)
    def path_proc_started(self, proc):
        #get time process started after boot in clock ticks
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
        system_uptime = "/proc/uptime"
        with open(system_uptime,"rb") as file_uptime:
            data_uptime = file_uptime.readline()
        file_uptime.close()
        uptime_data = data_uptime.decode().split()
        uptime_secs = float(uptime_data[0])
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 1. System uptime secs: %.3f (%s)", uptime_secs, system_uptime)

        #get time now
        now = time.time()
        started_time = now - (uptime_secs - started_secs)
        if DEBUG_BOOTTIME:
            logg.debug("  BOOT 1. Proc has been running since: %s" % (datetime.datetime.fromtimestamp(started_time)))

        # Variant 2:
        system_stat = "/proc/stat"
        system_btime = 0.
        with open(system_stat,"rb") as f:
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
        if not filename:
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
            logg.info("while reading %s: %s", env_file, e)
    def read_env_part(self, env_part): # -> generate[ (name, value) ]
        """ Environment=<name>=<value> is being scanned """
        ## systemd Environment= spec says it is a space-seperated list of 
        ## assignments. In order to use a space or an equals sign in a value 
        ## one should enclose the whole assignment with double quotes: 
        ##    Environment="VAR1=word word" VAR2=word3 "VAR3=$word 5 6"
        ## and the $word is not expanded by other environment variables.
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
    def show_environment(self, unit):
        """ [UNIT]. -- show environment parts """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("Unit %s could not be found.", unit)
            return False
        if _unit_property:
            return conf.getlist("Service", _unit_property)
        return self.get_env(conf)
    def extra_vars(self):
        return self._extra_vars # from command line
    def get_env(self, conf):
        env = os.environ.copy()
        for env_part in conf.getlist("Service", "Environment", []):
            for name, value in self.read_env_part(self.expand_special(env_part, conf)):
                env[name] = value # a '$word' is not special here (lazy expansion)
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
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
        expanded = re.sub("[$](\w+)", lambda m: get_env1(m), cmd.replace("\\\n",""))
        for depth in xrange(maxdepth):
            new_text = re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), expanded)
            if new_text == expanded:
                return expanded
            expanded = new_text
        logg.error("shell variable expansion exceeded maxdepth %s", maxdepth)
        return expanded
    def expand_special(self, cmd, conf = None):
        """ expand %i %t and similar special vars. They are being expanded
            before any other expand_env takes place which handles shell-style
            $HOME references. """
        def sh_escape(value):
            return "'" + value.replace("'","\\'") + "'"
        def get_confs(conf):
            confs={ "%": "%" }
            if not conf:
                return confs
            unit = parse_unit(conf.name())
            confs["N"] = unit.name
            confs["n"] = sh_escape(unit.name)
            confs["P"] = unit.prefix
            confs["p"] = sh_escape(unit.prefix)
            confs["I"] = unit.instance
            confs["i"] = sh_escape(unit.instance)
            confs["J"] = unit.component
            confs["j"] = sh_escape(unit.component)
            confs["f"] = sh_escape(strE(conf.filename()))
            VARTMP = "/var/tmp"
            TMP = "/tmp"
            RUN = "/run"
            DAT = "/var/lib"
            LOG = "/var/log"
            CACHE = "/var/cache"
            CONFIG = "/etc"
            HOME = "/root"
            USER = "root"
            UID = 0
            SHELL = "/bin/sh"
            if self.is_user_conf(conf):
                USER = os_getlogin()
                HOME = get_home()
                RUN = os.environ.get("XDG_RUNTIME_DIR", get_runtime_dir())
                CONFIG = os.environ.get("XDG_CONFIG_HOME", HOME + "/.config")
                CACHE = os.environ.get("XDG_CACHE_HOME", HOME + "/.cache")
                SHARE = os.environ.get("XDG_DATA_HOME", HOME + "/.local/share")
                DAT = CONFIG
                LOG = os.path.join(CONFIG, "log")
                SHELL = os.environ.get("SHELL", SHELL)
                VARTMP = os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", VARTMP)))
                TMP = os.environ.get("TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", TMP)))
            confs["V"] = os_path(self._root, VARTMP)
            confs["T"] = os_path(self._root, TMP)
            confs["t"] = os_path(self._root, RUN)
            confs["S"] = os_path(self._root, DAT)
            confs["s"] = SHELL
            confs["h"] = HOME
            confs["u"] = USER
            confs["C"] = os_path(self._root, CACHE)
            confs["E"] = os_path(self._root, CONFIG)
            return confs
        def get_conf1(m):
            confs = get_confs(conf)
            if m.group(1) in confs:
                return confs[m.group(1)]
            logg.warning("can not expand %%%s", m.group(1))
            return "''" # empty escaped string
        return re.sub("[%](.)", lambda m: get_conf1(m), cmd)
    def exec_cmd(self, cmd, env, conf = None):
        """ expand ExecCmd statements including %i and $MAINPID """
        cmd1 = cmd.replace("\\\n","")
        # according to documentation the %n / %% need to be expanded where in
        # most cases they are shell-escaped values. So we do it before shlex.
        cmd2 = self.expand_special(cmd1, conf)
        # according to documentation, when bar="one two" then the expansion
        # of '$bar' is ["one","two"] and '${bar}' becomes ["one two"]. We
        # tackle that by expand $bar before shlex, and the rest thereafter.
        def get_env1(m):
            if m.group(1) in env:
                return env[m.group(1)]
            logg.debug("can not expand $%s", m.group(1))
            return "" # empty string
        def get_env2(m):
            if m.group(1) in env:
                return env[m.group(1)]
            logg.debug("can not expand ${%s}", m.group(1))
            return "" # empty string
        cmd3 = re.sub("[$](\w+)", lambda m: get_env1(m), cmd2)
        newcmd = []
        for part in shlex.split(cmd3):
            newcmd += [ re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), part) ]
        return newcmd
    def path_journal_log(self, conf): # never None
        """ /var/log/zzz.service.log or /var/log/default.unit.log """
        filename = os.path.basename(strE(conf.filename()))
        unitname = (conf.name() or "default")+".unit"
        name = filename or unitname
        log_folder = conf.os_path_var(self._journal_log_folder)
        log_file = name.replace(os.path.sep,".") + ".log"
        if log_file.startswith("."):
            log_file = "dot."+log_file
        return os.path.join(log_folder, log_file)
    def open_journal_log(self, conf):
        log_file = self.path_journal_log(conf)
        log_folder = os.path.dirname(log_file)
        if not os.path.isdir(log_folder):
            os.makedirs(log_folder)
        return open(os.path.join(log_file), "a")
    def get_WorkingDirectory(self, conf):
        return conf.get("Service", "WorkingDirectory", "")
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
               logg.debug("chdir workingdir '%s'", into)
               os.chdir(into)
               return False
            except Exception as e:
               if not ignore:
                   logg.error("chdir workingdir '%s': %s", into, e)
                   return into
               else:
                   logg.debug("chdir workingdir '%s': %s", into, e)
                   return None
        return None
    NotifySocket = collections.namedtuple("NotifySocket", ["socket", "socketfile" ])
    def notify_socket_from(self, conf, socketfile = None):
        """ creates a notify-socket for the (non-privileged) user """
        notify_socket_folder = conf.os_path_var(_notify_socket_folder)
        notify_name = "notify." + str(conf.name() or "systemctl")
        notify_socket = os.path.join(notify_socket_folder, notify_name)
        socketfile = socketfile or notify_socket
        if len(socketfile) > 100:
            logg.debug("https://unix.stackexchange.com/questions/367008/%s",
                       "why-is-socket-path-length-limited-to-a-hundred-chars")
            logg.debug("old notify socketfile (%s) = %s", len(socketfile), socketfile)
            notify_socket_folder = re.sub("^(/var)?", get_runtime_dir(), _notify_socket_folder)
            notify_name = o99(notify_name, len(notify_socket_folder))
            socketfile = os.path.join(notify_socket_folder, notify_name)
            # occurs during testsuite.py for ~user/test.tmp/root path
            logg.info("new notify socketfile (%s) = %s", len(socketfile), socketfile)
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
                result_txt = result.replace("\n","|")
                result_len = len(result)
                logg.debug("read_notify_socket(%s):%s", result_len, result_txt)
        except socket.timeout as e:
            if timeout > 2:
                logg.debug("socket.timeout %s", e)
        return result
    def wait_notify_socket(self, notify, timeout, pid = None):
        if not os.path.exists(notify.socketfile):
            logg.info("no $NOTIFY_SOCKET exists")
            return {}
        #
        logg.info("wait $NOTIFY_SOCKET, timeout %s", timeout)
        results = {}
        seenREADY = None
        for attempt in xrange(int(timeout)+1):
            if pid and not self.is_active_pid(pid):
                logg.info("dead PID %s", pid)
                return results
            if not attempt: # first one
                time.sleep(1) # until TimeoutStartSec
                continue
            result = self.read_notify_socket(notify, 1) # sleep max 1 second
            if not result: # timeout
                time.sleep(1) # until TimeoutStartSec
                continue
            for name, value in self.read_env_part(result):
                results[name] = value
                if name == "READY":
                    seenREADY = value
                if name in ["STATUS", "ACTIVESTATE"]:
                    logg.debug("%s: %s", name, value) # TODO: update STATUS -> SubState
            if seenREADY:
                break
        if not seenREADY:
            logg.info(".... timeout while waiting for 'READY=1' status on $NOTIFY_SOCKET")
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
                    units += [ unit ]
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
        timeout = conf.get("Service", "TimeoutSec", strE(DefaultTimeoutStartSec))
        timeout = conf.get("Service", "TimeoutStartSec", timeout)
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def get_SocketTimeoutSec(self, conf):
        timeout = conf.get("Socket", "TimeoutSec", strE(DefaultTimeoutStartSec))
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def get_RemainAfterExit(self, conf):
        return conf.getbool("Service", "RemainAfterExit", "no")
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
        else:
            logg.error("start not implemented for unit type: %s", conf.name())
            return False
    def do_start_service_from(self, conf):
        timeout = self.get_TimeoutStartSec(conf)
        doRemainAfterExit = self.get_RemainAfterExit(conf)
        runs = conf.get("Service", "Type", "simple").lower()
        env = self.get_env(conf)
        self.exec_check_service(conf, env, "Exec") # all...
        # for StopPost on failure:
        returncode = 0
        service_result = "success"
        if True:
            if runs in [ "simple", "forking", "notify" ]:
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
            for cmd in conf.getlist("Service", "ExecStartPre", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info(" pre-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: 
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug(" pre-start done (%s) <-%s>",
                    run.returncode or "OK", run.signal or "")
                if run.returncode and check:
                    logg.error("the ExecStartPre control process exited with error code")
                    active = "failed"
                    self.write_status_from(conf, AS=active )
                    return False
        if runs in [ "oneshot" ]:
            status_file = self.status_file_from(conf)
            if self.get_status_from(conf, "ActiveState", "unknown") == "active":
                logg.warning("the service was already up once")
                return True
            for cmd in conf.getlist("Service", "ExecStart", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                run = subprocess_waitpid(forkpid)
                if run.returncode and check: 
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
        elif runs in [ "simple" ]: 
            status_file = self.status_file_from(conf)
            pid = self.read_mainpid_from(conf)
            if self.is_active_pid(pid):
                logg.warning("the service is already running on PID %s", pid)
                return True
            if doRemainAfterExit:
                logg.debug("%s RemainAfterExit -> AS=active", runs)
                self.write_status_from(conf, AS="active")
            cmdlist = conf.getlist("Service", "ExecStart", [])
            for idx, cmd in enumerate(cmdlist):
                logg.debug("ExecStart[%s]: %s", idx, cmd)
            for cmd in cmdlist:
                pid = self.read_mainpid_from(conf)
                env["MAINPID"] = strE(pid)
                newcmd = self.exec_cmd(cmd, env, conf)
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
                    if run.returncode:
                        service_result = "failed"
                        break
        elif runs in [ "notify" ]:
            # "notify" is the same as "simple" but we create a $NOTIFY_SOCKET 
            # and wait for startup completion by checking the socket messages
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
            cmdlist = conf.getlist("Service", "ExecStart", [])
            for idx, cmd in enumerate(cmdlist):
                logg.debug("ExecStart[%s]: %s", idx, cmd)
            mainpid = None
            for cmd in cmdlist:
                mainpid = self.read_mainpid_from(conf)
                env["MAINPID"] = strE(mainpid)
                newcmd = self.exec_cmd(cmd, env, conf)
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
                    if run.returncode:
                        service_result = "failed"
                        break
            if service_result in [ "success" ] and mainpid:
                logg.debug("okay, wating on socket for %ss", timeout)
                results = self.wait_notify_socket(notify, timeout, mainpid)
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
        elif runs in [ "forking" ]:
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecStart", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                if not newcmd: continue
                logg.info("%s start %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: # pragma: no cover
                    os.setsid() # detach child process from parent
                    self.execve_from(conf, newcmd, env)
                logg.info("%s started PID %s", runs, forkpid)
                run = subprocess_waitpid(forkpid)
                if run.returncode and check:
                    returncode = run.returncode
                    service_result = "failed"
                logg.info("%s stopped PID %s (%s) <-%s>", runs, run.pid, 
                    run.returncode or "OK", run.signal or "")
            if pid_file and service_result in [ "success" ]:
                pid = self.wait_pid_file(pid_file) # application PIDFile
                logg.info("%s start done PID %s [%s]", runs, pid, pid_file)
                if pid:
                    env["MAINPID"] = strE(pid)
            if not pid_file:
                time.sleep(MinimumTimeoutStartSec)
                logg.warning("No PIDFile for forking %s", strQ(conf.filename()))
                status_file = self.status_file_from(conf)
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
            for cmd in conf.getlist("Service", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-fail %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-fail done (%s) <-%s>", 
                    run.returncode or "OK", run.signal or "")
            return False
        else:
            for cmd in conf.getlist("Service", "ExecStartPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-start done (%s) <-%s>", 
                    run.returncode or "OK", run.signal or "")
            return True
    def get_socket_service_from(self, conf):
        socket_unit = conf.name()
        accept = conf.getbool("Socket", "Accept", "no")
        service_type = accept and "@.service" or ".service"
        service_name = path_replace_extension(socket_unit, ".socket", service_type)
        service_unit = conf.get("Socket", "Service", service_name)
        logg.debug("socket %s -> service %s", socket_unit, service_unit)
        return service_unit
    def do_start_socket_from(self, conf):
        runs = "socket"
        timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool("Socket", "Accept", "no")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None:
            logg.debug("unit could not be loaded (%s)", service_unit)
            logg.error("Unit %s not found.", service_unit)
            return False
        env = self.get_env(conf)
        if True:
            for cmd in conf.getlist("Socket", "ExecStartPre", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info(" pre-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid: 
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug(" pre-start done (%s) <-%s>",
                    run.returncode or "OK", run.signal or "")
                if run.returncode and check:
                    logg.error("the ExecStartPre control process exited with error code")
                    active = "failed"
                    self.write_status_from(conf, AS=active )
                    return False
        if not accept:
            # we do not listen but have the service started right away
            done = self.do_start_service_from(service_conf)
            service_result = done and "success" or "failed"
        else:
            service_result = "failed"
            logg.error("socket accept=yes is not implemented. sorry.")
        # POST sequence
        if not self.is_active_from(conf):
            logg.warning("%s start not active", runs)
            # according to the systemd documentation, a failed start-sequence
            # should execute the ExecStopPost sequence allowing some cleanup.
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist("Socket", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-fail %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-fail done (%s) <-%s>", 
                    run.returncode or "OK", run.signal or "")
            return False
        else:
            for cmd in conf.getlist("Socket", "ExecStartPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-start %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-start done (%s) <-%s>", 
                    run.returncode or "OK", run.signal or "")
            return True
        return False
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
        for var, val in self.read_env_file("/etc/locale.conf"):
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
        return self.expand_special(conf.get("Service", "User", ""), conf)
    def get_Group(self, conf):
        return self.expand_special(conf.get("Service", "Group", ""), conf)
    def get_SupplementaryGroups(self, conf):
        return self.expand_list(conf.getlist("Service", "SupplementaryGroups", []), conf)
    def execve_from(self, conf, cmd, env):
        """ this code is commonly run in a child process // returns exit-code"""
        runs = conf.get("Service", "Type", "simple").lower()
        logg.debug("%s process for %s", runs, strQ(conf.filename()))
        inp = open("/dev/zero")
        out = self.open_journal_log(conf)
        os.dup2(inp.fileno(), sys.stdin.fileno())
        os.dup2(out.fileno(), sys.stdout.fileno())
        os.dup2(out.fileno(), sys.stderr.fileno())
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
                cmd_args = [ arg for arg in cmd ] # satisfy mypy
                os.spawnvpe(os.P_WAIT, cmd[0], cmd_args, env)
                sys.exit(0)
            else: # pragma: no cover
                os.execve(cmd[0], cmd, env)
        except Exception as e:
            logg.error("(%s): %s", shell_cmd(cmd), e)
            sys.exit(1)
    def test_start_unit(self, unit):
        """ helper function to test the code that is normally forked off """
        conf = self.load_unit_conf(unit)
        if not conf: return None
        env = self.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            newcmd = self.exec_cmd(cmd, env, conf)
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
            logg.error("Unit %s not found.", unit)
            return False
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        return self.stop_unit_from(conf)

    def get_TimeoutStopSec(self, conf):
        timeout = conf.get("Service", "TimeoutSec", strE(DefaultTimeoutStartSec))
        timeout = conf.get("Service", "TimeoutStopSec", timeout)
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
        else:
            logg.error("stop not implemented for unit type: %s", conf.name())
            return False
    def do_stop_service_from(self, conf):
        timeout = self.get_TimeoutStopSec(conf)
        runs = conf.get("Service", "Type", "simple").lower()
        env = self.get_env(conf)
        self.exec_check_service(conf, env, "ExecStop")
        returncode = 0
        service_result = "success"
        if runs in [ "oneshot" ]:
            status_file = self.status_file_from(conf)
            if self.get_status_from(conf, "ActiveState", "unknown") == "inactive":
                logg.warning("the service is already down once")
                return True
            for cmd in conf.getlist("Service", "ExecStop", []):
                check, cmd = checkstatus(cmd)
                logg.debug("{env} %s", env)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and check: 
                    returncode = run.returncode
                    service_result = "failed"
                    break
            if True:
                if returncode:
                    self.set_status_from(conf, "ExecStopCode", strE(returncode))
                    self.write_status_from(conf, AS="failed")
                else:
                    self.clean_status_from(conf) # "inactive"
        ### fallback Stop => Kill for ["simple","notify","forking"]
        elif not conf.getlist("Service", "ExecStop", []):
            logg.info("no ExecStop => systemctl kill")
            if True:
                self.do_kill_unit_from(conf)
                self.clean_pid_file_from(conf)
                self.clean_status_from(conf) # "inactive"
        elif runs in [ "simple", "notify" ]:
            status_file = self.status_file_from(conf)
            size = os.path.exists(status_file) and os.path.getsize(status_file)
            logg.info("STATUS %s %s", status_file, size)
            pid = 0
            for cmd in conf.getlist("Service", "ExecStop", []):
                check, cmd = checkstatus(cmd)
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                run = must_have_failed(run, newcmd) # TODO: a workaround
                # self.write_status_from(conf, MainPID=run.pid) # no ExecStop
                if run.returncode and check:
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
        elif runs in [ "forking" ]:
            status_file = self.status_file_from(conf)
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecStop", []):
                # active = self.is_active_from(conf)
                if pid_file:
                    new_pid = self.read_mainpid_from(conf)
                    if new_pid:
                        env["MAINPID"] = strE(new_pid)
                check, cmd = checkstatus(cmd)
                logg.debug("{env} %s", env)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("fork stop %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if run.returncode and check:
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
            for cmd in conf.getlist("Service", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-stop %s", shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                logg.debug("post-stop done (%s) <-%s>", 
                    run.returncode or "OK", run.signal or "")
        return service_result == "success"
    def do_stop_socket_from(self, conf):
        runs = "socket"
        timeout = self.get_SocketTimeoutSec(conf)
        accept = conf.getbool("Socket", "Accept", "no")
        service_unit = self.get_socket_service_from(conf)
        service_conf = self.load_unit_conf(service_unit)
        if service_conf is None:
            logg.debug("unit could not be loaded (%s)", service_unit)
            logg.error("Unit %s not found.", service_unit)
            return False
        env = self.get_env(conf)
        if not accept:
            # we do not listen but have the service started right away
            done = self.do_stop_service_from(service_conf)
            service_result = done and "success" or "failed"
        else:
            service_result = "failed"
            logg.error("socket accept=yes is not implemented. sorry.")
        # POST sequence
        if not self.is_active_from(conf):
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist("Service", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
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
        logg.info("wait for PID %s to vanish (%ss)", pid, timeout)
        for x in xrange(int(timeout)):
            if not self.is_active_pid(pid):
                logg.info("wait for PID %s is done (%s.)", pid, x)
                return True
            time.sleep(1) # until TimeoutStopSec
        logg.info("wait for PID %s failed (%s.)", pid, x)
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
        else:
            logg.error("reload not implemented for unit type: %s", conf.name())
            return False
    def do_reload_service_from(self, conf):
        runs = conf.get("Service", "Type", "simple").lower()
        env = self.get_env(conf)
        self.exec_check_service(conf, env, "ExecReload")
        if runs in [ "simple", "notify", "forking" ]:
            if not self.is_active_from(conf):
                logg.info("no reload on inactive service %s", conf.name())
                return True
            for cmd in conf.getlist("Service", "ExecReload", []):
                env["MAINPID"] = strE(self.read_mainpid_from(conf))
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s reload %s", runs, shell_cmd(newcmd))
                forkpid = os.fork()
                if not forkpid:
                    self.execve_from(conf, newcmd, env) # pragma: no cover
                run = subprocess_waitpid(forkpid)
                if check and run.returncode: 
                    logg.error("Job for %s failed because the control process exited with error code. (%s)", 
                        conf.name(), run.returncode)
                    return False
            time.sleep(MinimumYield)
            return True
        elif runs in [ "oneshot" ]:
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
            logg.info(" restart unit %s => %s", conf.name(), strQ(conf.filename()))
            if not self.is_active_from(conf):
                return self.do_start_unit_from(conf)
            else:
                return self.do_restart_unit_from(conf)
    def do_restart_unit_from(self, conf):
        logg.info("(restart) => stop/start")
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
        elif conf.getlist("Service", "ExecReload", []):
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
        if conf.getlist("Service", "ExecReload", []):
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
        status_file = self.status_file_from(conf)
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
        if useKillMode in [ "control-group", "mixed" ]:
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
        # However: # TODO!!!!! BUG in original systemctl!!
        #   documentation says " exit code 0 if at least one is active"
        #   and "Unless --quiet is specified, print the unit state"
        units = []
        results = []
        for module in modules:
            units = self.match_units(to_list(module))
            if not units:
                logg.error("Unit %s not found.", unit_of(module))
                # self.error |= NOT_FOUND
                self.error |= NOT_ACTIVE
                results += [ "inactive" ]
                continue
            for unit in units:
                active = self.get_active_unit(unit) 
                enabled = self.enabled_unit(unit)
                if enabled != "enabled": 
                    active = "inactive" # "unknown"
                results += [ active ]
                break
        ## how it should work:
        status = "active" in results
        ## how 'systemctl' works:
        non_active = [ result for result in results if result != "active" ]
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
        status_file = self.status_file_from(conf)
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
        default_target = DefaultTarget
        sysinit_target = SysInitTarget
        if conf.name() in [ sysinit_target, "default.target", default_target ]:
            status = self.is_system_running()
            if status in [ "running" ]:
                return "active"
        return "inactive"
    def get_substate_from(self, conf):
        """ returns 'running' 'exited' 'dead' 'failed' 'plugged' 'mounted' """
        if not conf: return None
        pid_file = self.pid_file_from(conf)
        if pid_file:
            if not os.path.exists(pid_file):
                return "dead"
        status_file = self.status_file_from(conf)
        if self.getsize(status_file):
            state = self.get_status_from(conf, "ActiveState", "")
            if state:
                if state in [ "active" ]:
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
                results += [ "inactive" ]
                continue
            for unit in units:
                active = self.get_active_unit(unit) 
                enabled = self.enabled_unit(unit)
                if enabled != "enabled": 
                    active = "inactive"
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
        status_file = self.status_file_from(conf)
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
                    units += [ unit ]
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
    def system_preset_all(self, *modules):
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
        return conf.get("Install", "WantedBy", default, True)
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
                logg.info("matched %s", unit) #++
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
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            if self.user_mode():
                logg.error("Initscript %s not for --user mode", unit)
                return False
            return self.enable_unit_sysv(unit_file)
        conf = self.get_unit_conf(unit)
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        wanted = self.wanted_from(self.get_unit_conf(unit))
        if not wanted: 
            return False # "static" is-enabled
        folder = self.enablefolder(wanted)
        if self._root:
            folder = os_path(self._root, folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        if True:
            _f = self._force and "-f" or ""
            logg.info("ln -s {_f} '{unit_file}' '{target}'".format(**locals()))
        if self._force and os.path.islink(target):
            os.remove(target)
        if not os.path.islink(target):
            os.symlink(unit_file, target)
        return True
    def rc3_root_folder(self):
        old_folder = "/etc/rc3.d"
        new_folder = "/etc/init.d/rc3.d"
        if self._root:
            old_folder = os_path(self._root, old_folder)
            new_folder = os_path(self._root, new_folder)
        if os.path.isdir(old_folder): 
            return old_folder
        return new_folder
    def rc5_root_folder(self):
        old_folder = "/etc/rc5.d"
        new_folder = "/etc/init.d/rc5.d"
        if self._root:
            old_folder = os_path(self._root, old_folder)
            new_folder = os_path(self._root, new_folder)
        if os.path.isdir(old_folder): 
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
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            if self.user_mode():
                logg.error("Initscript %s not for --user mode", unit)
                return False
            return self.disable_unit_sysv(unit_file)
        conf = self.get_unit_conf(unit)
        if self.not_user_conf(conf):
            logg.error("Unit %s not for --user mode", unit)
            return False
        wanted = self.wanted_from(self.get_unit_conf(unit))
        if not wanted:
            return False # "static" is-enabled
        for folder in self.enablefolders(wanted):
            if self._root:
                folder = os_path(self._root, folder)
            target = os.path.join(folder, os.path.basename(unit_file))
            if os.path.isfile(target):
                try:
                    _f = self._force and "-f" or ""
                    logg.info("rm {_f} '{target}'".format(**locals()))
                    os.remove(target)
                except IOError as e:
                    logg.error("disable %s: %s", target, e)
                except OSError as e:
                    logg.error("disable %s: %s", target, e)
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
                    units += [ unit ]
        return self.is_enabled_units(units) # and found_all
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
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("Unit %s not found.", unit)
            return False
        if self.is_sysv_file(unit_file):
            return self.is_enabled_sysv(unit_file)
        wanted = self.wanted_from(self.get_unit_conf(unit))
        if not wanted:
            return True # "static"
        for folder in self.enablefolders(wanted):
            if self._root:
                folder = os_path(self._root, folder)
            target = os.path.join(folder, os.path.basename(unit_file))
            if os.path.isfile(target):
                return True
        return False
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
        if conf.masked:
            return "masked"
        wanted = self.wanted_from(conf)
        if not wanted:
            return "static"
        for folder in self.enablefolders(wanted):
            if self._root:
                folder = os_path(self._root, folder)
            target = os.path.join(folder, os.path.basename(unit_file))
            if os.path.isfile(target):
                return "enabled"
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
        if True:
            _f = self._force and "-f" or ""
            logg.debug("ln -s {_f} /dev/null '{target}'".format(**locals()))
        if self._force and os.path.islink(target):
            os.remove(target)
        if not os.path.exists(target):
            os.symlink("/dev/null", target)
            logg.info("Created symlink {target} -> /dev/null".format(**locals()))
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
            logg.debug("Symlink did exist anymore: %s", target)
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
                    units += [ unit ]
        return self.list_dependencies_units(units) # and found_all
    def list_dependencies_units(self, units):
        if self._now:
            return self.list_start_dependencies_units(units)
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
            for stop_recursion in [ "Conflict", "conflict", "reloaded", "Propagate" ]:
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
                restrict = ["Requires", "Requisite", "ConsistsOf", "Wants", 
                    "BindsTo", ".requires", ".wants"]
                for line in self.list_dependencies(dep, new_indent, new_mark, new_loop):
                    yield line
    def get_dependencies_unit(self, unit):
        conf = self.get_unit_conf(unit)
        deps = {}
        for style in [ "Requires", "Wants", "Requisite", "BindsTo", "PartOf",
            ".requires", ".wants", "PropagateReloadTo", "Conflicts",  ]:
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
                for requirelist in conf.getlist("Unit", style, []):
                    for required in requirelist.strip().split(" "):
                        deps[required.strip()] = style
        return deps
    def get_start_dependencies(self, unit): # pragma: no cover
        """ the list of services to be started as well / TODO: unused """
        deps = {}
        unit_deps = self.get_dependencies_unit(unit)
        for dep_unit, dep_style in unit_deps.items():
            restrict = ["Requires", "Requisite", "ConsistsOf", "Wants", 
                "BindsTo", ".requires", ".wants"]
            if dep_style in restrict:
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
            line = (item.name(),  "(%s)" % (" ".join(deps[item.name()])))
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
                    logg.debug("ignoring masked unit %s", unit)
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
                    logg.debug("ignoring masked unit %s", unit)
                    continue
                conflist.append(conf)
        sortlist = conf_sortedAfter(reversed(conflist))
        return [ item.name() for item in reversed(sortlist) ]
    def system_daemon_reload(self):
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
    def syntax_check_service(self, conf):
        unit = conf.name()
        if not conf.data.has_section("Service"):
           logg.error(" %s: a .service file without [Service] section", unit)
           return 101
        errors = 0
        haveType = conf.get("Service", "Type", "simple")
        haveExecStart = conf.getlist("Service", "ExecStart", [])
        haveExecStop = conf.getlist("Service", "ExecStop", [])
        haveExecReload = conf.getlist("Service", "ExecReload", [])
        usedExecStart = []
        usedExecStop = []
        usedExecReload = []
        if haveType not in [ "simple", "forking", "notify", "oneshot", "dbus", "idle"]:
            logg.error(" %s: Failed to parse service type, ignoring: %s", unit, haveType)
            errors += 100
        for line in haveExecStart:
            if not line.startswith("/") and not line.startswith("-/"):
                logg.error(" %s: Executable path is not absolute, ignoring: %s", unit, line.strip())
                errors += 1
            usedExecStart.append(line)
        for line in haveExecStop:
            if not line.startswith("/") and not line.startswith("-/"):
                logg.error(" %s: Executable path is not absolute, ignoring: %s", unit, line.strip())
                errors += 1
            usedExecStop.append(line)
        for line in haveExecReload:
            if not line.startswith("/") and not line.startswith("-/"):
                logg.error(" %s: Executable path is not absolute, ignoring: %s", unit, line.strip())
                errors += 1
            usedExecReload.append(line)
        if haveType in ["simple", "notify", "forking"]:
            if not usedExecStart and not usedExecStop:
                logg.error(" %s: Service lacks both ExecStart and ExecStop= setting. Refusing.", unit)
                errors += 101
            elif not usedExecStart and haveType != "oneshot":
                logg.error(" %s: Service has no ExecStart= setting, which is only allowed for Type=oneshot services. Refusing.",  unit)
                errors += 101
        if len(usedExecStart) > 1 and haveType != "oneshot":
            logg.error(" %s: there may be only one ExecStart statement (unless for 'oneshot' services)."
              + "\n\t\t\tYou can use ExecStartPre / ExecStartPost to add additional commands.", unit)
            errors += 1
        if len(usedExecStop) > 1 and haveType != "oneshot":
            logg.info(" %s: there should be only one ExecStop statement (unless for 'oneshot' services)."
              + "\n\t\t\tYou can use ExecStopPost to add additional commands (also executed on failed Start)", unit)
        if len(usedExecReload) > 1:
            logg.info(" %s: there should be only one ExecReload statement."
              + "\n\t\t\tUse ' ; ' for multiple commands (ExecReloadPost or ExedReloadPre do not exist)", unit)
        if len(usedExecReload) > 0 and "/bin/kill " in usedExecReload[0]:
            logg.warning(" %s: the use of /bin/kill is not recommended for ExecReload as it is asychronous."
              + "\n\t\t\tThat means all the dependencies will perform the reload simultanously / out of order.", unit)
        if conf.getlist("Service", "ExecRestart", []): #pragma: no cover
            logg.error(" %s: there no such thing as an ExecRestart (ignored)", unit)
        if conf.getlist("Service", "ExecRestartPre", []): #pragma: no cover
            logg.error(" %s: there no such thing as an ExecRestartPre (ignored)", unit)
        if conf.getlist("Service", "ExecRestartPost", []): #pragma: no cover 
            logg.error(" %s: there no such thing as an ExecRestartPost (ignored)", unit)
        if conf.getlist("Service", "ExecReloadPre", []): #pragma: no cover
            logg.error(" %s: there no such thing as an ExecReloadPre (ignored)", unit)
        if conf.getlist("Service", "ExecReloadPost", []): #pragma: no cover
            logg.error(" %s: there no such thing as an ExecReloadPost (ignored)", unit)
        if conf.getlist("Service", "ExecStopPre", []): #pragma: no cover
            logg.error(" %s: there no such thing as an ExecStopPre (ignored)", unit)
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
            if env_file.startswith("-"): continue
            if not os.path.isfile(os_path(self._root, env_file)):
                logg.error(" %s: Failed to load environment files: %s", unit, env_file)
                errors += 101
        return errors
    def exec_check_service(self, conf, env, exectype = ""):
        if not conf:
            return True
        if not conf.data.has_section("Service"):
            return True #pragma: no cover
        haveType = conf.get("Service", "Type", "simple")
        if self.is_sysv_file(conf.filename()):
            return True # we don't care about that
        abspath = 0
        notexists = 0
        for execs in [ "ExecStartPre", "ExecStart", "ExecStartPost", "ExecStop", "ExecStopPost", "ExecReload" ]:
            if not execs.startswith(exectype):
                continue
            for cmd in conf.getlist("Service", execs, []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                if not newcmd:
                    continue
                exe = newcmd[0]
                if not exe:
                    continue
                if exe[0] != "/":
                    logg.error(" Exec is not an absolute path:  %s=%s", execs, cmd)
                    abspath += 1
                if not os.path.isfile(exe):
                    logg.error(" Exec command does not exist: (%s) %s", execs, exe)
                    notexists += 1
                    newexe1 = os.path.join("/usr/bin", exe)
                    newexe2 = os.path.join("/bin", exe)
                    if os.path.exists(newexe1):
                        logg.error(" but this does exist: %s  %s", " " * len(execs), newexe1)
                    elif os.path.exists(newexe2):
                        logg.error(" but this does exist: %s      %s", " " * len(execs), newexe2)
        if not abspath and not notexists:
            return True
        if True:
            filename = strE(conf.filename())
            if len(filename) > 45: filename = "..." + filename[-42:]
            logg.error(" !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            logg.error(" Found %s problems in %s", abspath + notexists, filename)
            time.sleep(1)
            if abspath:
                logg.error(" The SystemD commands must always be absolute paths by definition.")
                time.sleep(1)
                logg.error(" Earlier versions of systemctl.py did use a subshell thus using $PATH")
                time.sleep(1)
                logg.error(" however newer versions use execve just like the real SystemD daemon")
                time.sleep(1)
                logg.error(" so that your docker-only service scripts may start to fail suddenly.")
                time.sleep(1)
            if notexists:
                logg.error(" Now %s executable paths were not found in the current environment.", notexists)
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
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units(to_list(module))
            if not matched:
                logg.error("Unit %s could not be found.", unit_of(module))
                units += [ module ]
                # self.error |= NOT_FOUND
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.show_units(units) + notfound # and found_all
    def show_units(self, units):
        logg.debug("show --property=%s", self._unit_property)
        result = []
        for unit in units:
            if result: result += [ "" ]
            for var, value in self.show_unit_items(unit):
                if self._unit_property:
                    if self._unit_property != var:
                        continue
                else:
                    if not value and not self._show_all:
                        continue
                result += [ "%s=%s" % (var, value) ]
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
        names = { unit: 1, conf.name(): 1 }
        yield "Id", conf.name()
        yield "Names", " ".join(sorted(names.keys()))
        yield "Description", self.get_description_from(conf) # conf.get("Unit", "Description")
        yield "PIDFile", self.pid_file_from(conf) # not self.pid_file_from w/o default location
        yield "MainPID", strE(self.active_pid_from(conf))            # status["MainPID"] or PIDFile-read
        yield "SubState", self.get_substate_from(conf) or "unknown"  # status["SubState"] or notify-result
        yield "ActiveState", self.get_active_from(conf) or "unknown" # status["ActiveState"]
        yield "LoadState", loaded
        yield "UnitFileState", self.enabled_from(conf)
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
        for env_part in conf.getlist("Service", "Environment", []):
            env_parts.append(self.expand_special(env_part, conf))
        if env_parts: 
            yield "Environment", " ".join(env_parts)
        env_files = []
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
            env_files.append(self.expand_special(env_file, conf))
        if env_files:
            yield "EnvironmentFile", " ".join(env_files)
    def get_SendSIGKILL(self, conf):
        return conf.getbool("Service", "SendSIGKILL", "yes")
    def get_SendSIGHUP(self, conf):
        return conf.getbool("Service", "SendSIGHUP", "no")
    def get_KillMode(self, conf):
        return conf.get("Service", "KillMode", "control-group")
    def get_KillSignal(self, conf):
        return conf.get("Service", "KillSignal", "SIGTERM")
    #
    igno_centos = [ "netconsole", "network" ]
    igno_opensuse = [ "raw", "pppoe", "*.local", "boot.*", "rpmconf*", "postfix*" ]
    igno_ubuntu = [ "mount*", "umount*", "ondemand", "*.local" ]
    igno_always = [ "network*", "dbus*", "systemd-*" ]
    igno_always += [ "purge-kernels.service", "after-local.service", "dm-event.*" ] # as on opensuse
    def _ignored_unit(self, unit, ignore_list):
        for ignore in ignore_list:
            if fnmatch.fnmatchcase(unit, ignore):
                return True # ignore
            if fnmatch.fnmatchcase(unit, ignore+".service"):
                return True # ignore
        return False
    def system_default_services(self, sysv = "S", default_target = None):
        """ show the default services 
            This is used internally to know the list of service to be started in 'default'
            runlevel when the container is started through default initialisation. It will
            ignore a number of services - use '--all' to show a longer list of services and
            use '--all --force' if not even a minimal filter shall be used.
        """
        igno = self.igno_centos + self.igno_opensuse + self.igno_ubuntu + self.igno_always
        if self._show_all:
            igno = self.igno_always
            if self._force:
                igno = []
        logg.debug("ignored services filter for default.target:\n\t%s", igno)
        return self.enabled_default_services(sysv, default_target, igno)
    def enabled_default_services(self, sysv = "S", default_target = None, igno = []):
        if self.user_mode():
            logg.debug("check for default user services")
            units = self.enabled_default_user_local_units(".socket", "sockets.target", igno)
            units += self.enabled_default_user_local_units(".service", default_target, igno)
            units += self.enabled_default_user_system_units(".service", default_target, igno)
            return units
        else:
            logg.debug("check for default system services")
            units = self.enabled_default_system_units(".socket", "sockets.target", igno)
            units += self.enabled_default_system_units(".service", default_target, igno)
            units += self.enabled_default_sysv_units(sysv, default_target, igno)
            return units
    def enabled_default_user_local_units(self, unit_kind = ".service", default_target = None, igno = []):
        target = default_target or self._default_target
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
    def enabled_default_user_system_units(self, unit_kind = ".service", default_target = None, igno = []):
        default_target = default_target or self._default_target
        units = []
        for basefolder in self.system_folders():
            if not basefolder:
                continue
            folder = self.default_enablefolder(default_target, basefolder)
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
                        if self.not_user_conf(conf):
                            pass 
                        else:
                            units.append(unit)
        return units
    def enabled_default_system_units(self, unit_type = ".service", default_target = None, igno = []):
        logg.debug("check for default system services")
        default_target = default_target or self._default_target
        units = []
        for basefolder in self.system_folders():
            if not basefolder:
                continue
            folder = self.default_enablefolder(default_target, basefolder)
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
    def enabled_default_sysv_units(self, sysv = "S", default_target = None, igno = []):
        units = []
        for folder in [ self.rc3_root_folder() ]:
            if not os.path.isdir(folder):
                logg.warning("non-existant %s", folder)
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
    def system_default(self, arg = True):
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
        default_target = self._default_target
        default_services = self.system_default_services("S", default_target)
        self.sysinit_status(SubState = "starting")
        self.start_units(default_services)
        logg.info(" -- system is up")
        if init:
            logg.info("init-loop start")
            sig = self.init_loop_until_stop(default_services)
            logg.info("init-loop %s", sig)
            self.stop_system_default()
        return True
    def stop_system_default(self):
        """ detect the default.target services and stop them.
            This is commonly run through 'systemctl halt' or
            at the end of a 'systemctl --init default' loop."""
        default_target = self._default_target
        default_services = self.system_default_services("K", default_target)
        self.sysinit_status(SubState = "stopping")
        self.stop_units(default_services)
        logg.info(" -- system is down")
        return True
    def system_halt(self, arg = True):
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
        current = self._default_target
        folder = os_path(self._root, self.mask_folder())
        target = os.path.join(folder, DefaultUnit)
        if os.path.islink(target):
            current = os.path.basename(os.readlink(target))
        return current
    def set_default_modules(self, *modules):
        """ set current default run-level"""
        if not modules:
            logg.debug(".. no runlevel given")
            self.error |= NOT_OK
            return "Too few arguments"
        current = self._default_target
        folder = os_path(self._root, self.mask_folder())
        target = os.path.join(folder, DefaultUnit)
        if os.path.islink(target):
            current = os.path.basename(os.readlink(target))
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
            if os.path.islink(target):
                os.unlink(target)
            if not os.path.isdir(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            os.symlink(targetfile, target)
            msg = "Created symlink from %s -> %s" % (target, targetfile)
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
                    units += [ unit ]
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
            log_path = self.path_journal_log(conf)
            try:
                opened = os.open(log_path, os.O_RDONLY | os.O_NONBLOCK)
                self._log_file[unit] = opened
                self._log_hold[unit] = b""
            except Exception as e:
                logg.error("can not open %s log: %s\n\t%s", unit, log_path, e)
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
                logg.error("can not close log: %s\n\t%s", unit, e)
        self._log_file = {}
        self._log_hold = {}

    def get_StartLimitBurst(self, conf):
        defaults = DefaultStartLimitBurst
        return to_int(conf.get("Service", "StartLimitBurst", strE(defaults)), defaults) # 5
    def get_StartLimitIntervalSec(self, conf, maximum = None):
        maximum = maximum or 999
        defaults = DefaultStartLimitIntervalSec
        interval = conf.get("Service", "StartLimitIntervalSec", strE(defaults)) # 10s
        return time_to_seconds(interval, maximum)
    def get_RestartSec(self, conf, maximum = None):
        maximum = maximum or DefaultStartLimitIntervalSec
        delay = conf.get("Service", "RestartSec", strE(DefaultRestartSec))
        return time_to_seconds(delay, maximum)
    def restart_failed_units(self, units, maximum = None):
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
                restartPolicy = conf.get("Service", "Restart", "no")
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
                                me, unit, [ "%.3fs" % (t - now) for t in restarted ])
                            while len(restarted):
                                oldest = restarted[0]
                                interval = time.time() - oldest
                                if interval > limitSecs:
                                    restarted = restarted[1:]
                                    continue
                                break
                            self._restarted_unit[unit] = restarted
                            logg.debug("[%s] [%s] ratelimit %s", 
                                me, unit, [ "%.3fs" % (t - now) for t in restarted ])
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
                logg.error("[%s] [%s] An error ocurred while restart checking: %s", me, unit, e)
        if not self._restart_failed_units:
            self.error |= NOT_OK
            return []
        # NOTE: this function is only called from InitLoop when "running"
        # let's check if any of the restart_units has its restartSec expired
        now = time.time()
        restart_done = []
        logg.debug("[%s] Restart checking  %s", 
            me, [ "%+.3fs" % (t - now) for t in self._restart_failed_units.values() ])
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
                logg.error("[%s] [%s] An error ocurred while restarting: %s", me, unit, e)
        for unit in restart_done:
            if unit in self._restart_failed_units:
                del self._restart_failed_units[unit]
        logg.debug("[%s] Restart remaining %s", 
            me, [ "%+.3fs" % (t - now) for t in self._restart_failed_units.values() ])
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
        self.start_log_files(units)
        self.sysinit_status(ActiveState = "active", SubState = "running")
        result = None
        while True:
            try:
                if DEBUG_INITLOOP:
                    logg.debug("DONE InitLoop (sleep %ss)", InitLoopSleep)
                time.sleep(InitLoopSleep)
                if DEBUG_INITLOOP:
                    logg.debug("NEXT InitLoop (after %ss)", InitLoopSleep)
                self.read_log_files(units)
                if DEBUG_INITLOOP:
                    logg.debug("reap zombies - check current processes")
                running = self.system_reap_zombies()
                if DEBUG_INITLOOP:
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
        self.read_log_files(units)
        self.read_log_files(units)
        self.stop_log_files(units)
        logg.debug("done - init loop")
        return result
    def system_reap_zombies(self):
        """ check to reap children """
        selfpid = os.getpid()
        running = 0
        for pid_file in os.listdir("/proc"):
            try: pid = int(pid_file)
            except: continue
            if pid == selfpid:
                continue
            proc_status = "/proc/%s/status" % pid
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
        status_file = self.status_file_from(conf)
        if not os.path.isfile(status_file):
            time.sleep(MinimumYield)
        if not os.path.isfile(status_file):
            return "offline"
        status = self.read_status_from(conf)
        return status.get("SubState", "unknown")
    def system_is_system_running(self):
        state = self.is_system_running()
        if state not in [ "running" ]:
            self.error |= NOT_OK # 1
        if self._quiet:
            return None
        return state
    def wait_system(self, target = None):
        target = target or SysInitTarget
        for attempt in xrange(int(SysInitWait)):
            state = self.is_system_running()
            if "init" in state:
                if target in [ SysInitTarget, "basic.target" ]:
                    logg.info("system not initialized - wait %s", target)
                    time.sleep(1)
                    continue
            if "start" in state or "stop" in state:
                if target in [ "basic.target" ]:
                    logg.info("system not running - wait %s", target)
                    time.sleep(1)
                    continue
            if "running" not in state:
                logg.info("system is %s", state)
            break
    def pidlist_of(self, pid):
        try: pid = int(pid)
        except: return []
        pidlist = [ pid ]
        pids = [ pid ]
        for depth in xrange(PROC_MAX_DEPTH):
            for pid_file in os.listdir("/proc"):
                try: pid = int(pid_file)
                except: continue
                proc_status = "/proc/%s/status" % pid
                if os.path.isfile(proc_status):
                    try:
                        for line in open(proc_status):
                            if line.startswith("PPid:"):
                                ppid_text = line[len("PPid:"):].strip()
                                try: ppid = int(ppid_text)
                                except: continue
                                if ppid in pidlist and pid not in pids:
                                    pids += [ pid ]
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
            for pid_dir in os.listdir("/proc"):
                pid_num = to_intN(pid_dir)
                if pid_num:
                    try:
                        cmdline = "/proc/{pid_dir}/cmdline".format(**locals())
                        cmd = open(cmdline).read().split("\0")
                        if DEBUG_KILLALL: logg.debug("cmdline %s", cmd)
                        found = None
                        cmd_exe = os.path.basename(cmd[0])
                        if DEBUG_KILLALL: logg.debug("cmd.exe '%s'", cmd_exe)
                        if fnmatch.fnmatchcase(cmd_exe, target): found = "exe"
                        if len(cmd) > 1 and cmd_exe.startswith("python"): 
                            cmd_arg = os.path.basename(cmd[1])
                            if DEBUG_KILLALL: logg.debug("cmd.arg '%s'", cmd_arg)
                            if fnmatch.fnmatchcase(cmd_arg, target): found = "arg"
                            if cmd_exe.startswith("coverage") or cmd_arg.startswith("coverage"):
                                x = cmd.index("--")
                                if x > 0 and x+1 < len(cmd):
                                    cmd_run = os.path.basename(cmd[x+1])
                                    if DEBUG_KILLALL: logg.debug("cmd.run '%s'", cmd_run)
                                    if fnmatch.fnmatchcase(cmd_run, target): found = "run"
                        if found:
                            if DEBUG_KILLALL: logg.debug("%s found %s %s", found, pid_num, [ c for c in cmd ])
                            if pid_num != os.getpid():
                                logg.debug(" kill -%s %s # %s", sig, pid_num, target)
                                os.kill(pid_num, sig)
                    except Exception as e:
                        logg.error("kill -%s %s : %s", sig, pid_num, e)
        return True
    def etc_hosts(self):
        path = "/etc/hosts"
        if self._root:
            return os_path(self._root, path)
        return path
    def force_ipv4(self, *args):
        """ only ipv4 localhost in /etc/hosts """
        logg.debug("checking /etc/hosts for '::1 localhost'")
        lines = []
        for line in open(self.etc_hosts()):
            if "::1" in line:
                newline = re.sub("\\slocalhost\\s", " ", line)
                if line != newline:
                    logg.info("/etc/hosts: '%s' => '%s'", line.rstrip(), newline.rstrip())
                    line = newline
            lines.append(line)
        f = open(self.etc_hosts(), "w")
        for line in lines:
            f.write(line)
        f.close()
    def force_ipv6(self, *args):
        """ only ipv4 localhost in /etc/hosts """
        logg.debug("checking /etc/hosts for '127.0.0.1 localhost'")
        lines = []
        for line in open(self.etc_hosts()):
            if "127.0.0.1" in line:
                newline = re.sub("\\slocalhost\\s", " ", line)
                if line != newline:
                    logg.info("/etc/hosts: '%s' => '%s'", line.rstrip(), newline.rstrip())
                    line = newline
            lines.append(line)
        f = open(self.etc_hosts(), "w")
        for line in lines:
            f.write(line)
        f.close()
    def show_help(self, *args):
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
                   arg = name[len("system_"):].replace("_","-")
                if name.startswith("show_"):
                   arg = name[len("show_"):].replace("_","-")
                if name.endswith("_of_unit"):
                   arg = name[:-len("_of_unit")].replace("_","-")
                if name.endswith("_modules"):
                   arg = name[:-len("_modules")].replace("_","-")
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
            arg = arg.replace("-","_")
            func1 = getattr(self.__class__, arg+"_modules", None)
            func2 = getattr(self.__class__, arg+"_of_unit", None)
            func3 = getattr(self.__class__, "show_"+arg, None)
            func4 = getattr(self.__class__, "system_"+arg, None)
            func = func1 or func2 or func3 or func4
            if func is None:
                print("error: no such command '%s'" % arg)
                okay = False
            else:
                doc_text = "..."
                doc = getattr(func, "__doc__", None)
                if doc:
                    doc_text = doc.replace("\n","\n\n", 1).strip()
                    if "--" not in doc_text:
                        doc_text = "-- " + doc_text
                else: 
                    func_name = arg # FIXME
                    logg.debug("__doc__ of %s is none", func_name)
                    if not self._show_all: continue
                lines.append("%s %s %s" % (prog, arg, doc_text))
        if not okay:
            self.show_help()
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
    def systems_version(self):
        return [ self.systemd_version(), self.systemd_features() ]

def print_result(result):
    # logg_info = logg.info
    # logg_debug = logg.debug
    def logg_info(*msg): pass
    def logg_debug(*msg): pass
    exitcode = 0
    if result is None:
        logg_info("EXEC END None")
    elif result is True:
        logg_info("EXEC END True")
        exitcode = 0
    elif result is False:
        logg_info("EXEC END False")
        exitcode = NOT_OK # the only case that exitcode gets set
    elif isinstance(result, int):
        logg_info("EXEC END %s", result)
        # exitcode = result # we do not do that anymore
    elif isinstance(result, basestring):
        print(result)
        result1 = result.split("\n")[0][:-20]
        if result == result1:
            logg_info("EXEC END '%s'", result)
        else:
            logg_info("EXEC END '%s...'", result1)
            logg_debug("    END '%s'", result)
    elif isinstance(result, list) or hasattr(result, "next") or hasattr(result, "__next__"):
        shown = 0
        for element in result:
            if isinstance(element, tuple):
                print("\t".join([ str(elem) for elem in element] ))
            else:
                print(element)
            shown += 1
        logg_info("EXEC END %s items", shown)
        logg_debug("    END %s", result)
    elif hasattr(result, "keys"):
        shown = 0
        for key in sorted(result.keys()):
            element = result[key]
            if isinstance(element, tuple):
                print(key,"=","\t".join([ str(elem) for elem in element]))
            else:
                print("%s=%s" % (key,element))
            shown += 1
        logg_info("EXEC END %s items", shown)
        logg_debug("    END %s", result)
    else:
        logg.warning("EXEC END Unknown result type %s", str(type(result)))
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
    _o.add_option("-t","--type", metavar="TYPE", dest="unit_type", default=_unit_type,
        help="List units of a particual type")
    _o.add_option("--state", metavar="STATE", default=_unit_state,
        help="List units with particular LOAD or SUB or ACTIVE state")
    _o.add_option("-p", "--property", metavar="NAME", dest="unit_property", default=_unit_property,
        help="Show only properties by this name")
    _o.add_option("-a", "--all", action="store_true", dest="show_all", default=_show_all,
        help="Show all loaded units/properties, including dead empty ones. To list all units installed on the system, use the 'list-unit-files' command instead")
    _o.add_option("-l","--full", action="store_true", default=_full,
        help="Don't ellipsize unit names on output (never ellipsized)")
    _o.add_option("--reverse", action="store_true",
        help="Show reverse dependencies with 'list-dependencies' (ignored)")
    _o.add_option("--job-mode", metavar="MODE",
        help="Specifiy how to deal with already queued jobs, when queuing a new job (ignored)")    
    _o.add_option("--show-types", action="store_true",
        help="When showing sockets, explicitly show their type (ignored)")
    _o.add_option("-i","--ignore-inhibitors", action="store_true",
        help="When shutting down or sleeping, ignore inhibitors (ignored)")
    _o.add_option("--kill-who", metavar="WHO",
        help="Who to send signal to (ignored)")
    _o.add_option("-s", "--signal", metavar="SIG",
        help="Which signal to send (ignored)")
    _o.add_option("--now", action="store_true", default=_now,
        help="Start or stop unit in addition to enabling or disabling it")
    _o.add_option("-q","--quiet", action="store_true", default=_quiet,
        help="Suppress output")
    _o.add_option("--no-block", action="store_true", default=False,
        help="Do not wait until operation finished (ignored)")
    _o.add_option("--no-legend", action="store_true", default=_no_legend,
        help="Do not print a legend (column headers and hints)")
    _o.add_option("--no-wall", action="store_true", default=False,
        help="Don't send wall message before halt/power-off/reboot (ignored)")
    _o.add_option("--no-reload", action="store_true",
        help="Don't reload daemon after en-/dis-abling unit files (ignored)")
    _o.add_option("--no-ask-password", action="store_true", default=_no_ask_password,
        help="Do not ask for system passwords")
    # _o.add_option("--global", action="store_true", dest="globally", default=_globally,
    #    help="Enable/disable unit files globally") # for all user logins
    # _o.add_option("--runtime", action="store_true",
    #     help="Enable unit files only temporarily until next reboot")
    _o.add_option("--force", action="store_true", default=_force,
        help="When enabling unit files, override existing symblinks / When shutting down, execute action immediately")
    _o.add_option("--preset-mode", metavar="TYPE", default=_preset_mode,
        help="Apply only enable, only disable, or all presets [%default]")
    _o.add_option("--root", metavar="PATH", default=_root,
        help="Enable unit files in the specified root directory (used for alternative root prefix)")
    _o.add_option("-n","--lines", metavar="NUM",
        help="Number of journal entries to show (ignored)")
    _o.add_option("-o","--output", metavar="CAT",
        help="change journal output mode [short, ..., cat] (ignored)")
    _o.add_option("--plain", action="store_true",
        help="Print unit dependencies as a list instead of a tree (ignored)")
    _o.add_option("--no-pager", action="store_true",
        help="Do not pipe output into pager (ignored)")
    #
    _o.add_option("-c","--config", metavar="NAME=VAL", action="append", default=[],
        help="..override internal variables (InitLoopSleep,SysInitTarget) {%default}")
    _o.add_option("-e","--extra-vars", "--environment", metavar="NAME=VAL", action="append", default=[],
        help="..override settings in the syntax of 'Environment='")
    _o.add_option("-v","--verbose", action="count", default=0,
        help="..increase debugging information level")
    _o.add_option("-4","--ipv4", action="store_true", default=False,
        help="..only keep ipv4 localhost in /etc/hosts")
    _o.add_option("-6","--ipv6", action="store_true", default=False,
        help="..only keep ipv6 localhost in /etc/hosts")
    _o.add_option("-1","--init", action="store_true", default=False,
        help="..keep running as init-process (default if PID 1)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = max(0, logging.FATAL - 10 * opt.verbose))
    logg.setLevel(max(0, logging.ERROR - 10 * opt.verbose))
    #
    _extra_vars = opt.extra_vars
    _force = opt.force
    _full = opt.full
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
    # being PID 1 (or 0) in a container will imply --init
    _pid = os.getpid()
    _init = opt.init or _pid in [ 1, 0 ]
    _user_mode = opt.user
    if os.geteuid() and _pid in [ 1, 0 ]:
        _user_mode = True
    if opt.system:
        _user_mode = False # override --user
    #
    for setting in opt.config:
        if "=" in setting:
            nam, val = setting.split("=", 1)
            if nam in globals():
                old = globals()[nam]
                if old is False or old is True:
                    logg.debug("yes %s=%s", nam, val)
                    globals()[nam] = (val in ("true", "True", "TRUE", "yes", "y", "Y", "YES"))
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
                else:
                    logg.warning("(ignored) unknown target type -c '%s' : %s", nam, type(old))
            else:
                logg.warning("(ignored) unknown target config -c '%s' : no such variable", nam)
        else:
            logg.warning("(ignored) not a config setting format -c '%s'", setting)
    #
    if _user_mode:
        systemctl_debug_log = os_path(_root, _var_path(SYSTEMCTL_DEBUG_LOG))
        systemctl_extra_log = os_path(_root, _var_path(SYSTEMCTL_EXTRA_LOG))
    else:
        systemctl_debug_log = os_path(_root, SYSTEMCTL_DEBUG_LOG)
        systemctl_extra_log = os_path(_root, SYSTEMCTL_EXTRA_LOG)
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
    logg.info("EXEC BEGIN %s %s%s%s", os.path.realpath(sys.argv[0]), " ".join(args),
        _user_mode and " --user" or " --system", _init and " --init" or "", )
    #
    #
    systemctl = Systemctl()
    if opt.version:
        args = [ "version" ]
    if not args:
        if _init:
            args = [ "default" ]
        else:
            args = [ "list-units" ]
    logg.debug("======= systemctl.py " + " ".join(args))
    command = args[0]
    modules = args[1:]
    if opt.ipv4:
        systemctl.force_ipv4()
    elif opt.ipv6:
        systemctl.force_ipv6()
    found = False
    # command NAME
    if command.startswith("__"):
        command_name = command[2:]
        command_func = getattr(systemctl, command_name, None)
        if callable(command_func) and not found:
            found = True
            result = command_func(*modules)
    command_name = command.replace("-","_").replace(".","_")+"_modules"
    command_func = getattr(systemctl, command_name, None)
    if callable(command_func) and not found:
        found = True
        result = command_func(*modules)
    command_name = "show_"+command.replace("-","_").replace(".","_")
    command_func = getattr(systemctl, command_name, None)
    if callable(command_func) and not found:
        found = True
        result = command_func(*modules)
    command_name = "system_"+command.replace("-","_").replace(".","_")
    command_func = getattr(systemctl, command_name, None)
    if callable(command_func) and not found:
        found = True
        result = command_func()
    command_name = "systems_"+command.replace("-","_").replace(".","_")
    command_func = getattr(systemctl, command_name, None)
    if callable(command_func) and not found:
        found = True
        result = command_func()
    if not found:
        logg.error("Unknown operation %s.", command)
        sys.exit(1)
    #
    exitcode = print_result(result)
    exitcode |= systemctl.error
    sys.exit(exitcode)
