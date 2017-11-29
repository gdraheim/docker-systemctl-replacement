#! /usr/bin/python
from __future__ import print_function

__copyright__ = "(C) 2016-2017 Guido U. Draheim, licensed under the EUPL"
__version__ = "1.0.1472"

import logging
logg = logging.getLogger("systemctl")

import re
import fnmatch
import shlex
import collections
import errno
import os
import sys
import subprocess
import signal
import time
import socket
import tempfile

if sys.version[0] == '2':
    string_types = basestring
else:
    string_types = str
    xrange = range

DEBUG_AFTER = False

# defaults for options
_force = False
_full = False
_now = False
_no_legend = False
_no_ask_password = False
_preset_mode = "all"
_quiet = False
_root = ""
_unit_type = None
_unit_property = None
_show_all = False

# common default paths
_sysd_default = "multi-user.target"
_sysd_folder1 = "/etc/systemd/system"
_sysd_folder2 = "/var/run/systemd/system"
_sysd_folder3 = "/usr/lib/systemd/system"
_sysd_folder4 = "/lib/systemd/system"
_sysv_folder1 = "/etc/init.d"
_sysv_folder2 = "/var/run/init.d"
_preset_folder1 = "/etc/systemd/system-preset"
_preset_folder2 = "/var/run/systemd/system-preset"
_preset_folder3 = "/usr/lib/systemd/system-preset"
_preset_folder4 = "/lib/systemd/system-preset"
_waitprocfile = 100
_waitkillproc = 10

MinimumSleep = 2
MinimumWaitProcFile = 9
MinimumWaitKillProc = 3
DefaultWaitProcFile = 100
DefaultWaitKillProc = 9
DefaultTimeoutStartSec = 9 # officially 90
DefaultTimeoutStopSec = 9  # officially 90
DefaultMaximumTimeout = 200

_notify_socket_folder = "/var/run/systemd" # alias /run/systemd
_notify_socket_name = "notify" # NOTIFY_SOCKET="/var/run/systemd/notify"
_pid_file_folder = "/var/run"
_journal_log_folder = "/var/log/journal"

_systemctl_debug_log = "/var/log/systemctl.debug.log"
_systemctl_extra_log = "/var/log/systemctl.log"

_runlevel_targets = [ "runlevel0.target", "runlevel1.target", "runlevel2.target", "runlevel3.target", "runlevel4.target", "runlevel5.target", "runlevel6.target" ]
_default_targets = [ "poweroff.target", "rescue.target", "sysinit.target", "basic.target", "multi-user.target", "graphical.target", "reboot.target" ]
_feature_targets = [ "network.target", "remote-fs.target", "local-fs.target", "timers.target", "nfs-client.target" ]
_all_common_targets = [ "default.target" ] + _default_targets + _runlevel_targets + _feature_targets

# inside a docker we pretend the following
_all_common_enabled = [ "default.target", "runlevel3.target", "multi-user.target", "remote-fs.target" ]
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
_sysv_mappings["$network"] = "network.target"
_sysv_mappings["$remote_fs"] = "remote-fs.target"
_sysv_mappings["$local_fs"] = "local-fs.target"
_sysv_mappings["$timer"] = "timers.target"

def shell_cmd(cmd):
    return " ".join(["'%s'" % part for part in cmd])
def to_int(value, default = 0):
    try:
        return int(value)
    except:
        return default
def to_list(value):
    if isinstance(value, string_types):
         return [ value ]
    return value

def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
       path = path[1:]
    return os.path.join(root, path)

def shutil_chown(filename, user = None, group = None):
    """ in python 3.3. there is shutil.chown """
    uid = -1
    gid = -1
    if group:
        import grp
        gid = grp.getgrnam(group).gr_gid
    if user:
        import pwd
        uid = pwd.getpwnam(user).pw_uid
    if os.path.exists(filename):
        os.chown(filename, uid, gid)

def shutil_setuid(user = None, group = None):
    """ set fork-child uid/gid """
    if group:
        import grp
        gid = grp.getgrnam(group).gr_gid
        os.setgid(gid)
        logg.debug("setgid %s '%s'", gid, group)
    if user:
        import pwd
        uid = pwd.getpwnam(user).pw_uid
        os.setuid(uid)
        logg.debug("setuid %s '%s'", uid, user)

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
        if e.errno == errno.ENOENT:
            return False
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

class UnitConfigParser:
    """ A *.service files has a structure similar to an *.ini file but it is
        actually not like it. Settings may occur multiple times in each section
        and they create an implicit list. In reality all the settings are
        globally uniqute, so that an 'environment' can be printed without
        adding prefixes. Settings are continued with a backslash at the end
        of the line.  """
    def __init__(self, defaults=None, dict_type=None, allow_no_value=False):
        self._defaults = defaults or {}
        self._dict_type = dict_type or collections.OrderedDict
        self._allow_no_value = allow_no_value
        self._dict = self._dict_type()
        self._files = []
    def defaults(self):
        return self._defaults
    def sections(self):
        return list(self._dict.keys())
    def add_section(self, section):
        if section not in self._dict:
            self._dict[section] = self._dict_type()
    def has_section(self, section):
        return section in self._dict
    def has_option(self, section, option):
        if section not in self._dict:
            return False
        return option in self._dict[section]
    def set(self, section, option, value):
        if section not in self._dict:
            self._dict[section] = self._dict_type()
        if option not in self._dict[section]:
            self._dict[section][option] = [ value ]
        else:
            self._dict[section][option].append(value)
        if value is None:
            self._dict[section][option] = []
    def get(self, section, option, default = None, allow_no_value = False):
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._dict:
            if default is not None:
                return default
            if allow_no_value:
                return None
            logg.error("section {} does not exist".format(section))
            logg.error("  have {}".format(self.sections()))
            raise AttributeError("section {} does not exist".format(section))
        if option not in self._dict[section]:
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError("option {} in {} does not exist".format(option, section))
        if not self._dict[section][option]: # i.e. an empty list
            if default is not None:
                return default
            if allow_no_value:
                return None
            raise AttributeError("option {} in {} is None".format(option, section))
        return self._dict[section][option][0] # the first line in the list of configs
    def getlist(self, section, option, default = None, allow_no_value = False):
        allow_no_value = allow_no_value or self._allow_no_value
        if section not in self._dict:
            if default is not None:
                return default
            if allow_no_value:
                return []
            logg.error("section {} does not exist".format(section))
            logg.error("  have {}".format(self.sections()))
            raise AttributeError("section {} does not exist".format(section))
        if option not in self._dict[section]:
            if default is not None:
                return default
            if allow_no_value:
                return []
            raise AttributeError("option {} in {} does not exist".format(option, section))
        return self._dict[section][option] # returns a list, possibly empty
    def loaded(self):
        return len(self._files)
    def name(self):
        name = ""
        filename = self.filename()
        if filename:
            name = os.path.basename(filename)
        return self.get("Unit", "Id", name)
    def filename(self):
        """ returns the last filename that was parsed """
        if self._files:
            return self._files[-1]
        return None
    def read(self, filename):
        return self.read_sysd(filename)
    def read_sysd(self, filename):
        initscript = False
        initinfo = False
        section = None
        if os.path.isfile(filename):
            self._files.append(filename)
        nextline = False
        name, text = "", ""
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
                self.set(section, name, text)
    def read_sysv(self, filename):
        """ an LSB header is scanned and converted to (almost)
            equivalent settings of a SystemD ini-style input """
        initscript = False
        initinfo = False
        section = None
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
                    m = re.match(r"^\S+\s*(\w[\w_-]*):(.*)", line)
                    if m:
                        self.set(section, m.group(1), m.group(2).strip())
                continue
        description = self.get("init.d", "Description", "")
        self.set("Unit", "Description", description)
        check = self.get("init.d", "Required-Start","")
        for item in check.split(" "):
            if item.strip() in _sysv_mappings:
                self.set("Unit", "Requires", _sysv_mappings[item.strip()])
        provides = self.get("init.d", "Provides", "")
        if provides:
            self.set("Install", "Alias", provides)
        # if already in multi-user.target then start it there.
        runlevels = self.get("init.d", "Default-Start","")
        for item in runlevels.split(" "):
            if item.strip() in _runlevel_mappings:
                self.set("Install", "WantedBy", _runlevel_mappings[item.strip()])
        self.set("Service", "Type", "sysv")

# UnitParser = ConfigParser.RawConfigParser
UnitParser = UnitConfigParser

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
                    logg.debug("%s %s => %s [%s]", status, pattern, unit, self.filename())
                    return status
        return None

def subprocess_wait(cmd, env=None, check = False, shell=False):
    # logg.warning("running = %s", cmd)
    run = subprocess.Popen(cmd, shell=shell, env=env)
    run.wait()
    if check and run.returncode: 
        logg.error("returncode %i\n %s", run.returncode, cmd)
        raise Exception("command failed")
    return run

def time_to_seconds(text, maximum = None):
    if maximum is None:
        maximum = DefaultMaximumTimeout
    value = 0
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
    if not value:
        return 1
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

def sortedAfter(conflist, cmp = compareAfter):
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
        # from command line options or the defaults
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
        self._unit_type = _unit_type
        # some common constants that may be changed
        self._sysd_folder1 = _sysd_folder1
        self._sysd_folder2 = _sysd_folder2
        self._sysd_folder3 = _sysd_folder3
        self._sysd_folder4 = _sysd_folder4
        self._sysv_folder1 = _sysv_folder1
        self._sysv_folder2 = _sysv_folder2
        self._preset_folder1 = _preset_folder1
        self._preset_folder2 = _preset_folder2
        self._preset_folder3 = _preset_folder3
        self._preset_folder4 = _preset_folder4
        self._notify_socket_folder = _notify_socket_folder
        self._notify_socket_name = _notify_socket_name
        self._pid_file_folder = _pid_file_folder 
        self._journal_log_folder = _journal_log_folder
        self._WaitProcFile = DefaultWaitProcFile
        self._WaitKillProc = DefaultWaitKillProc
        # and the actual internal runtime state
        self._loaded_file_sysv = {} # /etc/init.d/name => config data
        self._loaded_file_sysd = {} # /etc/systemd/system/name.service => config data
        self._file_for_unit_sysv = None # name.service => /etc/init.d/name
        self._file_for_unit_sysd = None # name.service => /etc/systemd/system/name.service
        self._preset_file_list = None # /etc/systemd/system-preset/* => file content
    def unit_file(self, module = None): # -> filename?
        """ file path for the given module (sysv or systemd) """
        path = self.unit_sysd_file(module)
        if path is not None: return path
        path = self.unit_sysv_file(module)
        if path is not None: return path
        return None
    def scan_unit_sysd_files(self, module = None): # -> [ unit-names,... ]
        """ reads all unit files, returns the first filename for the unit given """
        if self._file_for_unit_sysd is None:
            self._file_for_unit_sysd = {}
            for folder in (self._sysd_folder1, self._sysd_folder2, self._sysd_folder3, self._sysd_folder4):
                if self._root:
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
    def unit_sysd_file(self, module = None): # -> filename?
        """ file path for the given module (systemd) """
        self.scan_unit_sysd_files()
        if module and module in self._file_for_unit_sysd:
            return self._file_for_unit_sysd[module]
        if module and module+".service" in self._file_for_unit_sysd:
            return self._file_for_unit_sysd[module+".service"]
        return None
    def scan_unit_sysv_files(self, module = None): # -> [ unit-names,... ]
        """ reads all init.d files, returns the first filename when unit is a '.service' """
        if self._file_for_unit_sysv is None:
            self._file_for_unit_sysv = {}
            for folder in (self._sysv_folder1, self._sysv_folder2):
                if self._root:
                    folder = os_path(self._root, folder)
                if not os.path.isdir(folder):
                    continue
                for name in os.listdir(folder):
                    path = os.path.join(folder, name)
                    if os.path.isdir(path):
                        continue
                    service_name = name+".service"
                    if service_name not in self._file_for_unit_sysv:
                        self._file_for_unit_sysv[service_name] = path
            logg.debug("found %s sysv files", len(self._file_for_unit_sysv))
        return list(self._file_for_unit_sysv.keys())
    def unit_sysv_file(self, module = None): # -> filename?
        """ file path for the given module (sysv) """
        self.scan_unit_sysv_files()
        if module and module in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[module]
        if module and module+".service" in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[module+".service"]
        return None
    def is_sysv_file(self, filename):
        """ for routines that have a special treatment for init.d services """
        self.unit_file() # scan all
        if not filename: return None
        if filename in self._file_for_unit_sysd.values(): return False
        if filename in self._file_for_unit_sysv.values(): return True
        return None # not True
    def load_unit_conf(self, module): # -> conf | None(not-found)
        """ read the unit file with a UnitParser (sysv or systemd) """
        try:
            data = self.load_sysd_unit_conf(module)
            if data is not None: 
                return data
            data = self.load_sysv_unit_conf(module)
            if data is not None: 
                return data
        except Exception as e:
            logg.error("%s: %s", module, e)
        return None
    def load_sysd_unit_conf(self, module): # -> conf?
        """ read the unit file with a UnitParser (systemd) """
        path = self.unit_sysd_file(module)
        if not path: return None
        if path in self._loaded_file_sysd:
            return self._loaded_file_sysd[path]
        unit = UnitParser()
        unit.read_sysd(path)
        override_d = path + ".d"
        if os.path.isdir(override_d):
            for name in os.listdir(override_d):
                path = os.path.join(override_d, name)
                if os.path.isdir(path):
                    continue
                if name.endswith(".conf"):
                    unit.read_sysd(path)
        self._loaded_file_sysd[path] = unit
        return unit
    def load_sysv_unit_conf(self, module): # -> conf?
        """ read the unit file with a UnitParser (sysv) """
        path = self.unit_sysv_file(module)
        if not path: return None
        if path in self._loaded_file_sysv:
            return self._loaded_file_sysv[path]
        unit = UnitParser()
        unit.read_sysv(path)
        self._loaded_file_sysv[path] = unit
        return unit
    def default_unit_conf(self, module): # -> conf
        """ a unit conf that can be printed to the user where
            attributes are empty and loaded() is False """
        conf = UnitParser()
        conf.set("Unit","Id", module)
        conf.set("Unit", "Names", module)
        conf.set("Unit", "Description", "NOT-FOUND "+module)
        return conf
    def get_unit_conf(self, module): # -> conf (conf | default-conf)
        """ accept that a unit does not exist 
            and return a unit conf that says 'not-loaded' """
        conf = self.load_unit_conf(module)
        if conf is not None:
            return conf
        return self.default_unit_conf(module)
    def match_units(self, modules = None, suffix=".service"): # -> [ units,.. ]
        """ Helper for about any command with multiple units which can
            actually be glob patterns on their respective unit name. 
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        found = []
        for unit in self.match_sysd_units(modules, suffix):
            if unit not in found:
                found.append(unit)
        for unit in self.match_sysv_units(modules, suffix):
            if unit not in found:
                found.append(unit)
        return found
    def match_sysd_units(self, modules = None, suffix=".service"): # -> generate[ unit ]
        """ make a file glob on all known units (systemd areas).
            It returns all modules if no modules pattern were given.
            Also a single string as one module pattern may be given. """
        modules = to_list(modules)
        self.scan_unit_sysd_files()
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
        for item in sorted(self._file_for_unit_sysv.keys()):
            if not modules:
                yield item
            elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                yield item
            elif [ module for module in modules if module+suffix == item ]:
                yield item
    def list_service_unit_basics(self):
        """ show all the basic loading state of services """
        filename = self.unit_file() # scan all
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
        for unit in self.match_units(modules):
            result[unit] = "not-found"
            active[unit] = "inactive"
            substate[unit] = "dead"
            description[unit] = ""
            try: 
                conf = self.get_unit_conf(unit)
                result[unit] = "loaded"
                description[unit] = self.get_description_from(conf)
                active[unit] = self.get_active_from(conf)
                substate[unit] = self.get_substate_from(conf)
            except Exception as e:
                logg.warning("list-units: %s", e)
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
        return result + [ "", found, hint ]
    def list_service_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """ show all the service units and the enabled status"""
        result = {}
        enabled = {}
        for unit in self.match_units(modules):
            result[unit] = None
            enabled[unit] = ""
            try: 
                conf = self.get_unit_conf(unit)
                result[unit] = conf
                enabled[unit] = self.enabled_from(conf)
            except Exception as e:
                logg.warning("list-units: %s", e)
        return [ (unit, enabled[unit]) for unit in sorted(result) ]
    def list_target_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """ show all the target units and the enabled status"""
        result = {}
        enabled = {}
        for unit in _all_common_targets:
            result[unit] = None
            enabled[unit] = "static"
            if unit in _all_common_enabled:
                enabled[unit] = "enabled"
            if unit in _all_common_disabled:
                enabled[unit] = "enabled"
        return [ (unit, enabled[unit]) for unit in sorted(result) ]
    def show_list_unit_files(self, *modules): # -> [ (unit,enabled) ]
        """[PATTERN]... -- List installed unit files
        List installed unit files and their enablement state (as reported
        by is-enabled). If one or more PATTERNs are specified, only units
        whose filename (just the last component of the path) matches one of
        them are shown. This command reacts to limitations of --type being
        --type=service or --type=target (and --now for some basics)."""
        if self._now:
            result = self.list_service_unit_basics()
        elif self._unit_type == "target":
            result = self.list_target_unit_files()
        elif self._unit_type == "service":
            result = self.list_service_unit_files()
        elif self._unit_type:
            logg.error("unsupported unit --type=%s", self._unit_type)
            result = []
        else:
            result = self.list_target_unit_files()
            result += self.list_service_unit_files(*modules)
        if self._no_legend:
            return result
        found = "%s unit files listed." % len(result)
        return [ ("UNIT FILE", "STATE") ] + result + [ "", found ]
    ##
    ##
    def get_description(self, unit, default = None):
        return self.get_description_from(self.load_unit_conf(unit))
    def get_description_from(self, conf, default = None): # -> text
        """ Unit.Description could be empty sometimes """
        if not conf: return default or ""
        return conf.get("Unit", "Description", default or "")
    def write_pid_file(self, pid_file, pid): # -> bool(written)
        """ if a pid_file is known then path is created and the
            give pid is written as the only content. """
        if not pid_file: 
            logg.debug("pid %s but no pid_file", pid)
            return False
        dirpath = os.path.dirname(os.path.abspath(pid_file))
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        try:
            with open(pid_file, "w") as f:
                f.write("{}\n".format(pid))
        except IOError as e:
            logg.error("PID %s -- %s", pid, e)
        return True
    def read_pid_file(self, pid_file, default = None):
        pid = default
        if not pid_file:
            return default
        if not os.path.isfile(pid_file):
            return default
        try:
            for line in open(pid_file):
                if line.strip(): 
                    pid = to_int(line.strip())
                    break
        except:
            logg.warning("bad read of pid file '%s'", pid_file)
        return pid
    def wait_pid_file(self, pid_file, timeout = None): # -> pid?
        """ wait some seconds for the pid file to appear and return the pid """
        timeout = int(timeout or self._WaitProcFile)
        timeout = max(timeout, MinimumWaitProcFile)        
        dirpath = os.path.dirname(os.path.abspath(pid_file))
        for x in xrange(timeout):
            if not os.path.isdir(dirpath):
                self.sleep(1)
                continue
            pid = self.read_pid_file(pid_file)
            if not pid:
                self.sleep(1)
                continue
            if not pid_exists(pid):
                self.sleep(1)
                continue
            return pid
        return None
    def default_pid_file(self, unit): # -> text
        """ default file pattern where to store a pid """
        folder = self._pid_file_folder
        if self._root:
            folder = os_path(self._root, folder)
        name = "%s.pid" % unit
        return os.path.join(folder, name)
    def get_pid_file(self, unit):
        """ get the specified or default pid file path """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return None
        return self.get_pid_file_from(conf)
    def get_pid_file_from(self, conf, default = None):
        """ get the specified or default pid file path """
        if not conf: return default
        if not conf.filename(): return default
        unit = os.path.basename(conf.filename())
        if default is None:
            default = self.default_pid_file(unit)
        return self.pid_file_from(conf, default)
    def pid_file_from(self, conf, default = ""):
        """ get the specified pid file path (not a computed default) """
        return conf.get("Service", "PIDFile", default)
    def default_status_file(self, unit): # -> text
        """ default file pattern where to store a status mark """
        folder = self._pid_file_folder
        if self._root:
            folder = os_path(self._root, folder)
        name = "%s.status" % unit
        return os.path.join(folder, name)
    def get_status_file(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return None
        return self.get_status_file_from(conf)
    def get_status_file_from(self, conf, default = None):
        if not conf: return default
        if not conf.filename(): return default
        unit = os.path.basename(conf.filename())
        if default is None:
            default = self.default_status_file(unit)
        return self.status_file_from(conf, default)
    def status_file_from(self, conf, default = ""):
        return conf.get("Service", "StatusFile", default)
        # this not a real setting.
    def write_status_file(self, status_file, **status): # -> bool(written)
        """ if a status_file is known then path is created and the
            give status is written as the only content. """
        if not status_file: 
            logg.debug("status %s but no status_file", pid)
            return False
        dirpath = os.path.dirname(os.path.abspath(status_file))
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        try:
            with open(status_file, "w") as f:
                for key in sorted(status.keys()):
                    value = status[key]
                    if value is None: value = ""
                    if key.upper() == "AS": key = "ACTIVESTATE"
                    if key.upper() == "PID": key = "MAINPID"
                    if key.upper() == "EXIT": key = "EXIT_STATUS"
                    f.write("{}={}\n".format(key.upper(), str(value)))
        except IOError as e:
            logg.error("STATUS %s -- %s", status, e)
        return True
    def read_status_file(self, status_file, defaults = None):
        status = {}
        if hasattr(defaults, "keys"):
           for key in defaults.keys():
               status[key] = defaults[key]
        elif isinstance(defaults, string_types):
           status["ACTIVESTATE"] = defaults
        if not status_file:
            return status
        if not os.path.isfile(status_file):
            return status
        try:
            for line in open(status_file):
                if line.strip(): 
                    m = re.match(r"^(\w+)[:=](.*)", line)
                    if m:
                        key, value = m.group(1), m.group(2)
                        if key.strip():
                            status[key.strip()] = value.strip()
                    elif line in [ "active", "inactive", "failed"]:
                        status["ACTIVESTATE"] = line
                    else:
                        logg.warning("ignored %s", line.strip())
        except:
            logg.warning("bad read of status file '%s'", status_file)
        return status
    #
    def sleep(self, seconds = None): 
        """ just sleep """
        seconds = seconds or MinimumSleep
        time.sleep(seconds)
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
        try:
            for real_line in env_part.split("\n"):
                line = real_line.strip()
                if not line or line.startswith("#"):
                    continue
                for m in re.finditer(r'"([\w_]+)[=]([^"]*)"', line):
                    line = line.replace(m.group(0), '', 1)
                    yield m.group(1), m.group(2)
                for m in re.finditer(r"([\w_]+)[=]'([^']*)'", line):
                    line = line.replace(m.group(0), '', 1)
                    yield m.group(1), m.group(2)
                for m in re.finditer(r'([\w_]+)[=]"([^"]*)"', line):
                    line = line.replace(m.group(0), '', 1)
                    yield m.group(1), m.group(2)
                for m in re.finditer(r'([\w_]+)[=](.*)', line):
                    line = line.replace(m.group(0), '', 1)
                    yield m.group(1).lstrip(), m.group(2).rstrip()
        except Exception as e:
            logg.info("while reading %s: %s", env_part, e)
    def show_environment(self, unit):
        """ [UNIT]. -- show environment parts """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        return self.get_env(conf)
    def bad_service_from(self, conf):
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
            if env_file.startswith("-"): continue
            if not os.path.isfile(os_path(self._root, env_file)):
                logg.warning("non-existant EnvironmentFile=%s", env_file)
                return True
        return False
    def get_env(self, conf):
        env = os.environ.copy()
        for env_part in conf.getlist("Service", "Environment", []):
            for name, value in self.read_env_part(env_part):
                env[name] = self.expand_env(value, env)
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
            for name, value in self.read_env_file(env_file):
                env[name] = self.expand_env(value, env)
        return env
    def expand_env(self, cmd, env):
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
        #
        maxdepth = 20
        expanded = re.sub("[$](\w+)", lambda m: get_env1(m), cmd.replace("\\\n",""))
        for depth in xrange(maxdepth):
            new_text = re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), expanded)
            if new_text == expanded:
                return expanded
            expanded = new_text
        logg.error("shell variable expansion exceeded maxdepth %s", maxdepth)
        return expanded
    def exec_cmd(self, cmd, env, conf = None):
        cmd1 = cmd.replace("\\\n","")
        # according to documentation the %n / %% need to be expanded where in
        # most cases they are shell-escaped values. So we do it before shlex.
        def sh_escape(value):
            return "'" + value.replace("'","\\'") + "'"
        def get_confs(conf):
            confs={ "%": "%" }
            if not conf:
                return confs
            confs["N"] = conf.name()
            confs["n"] = sh_escape(conf.name())
            confs["f"] = sh_escape(conf.filename())
            confs["t"] = os_path(self._root, "/var")
            unit_name = conf.name()
            suffix = unit_name.rfind(".")
            if suffix > 0: unit_name = unit_name[:suffix]
            prefix, instance = unit_name, ""
            if "@" in unit_name:
                prefix, instance = unit_name.split("@", 1)
            confs["P"] = prefix
            confs["p"] = sh_escape(prefix)
            confs["I"] = instance
            confs["i"] = sh_escape(instance)
            return confs
        def get_conf1(m):
            confs = get_confs(conf)
            if m.group(1) in confs:
                return confs[m.group(1)]
            logg.warning("can not expand %%%s", m.group(1))
            return "''" # empty escaped string
        cmd2 = re.sub("[%](.)", lambda m: get_conf1(m), cmd1)
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
        import shlex
        newcmd = []
        for part in shlex.split(cmd3):
            newcmd += [ re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), part) ]
        return newcmd
    def sudo_from(self, conf):
        """ calls runuser with a (non-priviledged) user """
        runuser = conf.get("Service", "User", "")
        rungroup = conf.get("Service", "Group", "")
        sudo = []
        if os.geteuid() == 0:
            if runuser and rungroup:
                sudo = ["/usr/sbin/runuser", "-g", rungroup, "-u", runuser, "--"]
            elif runuser:
                sudo = ["/usr/sbin/runuser", "-u", runuser, "--"]
            elif rungroup:
                sudo = ["/usr/sbin/runuser", "-g", rungroup, "--"]
        elif os.path.exists("/usr/bin/sudo"):
            if runuser and rungroup:
                sudo = ["/usr/bin/sudo", "-n", "-H", "-g", rungroup, "-u", runuser, "--"]
            elif runuser:
                sudo = ["/usr/bin/sudo", "-n", "-H", "-u", runuser, "--"]
            elif rungroup:
                sudo = ["/usr/bin/sudo", "-n", "-H", "-g", rungroup, "--"]
            if sudo and not self._no_ask_password:
                logg.warning("non-root execution, better use --no-ask-password")
        else:
            if runuser or rungroup:
               logg.error("can not find sudo but it is required for runuser")
        return sudo
    def open_journal_log(self, conf):
        name = conf.filename()
        if name:
            log_folder = self._journal_log_folder
            if self._root:
                log_folder = os_path(self._root, log_folder)
            log_file = name.replace(os.path.sep,".") + ".log"
            x = log_file.find(".", 1)
            if x > 0: log_file = log_file[x+1:]
            if not os.path.isdir(log_folder):
                os.makedirs(log_folder)
            return open(os.path.join(log_folder, log_file), "w")
        return open("/dev/null", "w")
    def chdir_workingdir(self, conf, check = True):
        """ if specified then change the working directory """
        # the original systemd will start in '/' even if User= is given
        if self._root:
            os.chdir(self._root)
        workingdir = conf.get("Service", "WorkingDirectory", "")
        if workingdir:
            ignore = False
            if workingdir.startswith("-"):
                workingdir = workingdir[1:]
                ignore = True
            into = os_path(self._root, workingdir)
            try: 
               return os.chdir(into)
            except Exception as e:
               if not ignore:
                   logg.error("chdir workingdir '%s': %s", into, e)
                   if check: raise
        return None
    def notify_socket_from(self, conf, socketfile = None):
        """ creates a notify-socket for the (non-privileged) user """
        NotifySocket = collections.namedtuple("NotifySocket", ["socket", "socketfile" ])
        runuser = conf.get("Service", "User", "")
        sudo = ""
        if runuser and os.geteuid() != 0:
           logg.error("can not exec notify-service from non-root caller")
           return None
        notify_socket_folder = self._notify_socket_folder
        if self._root:
           notify_socket_folder = os_path(self._root, notify_socket_folder)
        notify_socket = os.path.join(notify_socket_folder, self._notify_socket_name)
        socketfile = socketfile or notify_socket
        if not os.path.isdir(os.path.dirname(socketfile)):
            os.makedirs(os.path.dirname(socketfile))
        if os.path.exists(socketfile):
           os.unlink(socketfile)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(socketfile)
        os.chmod(socketfile, 0o777)
        return NotifySocket(sock, socketfile)
    def read_notify_socket(self, notify, timeout):
        notify.socket.settimeout(timeout or DefaultMaximumTimeout)
        result = ""
        try:
            result, client_address = notify.socket.recvfrom(4096)
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
        if not notify:
            logg.info("no $NOTIFY_SOCKET, waiting %s", timeout)
            time.sleep(timeout)
            return {}
        if not os.path.exists(notify.socketfile):
            logg.info("no $NOTIFY_SOCKET exists")
            return {}
        #
        logg.info("wait $NOTIFY_SOCKET, timeout %s", timeout)
        results = {}
        seenREADY = None
        for attempt in xrange(timeout+1):
            if pid and not self.is_active_pid(pid):
                logg.info("dead PID %s", pid)
                return results
            if not attempt: # first one
                time.sleep(1)
                continue
            result = self.read_notify_socket(notify, 1) # sleep max 1 second
            if not result: # timeout
                time.sleep(1)
                continue
            for name, value in self.read_env_part(result):
                results[name] = value
                if name == "READY":
                    seenREADY = value
                if name in ["STATUS", "ACTIVESTATE"]:
                    logg.debug("%s: %s", name, value)
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
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
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
        done = True
        for unit in self.sortedAfter(units):
            if not self.start_unit(unit):
                done = False
        if init:
            logg.info("init-loop start")
            sig = self.init_loop_until_stop()
            logg.info("init-loop %s", sig)
            for unit in self.sortedBefore(units):
                self.stop_unit(unit)
        return done
    def start_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" start unit %s => %s", unit, conf.filename())
        return self.start_unit_from(conf)
    def get_TimeoutStartSec(self, conf):
        timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutStartSec)
        timeout = conf.get("Service", "TimeoutStartSec", timeout)
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def start_unit_from(self, conf):
        if not conf: return
        if self.bad_service_from(conf): return False
        timeout = self.get_TimeoutStartSec(conf)
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        # for StopPost on failure:
        returncode = 0
        service_result = "success"
        if True:
            if runs in [ "simple", "forking", "notify" ]:
                pid_file = self.get_pid_file_from(conf)
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
            for cmd in conf.getlist("Service", "ExecStartPre", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info(" pre-start %s", shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
        if runs in [ "sysv" ]:
            status_file = self.get_status_file_from(conf)
            if True:
                exe = conf.filename()
                cmd = "'%s' start" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode:
                    logg.info("%s start done %s", runs, run.returncode)
                    self.write_status_file(status_file, AS="failed", EXIT=run.returncode)
                else:
                    logg.info("%s start done OK", runs)
                    self.write_status_file(status_file, AS="active")
                return True
        elif runs in [ "oneshot" ]:
            status_file = self.get_status_file_from(conf)
            status = self.read_status_file(status_file)
            if status.get("ACTIVESTATE", "unkown") == "active":
                logg.warning("the service was already up once")
                return True
            for cmd in conf.getlist("Service", "ExecStart", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode and check: 
                    returncode = run.returncode
                    service_result = "failed"
                    logg.error("%s start %s (%s)", runs, service_result, returncode)
                    break
                logg.info("%s start done (%s)", runs, returncode)
            if True:
                if returncode:
                    self.write_status_file(status_file, AS="failed", EXIT=returncode)
                else:
                    self.write_status_file(status_file, AS="active")
        elif runs in [ "simple" ]: 
            pid_file = self.get_pid_file_from(conf)
            pid = self.read_pid_file(pid_file, "")
            if self.is_active_pid(pid):
                logg.warning("the service is already running on PID %s", pid)
                return True
            runuser = conf.get("Service", "User", "")
            rungroup = conf.get("Service", "Group", "")
            if not os.fork(): # pragma: no cover
                os.setsid() # detach child process from parent
                sys.exit(self.exec_start_from(conf, env)) # and exit after call
            else:
                # parent
                pid = self.wait_pid_file(pid_file)
                logg.info("%s start done PID %s [%s]", runs, pid, pid_file)
                time.sleep(1) # give it another second to come up
                pid = self.read_pid_file(pid_file, "")
                if pid:
                   env["MAINPID"] = str(pid)
                else:
                   service_result = "timeout" # "could not start service"
        elif runs in [ "notify" ]:
            # "notify" is the same as "simple" but we create a $NOTIFY_SOCKET 
            # and wait for startup completion by checking the socket messages
            pid_file = self.get_pid_file_from(conf)
            pid = self.read_pid_file(pid_file, "")
            if self.is_active_pid(pid):
                logg.error("the service is already running on PID %s", pid)
                return False
            runuser = conf.get("Service", "User", "")
            rungroup = conf.get("Service", "Group", "")
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                logg.debug("use NOTIFY_SOCKET=%s", notify.socketfile)
            if not os.fork(): # pragma: no cover
                os.setsid() # detach child process from parent
                sys.exit(self.exec_start_from(conf, env)) # and exit after call
            else:
                # parent
                mainpid = self.wait_pid_file(pid_file) # fork is running
                results = self.wait_notify_socket(notify, timeout, mainpid)
                if "MAINPID" in results:
                    new_pid = results["MAINPID"]
                    if new_pid and to_int(new_pid) != mainpid:
                        logg.info("NEW PID %s from sd_notify (was PID %s)", new_pid, mainpid)
                        self.write_pid_file(pid_file, new_pid)
                logg.info("%s start done %s", runs, pid_file)
                pid = self.read_pid_file(pid_file, "")
                if pid:
                    env["MAINPID"] = str(pid)
                else:
                    service_result = "timeout" # "could not start service"
        elif runs in [ "forking" ]:
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecStart", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s start %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode and check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
                if pid_file:
                    pid = self.wait_pid_file(pid_file)
                    logg.info("%s start done PID %s [%s]", runs, pid, pid_file)
                    if pid:
                        env["MAINPID"] = str(pid)
            if not pid_file:
                self.sleep()
                logg.warning("No PIDFile for forking %s", conf.filename())
                status_file = self.get_status_file_from(conf)
                if not returncode:
                    self.write_status_file(status_file, AS="active")
                else:
                    self.write_status_file(status_file, AS="failed", EXIT=returncode)
        else:
            logg.error("unsupported run type '%s'", runs)
            return False
        # POST sequence
        active = self.is_active_from(conf)
        if not active:
            # according to the systemd documentation, a failed start-sequence
            # should execute the ExecStopPost sequence allowing some cleanup.
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist("Service", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-fail %s", shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
            return False
        else:
            for cmd in conf.getlist("Service", "ExecStartPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-start %s", shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
            return True
    def exec_start_unit(self, unit):
        """ helper function to test the code that is normally forked off """
        conf = self.load_unit_conf(unit)
        env = self.get_env(conf)
        return self.exec_start_from(conf, env)
    def exec_start_from(self, conf, env):
        """ this code is commonly run in a child process // returns exit-code"""
        runs = conf.get("Service", "Type", "simple").lower()
        logg.debug("%s process for %s", runs, conf.filename())
        #
        # os.setsid() # detach from parent // required to be done in caller code 
        #
        returncode = None
        pid_file = self.get_pid_file_from(conf)
        inp = open("/dev/zero")
        out = self.open_journal_log(conf)
        os.dup2(inp.fileno(), sys.stdin.fileno())
        os.dup2(out.fileno(), sys.stdout.fileno())
        os.dup2(out.fileno(), sys.stderr.fileno())
        runuser = conf.get("Service", "User", "")
        rungroup = conf.get("Service", "Group", "")
        shutil_truncate(pid_file)
        shutil_chown(pid_file, runuser, rungroup)
        shutil_setuid(runuser, rungroup)
        self.chdir_workingdir(conf, check = False)
        cmdlist = conf.getlist("Service", "ExecStart", [])
        for idx, cmd in enumerate(cmdlist):
            logg.debug("ExecStart[%s]: %s", idx, cmd)
        for cmd in cmdlist:
            pid = self.read_pid_file(pid_file, "")
            env["MAINPID"] = str(pid)
            newcmd = self.exec_cmd(cmd, env, conf)
            logg.info("%s start %s", runs, shell_cmd(newcmd))
            run = subprocess.Popen(newcmd, env=env, close_fds=True, 
                stdin=inp, stdout=out, stderr=out)
            self.write_pid_file(pid_file, run.pid)
            logg.info("%s started PID %s", runs, run.pid)
            run.wait()
            logg.info("%s stopped PID %s EXIT %s", runs, run.pid, run.returncode)
            returncode = run.returncode
            pid = self.read_pid_file(pid_file, "")
            if str(pid) == str(run.pid):
                self.write_pid_file(pid_file, "")
        logg.info("returncode %s", returncode)
        return returncode
    def stop_modules(self, *modules):
        """ [UNIT]... -- stop these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.stop_units(units) and found_all
    def stop_units(self, units):
        """ fails if any unit fails to stop """
        done = True
        for unit in self.sortedBefore(units):
            if not self.stop_unit(unit):
                done = False
        return done
    def stop_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" stop unit %s => %s", unit, conf.filename())
        return self.stop_unit_from(conf)
    def get_TimeoutStopSec(self, conf):
        timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutStartSec)
        timeout = conf.get("Service", "TimeoutStopSec", timeout)
        return time_to_seconds(timeout, DefaultMaximumTimeout)
    def stop_unit_from(self, conf):
        if not conf: return
        if self.bad_service_from(conf): return False
        timeout = self.get_TimeoutStopSec(conf)
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        returncode = 0
        service_result = "success"
        if runs in [ "sysv" ]:
            status_file = self.get_status_file_from(conf)
            if True:
                exe = conf.filename()
                cmd = "'%s' stop" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode:
                    self.write_status_file(status_file, AS="failed", EXIT=run.returncode)
                elif os.path.isfile(status_file):
                    os.remove(status_file)
                return True
        elif runs in [ "oneshot" ]:
            status_file = self.get_status_file_from(conf)
            status = self.read_status_file(status_file)
            if status.get("ACTIVESTATE", "unknown") == "inactive":
                logg.warning("the service is already down once")
                return True
            for cmd in conf.getlist("Service", "ExecStop", []):
                check, cmd = checkstatus(cmd)
                logg.debug("{env} %s", env)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode and check: 
                    returncode = run.returncode
                    service_result = "failed"
                    break
            if True:
                if returncode:
                    self.write_status_file(status_file, AS="failed", EXIT=returncode)
                elif os.path.isfile(status_file):
                    os.remove(status_file)
        ### fallback Stop => Kill for ["simple","notify","forking"]
        elif not conf.getlist("Service", "ExecStop", []):
            logg.info("no ExecStop => systemctl kill")
            if True:
                status_file = self.get_pid_file_from(conf)
                pid_file = self.get_pid_file_from(conf)
                self.kill_unit_from(conf)
                if os.path.isfile(pid_file):
                    os.remove(pid_file)
                if os.path.isfile(status_file):
                    os.remove(status_file)
        elif runs in [ "simple", "notify" ]:
            pid_file = self.get_pid_file_from(conf)
            pid = 0
            for cmd in conf.getlist("Service", "ExecStop", []):
                check, cmd = checkstatus(cmd)
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s stop %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                # self.write_pid_file(pid_file, run.pid)
                if run.returncode and check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = env.get("MAINPID",0)
            if pid:
                if self.wait_vanished_pid(pid, timeout):
                    if os.path.isfile(pid_file):
                        os.remove(pid_file)
            else:
                logg.info("%s sleep as no PID was found on Stop", runs)
                self.sleep()
                pid = self.read_pid_file(pid_file, "")
                if not pid or not pid_exists(pid) or pid_zombie(pid):
                    if os.path.isfile(pid_file):
                        os.remove(pid_file)
        elif runs in [ "forking" ]:
            status_file = self.get_status_file_from(conf)
            pid_file = self.pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecStop", []):
                active = self.is_active_from(conf)
                if pid_file:
                    new_pid = self.read_pid_file(pid_file, "")
                    if new_pid:
                        env["MAINPID"] = str(new_pid)
                check, cmd = checkstatus(cmd)
                logg.debug("{env} %s", env)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("fork stop %s", shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode and check:
                    returncode = run.returncode
                    service_result = "failed"
                    break
            pid = env.get("MAINPID",0)
            if pid:
                if self.wait_vanished_pid(pid, timeout):
                    if os.path.isfile(pid_file):
                        os.remove(pid_file)
            else:
                logg.info("%s sleep as no PID was found on Stop", runs)
                self.sleep()
                pid = self.read_pid_file(pid_file, "")
                if not pid or not pid_exists(pid) or pid_zombie(pid):
                    if os.path.isfile(pid_file):
                        os.remove(pid_file)
            if os.path.isfile(status_file):
                if not returncode:
                    os.remove(status_file)
                else:
                    self.write_status_file(status_file, AS=service_result, EXIT=returncode)
        else:
            logg.error("unsupported run type '%s'", runs)
            return False
        # POST sequence
        active = self.is_active_from(conf)
        if not active:
            env["SERVICE_RESULT"] = service_result
            for cmd in conf.getlist("Service", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("post-stop %s", shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
        return service_result == "success"
    def wait_vanished_pid(self, pid, timeout):
        if not pid:
            return True
        logg.info("wait for PID %s to vanish", pid)
        for x in xrange(int(timeout)):
            if not self.is_active_pid(pid):
                logg.info("wait for PID %s is done (%s.)", pid, x)
                return True
            self.sleep()
        logg.info("wait for PID %s failed (%s.)", pid, x)
        return False
    def reload_modules(self, *modules):
        """ [UNIT]... -- reload these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.reload_units(units) and found_all
    def reload_units(self, units):
        """ fails if any unit fails to reload """
        done = True
        for unit in self.sortedAfter(units):
            if not self.reload_unit(unit):
                done = False
        return done
    def reload_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" reload unit %s => %s", unit, conf.filename())
        return self.reload_unit_from(conf)
    def reload_unit_from(self, conf):
        if not conf: return
        if self.bad_service_from(conf): return False
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        if runs in [ "sysv" ]:
            status_file = self.get_status_file_from(conf)
            if True:
                exe = conf.filename()
                cmd = "'%s' reload" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s reload %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if run.returncode:
                    self.write_status_file(status_file, AS="failed", EXIT=run.returncode)
                    return False
                else:
                    self.write_status_file(status_file, AS="active")
                    return True
        elif runs in [ "simple", "notify", "forking" ]:
            if not self.is_active_from(conf):
                logg.info("no reload on inactive service %s", conf.name())
                return True
            for cmd in conf.getlist("Service", "ExecReload", []):
                pid_file = self.get_pid_file_from(conf)
                if pid_file:
                    pid = self.read_pid_file(pid_file, "")
                    env["MAINPID"] = str(pid)
                check, cmd = checkstatus(cmd)
                newcmd = self.exec_cmd(cmd, env, conf)
                logg.info("%s reload %s", runs, shell_cmd(sudo+newcmd))
                run = subprocess_wait(sudo+newcmd, env)
                if check and run.returncode: raise Exception("ExecReload")
            self.sleep()
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
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.restart_units(units) and found_all
    def restart_units(self, units):
        """ fails if any unit fails to restart """
        done = True
        for unit in self.sortedAfter(units):
            if not self.restart_unit(unit):
                done = False
        return done
    def restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" restart unit %s => %s", unit, conf.filename())
        if not self.is_active_from(conf):
            return self.start_unit_from(conf)
        else:
            return self.restart_unit_from(conf)
    def restart_unit_from(self, conf):
        if not conf: return
        if self.bad_service_from(conf): return False
        logg.info("(restart) => stop/start")
        self.stop_unit_from(conf)
        return self.start_unit_from(conf)
    def try_restart_modules(self, *modules):
        """ [UNIT]... -- try-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.try_restart_units(units) and found_all
    def try_restart_units(self, units):
        """ fails if any module fails to try-restart """
        done = True
        for unit in self.sortedAfter(units):
            if not self.try_restart_unit(unit):
                done = False
        return done
    def try_restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        if self.is_active_from(conf):
            return self.restart_unit_from(conf)
        return True
    def reload_or_restart_modules(self, *modules):
        """ [UNIT]... -- reload-or-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.reload_or_restart_units(units) and found_all
    def reload_or_restart_units(self, units):
        """ fails if any unit does not reload-or-restart """
        done = True
        for unit in self.sortedAfter(units):
            if not self.reload_or_restart_unit(unit):
                done = False
        return done
    def reload_or_restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" reload-or-restart unit %s => %s", unit, conf.filename())
        return self.reload_or_restart_unit_from(conf)
    def reload_or_restart_unit_from(self, conf):
        if not self.is_active_from(conf):
            # try: self.stop_unit_from(conf)
            # except Exception as e: pass
            return self.start_unit_from(conf)
        elif conf.getlist("Service", "ExecReload", []):
            logg.info("found service to have ExecReload -> 'reload'")
            return self.reload_unit_from(conf)
        else:
            logg.info("found service without ExecReload -> 'restart'")
            return self.restart_unit_from(conf)
    def reload_or_try_restart_modules(self, *modules):
        """ [UNIT]... -- reload-or-try-restart these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.reload_or_try_restart_units(units) and found_all
    def reload_or_try_restart_units(self, units):
        """ fails if any unit fails to reload-or-try-restart """
        done = True
        for unit in self.sortedAfter(units):
            if not self.reload_or_try_restart_unit(unit):
                done = False
        return done
    def reload_or_try_restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" reload-or-try-restart unit %s => %s", unit, conf.filename())
        return self.reload_or_try_restart_unit_from(conf)
    def reload_or_try_restart_unit_from(self, conf):
        if conf.getlist("Service", "ExecReload", []):
            return self.reload_unit_from(conf)
        elif not self.is_active_from(conf):
            return True
        else:
            return self.restart_unit_from(conf)
    def kill_modules(self, *modules):
        """ [UNIT]... -- kill these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.kill_units(units) and found_all
    def kill_units(self, units):
        """ fails if any unit could not be killed """
        done = True
        for unit in self.sortedBefore(units):
            if not self.kill_unit(unit):
                done = False
        return done
    def kill_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info(" kill unit %s => %s", unit, conf.filename())
        return self.kill_unit_from(conf)
    def kill_unit_from(self, conf):
        if not conf: return None
        # useKillMode = conf.get("Service", "KillMode", "process")
        sendSIGKILL = conf.get("Service", "SendSIGKILL", "yes")
        sendSIGHUP = conf.get("Service", "SendSIGHUP", "no")
        useKillSignal = conf.get("Service", "KillSignal", "SIGTERM")
        kill_signal = getattr(signal, useKillSignal)
        timeout = self.get_TimeoutStopSec(conf)
        pid_file = self.get_pid_file_from(conf)
        pid = self.read_pid_file(pid_file)
        if not pid:
            logg.info("no main PID [%s]", conf.filename())
            return False
        logg.info("stop kill PID %s (%s)", pid, pid_file)
        dead = self._kill_pid(pid, kill_signal)
        if "y" in sendSIGHUP: 
            # TODO: should be sent to all the children
            self._kill_pid(pid, signal.SIGHUP)
        if not dead:
            dead = self._wait_killed_pid(pid, timeout)
        if not dead and "y" in sendSIGKILL:
            logg.info("hard kill PID %s (%s)", pid, pid_file)
            dead = self._kill_pid(pid, signal.SIGKILL)
            if not dead:
                dead = self._wait_killed_pid(pid, timeout)
        logg.info("done kill PID %s %s", pid, dead and "OK")
        return dead
    def _kill_pid(self, pid, kill_signal = None):
        try: 
            sig = kill_signal or signal.SIGTERM
            os.kill(pid, sig)
        except OSError as e:
            if e.errno == errno.ESRCH or e.errno == errno.ENOENT:
                logg.info("kill PID %s => No such process", pid)
                return True
            else:
                logg.error("kill PID %s => %s", pid, str(e))
                return False
        return not pid_exists(pid) or pid_zombie(pid)
    def _wait_killed_pid(self, pid, timeout):
        timeout = int(timeout or self._WaitKillProc)
        timeout = max(timeout, MinimumWaitKillProc)
        for x in xrange(timeout):
            if not pid_exists(pid) or pid_zombie(pid):
                break
            self.sleep(1)
        return not pid_exists(pid) or pid_zombie(pid)
    def is_active_modules(self, *modules):
        """ [UNIT].. -- check if these units are in active state
        implements True if all is-active = True """
        # systemctl returns multiple lines, one for each argument
        #   "active" when is_active
        #   "inactive" when not is_active
        #   "unknown" when not found
        # The return code is set to
        #   0 when "active"
        #   3 when any "inactive" or "unknown"
        # However: # TODO!!!!! BUG in original systemctl!!
        #   documentation says " exit code 0 if at least one is active"
        #   and "Unless --quiet is specified, print the unit state"
        found_all = True
        units = []
        results = []
        for module in modules:
            units = self.match_units([ module ])
            if not units:
                # logg.error("no such service '%s'", module)
                results += ["unknown"]
                found_all = False
                continue
            for unit in units:
                active = self.get_active_unit(unit) 
                results += [ active ]
                break
        known = [ result for result in results if result != "unknown" ]
        if True:
            ## how 'systemctl' works:
            inactive = "inactive" in results
            status = found_all and not inactive and not not known
        else:
            ## how it should work:
            active = "active" in results
            status = found_all and active and not not known
        if not _quiet:
            return status, results
        else:
            return status
    def is_active_from(self, conf):
        """ used in try-restart/other commands to check if needed. """
        if not conf: return False
        return self.get_active_from(conf) == "active"
    def active_pid_from(self, conf):
        if not conf: return False
        pid_file = self.get_pid_file_from(conf)
        pid = self.read_pid_file(pid_file)
        logg.debug("pid_file '%s' => PID %s", pid_file, pid)
        return self.is_active_pid(pid)
    def is_active_pid(self, pid):
        """ returns pid if the pid is still an active process """
        if pid and pid_exists(pid) and not pid_zombie(pid):
            return pid # usually a string (not null)
        return None
    def get_active_unit(self, unit):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        conf = self.get_unit_conf(unit)
        if not conf.loaded():
            logg.warning("no such unit '%s'", unit)
            return "unknown"
        return self.get_active_from(conf)
    def get_active_from(self, conf):
        """ returns 'active' 'inactive' 'failed' 'unknown' """
        # used in try-restart/other commands to check if needed.
        if not conf: return "unkonwn"
        status_file = self.get_status_file_from(conf)
        if status_file and os.path.exists(status_file):
            status = self.read_status_file(status_file)
            return status.get("ACTIVESTATE", "failed")
        pid_file = self.get_pid_file_from(conf)
        if not pid_file or not os.path.exists(pid_file):
            return "inactive"
        pid = self.read_pid_file(pid_file)
        logg.debug("pid_file '%s' => PID %s", pid_file, pid)
        if not pid_exists(pid) or pid_zombie(pid):
            return "failed"
        return "active"
    def get_substate_from(self, conf):
        """ returns 'running' 'exited' 'dead' 'failed' 'plugged' 'mounted' """
        if not conf: return False
        status_file = self.get_status_file_from(conf)
        if status_file and os.path.exists(status_file):
            status = self.read_status_file(status_file)
            state = status.get("ACTIVESTATE", "failed")
            if state in [ "active" ]:
                return status.get("STATUS", "running")
            else:
                return status.get("STATUS", "dead")
            # "STATUS" is defined in sd_notify(3) while
            # our "ACTIVESTATE" is used for the "ActiveState" property
        pid_file = self.get_pid_file_from(conf)
        if not pid_file or not os.path.exists(pid_file):
            return "dead"
        pid = self.read_pid_file(pid_file)
        logg.debug("pid_file '%s' => PID %s", pid_file, pid)
        if not pid_exists(pid) or pid_zombie(pid):
            return "failed"
        return "running"
    def is_failed_modules(self, *modules):
        """ [UNIT]... -- check if these units are in failes state
        implements True if any is-active = True """

        found_all = True
        units = []
        results = []
        for module in modules:
            units = self.match_units([ module ])
            if not units:
                # logg.error("no such service '%s'", module)
                results += ["unknown"]
                found_all = False
                continue
            for unit in units:
                active = self.get_active_unit(unit) 
                results += [ active ]
                break
        known = [ result for result in results if result != "unknown" ]
        failed = "failed" in results
        status = found_all and failed or not known
        if not _quiet:
            return status, results
        else:
            return status
    def is_failed_from(self, conf):
        if conf is None: return True
        return self.get_active_from(conf) == "failed"
    def status_modules(self, *modules):
        """ [UNIT]... check the status of these units.
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        status, result = self.status_units(units)
        if not found_all:
            status = 3 # same as (dead) # original behaviour
        return (status, result)
    def status_units(self, units):
        """ concatenates the status output of all units
            and the last non-successful statuscode """
        status, result = 0, ""
        for unit in units:
            status1, result1 = self.status_unit(unit)
            if status1: status = status1
            if result: result += "\n\n"
            result += result1
        return status, result
    def status_unit(self, unit):
        conf = self.get_unit_conf(unit)
        result = "%s - %s" % (unit, self.get_description_from(conf))
        if conf.loaded():
            result += "\n    Loaded: loaded ({}, {})".format(conf.filename(), self.enabled_from(conf) )
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
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        done, result = self.cat_units(units)
        return (done and found_all, result)
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
        return done, result
    def cat_unit(self, unit):
        try:
            unit_file = self.unit_file(unit)
            if unit_file:
                return open(unit_file).read()
            logg.error("no file for unit '%s'", unit)
        except Exception as e:
            print("Unit {} is not-loaded: {}".format(unit, e))
        return False
    ##
    ##
    def load_preset_files(self, module = None): # -> [ preset-file-names,... ]
        """ reads all preset files, returns the scanned files """
        if self._preset_file_list is None:
            self._preset_file_list = {}
            for folder in (self._preset_folder1, self._preset_folder2, self._preset_folder3, self._preset_folder4):
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
        for filename in sorted(self._preset_file_list.keys()):
            preset = self._preset_file_list[filename]
            status = preset.get_preset(unit)
            if status:
                return status
        return None
    def preset_modules(self, *modules):
        """ [UNIT]... -- set 'enabled' when in *.preset
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.preset_units(units) and found_all
    def preset_units(self, units):
        """ fails if any unit could not be changed """
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
        found_all = True
        units = self.match_units() # TODO: how to handle module arguments
        return self.preset_units(units) and found_all
    def wanted_from(self, conf, default = None):
        if not conf: return default
        return conf.get("Install", "WantedBy", default, True)
    def enablefolder(self, wanted = None):
        if not wanted: 
            return None
        if not wanted.endswith(".wants"):
            wanted = wanted + ".wants"
        return os.path.join("/etc/systemd/system", wanted)
    def enable_modules(self, *modules):
        """ [UNIT]... -- enable these units """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.enable_units(units) and found_all
    def enable_units(self, units):
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
            logg.error("no such unit '%s'", unit)
            return False
        if self.is_sysv_file(unit_file):
            return self.enable_unit_sysv(unit_file)
        wanted = self.wanted_from(self.get_unit_conf(unit))
        if not wanted: return False # wanted = "multi-user.target"
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
            m = re.match("S\d\d(.*)", found)
            if m and m.group(1) == name:
                nameS = found
            m = re.match("K\d\d(.*)", found)
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
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.disable_units(units) and found_all
    def disable_units(self, units):
        done = True
        for unit in units:
            if not self.disable_unit(unit):
               done = False
        return done
    def disable_unit(self, unit):
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("no such unit '%s'", unit)
            return False
        if self.is_sysv_file(unit_file):
            return self.disable_unit_sysv(unit_file)
        wanted = self.wanted_from(self.get_unit_conf(unit))
        folder = self.enablefolder(wanted)
        if self._root:
            folder = os_path(self._root, folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        if os.path.isfile(target):
            _f = self._force and "-f" or ""
            logg.info("rm {_f} '{target}'".format(**locals()))
            os.remove(target)
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
            m = re.match("S\d\d(.*)", found)
            if m and m.group(1) == name:
                nameS = found
            m = re.match("K\d\d(.*)", found)
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
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
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
        return result, infos
    def is_enabled(self, unit):
        unit_file = self.unit_file(unit)
        if not unit_file:
            logg.error("no such unit '%s'", unit)
            return False
        if self.is_sysv_file(unit_file):
            return self.is_enabled_sysv(unit_file)
        wanted = self.wanted_from(self.get_unit_conf(unit))
        folder = self.enablefolder(wanted)
        if self._root:
            folder = os_path(self._root, folder)
        if not wanted:
            return True
        target = os.path.join(folder, os.path.basename(unit_file))
        if os.path.isfile(target):
            return True
        return False
    def enabled_unit(self, unit):
        conf = self.get_unit_conf(unit)
        return self.enabled_from(conf)
    def enabled_from(self, conf):
        unit_file = conf.filename()
        if self.is_sysv_file(unit_file):
            state = self.is_enabled_sysv(unit_file)
            if state: 
                return "enabled"
            return "disabled"
        wanted = self.wanted_from(conf)
        if not wanted:
            return "static"
        folder = self.enablefolder(wanted)
        if self._root:
            folder = os_path(self._root, folder)
        target = os.path.join(folder, os.path.basename(unit_file))
        if os.path.isfile(target):
            return "enabled"
        return "disabled"
    def list_dependencies_modules(self, *modules):
        """ [UNIT]... show the dependency tree"
        """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
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
                for folder in [ self._sysd_folder1, self._sysd_folder2, self._sysd_folder3, self._sysd_folder4 ]:
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
                styles = to_list(styles)
                for dep_style in styles:
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
        for dep in sortedAfter(deps_conf, cmp=compareAfter):
            line = (dep.name(),  "(%s)" % (" ".join(deps[dep.name()])))
            result.append(line)
        return result
    def sortedAfter(self, unitlist):
        conflist = [ self.get_unit_conf(unit) for unit in unitlist ]
        sortlist = sortedAfter(conflist)
        return [ item.name() for item in sortlist ]
    def sortedBefore(self, unitlist):
        conflist = [ self.get_unit_conf(unit) for unit in unitlist ]
        sortlist = sortedAfter(reversed(conflist))
        return [ item.name() for item in reversed(sortlist) ]
    def system_daemon_reload(self):
        """ reload does will only check the service files here """
        ok = True
        for unit in self.match_units():
            try:
                conf = self.get_unit_conf(unit)
            except Exception as e:
                logg.error("%s: can not read unit file %s\n\t%s", 
                    unit, conf.filename(), e)
                continue
            self.syntax_check(conf)
        return True # and ok
    def syntax_check(self, conf):
        unit = conf.name()
        if not conf.has_section("Service"):
            if conf.filename() and conf.filename().endswith(".service"):
               logg.error("%s: .service file without [Service] section", unit)
            return False
        ok = False
        haveType = conf.get("Service", "Type", "simple")
        haveExecStart = conf.getlist("Service", "ExecStart", [])
        haveExecStop = conf.getlist("Service", "ExecStop", [])
        haveExecReload = conf.getlist("Service", "ExecReload", [])
        usedExecStart = []
        usedExecStop = []
        usedExecReload = []
        for line in haveExecStart:
            if not line.startswith("/") and not line.startswith("-/"):
                logg.error("%s: Executable path is not absolute, ignoring: %s", unit, line.strip())
                ok = False
            usedExecStart.append(line)
        for line in haveExecStop:
            if not line.startswith("/") and not line.startswith("-/"):
                logg.error("%s: Executable path is not absolute, ignoring: %s", unit, line.strip())
                ok = False
            usedExecStop.append(line)
        for line in haveExecReload:
            if not line.startswith("/") and not line.startswith("-/"):
                logg.error("%s: Executable path is not absolute, ignoring: %s", unit, line.strip())
                ok = False
            usedExecReload.append(line)
        if haveType in ["simple", "notify", "forking"]:
            if not usedExecStart and not usedExecStop:
                logg.error("%s: Service lacks both ExecStart and ExecStop= setting. Refusing.", unit)
                ok = False
            elif not usedExecStart and haveType != "oneshot":
                logg.error("%s: Service has no ExecStart= setting, which is only allowed for Type=oneshot services. Refusing.",  unit)
                ok = False
        if len(usedExecStart) > 1 and haveType != "oneshot":
            logg.error("%s: there may be only one ExecStart statement (unless for 'oneshot' services)."
              + "Use ' ; ' for multiple commands or better use ExecStartPre / ExecStartPost", unit)
            ok = False
        if len(usedExecStop) > 1 and haveType != "oneshot":
            logg.error("%s: there may be only one ExecStop statement (unless for 'oneshot' services)."
              + "Use ' ; ' for multiple commands or better use ExecStopPost", unit)
            ok = False
        if len(usedExecReload) > 1:
            logg.error("%s: there may be only one ExecReload statement."
              + "Use ' ; ' for multiple commands (ExecReloadPost or ExedReloadPre do not exit)", unit)
            ok = False
        if len(usedExecReload) > 0 and "/bin/kill " in usedExecReload[0]:
            logg.info("%s: the use of /bin/kill is not recommended for ExecReload as it is asychronous."
              + "That means all the dependencies will perform the reload simultanously / out of order.", unit)
        if conf.getlist("Service", "ExecRestart", []): #pragma: no cover
            logg.error("%s: there no such thing as an ExecRestart (ignored)", unit)
        if conf.getlist("Service", "ExecRestartPre", []): #pragma: no cover
            logg.error("%s: there no such thing as an ExecRestartPre (ignored)", unit)
        if conf.getlist("Service", "ExecRestartPost", []): #pragma: no cover 
            logg.error("%s: there no such thing as an ExecRestartPost (ignored)", unit)
        if conf.getlist("Service", "ExecReloadPre", []): #pragma: no cover
            logg.error("%s: there no such thing as an ExecReloadPre (ignored)", unit)
        if conf.getlist("Service", "ExecReloadPost", []): #pragma: no cover
            logg.error("%s: there no such thing as an ExecReloadPost (ignored)", unit)
        if conf.getlist("Service", "ExecStopPre", []): #pragma: no cover
            logg.error("%s: there no such thing as an ExecStopPre (ignored)", unit)
        return ok
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
  
           NOTE: only a subset of properties is implemented """
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.show_units(units) # and found_all
    def show_units(self, units):
        logg.debug("show --property=%s", self._unit_property)
        result = []
        for unit in units:
            if result: result += [ "", "" ]
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
        yield "Id", unit
        yield "Names", unit
        yield "Description", self.get_description_from(conf) # conf.get("Unit", "Description")
        yield "PIDFile", self.pid_file_from(conf) # not self.get_pid_file_from w/ default location
        yield "MainPID", self.active_pid_from(conf) or "0"  # status["MAINPID"]
        yield "SubState", self.get_substate_from(conf)      # status["STATUS"]
        yield "ActiveState", self.get_active_from(conf)     # status["ACTIVESTATE"]
        yield "LoadState", conf.loaded() and "loaded" or "not-loaded"
        yield "UnitFileState", self.enabled_from(conf)
        yield "TimeoutStartUSec", seconds_to_time(self.get_TimeoutStartSec(conf))
        yield "TimeoutStopUSec", seconds_to_time(self.get_TimeoutStopSec(conf))
        env_parts = []
        for env_part in conf.getlist("Service", "Environment", []):
            env_parts.append(env_part)
        if env_parts: 
            yield "Environment", " ".join(env_parts)
        env_files = []
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
            env_files.append(env_file)
        if env_files:
            yield "EnvironmentFile", " ".join(env_files)
    #
    igno_centos = [ "netconsole", "network" ]
    igno_opensuse = [ "raw", "pppoe", "*.local", "boot.*", "rpmconf*", "purge-kernels*", "postfix*" ]
    igno_ubuntu = [ "mount*", "umount*", "ondemand", "*.local" ]
    igno_always = [ "network*", "dbus", "systemd-*" ]
    def _ignored_unit(self, unit, ignore_list):
        for ignore in ignore_list:
            if fnmatch.fnmatchcase(unit, ignore):
                return True # ignore
            if fnmatch.fnmatchcase(unit, ignore+".service"):
                return True # ignore
        return False
    def system_default_services(self, sysv = "S", default_target = "multi-user.target"):
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
    def enabled_default_services(self, sysv = "S", default_target = "multi-user.target", igno = []):
        default_services = []
        for folder in [ self._sysd_folder1, self._sysd_folder2 ]:
            if self._root:
                folder = os_path(self._root, folder)
            enabled_folder = os.path.join(folder, default_target + ".wants")
            if os.path.isdir(enabled_folder):
                for unit in sorted(os.listdir(enabled_folder)):
                    path = os.path.join(enabled_folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(".service"):
                        default_services.append(unit)
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
                    unit = service+".service"
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    default_services.append(unit)
        return default_services
    def system_default(self, arg = True):
        """ start units for default system level
            This will go through the enabled services in the default 'multi-user.target'.
            However some services are ignored as being known to be installation garbage
            from unintended services. Use '--all' so start all of the installed services
            and with '--all --force' even those services that are otherwise wrong. 
            /// SPECIAL: with --now or --init the init-loop is run and afterwards
                a system_halt is performed with the enabled services to be stopped."""
        logg.info("system default requested - %s", arg)
        init = self._now or self._init
        self.start_system_default(init = init)
    def start_system_default(self, init = False):
        """ detect the default.target services and start them.
            When --init is given then the init-loop is run and
            the services are stopped again by 'systemctl halt'."""
        default_target = "multi-user.target"
        default_services = self.system_default_services("S", default_target)
        self.start_units(default_services)
        logg.info("system is up")
        if init:
            logg.info("init-loop start")
            sig = self.init_loop_until_stop()
            logg.info("init-loop %s", sig)
            self.stop_system_default()
    def stop_system_default(self):
        """ detect the default.target services and stop them.
            This is commonly run through 'systemctl halt' or
            at the end of a 'systemctl --init default' loop."""
        default_target = "multi-user.target"
        default_services = self.system_default_services("K", default_target)
        self.stop_units(default_services)
        logg.info("system is down")
    def system_halt(self, arg = True):
        """ stop units from default system level """
        logg.info("system halt requested - %s", arg)
        self.stop_system_default()
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
            return self.init_loop_until_stop()
        if not modules:
            # alias 'systemctl --init default'
            return self.start_system_default(init = True)
        #
        found_all = True
        units = []
        for module in modules:
            matched = self.match_units([ module ])
            if not matched:
                logg.error("no such service '%s'", module)
                found_all = False
                continue
            for unit in matched:
                if unit not in units:
                    units += [ unit ]
        return self.start_units(units, init = True) # and found_all
    def init_loop_until_stop(self):
        """ this is the init-loop - it checks for any zombies to be reaped and
            waits for an interrupt. When a SIGTERM /SIGINT /Control-C signal
            is received then the signal name is returned. Any other signal will 
            just raise an Exception like one would normally expect. """
        signal.signal(signal.SIGINT, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGINT"))
        signal.signal(signal.SIGTERM, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt("SIGTERM"))
        while True:
            try:
                time.sleep(5)
                self.system_reap_zombies()
            except KeyboardInterrupt as e:
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                return e.message or "STOPPED"
        return None
    def system_reap_zombies(self):
        """ check to reap children """
        for pid in os.listdir("/proc"):
            try: pid = int(pid)
            except: continue
            status_file = "/proc/%s/status" % pid
            if os.path.isfile(status_file):
                zombie = False
                ppid = -1
                for line in open(status_file):
                    m = re.match(r"State:\s*Z.*", line)
                    if m: zombie = True
                    m = re.match(r"PPid:\s*(\d+)", line)
                    if m: ppid = int(m.group(1))
                if zombie and ppid == os.getpid():
                    logg.info("reap zombie %s", pid)
                    try: os.waitpid(pid, os.WNOHANG)
                    except OSError as e: 
                        logg.warning("reap zombie %s: %s", e.strerror)
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
            print(prog, "command","[options]...")
            print("")
            print("Commands:")
            for arg in sorted(argz):
                name = argz[arg]
                method = getattr(self, name)
                doc = getattr(method, "__doc__")
                doc = doc or "..."
                firstline = doc.split("\n")[0]
                if "--" not in firstline:
                    print(" ",arg,"--", firstline.strip())
                else:
                    print(" ", arg, firstline.strip())
            return True
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
                doc = getattr(func, "__doc__", None)
                if doc is None:
                    logg.debug("__doc__ of %s is none", func_name)
                    print(prog, arg, "...")
                elif "--" in doc:
                    print(prog, arg, doc.replace("\n","\n\n", 1))
                else:
                    print(prog, arg, "--", doc.replace("\n","\n\n", 1))
        if not okay:
            self.show_help()
            return False
        return True
    def systemd_version(self):
        """ the the version line for systemd compatibility """
        return "systemd 0 (systemctl.py %s)" % __version__
    def systemd_features(self):
        """ the the info line for systemd features """
        features1 = "-PAM -AUDIT -SELINUX -IMA -APPARMOR -SMACK"
        features2 = " +SYSVINIT -UTMP -LIBCRYPTSETUP -GCRYPT -GNUTLS"
        features3 = " -ACL -XZ -LZ4 -SECCOMP -BLKID -ELFUTILS -KMOD -IDN"
        return features1+features2+features3
    def systems_version(self):
        return [ self.systemd_version(), self.systemd_features() ]

def print_result(result):
    exitcode = 0
    if result is None:
        logg.info("EXEC END None")
    elif result is True:
        logg.info("EXEC END True")
        result = None
        exitcode = 0
    elif result is False:
        logg.info("EXEC END False")
        result = None
        exitcode = 1
    elif isinstance(result, tuple) and len(result) == 2:
        exitcode, status = result
        logg.info("EXEC END %s '%s'", exitcode, status)
        if exitcode is True: exitcode = 0
        if exitcode is False: exitcode = 1
        result = status
    #
    if result is None:
        pass
    elif isinstance(result, string_types):
        print(result)
        result1 = result.split("\n")[0][:-20]
        if result == result1:
            logg.info("EXEC END '%s'", result)
        else:
            logg.info("EXEC END '%s...'", result1)
            logg.debug("    END '%s'", result)
    elif isinstance(result, list) or hasattr(result, "next") or hasattr(result, "__next__"):
        shown = 0
        for element in result:
            if isinstance(element, tuple):
                print("\t".join([ str(elem) for elem in element] ))
            else:
                print(element)
            shown += 1
        logg.info("EXEC END %s items", shown)
        logg.debug("    END %s", result)
    elif hasattr(result, "keys"):
        shown = 0
        for key in sorted(result.keys()):
            element = result[key]
            if isinstance(element, tuple):
                print(key,"=","\t".join([ str(elem) for elem in element]))
            else:
                print("%s=%s" % (key,element))
            shown += 1
        logg.info("EXEC END %s items", shown)
        logg.debug("    END %s", result)
    else:
        logg.warning("EXEC END Unknown result type %s", str(type(result)))
    return exitcode

if __name__ == "__main__":
    import optparse
    _o = optparse.OptionParser("%prog [options] command [name...]", 
        epilog="use 'help' command for more information")
    _o.add_option("--version", action="store_true",
        help="Show package version")
    _o.add_option("--system", action="store_true",
        help="Connect to system manager (only possibility)")
    _o.add_option("--user", action="store_true",
        help="Connect to user service manager (ignored)")
    # _o.add_option("-H", "--host", metavar="[USER@]HOST",
    #     help="Operate on remote host*")
    # _o.add_option("-M", "--machine", metavar="CONTAINER",
    #     help="Operate on local container*")
    _o.add_option("-t","--type", metavar="TYPE", dest="unit_type", default=_unit_type,
        help="List units of a particual type")
    _o.add_option("--state", metavar="STATE",
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
    _force = opt.force
    _full = opt.full
    _no_legend = opt.no_legend
    _no_ask_password = opt.no_ask_password
    _now = opt.now
    _preset_mode = opt.preset_mode
    _quiet = opt.quiet
    _root = opt.root
    _show_all = opt.show_all
    _unit_type = opt.unit_type
    _unit_property = opt.unit_property
    # being PID 1 (or 0) in a container will imply --init
    _pid = os.getpid()
    _init = opt.init or _pid in [ 1, 0 ]
    #
    if _root:
        _systemctl_debug_log = os_path(_root, _systemctl_debug_log)
        _systemctl_extra_log = os_path(_root, _systemctl_extra_log)
    if os.path.exists(_systemctl_extra_log):
        loggfile = logging.FileHandler(_systemctl_extra_log)
        loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logg.addHandler(loggfile)
        logg.setLevel(max(0, logging.INFO - 10 * opt.verbose))
    if os.path.exists(_systemctl_debug_log):
        loggfile = logging.FileHandler(_systemctl_debug_log)
        loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logg.addHandler(loggfile)
        logg.setLevel(logging.DEBUG)
    logg.info("EXEC BEGIN %s %s", os.path.realpath(sys.argv[0]), " ".join(args))
    #
    systemctl = Systemctl()
    if opt.version:
        args = [ "version" ]
    if not args: 
        if _init:
            args = [ "init" ] # alias "--init default"
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
        logg.error("EXEC END no method for '%s'", command)
        sys.exit(1)
    #
    sys.exit(print_result(result))
