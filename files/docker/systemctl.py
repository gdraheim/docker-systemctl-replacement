#! /usr/bin/python
__copyright__ = "(C) 2016-2017 Guido U. Draheim, for free use (CC-BY, GPL, BSD)"
__version__ = "0.7.1237"

import logging
logg = logging.getLogger("systemctl")

import re
import fnmatch
import shlex
import collections
import ConfigParser
import errno
import os
import sys
import subprocess
import signal
import time
import socket
import tempfile

_root = ""
_sysd_default = "multi-user.target"
_sysd_folder1 = "/etc/systemd/system"
_sysd_folder2 = "/var/run/systemd/system"
_sysd_folder3 = "/usr/lib/systemd/system"
_sysv_folder1 = "/etc/init.d"
_sysv_folder2 = "/var/run/init.d"
_preset_folder1 = "/etc/systemd/system-preset"
_preset_folder2 = "/var/run/systemd/system-preset"
_preset_folder3 = "/usr/lib/systemd/system-preset"
_waitprocfile = 100
_waitkillproc = 10
_force = False
_quiet = False
_full = False
_now = False
_property = None
_no_legend = False
_no_block = False
_no_wall = False
_no_ask_password = False

MinimumWaitProcFile = 10
MinimumWaitKillProc = 3
DefaultWaitProcFile = 100
DefaultWaitKillProc = 10
DefaultTimeoutReloadSec = 2 # officially 0.1
DefaultTimeoutRestartSec = 2 # officially 0.1
DefaultTimeoutStartSec = 10 # officially 90
DefaultTimeoutStopSec = 10 # officially 90
DefaultMaximumTimeout = 200

_notify_socket_folder = "/var/run/systemd" # alias /run/systemd
_notify_socket_name = "notify" # NOTIFY_SOCKET="/var/run/systemd/notify"
_pid_file_folder = "/var/run"
_journal_log_folder = "/var/log/journal"

def shell_cmd(cmd):
    return " ".join(["'%s'" % part for part in cmd])
def to_int(value, default = 0):
    try:
        return int(value)
    except:
        return default

def homedir_user(user = None, default = None):
    if user:
        import pwd
        return pwd.getpwnam(user).pw_dir
    return default

def os_path(root, path):
    if not root:
        return path
    while path.startswith(os.path.sep):
       path = path[1:]
    return os.path.join(root, path)

def shutil_chown(name, user = None, group = None):
    """ in python 3.3. there is shutil.chown """
    uid = -1
    gid = -1
    if group:
        import grp
        gid = grp.getgrnam(user).gr_gid
    if user:
        import pwd
        uid = pwd.getpwnam(user).pw_uid
    os.chown(name, uid, gid)

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

def shutil_truncate(name):
    """ truncate file """
    f = open(name, "w")
    f.write("")
    f.close()

# http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid is None:
        return False
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
    if pid is None:
        return False
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
    except IOError, e:
        if e.errno == errno.ENOENT:
            return False
        raise
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
        return self.defaults
    def sections(self):
        return self._dict.keys()
    def add_section(self, section):
        if section not in self._dict:
            self._dict[section] = self._dict_type()
    def has_section(self, section):
        return section in self._dict
    def has_option(self, section, option):
        if section in self._dict:
            return False
        return option in self._dict[section]
    def set(self, section, option, value):
        if section not in self._dict:
            self._dict[section] = self._dict_type()
        if option not in self._dict[section]:
            self._dict[section][option] = [ value ]
        else:
            self._dict[section][option].append(value)
        if not value:
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
        if not self._dict[section][option]:
            if default is not None:
                return default
            if allow_no_value:
                return None
        return self._dict[section][option][0] # the first line in the unit config
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
                return None
            raise AttributeError("option {} in {} does not exist".format(option, section))
        return self._dict[section][option]
    def loaded(self):
        return len(self._files)
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
                if text.rstrip().endswith("\\"):
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
            if line.startswith("["):
                x = line.find("]")
                if x > 0:
                    section = line[1:x]
                    self.add_section(section)
                continue
            m = re.match(r"(\w+)=(.*)", line)
            if not m:
                logg.warning("bad ini line: %s", line)
                raise Exception("bad ini line")
            name, text = m.group(1), m.group(2).strip()
            if text.endswith("\\"):
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
            if item.strip() == "$network":
                self.set("Unit", "After", "network.target")
            if item.strip() == "$remote_fs":
                self.set("Unit", "After", "remote-fs.target")
            if item.strip() == "$local_fs":
                self.set("Unit", "After", "local-fs.target")
            if item.strip() == "$timer":
                self.set("Unit", "Requires", "basic.target")
        provides = self.get("init.d", "Provides", "")
        if provides:
            self.set("Install", "Alias", provides)
        # if already in multi-user.target then start it there.
        runlevels = self.get("init.d", "Default-Start","")
        if "5" in runlevels:
            self.set("Install", "WantedBy", "graphical.target")
        if "3" in runlevels:
            self.set("Install", "WantedBy", "multi-user.target")
        self.set("Service", "Type", "sysv")

UnitParser = ConfigParser.RawConfigParser
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

def subprocess_wait(cmd, env=None, check = False):
    run = subprocess.Popen(cmd, shell=True, env=env)
    run.wait()
    if check and run.returncode: 
        logg.error("returncode %i\n %s", run.returncode, cmd)
        raise Exception("command failed")
    return run

def subprocess_output(cmd, env=None, check = False):
    run = subprocess.Popen(cmd, shell=True, env=env, stdout = subprocess.PIPE)
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
        if not item: 
            continue
        if item == "infinity":
            return maximum
        if item.endswith("m"):
            try: value += 60 * int(item[:-1])
            except: pass
        elif item.endswith("s"):
            try: value += int(item[:-1])
            except: pass
        else:
            try: value += int(item)
            except: pass
    if value > maximum:
        return maximum
    if not value:
        return 1
    return value

class Systemctl:
    def __init__(self):
        self._root = _root
        self._sysd_folder1 = _sysd_folder1
        self._sysd_folder2 = _sysd_folder2
        self._sysd_folder3 = _sysd_folder3
        self._sysv_folder1 = _sysv_folder1
        self._sysv_folder2 = _sysv_folder2
        self._preset_folder1 = _preset_folder1
        self._preset_folder2 = _preset_folder2
        self._preset_folder3 = _preset_folder3
        self._notify_socket_folder = _notify_socket_folder
        self._notify_socket_name = _notify_socket_name
        self._pid_file_folder = _pid_file_folder 
        self._journal_log_folder = _journal_log_folder
        self._WaitProcFile = DefaultWaitProcFile
        self._WaitKillProc = DefaultWaitKillProc
        self._force = _force
        self._quiet = _quiet
        self._full = _full
        self._now = _now
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
            for folder in (self._sysd_folder1, self._sysd_folder2, self._sysd_folder3):
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
        return self._file_for_unit_sysd.keys()
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
        return self._file_for_unit_sysv.keys()
    def unit_sysv_file(self, module = None): # -> filename?
        """ file path for the given module (sysv) """
        self.scan_unit_sysv_files()
        if module and module in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[module]
        if module and module+".service" in self._file_for_unit_sysv:
            return self._file_for_unit_sysv[module+".service"]
        return None
    def is_sysv_unit(self, module): # -> bool?
        """ for routines that have a special treatment for init.d services """
        self.unit_file() # scan all
        if not filename: return None
        if module in self._file_for_unit_sysd: return False
        if module in self._file_for_unit_sysv: return True
        return None # not True
    def is_sysv_file(self, filename):
        """ for routines that have a special treatment for init.d services """
        self.unit_file() # scan all
        if not filename: return None
        if filename in self._file_for_unit_sysd.values(): return False
        if filename in self._file_for_unit_sysv.values(): return True
        return None # not True
    def load_unit_conf(self, module): # -> conf | None(not-found)
        """ read the unit file with a UnitParser (sysv or systemd) """
        data = self.load_sysd_unit_conf(module)
        if data is not None: 
            return data
        data = self.load_sysv_unit_conf(module)
        if data is not None: 
            return data
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
    def match_unit(self, module, suffix=".service"): # -> [ units,.. ]
        """ call for about some commands with multiple units which can
            actually be glob patterns on their respective service name. """
        for unit in self.match_sysd_units([ module ], suffix):
            return unit
        for unit in self.match_sysv_units([ module ], suffix):
            return unit
        return None
    def match_units(self, modules, suffix=".service"): # -> [ units,.. ]
        """ call for about any command with multiple units which can
            actually be glob patterns on their respective unit name. """
        found = []
        for unit in self.match_sysd_units(modules, suffix):
            if unit not in found:
                found.append(unit)
        for unit in self.match_sysv_units(modules, suffix):
            if unit not in found:
                found.append(unit)
        return found
    def match_sysd_units(self, modules, suffix=".service"): # -> generate[ unit ]
        """ make a file glob on all known units (systemd areas) """
        if isinstance(modules, basestring):
            modules = [ modules ]
        self.scan_unit_sysd_files()
        for item in sorted(self._file_for_unit_sysd.keys()):
            if not modules:
                yield item
            elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                yield item
            elif [ module for module in modules if module+suffix == item ]:
                yield item
    def match_sysv_units(self, modules, suffix=".service"): # -> generate[ unit ]
        """ make a file glob on all known units (sysv areas) """
        if isinstance(modules, basestring):
            modules = [ modules ]
        self.scan_unit_sysv_files()
        for item in sorted(self._file_for_unit_sysv.keys()):
            if not modules:
                yield item
            elif [ module for module in modules if fnmatch.fnmatchcase(item, module) ]:
                yield item
            elif [ module for module in modules if module+suffix == item ]:
                yield item
    def system_list_services(self):
        """ show all the services """
        filename = self.unit_file() # scan all
        result = ""
        for name, value in self._file_for_unit_sysd.items():
            result += "\nSysD {name} = {value}".format(**locals())
        for name, value in self._file_for_unit_sysv.items():
            result += "\nSysV {name} = {value}".format(**locals())
        return result
    def show_list_units(self, *modules): # -> [ (unit,loaded,description) ]
        """ show all the units """
        result = {}
        description = {}
        for unit in self.match_units(modules):
            result[unit] = None
            description[unit] = ""
            try: 
                conf = self.get_unit_conf(unit)
                result[unit] = conf
                description[unit] = self.get_description_from(conf)
            except Exception, e:
                logg.warning("list-units: %s", e)
        return [ (unit, result[unit] and "loaded" or "", description[unit]) for unit in sorted(result) ]
    ##
    ##
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
        except IOError, e:
            logg.error("PID %s -- %s", pid, e)
        return True
    def pid_exists(self, pid): # -> bool
        """ check if a pid does still exist (unix standard) """
        # return os.path.isdir("/proc/%s" % pid) # (linux standard) 
        return pid_exists(pid)
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
    def read_env_file(self, env_file): # -> generate[ (name,value) ]
        """ EnvironmentFile=<name> is being scanned """
        if env_file.startswith("-"):
            env_file = env_file[1:]
            if not os.path.isfile(env_file):
                return
        try:
            for real_line in open(env_file):
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
        except Exception, e:
            logg.info("while reading %s: %s", env_file, e)
    def read_env_part(self, env_part): # -> generate[ (name, value) ]
        """ Environment=<name>=<value> is being scanned """
        try:
            for real_line in env_part.split("\n"):
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
        except Exception, e:
            logg.info("while reading %s: %s", env_part, e)
    def sleep(self, seconds = None): 
        """ just sleep """
        seconds = seconds or 1
        time.sleep(seconds)
    def sudo_from(self, conf):
        """ calls runuser with a (non-priviledged) user """
        runuser = conf.get("Service", "User", "")
        rungroup = conf.get("Service", "Group", "")
        sudo = ""
        if os.geteuid() == 0:
            if runuser and rungroup:
                sudo = "/usr/sbin/runuser -g %s -u %s -- " % (rungroup, runuser)
            elif runuser:
                sudo = "/usr/sbin/runuser -u %s -- " % (runuser)
            elif rungroup:
                sudo = "/usr/sbin/runuser -g %s -- " % (rungroup)
        elif os.path.exists("/usr/bin/sudo"):
            if not _no_ask_password:
                logg.warning("non-root execution without --no-ask-password (not supported)")
            if runuser and rungroup:
                sudo = "/usr/bin/sudo -n -H -g %s -u %s -- " % (rungroup, runuser)
            elif runuser:
                sudo = "/usr/bin/sudo -n -H -u %s -- " % (runuser)
            elif rungroup:
                sudo = "/usr/bin/sudo -n -H -g %s -- " % (rungroup)
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
        runuser = conf.get("Service", "User", "")
        workingdir = conf.get("Service", "WorkingDirectory", "")
        if workingdir: 
            try: return os.chdir(workingdir)
            except Exception, e:
               logg.error("chdir workingdir '%s': %s", workingdir, e)
               if check: raise
        if runuser: 
            homedir = homedir_user(runuser)
            try: return os.chdir(homedir)
            except Exception, e:
               logg.error("chdir %s home '%s': %s", runuser, homedir, e)
               if check: raise
        tempdir = tempfile.gettempdir()
        if tempdir:
            try: return os.chdir(tempdir)
            except Exception, e:
               logg.error("chdir tempdir '%s': %s", tempdir, e)
               if check: raise
        return None
    def non_shell_cmd(self, cmd, env):
        # according to documentation, when bar="one two" then the expansion
        # of '$bar' is ["one","two"] and '${bar}' becomes ["one two"]
        def get_env1(m):
            if m.group(1) in env:
                return env[m.group(1)]
            logg.debug("can not expand $%s", m.group(1))
            return ""
        def get_env2(m):
            if m.group(1) in env:
                return env[m.group(1)]
            logg.debug("can not expand ${%s}", m.group(1))
            return "${"+m.group(1)+"}"
        expanded = re.sub("[$](\w+)", lambda m: get_env1(m), cmd.replace("\\\n",""))
        import shlex
        newcmd = []
        for part in shlex.split(expanded):
            newcmd += [ re.sub("[$][{](\w+)[}]", lambda m: get_env2(m), part) ]
        return newcmd
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
        os.chmod(socketfile, 0777)
        return NotifySocket(sock, socketfile)
    def read_notify_socket(self, notify, timeout):
        notify.socket.settimeout(timeout or DefaultMaximumTimeout)
        result = ""
        try:
            result, client_address = notify.socket.recvfrom(4096)
            if result:
                logg.debug("read_notify_socket(%s):%s", len(result), result.replace("\n","|"))
        except socket.timeout, e:
            if timeout > 2:
                logg.debug("socket.timeout %s", e)
        try:
            notify.socket.close()
        except Exception, e:
            logg.debug("socket.close %s", e)
        return result
    def wait_notify_socket(self, notify, timeout, pid = None):
        if not notify:
            logg.info("no $NOTIFY_SOCKET, waiting %s", timeout)
            time.sleep(timeout)
            return {}
        #
        logg.info("wait $NOTIFY_SOCKET, timeout %s", timeout)
        results = {}
        seenREADY = None
        for attempt in xrange(timeout+1):
            if pid:
               if not pid_exists(pid) or pid_zombie(pid):
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
                if name == "STATUS":
                    logg.debug("STATUS: %s", value)
            if seenREADY:
                break
        logg.debug("notify = %s", results)
        return results
    def execstart_of_unit(self, unit):
        conf = self.load_unit_conf(unit)
        cmdlist = conf.getlist("Service", "ExecStart", [])
        for idx, cmd in enumerate(cmdlist):
            print "ExecStart[%s]: %s" % (idx, cmd)
    def start_of_units(self, *modules):
        """ [UNIT]... -- start these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.start_unit(unit):
                done = False
        return done
    def start_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        logg.info("%s => %s", conf, conf.filename())
        return self.start_unit_from(conf)
    def start_unit_from(self, conf):
        if not conf: return
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        logg.info("env = %s", env)
        if True:
            for cmd in conf.getlist("Service", "ExecStartPre", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecStartPre:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        if runs in [ "sysv" ]:
            if True:
                exe = conf.filename()
                cmd = "'%s' start" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                logg.info("(start) %s", cmd)
                run = subprocess_wait(cmd, env)
        elif runs in [ "simple" ]: 
            pid_file = self.get_pid_file_from(conf)
            pid = self.read_pid_file(pid_file, "")
            if pid and pid_exists(pid) and not pid_zombie(pid):
                logg.error("the service is already running on PID %s", pid)
                return False
            runuser = conf.get("Service", "User", "")
            rungroup = conf.get("Service", "Group", "")
            shutil_truncate(pid_file)
            shutil_chown(pid_file, runuser, rungroup)
            if not os.fork():
                logg.debug("> simple process for %s", conf.filename())
                os.setsid() # detach from parent
                inp = open("/dev/zero")
                out = self.open_journal_log(conf)
                os.dup2(inp.fileno(), sys.stdin.fileno())
                os.dup2(out.fileno(), sys.stdout.fileno())
                os.dup2(out.fileno(), sys.stderr.fileno())
                shutil_setuid(runuser, rungroup)
                self.chdir_workingdir(conf, check = False)
                cmdlist = conf.getlist("Service", "ExecStart", [])
                for idx, cmd in enumerate(cmdlist):
                    logg.debug("ExecStart[%s]: %s", idx, cmd)
                for cmd in cmdlist:
                    pid = self.read_pid_file(pid_file, "")
                    env["MAINPID"] = str(pid)
                    newcmd = self.non_shell_cmd(cmd, env)
                    logg.info("> start %s", shell_cmd(newcmd))
                    run = subprocess.Popen(newcmd, env=env, close_fds=True, 
                        stdin=inp, stdout=out, stderr=out)
                    self.write_pid_file(pid_file, run.pid)
                    logg.info("> started PID %s", run.pid)
                    run.wait()
                    logg.info("> stopped PID %s EXIT %s", run.pid, run.returncode)
                    pid = self.read_pid_file(pid_file, "")
                    if str(pid) == str(run.pid):
                        self.write_pid_file(pid_file, "")
            else:
                # parent
                pid = self.wait_pid_file(pid_file)
                logg.info("> done simple PID %s [%s]", pid, pid_file)
                time.sleep(1) # give it another second to come up
                if not self.read_pid_file(pid_file, ""):
                   raise Exception("could not start service")
        elif runs in [ "notify" ]:
            # same as "simple" but create $NOTIFY_SOCKET and check it
            pid_file = self.get_pid_file_from(conf)
            pid = self.read_pid_file(pid_file, "")
            if pid and pid_exists(pid) and not pid_zombie(pid):
                logg.error("the service is already running on PID %s", pid)
                return False
            runuser = conf.get("Service", "User", "")
            rungroup = conf.get("Service", "Group", "")
            shutil_truncate(pid_file)
            shutil_chown(pid_file, runuser, rungroup)
            timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutStartSec)
            timeout = conf.get("Service", "TimeoutStartSec", timeout)
            timeout = time_to_seconds(timeout, DefaultMaximumTimeout)
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                logg.debug("use NOTIFY_SOCKET=%s", notify.socketfile)
            if not os.fork():
                logg.debug("> simple process for %s", conf.filename())
                os.setsid() # detach from parent
                inp = open("/dev/zero")
                out = self.open_journal_log(conf)
                os.dup2(inp.fileno(), sys.stdin.fileno())
                os.dup2(out.fileno(), sys.stdout.fileno())
                os.dup2(out.fileno(), sys.stderr.fileno())
                shutil_setuid(runuser, rungroup)
                self.chdir_workingdir(conf, check = False)
                cmdlist = conf.getlist("Service", "ExecStart", [])
                for idx, cmd in enumerate(cmdlist):
                    logg.debug("ExecStart[%s]: %s", idx, cmd)
                for cmd in cmdlist:
                    pid = self.read_pid_file(pid_file, "")
                    env["MAINPID"] = str(pid)
                    newcmd = self.non_shell_cmd(cmd, env)
                    logg.info("* start %s", shell_cmd(newcmd))
                    run = subprocess.Popen(newcmd, env=env, close_fds=True, 
                        stdin=inp, stdout=out, stderr=out)
                    self.write_pid_file(pid_file, run.pid)
                    logg.info("* started PID %s", run.pid)
                    run.wait()
                    logg.info("* stopped PID %s EXIT %s", run.pid, run.returncode)
                    pid = self.read_pid_file(pid_file, "")
                    if str(pid) == str(run.pid):
                        self.write_pid_file(pid_file, "")
            else:
                # parent
                mainpid = self.wait_pid_file(pid_file) # fork is running
                results = self.wait_notify_socket(notify, timeout, mainpid)
                if "MAINPID" in results:
                    new_pid = results["MAINPID"]
                    if new_pid and to_int(new_pid) != mainpid:
                        logg.info("NEW PID %s from sd_notify (was PID %s)", new_pid, mainpid)
                        self.write_pid_file(pid_file, new_pid)
                logg.info("* done notify %s", pid_file)
                if not self.read_pid_file(pid_file, ""):
                   raise Exception("could not start service")
        elif runs in [ "oneshot" ]:
            for cmd in conf.getlist("Service", "ExecStart", []):
                check, cmd = checkstatus(cmd)
                logg.info("! start %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                if check and run.returncode: raise Exception("ExecStart")
                logg.info("* done oneshot start")
        elif runs in [ "forking" ]:
            for cmd in conf.getlist("Service", "ExecStart", []):
                check, cmd = checkstatus(cmd)
                logg.info(": start %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                if check and run.returncode: raise Exception("ExecStart")
                pid_file = self.get_pid_file_from(conf)
                pid = self.wait_pid_file(pid_file)
                logg.info(": done forking PID %s [%s]", pid, pid_file)
        else:
            logg.error("unsupported run type '%s'", runs)
            raise Exception("unsupported run type")
        if True:
            for cmd in conf.getlist("Service", "ExecStartPost", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecStartPost:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
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
    def kill_pid(self, pid, timeout = None, kill_signal = None):
        if not pid:
            return None
        #
        timeout = int(timeout or self._WaitKillProc)
        timeout = max(timeout, MinimumWaitKillProc)
        if isinstance(kill_signal, basestring):
           sig = getattr(signal, kill_signal)
        else:
           sig = kill_signal or signal.SIGTERM
        try: os.kill(pid, sig)
        except OSError, e:
            if e.errno == errno.ESRCH or e.errno == errno.ENOENT:
                logg.info("kill PID %s => No such process", pid)
                return True
            else:
                logg.error("kill PID %s => %s", pid, str(e))
                return False
        for x in xrange(timeout):
            if not self.pid_exists(pid):
                break
            self.sleep(1)
        return not self.pid_exists(pid)
    def environment_of_unit(self, unit):
        """ [UNIT]. -- show environment parts """
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        return self.get_env(conf)
    def get_env(self, conf):
        env = os.environ.copy()
        for env_part in conf.getlist("Service", "Environment", []):
            for name, value in self.read_env_part(env_part):
                env[name] = value
        for env_file in conf.getlist("Service", "EnvironmentFile", []):
            for name, value in self.read_env_file(env_file):
                env[name] = value
        return env
    def stop_of_units(self, *modules):
        """ [UNIT]... -- stop these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.stop_unit(unit):
                done = False
        return done
    def stop_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        return self.stop_unit_from(conf)
    def stop_unit_from(self, conf):
        if not conf: return
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        if True:
            for cmd in conf.getlist("Service", "ExecStopPre", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecStopPre:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        if runs in [ "sysv" ]:
            if True:
                exe = conf.filename()
                cmd = "'%s' stop" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                logg.info("(stop) %s", cmd)
                run = subprocess_wait(cmd, env)
        elif not conf.getlist("Service", "ExecStop", []):
            if True:
                pid_file = self.get_pid_file_from(conf)
                self.kill_unit_from(conf)
                if os.path.isfile(pid_file):
                    os.remove(pid_file)
        elif runs in [ "simple" ]:
            pid_file = self.get_pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecStop", []):
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                logg.info("& stop %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                # self.write_pid_file(pid_file, run.pid)
        elif runs in [ "notify" ]:
            pid_file = self.get_pid_file_from(conf)
            timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutStopSec)
            timeout = conf.get("Service", "TimeoutStopSec", timeout)
            timeout = time_to_seconds(timeout, DefaultMaximumTimeout)
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                logg.debug("use NOTIFY_SOCKET=%s", notify.socketfile)
            for cmd in conf.getlist("Service", "ExecStop", []):
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                logg.info("* stop %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                # self.write_pid_file(pid_file, run.pid)
                mainpid = self.wait_pid_file(pid_file) # fork is running
                results = self.wait_notify_socket(notify, timeout, mainpid)
                if "MAINPID" in results:
                    new_pid = results["MAINPID"]
                    if new_pid and new_pid.strip() != mainpid:
                        logg.info("NEW PID %s from sd_notify", new_pid)
                        self.write_pid_file(pid_file, new_pid)
        elif runs in [ "oneshot" ]:
            for cmd in conf.getlist("Service", "ExecStop", []):
                check, cmd = checkstatus(cmd)
                logg.info(" {env} %s", env)
                logg.info("! stop %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
        elif runs in [ "forking" ]:
            pid_file = self.get_pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecStop", []):
                active = self.is_active_from(conf)
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                check, cmd = checkstatus(cmd)
                logg.info(" {env} %s", env)
                logg.info(": stop %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                if active:
                    if check and run.returncode: raise Exception("ExecStop")
                pid_file = self.get_pid_file_from(conf)
                pid = self.wait_pid_file(pid_file)
        else:
            logg.error("unsupported run type '%s'", runs)
            raise Exception("unsupported run type")
        if True:
            for cmd in conf.getlist("Service", "ExecStopPost", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecStopPost:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        return True
    def reload_of_units(self, *modules):
        """ [UNIT]... -- reload these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.reload_unit(unit):
                done = False
        return done
    def reload_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        return self.reload_unit_from(conf)
    def reload_unit_from(self, conf):
        if not conf: return
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        if True:
            for cmd in conf.getlist("Service", "ExecReloadPre", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecReloadPre:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        if runs in [ "sysv" ]:
            if True:
                exe = conf.filename()
                cmd = "'%s' reload" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                logg.info("(reload) %s", cmd)
                run = subprocess_wait(cmd, env)
        elif runs in [ "simple" ]:
            for cmd in conf.getlist("Service", "ExecReload", []):
                pid_file = self.get_pid_file_from(conf)
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                logg.info("& reload %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                # self.write_pid_file(pid_file, run.pid)
        elif runs in [ "notify" ]:
            pid_file = self.get_pid_file_from(conf)
            timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutReloadSec)
            timeout = conf.get("Service", "TimeoutReloadSec", timeout)
            timeout = time_to_seconds(timeout, DefaultMaximumTimeout)
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                logg.debug("use NOTIFY_SOCKET=%s", notify.socketfile)
            for cmd in conf.getlist("Service", "ExecReload", []):
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                logg.info("* reload %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                # self.write_pid_file(pid_file, run.pid)
                mainpid = self.wait_pid_file(pid_file) # fork is running
                results = self.wait_notify_socket(notify, timeout, mainpid)
                if "MAINPID" in results:
                    new_pid = results["MAINPID"]
                    if new_pid and new_pid.strip() != mainpid:
                        logg.info("NEW PID %s from sd_notify", new_pid)
                        self.write_pid_file(pid_file, new_pid)
        elif runs in [ "oneshot" ]:
            for cmd in conf.getlist("Service", "ExecReload", []):
                check, cmd = checkstatus(cmd)
                logg.info("! reload %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
        elif runs in [ "forking" ]:
            pid_file = self.get_pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecReload", []):
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                check, cmd = checkstatus(cmd)
                logg.info(": reload %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                if check and run.returncode: raise Exception("ExecReload")
                pid_file = self.get_pid_file_from(conf)
                pid = self.wait_pid_file(pid_file)
        else:
            logg.error("unsupported run type '%s'", runs)
            raise Exception("unsupported run type")
        if True:
            for cmd in conf.getlist("Service", "ExecReloadPost", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecReloadPost:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        return True
    def restart_of_units(self, *modules):
        """ [UNIT]... -- restart these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.restart_unit(unit):
                done = False
        return done
    def restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        return self.restart_unit_from(conf)
    def restart_unit_from(self, conf):
        if not conf: return
        runs = conf.get("Service", "Type", "simple").lower()
        sudo = self.sudo_from(conf)
        env = self.get_env(conf)
        if True:
            for cmd in conf.getlist("Service", "ExecRestartPre", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecRestartPre:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        if runs in [ "sysv" ]:
            if True:
                exe = conf.filename()
                cmd = "'%s' restart" % exe
                env["SYSTEMCTL_SKIP_REDIRECT"] = "yes"
                logg.info("(restart) %s", cmd)
                run = subprocess_wait(cmd, env)
        elif not conf.getlist("Service", "ExecRestart", []):
            logg.info("(restart) => stop/start")
            self.stop_unit_from(conf)
            self.start_unit_from(conf)
        elif runs in [ "simple" ]:
            pid_file = self.get_pid_file_from(conf)
            for cmd in conf.getlist("Service", "ExecRestart", []):
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                logg.info("& restart %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                # self.write_pid_file(pid_file, run.pid)
        elif runs in [ "notify" ]:
            pid_file = self.get_pid_file_from(conf)
            timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutRestartSec)
            timeout = conf.get("Service", "TimeoutRestartSec", timeout)
            timeout = time_to_seconds(timeout, DefaultMaximumTimeout)
            notify = self.notify_socket_from(conf)
            if notify:
                env["NOTIFY_SOCKET"] = notify.socketfile
                logg.debug("use NOTIFY_SOCKET=%s", notify.socketfile)
            for cmd in conf.getlist("Service", "ExecRestart", []):
                pid = self.read_pid_file(pid_file, "")
                env["MAINPID"] = str(pid)
                logg.info("* restart %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                # self.write_pid_file(pid_file, run.pid)
                mainpid = self.wait_pid_file(pid_file) # fork is running
                results = self.wait_notify_socket(notify, timeout, mainpid)
                if "MAINPID" in results:
                    new_pid = results["MAINPID"]
                    if new_pid:
                        logg.info("NEW PID %s from sd_notify", new_pid)
                        self.write_pid_file(pid_file, new_pid)
        elif runs in [ "oneshot" ]:
            for cmd in conf.getlist("Service", "ExecRestart", []):
                check, cmd = checkstatus(cmd)
                logg.info("! restart %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
        elif runs in [ "forking" ]:
            for cmd in conf.getlist("Service", "ExecRestart", []):
                check, cmd = checkstatus(cmd)
                logg.info(": restart %s", sudo+cmd)
                run = subprocess_wait(sudo+cmd, env)
                if check and run.returncode: raise Exception("ExecRestart")
                pid_file = self.get_pid_file_from(conf)
                pid = self.wait_pid_file(pid_file)
        else:
            logg.error("unsupported run type '%s'", runs)
            raise Exception("unsupported run type")
        if True:
            for cmd in conf.getlist("Service", "ExecRestartPost", []):
                check, cmd = checkstatus(cmd)
                logg.info("ExecRestartPost:%s:%s", check, cmd)
                subprocess_wait(cmd, env, check=check)
        return True
    def get_pid_file(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return None
        return self.get_pid_file_from(conf)
    def get_pid_file_from(self, conf, default = None):
        if not conf: return default
        if not conf.filename(): return default
        unit = os.path.basename(conf.filename())
        if default is None:
            default = self.default_pid_file(unit)
        return conf.get("Service", "PIDFile", default)
    def try_restart_of_units(self, *modules):
        """ [UNIT]... -- try-restart these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.try_restart_unit(unit):
                done = False
        return done
    def try_restart_unit(unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        if self.is_active_from(conf):
            return self.restart_unit_from(conf)
        return True
    def reload_or_restart_of_units(self, *modules):
        """ [UNIT]... -- reload-or-start these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.reload_or_restart_unit(unit):
                done = False
        return done
    def reload_or_restart_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        if not self.is_active_from(conf):
            # try: self.stop_unit_from(conf)
            # except Exception, e: pass
            return self.start_unit_from(conf)
        elif conf.getlist("Service", "ExecReload", []):
            return self.reload_unit_from(conf)
        else:
            return self.restart_unit_from(conf)
    def reload_or_try_restart_of_units(self, *modules):
        """ [UNIT]... -- reload-or-try-restart these units """
        done = True
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            elif not self.reload_or_try_restart_unit(unit):
                done = False
        return done
    def reload_or_try_restart_unit(unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        if conf.getlist("Service", "ExecReload", []):
            return self.reload_unit_from(conf)
        elif not self.is_active_from(conf):
            return True
        else:
            return self.restart_unit_from(conf)
    def kill_of_units(self, *modules):
        """ [UNIT]... -- kill these units """
        units = {}
        for module in modules:
            unit = self.match_unit(module)
            if not unit:
                logg.error("no such service '%s'", module)
                done = False
            else:
                units[unit] = 1
        done = True
        for unit in units:
            if not self.kill_unit(unit):
                done = False
        return done
    def kill_unit(self, unit):
        conf = self.load_unit_conf(unit)
        if conf is None:
            logg.error("no such unit: '%s'", unit)
            return False
        return self.kill_unit_from(conf)
    def kill_unit_from(self, conf):
        if not conf: return None
        sendSIGKILL = conf.get("Service", "SendSIGKILL", "yes")
        kill_signal = conf.get("Service", "KillSignal", signal.SIGTERM)
        timeout = conf.get("Service", "TimeoutSec", DefaultTimeoutStopSec)
        timeout = conf.get("Service", "TimeoutStopSec", timeout)
        pid_file = self.get_pid_file_from(conf)
        pid = self.read_pid_file(pid_file)
        if not pid:
            logg.info("no main PID [%s]", conf.filename())
            return False
        logg.info("stop kill PID %s (%s)", pid, pid_file)
        if not self.kill_pid(pid, timeout, kill_signal):
            if "y" in sendSIGKILL:
                logg.info("hard kill PID %s (%s)", pid, pid_file)
                return self.kill_pid(pid, timeout, signal.SIGKILL)
            else:
                logg.info("no hard kill PID %s (no SendSIGKILL)", pid)
                return False
        else:
            logg.info("done kill PID %s", pid)
            return True
    def is_active_of_units(self, *modules):
        """ [UNIT].. -- check if these units are in active state
        implements True if any is-active = True """
        units = {}
        for unit in self.match_units(modules):
            units[unit] = 1
        result = False
        for unit in units:
            if self.is_active(unit):
                result = True
        return result
    def is_active(self, unit):
        conf = self.get_unit_conf(unit)
        if not conf.loaded():
            logg.warning("no such unit '%s'", unit)
        return self.is_active_from(conf)
    def active_pid_from(self, conf):
        if not conf: return False
        pid_file = self.get_pid_file_from(conf)
        pid = self.read_pid_file(pid_file)
        logg.debug("pid_file '%s' => PID %s", pid_file, pid)
        exists = self.pid_exists(pid)
        if not exists:
           return None
        return pid # string!!
    def is_active_from(self, conf):
        if not conf: return False
        if self.active_pid_from(conf) is None:
           return False
        return True
    def active_from(self, conf):
        if not conf: return False
        pid = self.active_pid_from(conf)
        if pid is None: return "dead"
        return "PID %s" % pid
    def is_failed_of_units(self, *modules):
        """ [UNIT]... -- check if these units are in failes state
        implements True if any is-active = True """
        result = False
        for unit in self.match_units(modules):
            if self.is_failed(unit):
                result = True
        return result
    def is_failed(self, unit):
        conf = self.get_unit_conf(unit)
        if not conf.loaded():
            logg.warning("no such unit '%s'", unit)
        return self.is_failed_from(conf)
    def is_failed_from(self, conf):
        if not conf: return True
        pid_file = self.get_pid_file_from(conf)
        pid = self.read_pid_file(pid_file)
        logg.debug("pid_file '%s' => PID %s", pid_file, pid)
        return not self.pid_exists(pid)
    def status_of_units(self, *modules):
        """ [UNIT]... check the status of these units.
        """
        found = False
        status, result = 0, ""
        for unit in self.match_units(modules):
            status1, result1 = self.status_unit(unit)
            if status1: status = status1
            if result: result += "\n\n"
            result += result1
            found = True
        if not found: status = 1
        return status, result
    def status_unit(self, unit):
        conf = self.get_unit_conf(unit)
        result = "%s - %s" % (unit, self.get_description_from(conf))
        if conf.loaded():
            result += "\n    Loaded: loaded ({}, {})".format(conf.filename(), self.enabled_from(conf) )
        else:
            result += "\n    Loaded: failed"
            return 3, result
        if self.is_active_from(conf):
            result += "\n    Active: active ({})".format(self.active_from(conf))
            return 0, result
        else:
            result += "\n    Active: inactive ({})".format(self.active_from(conf))
            return 3, result
    def cat_of_units(self, *modules):
        """ [UNIT]... show the *.system file for these"
        """
        done = True
        for unit in self.match_units(modules):
            if not self.cat_unit(unit):
                done = False
        return done
    def cat_unit(self, unit):
        try:
            unit_file = self.unit_file(unit)
            return open(unit_file).read()
        except Exception, e:
            print "Unit {} is not-loaded: {}".format(unit, e)
            return False
    ##
    ##
    def load_preset_files(self, module = None): # -> [ preset-file-names,... ]
        """ reads all preset files, returns the scanned files """
        if self._preset_file_list is None:
            self._preset_file_list = {}
            for folder in (self._preset_folder1, self._preset_folder2, self._preset_folder3):
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
    def preset_of_units(self, *modules):
        """ [UNIT]... -- set 'enabled' when in *.preset
        """
        done = True
        for unit in self.match_units(modules):
            status = self.get_preset_of_unit(unit)
            if status and status.startswith("enable"):
                if not self.enable_unit(unit):
                    done = False
            if status and status.startswith("disable"):
                if not self.disable_unit(unit):
                    done = False
        return done
    def system_preset_all(self):
        """ 'preset' all services
        enable or disable services according to *.preset files
        """
        done = True
        for unit in self.match_units():
            status = self.get_preset_of_unit(unit)
            if status and status.startswith("enable"):
                if not self.enable_unit(unit):
                    done = False
            if status and status.startswith("disable"):
                if not self.disable_unit(unit):
                    done = False
        return done
    def wanted_from(self, conf, default = None):
        if not conf: return default
        return conf.get("Install", "WantedBy", default, True)
    def enablefolder(self, wanted = None):
        if not wanted: 
            return None
        if not wanted.endswith(".wants"):
            wanted = wanted + ".wants"
        return os.path.join("/etc/system/systemd", wanted)
    def enable_of_units(self, *modules):
        """ [UNIT]... -- enable these units """
        done = True
        for unit in self.match_units(modules):
            if not self.enable_unit(unit):
                done = False
            elif self._now:
               self.start_unit(unit)
        return done
    def enable_unit(self, unit):
        unit_file = self.unit_file(unit)
        if self.is_sysv_file(unit_file):
            return self.enable_unit_sysv(unit_file)
        wanted = self.wanted_from(self.get_unit_conf(unit))
        if not wanted: return False # wanted = "multi-user.target"
        folder = self.enablefolder(wanted)
        if self._root.
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
        # do not double existing entries
        if found in os.listdir(rc_folder):
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
    def disable_of_units(self, *modules):
        """ [UNIT]... -- disable these units """
        done = True
        for unit in self.match_units(modules):
            if not self.disable_unit(unit):
               done = False
        return done
    def disable_unit(self, unit):
        unit_file = self.unit_file(unit)
        if self.is_sysv_file(unit_file):
            return self.disable_unit_sysv(unit_file)
        wanted = self.wanted_from(self.get_unit_conf(unit))
        folder = self.enablefolder(wanted)
        if self._root:
            folder = os_path(self._root, folder)
        if not os.path.isdir(folder):
            return False
        target = os.path.join(folder, os.path.basename(unit_file))
        if os.path.isfile(target):
            _f = self._force and "-f" or ""
            logg.info("rm {_f} '{target}'".format(**locals()))
            os.remove(target)
        return True
    def disable_unit_sysv(self, unit_file):
        rc3 = self.disable_unit_sysv(unit_file, self.rc3_root_folder())
        rc5 = self.disable_unit_sysv(unit_file, self.rc5_root_folder())
        return rc3 and rc5
    def _disable_unit_sysv(self, unit_file, rc_folder):
        # a "multi-user.target"/rc3 is also started in /rc5
        name = os.path.basename(unit_file)
        nameS = "S50"+name
        nameK = "K50"+name
        # do not forget the existing entries
        if found in os.listdir(rc_folder):
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
    def is_enabled_of_units(self, *modules):
        """ [UNIT]... -- check if these units are enabled 
        returns True if any of them is enabled."""
        result = False
        for unit in self.match_units(modules):
            if self.is_enabled(unit):
               result = True
        return result
    def is_enabled(self, unit):
        unit_file = self.unit_file(unit)
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
    def enabled_from(self, conf):
        unit_file = conf.filename()
        if self.is_sysv_file(unit_file):
            return self.is_enabled_sysv(unit_file)
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
    def system_daemon_reload(self):
        """ reload does nothing here """
        logg.info("ignored daemon-reload")
        return True
    def show_of_units(self, *modules):
        """ [UNIT]... -- show runtime status if these units
        """
        result = ""
        for unit in self.match_units(modules):
            if result: result += "\n\n"
            for var, value in self.show_unit_items(unit):
               if not _property or _property == var:
                   result += "%s=%s\n" % (var, value)
        if not result and modules:
            unit = modules[0]
            for var, value in self.show_unit_items(unit):
               if not _property or _property == var:
                   result += "%s=%s\n" % (var, value)
        return result
    def show_unit_items(self, unit):
        """ [UNIT]... -- show runtime status if these units
        """
        logg.info("try read unit %s", unit)
        conf = self.get_unit_conf(unit)
        for entry in self.each_unit_items(unit, conf):
            yield entry
    def each_unit_items(self, unit, conf):
        yield "Id", unit
        yield "Names", unit
        yield "Description", self.get_description_from(conf) # conf.get("Unit", "Description")
        yield "MainPID", self.active_pid_from(conf) or "0"
        yield "SubState", self.active_from(conf)
        yield "ActiveState", self.is_active_from(conf) and "active" or "dead"
        yield "LoadState", conf.loaded() and "loaded" or "not-loaded"
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
    def system_default_services(self, sysv="S", default_target = "multi-user.target"):
        """ show the default services """
        igno = self.igno_always
        wants_services = []
        for folder in [ self._sysd_folder1, self._sysd_folder2 ]:
            if self._root:
                folder = os_path(self._root, folder)
            wants_folder = os.path.join(folder, default_target + ".wants")
            if os.path.isdir(wants_folder):
                for unit in sorted(os.listdir(wants_folder)):
                    path = os.path.join(wants_folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(".service"):
                        wants_services.append(unit)
        for folder in [ self.rc3_root_folder() ]:
            for unit in sorted(os.listdir(folder)):
                path = os.path.join(folder, unit)
                if os.path.isdir(path): continue
                m = re.match(sysv+r"\d\d(.*)", unit)
                if m:
                    service = m.group(1)
                    unit = service+".service"
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    wants_services.append(unit)
        return wants_services
    def system_wants_services(self, sysv="S", default_target = "multi-user.target"):
        """ show the names of the default services to be started """
        igno = self.igno_centos + self.igno_opensuse + self.igno_ubuntu + self.igno_always
        logg.info("igno = %s", igno)
        wants_services = []
        for folder in [ self._sysd_folder1, self._sysd_folder2 ]:
            if self._root:
                folder = os_path(self._root, folder)
            wants_folder = os.path.join(folder, default_target + ".wants")
            if os.path.isdir(wants_folder):
                for unit in sorted(os.listdir(wants_folder)):
                    path = os.path.join(wants_folder, unit)
                    if os.path.isdir(path): continue
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    if unit.endswith(".service"):
                        wants_services.append(unit)
        for folder in [ self.rc3_root_folder() ]:
            for unit in sorted(os.listdir(folder)):
                path = os.path.join(folder, unit)
                if os.path.isdir(path): continue
                m = re.match(sysv+r"\d\d(.*)", unit)
                if m:
                    service = m.group(1)
                    unit = service+".service"
                    if self._ignored_unit(unit, igno):
                        continue # ignore
                    wants_services.append(unit)
        return wants_services
    def system_default(self, arg = True):
        """ start units for default system level """
        logg.info("system default requested - %s", arg)
        default_target = "multi-user.target"
        wants_services = self.system_wants_services("S", default_target)
        self.start_of_units(*wants_services)
        logg.info("system is up")
    def system_halt(self, arg = True):
        """ stop units from default system level """
        logg.info("system halt requested - %s", arg)
        default_target = "multi-user.target"
        wants_services = self.system_wants_services("K", default_target)
        self.stop_of_units(*wants_services)
        logg.info("system is down")
    def system_init0(self):
        """ run as init process - when PID 0 """
        return self.system_init("init 0")
    def system_init1(self):
        """ run as init process - when PID 1 """
        return self.system_init("init 1")
    def system_init(self, info = "init"):
        """ runs as init process => 'default' + 'wait' 
        It will start the nabled services, then wait for any
        zombies to be reaped or a SIGSTOP to initiate a
        shutdown of the enabled services. A Control-C in
        in interactive mode will also run 'stop' on all
        the enabled services.
        """
        self.system_default(info)
        return self.system_wait(info)
    def system_wait(self, arg = True):
        """ wait and reap children """
        signal.signal(signal.SIGTERM, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt('SIGTERM'))
        signal.signal(signal.SIGINT, lambda signum, frame: ignore_signals_and_raise_keyboard_interrupt('SIGINT'))
        while True:
            try:
                time.sleep(10)
                self.system_reap_zombies()
            except KeyboardInterrupt:
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                self.system_halt(arg)
                return True
        return False
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
		    except OSError, e: 
			logg.warning("reap zombie %s: %s", e.strerror)
    def etc_hosts(self):
        path = "/etc/hosts"
        if self._root:
            return os_path(self._root, path)
        return path
    def system_ipv4(self, *args):
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
    def system_ipv6(self, *args):
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
                if name.endswith("_of_units"):
                   arg = name[:-len("_of_units")].replace("_","-")
                if arg:
                   argz[arg] = name
            print prog, "command","[options]..."
            print ""
            print "Commands:"
            for arg in sorted(argz):
                name = argz[arg]
                method = getattr(self, name)
                doc = getattr(method, "__doc__")
                doc = doc or "..."
                firstline = doc.split("\n")[0]
                if "--" not in firstline:
                    print " ",arg,"--", firstline.strip()
                else:
                    print " ", arg, firstline.strip()
            return True
        for arg in args:
            arg = arg.replace("-","_")
            func1 = getattr(self.__class__, arg+"_of_units", None)
            func2 = getattr(self.__class__, arg+"_of_unit", None)
            func3 = getattr(self.__class__, "show_"+arg, None)
            func4 = getattr(self.__class__, "system_"+arg, None)
            func = func1 or func2 or func3 or func4
            if func is None:
                logg.debug("func '%s' is none", func_name)
                self.show_help()
            else:
                doc = getattr(func, "__doc__", None)
                if doc is None:
                    logg.debug("__doc__ of %s is none", func_name)
                    print prog, arg, "..."
                elif "--" in doc:
                    print prog, arg, doc.replace("\n","\n\n", 1)
                else:
                    print prog, arg, "--", doc.replace("\n","\n\n", 1)
    def system_version(self):
        """ -- show the version and copyright info """
        return [ ("Version", __version__), ("Copyright", __copyright__) ]

if __name__ == "__main__":
    import optparse
    _o = optparse.OptionParser("%prog [options] command [name...]", 
        epilog="use 'help' command for more information \n [option* are not implemented]")
    _o.add_option("--version", action="store_true",
        help="Show package version")
    _o.add_option("--system", action="store_true",
        help="Connect to system manager (only possibility!)")
    # _o.add_option("--user", action="store_true",
    #     help="Connect to user service manager*")
    # _o.add_option("-H", "--host", metavar="[USER@]HOST",
    #     help="Operate on remote host*")
    # _o.add_option("-M", "--machine", metavar="CONTAINER",
    #     help="Operate on local container*")
    _o.add_option("-t","--type", metavar="TYPE",
        help="List units of a particual type*")
    _o.add_option("--state", metavar="STATE",
        help="List units with particular LOAD or SUB or ACTIVE state*")
    _o.add_option("-p", "--property", metavar="NAME",
        help="Show only properties by this name*")
    _o.add_option("-a", "--all", action="store_true",
        help="Show all loaded units/properties, including dead empty ones. To list all units installed on the system, use the 'list-unit-files' command instead*")
    _o.add_option("-l","--full", action="store_true", default=_full,
        help="Don't ellipsize unit names on output*")
    _o.add_option("--reverse", action="store_true",
        help="Show reverse dependencies with 'list-dependencies'*")
    _o.add_option("--job-mode", metavar="MODE",
        help="Specifiy how to deal with already queued jobs, when queuing a new job*")    
    _o.add_option("--show-types", action="store_true",
        help="When showing sockets, explicitly show their type*")
    _o.add_option("-i","--ignore-inhibitors", action="store_true",
        help="When shutting down or sleeping, ignore inhibitors*")
    _o.add_option("--kill-who", metavar="WHO",
        help="Who to send signal to*")
    _o.add_option("-s", "--signal", metavar="SIG",
        help="Which signal to send*")
    _o.add_option("--now", action="store_true", default=_now,
        help="Start or stop unit in addition to enabling or disabling it")
    _o.add_option("-q","--quiet", action="store_true", default=_quiet,
        help="Suppress output")
    _o.add_option("--no-block", action="store_true", default=_no_block,
        help="Do not wait until operation finished*")
    _o.add_option("--no-legend", action="store_true", default=_no_legend,
        help="Do not print a legend (column headers and hints)")
    _o.add_option("--no-wall", action="store_true", default=_no_wall,
        help="Don't send wall message before halt/power-off/reboot")
    _o.add_option("--no-reload", action="store_true",
        help="Don't reload daemon after en-/dis-abling unit files*")
    _o.add_option("--no-ask-password", action="store_true", default=_no_ask_password,
        help="Do not ask for system passwords")
    # _o.add_option("--global", action="store_true", dest="globally", default=_globally,
    #    help="Enable/disable unit files globally") # for all user logins
    # _o.add_option("--runtime", action="store_true",
    #     help="Enable unit files only temporarily until next reboot*")
    _o.add_option("--force", action="store_true", default=_force,
        help="When enabling unit files, override existing symblinks / When shutting down, execute action immediately")
    _o.add_option("--root", metavar="PATH", default=_root,
        help="Enable unit files in the specified root directory*")
    _o.add_option("-n","--lines", metavar="NUM",
        help="Number of journal entries to show*")
    _o.add_option("-o","--output", metavar="CAT",
        help="change journal output mode (short, ..., cat)*")
    _o.add_option("--plain", action="store_true",
        help="Print unit dependencies as a list instead of a tree*")
    _o.add_option("--no-pager", action="store_true",
        help="Do not pipe output into pager*")
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
    _root = opt.root
    _force = opt.force
    _quiet = opt.quiet
    _full = opt.full
    _property = getattr(opt, "property")
    _init = opt.init
    _now = opt.now
    _no_legend = opt.no_legend
    _no_block = opt.no_block
    _no_wall = opt.no_wall
    _no_ask_password = opt.no_ask_password
    #
    _systemctl_debug_log = "/var/log/systemctl.debug.log"
    _systemctl_extra_log = "/var/log/systemctl.log"
    if _root:
       _systemctl_debug_log = os.path.join(_root, _systemctl_debug_log)
       _systemctl_extra_log = os.path.join(_root, _systemctl_extra_log)
    if os.path.exists(_systemctl_debug_log):
       loggfile = logging.FileHandler(_systemctl_debug_log)
       loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
       logg.addHandler(loggfile)
       logg.setLevel(logging.DEBUG)
       logg.info("EXEC BEGIN %s %s", os.path.realpath(sys.argv[0]), " ".join(args))
    elif os.path.exists(_systemctl_extra_log):
       loggfile = logging.FileHandler(_systemctl_extra_log)
       loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
       logg.addHandler(loggfile)
       logg.setLevel(max(0, logging.INFO - 10 * opt.verbose))
       logg.info("EXEC BEGIN %s %s", os.path.realpath(sys.argv[0]), " ".join(args))
    #
    if opt.version:
       args = [ "version" ]
    if not args: 
        if os.getpid() == 0:
            _init = True
        if os.getpid() == 1:
            _init = True
        if _init:
            args = [ "default" ]
        else:
            args = [ "list-units" ]
    command = args[0]
    modules = args[1:]
    systemctl = Systemctl()
    if opt.ipv4:
        systemctl.system_ipv4()
    elif opt.ipv6:
        systemctl.system_ipv6()
    found = False
    # command NAME
    command_name = command.replace("-","_").replace(".","_")+"_of_unit"
    command_func = getattr(systemctl, command_name, None)
    if callable(command_func) and not found:
        found = True
        result = command_func(modules[0])
    command_name = command.replace("-","_").replace(".","_")+"_of_units"
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
        for comm in modules:
            comm_name = "system_"+comm.replace("-","_").replace(".","_")
            comm_func = getattr(systemctl, comm_name, None)
            if callable(comm_func):
                found = True
                result = comm_func()
    if not found:
        logg.error("EXEC END no method for '%s'", command)
        sys.exit(1)
    if _init:
        logg.info("continue as init process")
        systemctl.system_wait()
    if result is None:
        logg.info("EXEC END None")
        sys.exit(0)
    elif result is True:
        logg.info("EXEC END True")
        sys.exit(0)
    elif result is False:
        logg.info("EXEC END False")
        sys.exit(1)
    elif isinstance(result, tuple) and len(result) == 2:
        exitcode, status = result
        print status
        logg.info("EXEC END %s '%s'", exitcode, status)
        if exitcode is True: exitcode = 0
        if exitcode is False: exitcode = 1
        sys.exit(exitcode)
    elif isinstance(result, basestring):
        print result
        logg.info("EXEC END '%s'", result)
    elif isinstance(result, list):
        for element in result:
            if isinstance(element, tuple):
                print "\t".join(element)
            else:
                print element
        logg.info("EXEC END %s", result)
    elif hasattr(result, "keys"):
        for key in sorted(result.keys()):
            element = result[key]
            if isinstance(element, tuple):
                print key,"=","\t".join(element)
            else:
                print key,"=",element
        logg.info("EXEC END %s", result)
    else:
        logg.warning("EXEC END Unknown result type %s", str(type(result)))
