#! /usr/bin/env python
""" Testcases for docker-systemctl-replacement functionality """

from __future__ import print_function

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "1.3.2313"

## NOTE:
## The testcases 1000...4999 are using a --root=subdir environment
## The testcases 5000...9999 will start a docker container to work.

import subprocess
import os.path
import time
import datetime
import unittest
import shutil
import inspect
import types
import logging
import re
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json

logg = logging.getLogger("TESTING")
_python = "/usr/bin/python"
_systemctl_py = "files/docker/systemctl.py"
_top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* ' | grep -v -e ' ps ' -e ' grep ' -e 'kworker/'"
_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"
_cov = ""
_cov_run = "coverage2 run '--omit=*/six.py' --append -- "
_cov_cmd = "coverage2"
_cov3run = "coverage3 run '--omit=*/six.py' --append -- "
_cov3cmd = "coverage3"
_python_coverage = "python-coverage"
_python3coverage = "python3-coverage"
COVERAGE = False

IMAGES = "localhost:5000/testingsystemctl"
CENTOS = "centos:7.4.1708"
UBUNTU = "ubuntu:14.04"
OPENSUSE = "opensuse:42.3"

DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"

realpath = os.path.realpath

def sh____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out
def output2(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out, run.returncode
def output3(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return out, err, run.returncode
def _lines(lines):
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def lines(text):
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def grep(pattern, lines):
    for line in _lines(lines):
       if re.search(pattern, line.rstrip()):
           yield line.rstrip()
def greps(lines, pattern):
    return list(grep(pattern, lines))

def download(base_url, filename, into):
    if not os.path.isdir(into):
        os.makedirs(into)
    if not os.path.exists(os.path.join(into, filename)):
        sh____("cd {into} && wget {base_url}/{filename}".format(**locals()))
def text_file(filename, content):
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
def shell_file(filename, content):
    text_file(filename, content)
    os.chmod(filename, 0770)
def copy_file(filename, target):
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename, target):
    copy_file(filename, target)
    os.chmod(target, 0750)

def get_caller_name():
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code.co_name
def get_caller_caller_name():
    frame = inspect.currentframe().f_back.f_back.f_back
    return frame.f_code.co_name
def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
       path = path[1:]
    return os.path.join(root, path)
def os_getlogin():
    """ NOT using os.getlogin() """
    import pwd
    return pwd.getpwuid(os.geteuid()).pw_name

class DockerSystemctlReplacementTest(unittest.TestCase):
    def caller_testname(self):
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix = None):
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self):
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 5000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    def makedirs(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)
    def real_folders(self):
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
    def rm_zzfiles(self, root):
        for folder in self.real_folders():
            for item in glob(os_path(root, folder + "/zz*")):
                logg.info("rm %s", item)
                os.remove(item)
            for item in glob(os_path(root, folder + "/test_*")):
                logg.info("rm %s", item)
                os.remove(item)
    def coverage(self, testname = None):
        testname = testname or self.caller_testname()
        newcoverage = ".coverage."+testname
        time.sleep(1) # TODO: flush output
        if os.path.isfile(".coverage"):
            # shutil.copy(".coverage", newcoverage)
            f = open(".coverage")
            text = f.read()
            f.close()
            text2 = re.sub(r"(\]\}\})[^{}]*(\]\}\})$", r"\1", text)
            f = open(newcoverage, "w")
            f.write(text2)
            f.close()
    def root(self, testdir, real = None):
        if real: return "/"
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def user(self):
        return os_getlogin()
    def ip_container(self, name):
        values = output("docker inspect "+name)
        values = json.loads(values)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"]    
    def with_local_centos_mirror(self, ver = None):
        """ detects a local centos mirror or starts a local
            docker container with a centos repo mirror. It
            will return the setting for extrahosts"""
        rmi = "localhost:5000"
        rep = "centos-repo"
        ver = ver or CENTOS.split(":")[1]
        find_repo_image = "docker images {rmi}/{rep}:{ver}"
        images = output(find_repo_image.format(**locals()))
        running = output("docker ps")
        if greps(images, rep) and not greps(running, rep+ver):
            cmd = "docker rm --force {rep}{ver}"
            sx____(cmd.format(**locals()))
            cmd = "docker run --detach --name {rep}{ver} {rmi}/{rep}:{ver}"
            sh____(cmd.format(**locals()))
        running = output("docker ps")
        if greps(running, rep+ver):
            ip_a = self.ip_container(rep+ver)
            logg.info("%s%s => %s", rep, ver, ip_a)
            result = "mirrorlist.centos.org:%s" % ip_a
            logg.info("--add-host %s", result)
            return result
        return ""
    def with_local_opensuse_mirror(self, ver = None):
        """ detects a local opensuse mirror or starts a local
            docker container with a centos repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000"
        rep = "opensuse-repo"
        ver = ver or OPENSUSE.split(":")[1]
        find_repo_image = "docker images {rmi}/{rep}:{ver}"
        images = output(find_repo_image.format(**locals()))
        running = output("docker ps")
        if greps(images, rep) and not greps(running, rep+ver):
            cmd = "docker rm --force {rep}{ver}"
            sx____(cmd.format(**locals()))
            cmd = "docker run --detach --name {rep}{ver} {rmi}/{rep}:{ver}"
            sh____(cmd.format(**locals()))
        running = output("docker ps")
        if greps(running, rep+ver):
            ip_a = self.ip_container(rep+ver)
            logg.info("%s%s => %s", rep, ver, ip_a)
            result = "download.opensuse.org:%s" % ip_a
            logg.info("--add-host %s", result)
            return result
        return ""
    def local_image(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            add_hosts = self.with_local_centos_mirror(version)
            if add_hosts:
                return "--add-host '{add_hosts}' {image}".format(**locals())
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            add_hosts = self.with_local_opensuse_mirror(version)
            if add_hosts:
                return "--add-host '{add_hosts}' {image}".format(**locals())
        return image
    def drop_container(self, name):
        cmd = "docker rm --force {name}"
        sx____(cmd.format(**locals()))
    def drop_centos(self):
        self.drop_container("centos")
    def drop_ubuntu(self):
        self.drop_container("ubuntu")
    def drop_opensuse(self):
        self.drop_container("opensuse")
    def make_opensuse(self):
        self.make_container("opensuse", OPENSUSE)
    def make_ubuntu(self):
        self.make_container("ubuntu", UBUNTU)
    def make_centos(self):
        self.make_container("centos", CENTOS)
    def make_container(self, name, image):
        self.drop_container(name)
        local_image = self.local_image(image)
        cmd = "docker run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd.format(**locals()))
        print("                 # " + local_image)
        print("  docker exec -it "+name+" bash")
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_1000(self):
        logg.info("\n  CENTOS = '%s'", CENTOS)
        self.with_local_centos_mirror()
    def test_1001_systemctl_testfile(self):
        """ the systemctl.py file to be tested does exist """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s",  root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(_systemctl_py, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
        self.coverage()
    def test_1002_systemctl_version(self):
        systemctl = _cov + _systemctl_py 
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "systemd 219"))
        self.assertTrue(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
        self.coverage()
    def real_1002_systemctl_version(self):
        cmd = "systemctl --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"systemd [234]\d\d"))
        self.assertFalse(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_1003_systemctl_help(self):
        """ the '--help' option and 'help' command do work """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} --help"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "--root=PATH"))
        self.assertTrue(greps(out, "--verbose"))
        self.assertTrue(greps(out, "--init"))
        self.assertTrue(greps(out, "for more information"))
        self.assertFalse(greps(out, "reload-or-try-restart"))
        cmd = "{systemctl} help" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "--verbose"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
        self.coverage()
    def test_1005_systemctl_help_command(self):
        """ for any command, 'help command' shows the documentation """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} help list-unit-files" 
        out, end = output2(cmd.format(**locals()))
        logg.info("%s\n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "for more information"))
        self.assertTrue(greps(out, "--type=service"))
        self.coverage()
    def test_1006_systemctl_help_command_other(self):
        """ for a non-existant command, 'help command' just shows the list """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} help list-foo" 
        out, end = output2(cmd.format(**locals()))
        logg.info("%s\n%s", cmd, out)
        self.assertEqual(end, 1)
        self.assertFalse(greps(out, "for more information"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
        self.coverage()
    def test_1010_systemctl_daemon_reload(self):
        """ daemon-reload always succeeds (does nothing) """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        self.coverage()
    def real_1011_systemctl_daemon_reload_root_ignored(self):
        self.test_1011_systemctl_daemon_reload_root_ignored(True)
    def test_1011_systemctl_daemon_reload_root_ignored(self, real = None):
        """ daemon-reload always succeeds (does nothing) """
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: systemctl = "/usr/bin/systemctl"
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            ExecStart=/usr/bin/sleep 3
        """)
        #
        cmd = "{systemctl} daemon-reload"
        out,end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def test_1020_systemctl_with_systemctl_log(self):
        """ when /var/log/systemctl.log exists then print INFO messages into it"""
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/systemctl.log")
        text_file(logfile,"")
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(len(greps(open(logfile), " INFO ")), 1)
        self.assertEqual(len(greps(open(logfile), " DEBUG ")), 0)
        self.rm_testdir()
        self.coverage()
    def test_1021_systemctl_with_systemctl_debug_log(self):
        """ when /var/log/systemctl.debug.log exists then print DEBUG messages into it"""
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/systemctl.debug.log")
        text_file(logfile,"")
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(len(greps(open(logfile), " INFO ")), 1)
        self.assertEqual(len(greps(open(logfile), " DEBUG ")), 3)
        self.rm_testdir()
        self.coverage()
    def test_1030_systemctl_force_ipv4(self):
        """ we can force --ipv4 for /etc/hosts """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/hosts"),"""
            127.0.0.1 localhost localhost4
            ::1 localhost localhost6""")
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        #
        cmd = "{systemctl} --ipv4 daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertFalse(greps(hosts, "::1.*localhost "))
        self.rm_testdir()
        self.coverage()
    def test_1031_systemctl_force_ipv6(self):
        """ we can force --ipv6 for /etc/hosts """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/hosts"),"""
            127.0.0.1 localhost localhost4
            ::1 localhost localhost6""")
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        #
        cmd = "{systemctl} --ipv6 daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertFalse(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        self.rm_testdir()
        self.coverage()
    def test_1050_can_create_a_test_service(self):
        """ check that a unit file can be created for testing """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertIn("\nDescription", textA)
        self.rm_testdir()
        self.coverage()
    def test_1051_can_parse_the_service_file(self):
        """ check that a unit file can be parsed atleast for a description """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        cmd = "{systemctl} __get_description zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "Testing A"))
        self.rm_testdir()
        self.coverage()
    def test_1052_can_describe_a_pid_file(self):
        """ check that a unit file can have a specific pdi file """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            PIDFile=/var/run/foo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "/var/run/foo.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1053_can_have_default_pid_file_for_simple_service(self):
        """ check that a unit file has a default pid file for simple services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertFalse(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        #TODO# self.assertTrue(greps(out, "/var/run/zza.service.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1055_other_services_use_a_status_file(self):
        """ check that other unit files may have a default status file """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=oneshot
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertFalse(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_status_file zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "/var/run/zza.service.status"))
        self.rm_testdir()
        self.coverage()
    def test_1060_can_have_shell_like_commments(self):
        """ check that a unit file can have comment lines with '#' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            #PIDFile=/var/run/zzfoo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "/var/run/zzfoo.pid"))
        #TODO# self.assertTrue(greps(out, "/var/run/zza.service.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1061_can_have_winini_like_commments(self):
        """ check that a unit file can have comment lines with ';' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            ;PIDFile=/var/run/zzfoo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "/var/run/zzfoo.pid"))
        #TODO# self.assertTrue(greps(out, "/var/run/zza.service.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1062_can_have_multi_line_settings_with_linebreak_mark(self):
        """ check that a unit file can have settings with '\\' at the line end """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A \
                which is quite special
            [Service]
            PIDFile=/var/run/zzfoo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "quite special"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_description zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "Testing A"))
        self.assertTrue(greps(out, "quite special"))
        self.rm_testdir()
        self.coverage()
    def test_1063_but_a_missing_linebreak_is_a_syntax_error(self):
        """ check that a unit file can have 'bad ini' lines throwing an exception """
        # the original systemd daemon would ignore services with syntax errors
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A 
                which is quite special
            [Service]
            PIDFile=/var/run/zzfoo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "quite special"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_description zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "Testing A"))
        self.assertFalse(greps(out, "quite special"))
        self.rm_testdir()
        self.coverage()
    def test_1070_external_env_files_can_be_parsed(self):
        """ check that a unit file can have a valid EnvironmentFile for settings """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A 
                which is quite special
            [Service]
            EnvironmentFile=/etc/sysconfig/zza.conf
            """)
        text_file(os_path(root, "/etc/sysconfig/zza.conf"),"""
            CONF1=a1
            CONF2="b2"
            CONF3='c3'
            #CONF4=b4
            """)
        cmd = "{systemctl} __read_env_file /etc/sysconfig/zza.conf -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "CONF1"))
        self.assertTrue(greps(out, "CONF2"))
        self.assertTrue(greps(out, "CONF3"))
        self.assertFalse(greps(out, "CONF4"))
        self.assertTrue(greps(out, "a1"))
        self.assertTrue(greps(out, "b2"))
        self.assertTrue(greps(out, "c3"))
        self.assertFalse(greps(out, '"b2"'))
        self.assertFalse(greps(out, "'c3'"))
        self.rm_testdir()
        self.coverage()
    def test_1080_preset_files_can_be_parsed(self):
        """ check that preset files do work internally"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} __load_preset_files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^our.preset"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} __get_preset_of_unit zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        # self.assertTrue(greps(out, r"^our.preset"))
        self.assertEqual(len(lines(out)), 0)
        #
        cmd = "{systemctl} __get_preset_of_unit zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^enable"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} __get_preset_of_unit zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^disable"))
        self.assertEqual(len(lines(out)), 1)
    def test_1090_syntax_errors_are_shown_on_daemon_reload(self):
        """ check that preset files do work internally"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=foo
            ExecStart=runA
            ExecReload=runB
            ExecStop=runC
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecReload=/usr/bin/kill -SIGHUP $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            Type=forking
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzg.service"),"""
            [Unit]
            Description=Testing G
            [Service]
            Type=foo
            ExecStart=runA
            ExecStart=runA2
            ExecReload=runB
            ExecReload=runB2
            ExecStop=runC
            ExecStop=runC2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} daemon-reload -vv 2>&1"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service:.* file without .Service. section"))
        self.assertTrue(greps(out, r"Failed to parse service type, ignoring: foo"))
        self.assertTrue(greps(out, r"b.service:.* Executable path is not absolute"))
        self.assertTrue(greps(out, r"c.service: Service has no ExecStart"))
        self.assertTrue(greps(out, r"d.service: Service lacks both ExecStart and ExecStop"))
        self.assertTrue(greps(out, r"g.service: there may be only one ExecStart statement"))
        self.assertTrue(greps(out, r"g.service: there may be only one ExecStop statement"))
        self.assertTrue(greps(out, r"c.service: the use of /bin/kill is not recommended"))
    def real_1090_syntax_errors_are_shown_in_journal_after_try_start(self):
        """ check that preset files do work internally"""
        testname = self.testname()
        root = ""
        systemctl = "/usr/bin/systemctl"
        sx____("rm /etc/systemd/system/zz*")
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=foo
            ExecStart=runA
            ExecReload=runB
            ExecStop=runC
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecReload=/usr/bin/kill -SIGHUP $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            Type=forking
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzg.service"),"""
            [Unit]
            Description=Testing G
            [Service]
            Type=foo
            ExecStart=runA
            ExecStart=runA2
            ExecReload=runB
            ExecReload=runB2
            ExecStop=runC
            ExecStop=runC2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} daemon-reload 2>&1"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        # there is not direct output
        self.assertFalse(greps(out, r"a.service:.* file without .Service. section"))
        self.assertFalse(greps(out, r"b.service:.* Executable path is not absolute"))
        self.assertFalse(greps(out, r"c.service:.* Service has no ExecStart"))
        self.assertFalse(greps(out, r"d.service:.* Service lacks both ExecStart and ExecStop"))
        self.assertFalse(greps(out, r"g.service:.* there may be only one ExecStart statement"))
        self.assertFalse(greps(out, r"g.service:.* there may be only one ExecStop statement"))
        self.assertFalse(greps(out, r"g.service:.* there may be only one ExecReload statement"))
        self.assertFalse(greps(out, r"c.service:.* the use of /bin/kill is not recommended"))
        # but let's try to start the services
        #
        cmd = "{systemctl} start zza zzb zzc zzd zzg 2>&1"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # fails to start
        self.assertTrue(greps(out, r"failed to load: Invalid argument. See system logs and 'systemctl status zz\w.service' for details."))
        cmd = "journalctl -xe --lines=50 2>&1"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)        
        self.assertFalse(greps(out, r"a.service:.* file without .Service. section")) # systemctl.py special
        self.assertTrue(greps(out, r"Failed to parse service type, ignoring: foo"))
        self.assertTrue(greps(out, r"b.service:.* Executable path is not absolute"))
        self.assertTrue(greps(out, r"c.service:.* Service has no ExecStart"))
        self.assertTrue(greps(out, r"d.service:.* Service lacks both ExecStart= and ExecStop="))
        self.assertFalse(greps(out, r"g.service:.* there may be only one ExecStart statement")) # systemctl.py special
        self.assertFalse(greps(out, r"g.service:.* there may be only one ExecStop statement")) # systemctl.py special
        self.assertFalse(greps(out, r"g.service:.* there may be only one ExecReload statement")) # systemctl.py special
        self.assertFalse(greps(out, r"c.service:.* the use of /bin/kill is not recommended")) # systemctl.py special
        sh____("rm /etc/systemd/system/zz*")
    def real_1201_get_default(self):
        self.test_1201_get_default(True)
    def test_1201_get_default(self, real = False):
        """ check that get-default works"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        cmd = "{systemctl} get-default"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if real: self.assertTrue(greps(out, "graphical.target"))
        else: self.assertTrue(greps(out, "multi-user.target"))
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def real_1211_set_default(self):
        self.test_1211_set_default(True)
    def test_1211_set_default(self, real = False):
        """ check that set-default works"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        cmd = "{systemctl} get-default"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if real: 
            old = "graphical.target"
            self.assertTrue(greps(out, old))
        else: 
            old = "multi-user.target"
            self.assertTrue(greps(out, old))
        runlevel = "basic.target"
        cmd = "{systemctl} set-default {runlevel}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} get-default"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, runlevel)) # <<<<<<<<<<
        cmd = "{systemctl} set-default {old}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} get-default"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if real: 
            old = "graphical.target"
            self.assertTrue(greps(out, old))
        else: 
            old = "multi-user.target"
            self.assertTrue(greps(out, old))
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def test_2001_can_create_test_services(self):
        """ check that two unit files can be created for testing """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B""")
        textA = file(os_path(root, "/etc/systemd/system/zza.service")).read()
        textB = file(os_path(root, "/etc/systemd/system/zzb.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textA)
        self.assertIn("\nDescription", textB)
        self.rm_testdir()
        self.coverage()
    def test_2002_list_units(self):
        """ check that two unit files can be found for 'list-units' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} list-units"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"zzb.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertIn("loaded units listed.", out)
        self.assertIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend list-units"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"zzb.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertNotIn("loaded units listed.", out)
        self.assertNotIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2003_list_unit_files(self):
        """ check that two unit service files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+static"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+static"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2004_list_unit_files_wanted(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+disabled"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+disabled"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2006_list_unit_files_wanted_and_unknown_type(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status plus handling unkonwn services"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=foo list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertIn("0 unit files listed.", out)
        self.assertEqual(len(lines(out)), 3)
        self.rm_testdir()
        self.coverage()
    def test_2008_list_unit_files_locations(self):
        """ check that unit files can be found for 'list-unit-files'
            in different standard locations on disk. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/usr/lib/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/lib/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/var/run/systemd/system/zzd.service"),"""
            [Unit]
            Description=Testing D
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+disabled"))
        self.assertTrue(greps(out, r"zzb.service\s+disabled"))
        self.assertTrue(greps(out, r"zzc.service\s+disabled"))
        self.assertTrue(greps(out, r"zzd.service\s+disabled"))
        self.assertIn("4 unit files listed.", out)
        self.assertEqual(len(lines(out)), 7)
        #
        cmd = "{systemctl} enable zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzd.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+enabled"))
        self.assertTrue(greps(out, r"zzb.service\s+enabled"))
        self.assertTrue(greps(out, r"zzc.service\s+enabled"))
        self.assertTrue(greps(out, r"zzd.service\s+enabled"))
        self.assertIn("4 unit files listed.", out)
        self.assertEqual(len(lines(out)), 7)
        #
        self.rm_testdir()
        self.coverage()
    def test_2010_list_unit_files_locations_user_mode(self):
        """ check that unit files can be found for 'list-unit-files'
            in different standard locations on disk for --user mode """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/usr/lib/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/lib/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/var/run/systemd/system/zzd.service"),"""
            [Unit]
            Description=Testing D
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/user/zzu.service"),"""
            [Unit]
            Description=Testing U
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/usr/lib/systemd/user/zzv.service"),"""
            [Unit]
            Description=Testing V
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, r"zza.service\s+disabled"))
        self.assertFalse(greps(out, r"zzb.service\s+disabled"))
        self.assertFalse(greps(out, r"zzc.service\s+disabled"))
        self.assertFalse(greps(out, r"zzd.service\s+disabled"))
        self.assertTrue(greps(out, r"zzu.service\s+disabled"))
        self.assertTrue(greps(out, r"zzv.service\s+disabled"))
        self.assertIn("2 unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        #
        cmd = "{systemctl} enable zza.service --user -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        cmd = "{systemctl} enable zzb.service --user -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        cmd = "{systemctl} enable zzu.service --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzv.service --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --type=service list-unit-files --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zzu.service\s+enabled"))
        self.assertTrue(greps(out, r"zzv.service\s+enabled"))
        self.assertIn("2 unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        #
        self.rm_testdir()
        self.coverage()
    def test_2014_list_unit_files_locations_user_extra(self):
        """ check that unit files can be found for 'list-unit-files'
            in different standard locations on disk for --user mode
            with some system files to be pinned on our user. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        user = self.user()
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            User={user}
            [Install]
            WantedBy=multi-user.target""".format(**locals()))
        text_file(os_path(root, "/usr/lib/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Sevice]
            User={user}
            [Install]
            WantedBy=multi-user.target""".format(**locals()))
        text_file(os_path(root, "/lib/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Sevice]
            User={user}
            [Install]
            WantedBy=multi-user.target""".format(**locals()))
        text_file(os_path(root, "/var/run/systemd/system/zzd.service"),"""
            [Unit]
            Description=Testing D
            [Sevice]
            User={user}
            [Install]
            WantedBy=multi-user.target""".format(**locals()))
        text_file(os_path(root, "/etc/systemd/user/zzu.service"),"""
            [Unit]
            Description=Testing U
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/usr/lib/systemd/user/zzv.service"),"""
            [Unit]
            Description=Testing V
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+disabled"))
        self.assertFalse(greps(out, r"zzb.service\s+disabled"))
        self.assertFalse(greps(out, r"zzc.service\s+disabled"))
        self.assertFalse(greps(out, r"zzd.service\s+disabled"))
        self.assertTrue(greps(out, r"zzu.service\s+disabled"))
        self.assertTrue(greps(out, r"zzv.service\s+disabled"))
        self.assertIn("3 unit files listed.", out)
        self.assertEqual(len(lines(out)), 6)
        #
        cmd = "{systemctl} enable zza.service --user -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzb.service --user -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        cmd = "{systemctl} enable zzu.service --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzv.service --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --type=service list-unit-files --user"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+enabled"))
        self.assertTrue(greps(out, r"zzu.service\s+enabled"))
        self.assertTrue(greps(out, r"zzv.service\s+enabled"))
        self.assertIn("3 unit files listed.", out)
        self.assertEqual(len(lines(out)), 6)
        #
        logg.info("enabled services for User=%s", user)
        self.rm_testdir()
        self.coverage()
    def test_2043_list_unit_files_common_targets(self):
        """ check that some unit target files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+static"))
        self.assertFalse(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        cmd = "{systemctl} --no-legend --type=target list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, r"zza.service\s+static"))
        self.assertFalse(greps(out, r"zzb.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertGreater(len(lines(out)), 10)
        num_targets = len(lines(out))
        cmd = "{systemctl} --no-legend list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), num_targets + 2)
        self.rm_testdir()
        self.coverage()
    def test_2044_list_unit_files_now(self):
        """ check that 'list-unit-files --now' presents a special debug list """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --no-legend --now list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+SysD\s+.*systemd/system/zza.service"))
        self.assertTrue(greps(out, r"zzb.service\s+SysD\s+.*systemd/system/zzb.service"))
        self.assertFalse(greps(out, r"multi-user.target"))
        self.assertFalse(greps(out, r"enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2140_show_environment_from_parts(self):
        """ check that the result of 'environment UNIT' can 
            list the settings from different locations."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/sysconfig/zzb.conf"),"""
            DEF1='def1'
            DEF2="def2"
            DEF3=def3
            """)
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            EnvironmentFile=/etc/sysconfig/zzb.conf
            Environment=DEF5=def5
            Environment=DEF6=def6
            ExecStart=/usr/bin/printf $DEF1 $DEF2 \
                                $DEF3 $DEF4 $DEF5
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} environment zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^DEF1=def1"))
        self.assertTrue(greps(out, r"^DEF2=def2"))
        self.assertTrue(greps(out, r"^DEF3=def3"))
        self.assertFalse(greps(out, r"^DEF4=def4"))
        self.assertTrue(greps(out, r"^DEF5=def5"))
        self.assertTrue(greps(out, r"^DEF6=def6"))
        self.assertFalse(greps(out, r"^DEF7=def7"))
        a_lines = len(lines(out))
        #
        self.rm_testdir()
        self.coverage()
    def test_2150_have_environment_with_multiple_parts(self):
        """ check that the result of 'environment UNIT' can 
            list the assignements that are crammed into one line."""
        # https://www.freedesktop.org/software/systemd/man/systemd.exec.html#Environment=
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/sysconfig/zzb.conf"),"""
            DEF1='def1'
            DEF2="def2"
            DEF3=def3
            """)
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            EnvironmentFile=/etc/sysconfig/zzb.conf
            Environment="VAR1=word1 word2" VAR2=word3 "VAR3=$word 5 6"
            ExecStart=/usr/bin/printf $DEF1 $DEF2 \
                                $VAR1 $VAR2 $VAR3
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} environment zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^DEF1=def1"))
        self.assertTrue(greps(out, r"^DEF2=def2"))
        self.assertTrue(greps(out, r"^DEF3=def3"))
        self.assertTrue(greps(out, r"^VAR1=word1 word2"))
        self.assertTrue(greps(out, r"^VAR2=word3"))
        self.assertTrue(greps(out, r"^VAR3=\$word 5 6"))
        a_lines = len(lines(out))
        #
        self.rm_testdir()
        self.coverage()
    def test_2220_show_unit_is_parseable(self):
        """ check that 'show UNIT' is machine-readable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "{systemctl} show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        num_lines = len(lines(out))
        #
        cmd = "{systemctl} --all show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertGreater(len(lines(out)), num_lines)
        #
        for line in lines(out):
            m = re.match(r"^\w+=", line)
            if not m:
                # found non-machine readable property line
                self.assertEqual("word=value", line)
        self.rm_testdir()
        self.coverage()
    def test_2221_show_unit_can_be_restricted_to_one_property(self):
        """ check that 'show UNIT' may return just one value if asked for"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "{systemctl} show zza.service --property=Description"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show zza.service --property=Description --all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show zza.service --property=PIDFile"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show zza.service --property=PIDFile --all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        self.assertEqual(lines(out), [ "PIDFile=" ])
        self.rm_testdir()
        self.coverage()
    def test_2225_show_unit_for_multiple_matches(self):
        """ check that the result of 'show UNIT' for multiple services is 
            concatenated but still machine readable. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        a_lines = len(lines(out))
        #
        cmd = "{systemctl} show zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        b_lines = len(lines(out))
        #
        cmd = "{systemctl} show zza.service zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        all_lines = len(lines(out))
        #
        self.assertGreater(all_lines, a_lines + b_lines)
        #
        for line in lines(out):
            if not line.strip():
                # empty lines are okay now
                continue
            m = re.match(r"^\w+=", line)
            if not m:
                # found non-machine readable property line
                self.assertEqual("word=value", line)
        self.rm_testdir()
        self.coverage()
    def test_2227_show_unit_for_oneshot_service(self):
        """ check that 'show UNIT' is machine-readable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=oneshot
            ExecStart=/bin/echo foo
            ExecStop=/bin/echo bar
            """)
        cmd = "{systemctl} show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        num_lines = len(lines(out))
        #
        cmd = "{systemctl} --all show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState=static"))
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertGreater(len(lines(out)), num_lines)
        #
        for line in lines(out):
            m = re.match(r"^\w+=", line)
            if not m:
                # found non-machine readable property line
                self.assertEqual("word=value", line)
        self.rm_testdir()
        self.coverage()
    def test_2230_show_unit_display_parsed_timeouts(self):
        """ check that 'show UNIT' show parsed timeoutss """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=29
            TimeoutStopSec=60
            """)
        cmd = "{systemctl} show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=29s", rep)
        self.assertIn("TimeoutStopUSec=1min", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=1m
            TimeoutStopSec=2min
            """)
        cmd = "{systemctl} show zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1min", rep)
        self.assertIn("TimeoutStopUSec=2min", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            TimeoutStartSec=1s
            TimeoutStopSec=2000ms
            """)
        cmd = "{systemctl} show zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1s", rep)
        self.assertIn("TimeoutStopUSec=2s", rep)
        #
        self.rm_testdir()
        self.coverage()
        ##
        text_file(os_path(root, "/etc/systemd/system/zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            TimeoutStartSec=90s
            TimeoutStopSec=2250ms
            """)
        cmd = "{systemctl} show zzd.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1min 30s", rep)
        self.assertIn("TimeoutStopUSec=2s 250ms", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/zze.service"),"""
            [Unit]
            Description=Testing E
            [Service]
            TimeoutStartSec=90s 250ms
            TimeoutStopSec=3m 25ms
            """)
        cmd = "{systemctl} show zze.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1min 30s 250ms", rep)
        self.assertIn("TimeoutStopUSec=3min 25ms", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/zzf.service"),"""
            [Unit]
            Description=Testing F
            [Service]
            TimeoutStartSec=180
            TimeoutStopSec=182
            """)
        cmd = "{systemctl} show zzf.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=3min", rep)
        self.assertIn("TimeoutStopUSec=3min 2s", rep)
        #
        self.rm_testdir()
        self.coverage()
    def test_2900_class_UnitConfParser(self):
        """ using systemctl.py as a helper library for 
            the UnitConfParser functions."""
        python = _python
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl_py_dir = os.path.dirname(realpath(_systemctl_py))
        unitconfparser_py = os_path(root, "/usr/bin/unitconfparser.py")
        service_file = os_path(root, "/etc/systemd/system/zzb.service")
        defaults = {"a1": "default1"}
        shell_file(unitconfparser_py,"""
            #! {python}
            from __future__ import print_function
            import sys
            sys.path += [ "{systemctl_py_dir}" ]
            import systemctl
            data = systemctl.UnitConfigParser({defaults})
            conf = systemctl.UnitConf(data)
            print("DEFAULTS", conf.data.defaults())
            print("FILENAME", conf.filename())
            data.read(sys.argv[1])
            print("filename=", conf.filename())
            print("sections=", conf.data.sections())
            print("has.Foo.Bar=", conf.data.has_option("Foo", "Bar"))
            print("has.Unit.Foo=", conf.data.has_option("Unit", "Foo"))
            try:
               conf.data.get("Foo", "Bar")
            except Exception as e:
               print("get.Foo.Bar:", str(e))
            try:
               conf.data.get("Unit", "Foo")
            except Exception as e:
               print("get.Unit.Foo:", str(e))
            try:
               conf.data.getlist("Foo", "Bar")
            except Exception as e:
               print("getlist.Foo.Bar:", str(e))
            try:
               conf.data.getlist("Unit", "Foo")
            except Exception as e:
               print("getlist.Unit.Foo:", str(e))
            print("get.none.Foo.Bar=", conf.data.get("Foo", "Bar", allow_no_value = True))
            print("get.none.Unit.Foo=", conf.data.get("Unit", "Foo", allow_no_value = True))
            print("getlist.none.Foo.Bar=", conf.data.getlist("Foo", "Bar", allow_no_value = True))
            print("getlist.none.Unit.Foo=", conf.data.getlist("Unit", "Foo", allow_no_value = True))
            print("get.defs.Foo.Bar=", conf.data.get("Foo", "Bar", "def1"))
            print("get.defs.Unit.Foo=", conf.data.get("Unit", "Foo", "def2"))
            print("getlist.defs.Foo.Bar=", conf.data.getlist("Foo", "Bar", ["def3"]))
            print("getlist.defs.Unit.Foo=", conf.data.getlist("Unit", "Foo", ["def4"]))
            data.set("Unit", "After", "network.target")
            print("getlist.unit.after1=", conf.data.getlist("Unit", "After"))
            print("getitem.unit.after1=", conf.data.get("Unit", "After"))
            data.set("Unit", "After", "postgres.service")
            print("getlist.unit.after2=", conf.data.getlist("Unit", "After"))
            print("getitem.unit.after2=", conf.data.get("Unit", "After"))
            data.set("Unit", "After", None)
            print("getlist.unit.after0=", conf.data.getlist("Unit", "After"))
            print("getitem.unit.after0=", conf.data.get("Unit", "After", allow_no_value = True))
            print("getlist.environment=", conf.data.getlist("Service", "Environment"))
            print("get.environment=", conf.data.get("Service", "Environment"))
            print("get.execstart=", conf.data.get("Service", "ExecStart"))
            """.format(**locals()))
        text_file(service_file,"""
            [Unit]
            Description=Testing B
            [Service]
            EnvironmentFile=/etc/sysconfig/zzb.conf
            Environment=DEF5=def5
            Environment=DEF6=def6
            ExecStart=/usr/bin/printf $DEF1 $DEF2 \\
                                $DEF3 $DEF4 $DEF5 \\
                                $DEF6 $DEF7
            [Install]
            WantedBy=multi-user.target""")
        testrun = _cov + unitconfparser_py
        cmd = "{testrun} {service_file}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "DEFAULTS {'a1': 'default1'}"))
        self.assertTrue(greps(out, "FILENAME None"))
        self.assertTrue(greps(out, "filename= .*"+service_file))
        self.assertTrue(greps(out, "sections= \\['Unit', 'Service', 'Install'\\]"))
        self.assertTrue(greps(out, "has.Foo.Bar= False"))
        self.assertTrue(greps(out, "has.Unit.Foo= False"))
        self.assertTrue(greps(out, "get.Foo.Bar: section Foo does not exist"))
        self.assertTrue(greps(out, "get.Unit.Foo: option Foo in Unit does not exist"))
        self.assertTrue(greps(out, "getlist.Foo.Bar: section Foo does not exist"))
        self.assertTrue(greps(out, "getlist.Unit.Foo: option Foo in Unit does not exist"))
        self.assertTrue(greps(out, "get.none.Foo.Bar= None"))
        self.assertTrue(greps(out, "get.none.Unit.Foo= None"))
        self.assertTrue(greps(out, "getlist.none.Foo.Bar= \\[\\]"))
        self.assertTrue(greps(out, "getlist.none.Unit.Foo= \\[\\]"))
        self.assertTrue(greps(out, "get.defs.Foo.Bar= def1"))
        self.assertTrue(greps(out, "get.defs.Unit.Foo= def2"))
        self.assertTrue(greps(out, "getlist.defs.Foo.Bar= \\['def3'\\]"))
        self.assertTrue(greps(out, "getlist.defs.Unit.Foo= \\['def4'\\]"))
        self.assertTrue(greps(out, "getlist.unit.after1= \\['network.target'\\]"))
        self.assertTrue(greps(out, "getlist.unit.after2= \\['network.target', 'postgres.service'\\]"))
        self.assertTrue(greps(out, "getlist.unit.after0= \\[\\]"))
        self.assertTrue(greps(out, "getitem.unit.after1= network.target"))
        self.assertTrue(greps(out, "getitem.unit.after2= network.target"))
        self.assertTrue(greps(out, "getitem.unit.after0= None"))
        self.assertTrue(greps(out, "getlist.environment= \\['DEF5=def5', 'DEF6=def6'\\]"))
        self.assertTrue(greps(out, "get.environment= DEF5=def5"))
        self.assertTrue(greps(out, "get.execstart= /usr/bin/printf \\$DEF1 \\$DEF2 \\\\$"))
        self.assertTrue(greps(out, "      \\$DEF3 \\$DEF4 \\$DEF5"))
        self.assertTrue(greps(out, "      \\$DEF6 \\$DEF7"))
        #
        self.rm_testdir()
        self.coverage()
    def real_3002_enable_service_creates_a_symlink(self):
        self.test_3002_enable_service_creates_a_symlink(True)
    def test_3002_enable_service_creates_a_symlink(self, real = False):
        """ check that a service can be enabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def real_3003_disable_service_removes_the_symlink(self):
        self.test_3003_disable_service_removes_the_symlink(True)
    def test_3003_disable_service_removes_the_symlink(self, real = False):
        """ check that a service can be enabled and disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        #
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertTrue(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} enable zz-other.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zz-other.service")
        self.assertFalse(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} disable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} disable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} disable zz-other.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        #
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def real_3004_list_unit_files_when_enabled(self):
        self.test_3004_list_unit_files_when_enabled(True)
    def test_3004_list_unit_files_when_enabled(self, real = False):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+disabled"))
        self.assertEqual(len(greps(out, "^zz")), 2)
        #
        cmd = "{systemctl} --no-legend enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertTrue(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+enabled"))
        self.assertEqual(len(greps(out, "^zz")), 2)
        #
        cmd = "{systemctl} --no-legend disable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"zza.service\s+static"))
        self.assertTrue(greps(out, r"zzb.service\s+disabled"))
        self.assertEqual(len(greps(out, "^zz")), 2)
        #
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def real_3005_is_enabled_result_when_enabled(self):
        self.test_3005_is_enabled_result_when_enabled(True)
    def test_3005_is_enabled_result_when_enabled(self, real = None):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} is-enabled zza.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} --no-legend enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} --no-legend disable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def test_3006_is_enabled_is_true_when_any_is_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled zzb.service zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        cmd = "{systemctl} is-enabled zza.service zzb.service zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 3)
        #
        cmd = "{systemctl} --no-legend enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} is-enabled zzb.service zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} is-enabled zzc.service zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        self.rm_testdir()
        self.coverage()
    def test_3009_sysv_service_enable(self):
        """ check that we manage SysV services in a root env
            with basic enable/disable commands, also being
            able to check its status."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "xxx.init"), """
            #! /bin/bash
            ### BEGIN INIT INFO
            # Required-Start: $local_fs $remote_fs $syslog $network 
            # Required-Stop:  $local_fs $remote_fs $syslog $network
            # Default-Start:  3 5
            # Default-Stop:   0 1 2 6
            # Short-Description: Testing Z
            # Description:    Allows for SysV testing
            ### END INIT INFO
        """)
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
            sleeptime=50
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} $sleeptime 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
               cat "RUNNING `cat {root}/var/run/zzz.init.pid`"
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
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
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "xxx.init"), os_path(root, "/etc/init.d/xxx"))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/etc/init.d/zzz"))
        #
        cmd = "{systemctl} is-enabled zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} enable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        self.assertEqual(end, 0)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} --no-legend disable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} disable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} disable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(len(lines(out)), 0)
        #
        self.rm_testdir()
        self.coverage()

    def test_3010_check_preset_all(self):
        """ check that 'is-enabled' reports correctly after 'preset-all' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset-all" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3011_check_preset_one(self):
        """ check that 'is-enabled' reports correctly after 'preset service' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset zzc.service -vv" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3012_check_preset_to_reset_one(self):
        """ check that 'enable' and 'preset service' are counterparts """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3013_check_preset_to_reset_some(self):
        """ check that 'enable' and 'preset services..' are counterparts """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset zzb.service zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset zzb.service zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset zzb.service zzc.service other.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3015_check_preset_all_only_enable(self):
        """ check that 'preset-all' works with --preset-mode=enable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset-all --preset-mode=enable" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        self.rm_testdir()
        self.coverage()
    def test_3016_check_preset_all_only_disable(self):
        """ check that 'preset-all' works with --preset-mode=disable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zzb.service
            disable zzc.service""")
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable zzb.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable zzc.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset-all --preset-mode=disable" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled zzb.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled zzc.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3020_default_services(self):
        """ check the 'default-services' to know the enabled services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        self.assertFalse(greps(out, "a.service"))
        self.assertTrue(greps(out, "b.service"))
        self.assertTrue(greps(out, "c.service"))
        #
        self.rm_testdir()
        self.coverage()
    def test_3021_default_services(self):
        """ check that 'default-services' skips some known services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/mount-disks.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/network.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable mount-disks.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable network.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services --all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 3)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services --all --force"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 4)
        self.assertEqual(end, 0)
        #
        self.rm_testdir()
        self.coverage()
    def test_3030_systemctl_py_start_simple(self):
        """ check that we can start simple services with root env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        top_recent = _top_recent
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3031_systemctl_py_start_extra_simple(self):
        """ check that we can start extra simple services with root env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        top_recent = _top_recent
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3032_systemctl_py_start_forking(self):
        """ check that we can start forking services with root env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExeeStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3033_systemctl_py_start_forking_without_pid_file(self):
        """ check that we can start forking services with root env without PIDFile"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &) &
               wait %1
               # ps -o pid,ppid,args >&2
            ;; stop)
               killall {testsleep}
               echo killed all {testsleep} >&2
               sleep 1
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vvvv 2>&1"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3041_systemctl_py_run_default_services_in_testenv(self):
        """ check that we can enable services in a test env to be run as default-services"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        #
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzb.service"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} default -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        self.assertTrue(greps(top, testsleep+" 50"))
        #
        cmd = "{systemctl} halt -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)        
        self.assertFalse(greps(top, testsleep))
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def real_3050_systemctl_py_check_is_active(self):
        self.test_3050_systemctl_py_check_is_active(True)
    def test_3050_systemctl_py_check_is_active(self, real = None):
        """ check is_active behaviour"""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        enable_A = "{systemctl} enable zza.service"
        enable_B = "{systemctl} enable zzb.service"
        enable_C = "{systemctl} enable zzc.service"
        enable_D = "{systemctl} enable zzd.service"
        doneA, exitA  = output2(enable_A.format(**locals()))
        doneB, exitB  = output2(enable_B.format(**locals()))
        doneC, exitC  = output2(enable_C.format(**locals()))
        doneD, exitD  = output2(enable_D.format(**locals()))
        if not real: self.assertEqual(exitA, 1) # TODO: real = 0
        self.assertEqual(exitB, 0)
        self.assertEqual(exitC, 0)
        self.assertEqual(exitD, 1)
        #
        is_active_A = "{systemctl} is-active zza.service"
        is_active_B = "{systemctl} is-active zzb.service"
        is_active_C = "{systemctl} is-active zzc.service"
        is_active_D = "{systemctl} is-active zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "unknown")
        self.assertEqual(actB.strip(), "inactive")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(exitA, 3)
        self.assertEqual(exitB, 3)
        self.assertEqual(exitC, 3)
        self.assertEqual(exitD, 3)
        #
        cmd = "{systemctl} start zzb.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        is_active_A = "{systemctl} is-active zza.service"
        is_active_B = "{systemctl} is-active zzb.service"
        is_active_C = "{systemctl} is-active zzc.service"
        is_active_D = "{systemctl} is-active zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "unknown")
        self.assertEqual(actB.strip(), "active")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertNotEqual(exitD, 0)
        #
        logg.info("== checking combinations of arguments")
        is_active_BC = "{systemctl} is-active zzb.service zzc.service "
        is_active_CD = "{systemctl} is-active zzc.service zzd.service"
        is_active_BD = "{systemctl} is-active zzb.service zzd.service"
        is_active_BCD = "{systemctl} is-active zzb.service zzc.service zzd.service"
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        actCD, exitCD  = output2(is_active_CD.format(**locals()))
        actBD, exitBD  = output2(is_active_BD.format(**locals()))
        actBCD, exitBCD  = output2(is_active_BCD.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "inactive", ""])
        self.assertEqual(actCD.split("\n"), [ "inactive", "unknown",""])
        self.assertEqual(actBD.split("\n"), [ "active", "unknown", ""])
        self.assertEqual(actBCD.split("\n"), ["active", "inactive", "unknown", ""])
        self.assertNotEqual(exitBC, 0)         ## this is how the original systemctl
        self.assertNotEqual(exitCD, 0)         ## works. The documentation however
        self.assertNotEqual(exitBD, 0)         ## says to return 0 if any service
        self.assertNotEqual(exitBCD, 0)        ## is found to be 'active'
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        cmd = "{systemctl} start zzc.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertEqual(exitBC, 0)         ## all is-active => return 0
        #
        cmd = "{systemctl} stop zzb.service zzc.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["inactive", "inactive", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def real_3051_systemctl_py_check_is_failed(self):
        self.test_3051_systemctl_py_check_is_failed(True)
    def test_3051_systemctl_py_check_is_failed(self, real = None):
        """ check is_failed behaviour"""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        enable_A = "{systemctl} enable zza.service"
        enable_B = "{systemctl} enable zzb.service"
        enable_C = "{systemctl} enable zzc.service"
        enable_D = "{systemctl} enable zzd.service"
        doneA, exitA  = output2(enable_A.format(**locals()))
        doneB, exitB  = output2(enable_B.format(**locals()))
        doneC, exitC  = output2(enable_C.format(**locals()))
        doneD, exitD  = output2(enable_D.format(**locals()))
        if not real: self.assertEqual(exitA, 1) # TODO: real = 0
        self.assertEqual(exitB, 0)
        self.assertEqual(exitC, 0)
        self.assertEqual(exitD, 1)
        #
        is_active_A = "{systemctl} is-failed zza.service"
        is_active_B = "{systemctl} is-failed zzb.service"
        is_active_C = "{systemctl} is-failed zzc.service"
        is_active_D = "{systemctl} is-failed zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "unknown")
        self.assertEqual(actB.strip(), "inactive")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertEqual(exitA, 1)
        self.assertEqual(exitB, 1)
        self.assertEqual(exitC, 1)
        self.assertEqual(exitD, 1)
        #
        cmd = "{systemctl} start zzb.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        is_active_A = "{systemctl} is-failed zza.service"
        is_active_B = "{systemctl} is-failed zzb.service"
        is_active_C = "{systemctl} is-failed zzc.service"
        is_active_D = "{systemctl} is-failed zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "unknown")
        self.assertEqual(actB.strip(), "active")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertEqual(exitA, 1)
        self.assertEqual(exitB, 1)
        self.assertEqual(exitC, 1)
        self.assertEqual(exitD, 1)
        #
        logg.info("== checking combinations of arguments")
        is_active_BC = "{systemctl} is-failed zzb.service zzc.service {vv}"
        is_active_CD = "{systemctl} is-failed zzc.service zzd.service {vv}"
        is_active_BD = "{systemctl} is-failed zzb.service zzd.service {vv}"
        is_active_BCD = "{systemctl} is-failed zzb.service zzc.service zzd.service {vv}"
        is_active_BCDX = "{systemctl} is-failed zzb.service zzc.service zzd.service --quiet {vv}"
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        actCD, exitCD  = output2(is_active_CD.format(**locals()))
        actBD, exitBD  = output2(is_active_BD.format(**locals()))
        actBCD, exitBCD  = output2(is_active_BCD.format(**locals()))
        actBCDX, exitBCDX  = output2(is_active_BCDX.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "inactive", ""])
        self.assertEqual(actCD.split("\n"), [ "inactive", "unknown",""])
        self.assertEqual(actBD.split("\n"), [ "active", "unknown", ""])
        self.assertEqual(actBCD.split("\n"), ["active", "inactive", "unknown", ""])
        self.assertEqual(actBCDX.split("\n"), [""])
        self.assertNotEqual(exitBC, 0)         ## this is how the original systemctl
        self.assertNotEqual(exitCD, 0)         ## works. The documentation however
        self.assertNotEqual(exitBD, 0)         ## says to return 0 if any service
        self.assertNotEqual(exitBCD, 0)        ## is found to be 'active'
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        cmd = "{systemctl} start zzc.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertNotEqual(exitBC, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        if not real: self.assertEqual(actBC.split("\n"), ["failed", "failed", ""]) # TODO real 'inactive'
        if not real: self.assertEqual(exitBC, 0)         ## all is-failed => return 0
        #
        cmd = "{systemctl} stop zzb.service zzc.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["inactive", "inactive", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def real_3060_is_active_for_forking(self):
        self.test_3060_is_active_for_forking(True)
    def test_3060_is_active_for_forking(self, real = None):
        """ check that we can start forking services and have them is-active"""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        bindir = os_path(root, "/usr/bin")
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("sleep")
        self.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        cmd = "{systemctl} daemon-reload"
        sh____(cmd.format(**locals()))
        #
        cmd = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(cmd.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["unknown", ""])
        self.assertEqual(exitZX, 3)
        #
        cmd = "{systemctl} enable zzz.service {vv}"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(cmd.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["inactive", ""])
        self.assertEqual(exitZX, 3)
        #
        cmd = "{systemctl} start zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        is_active_ZX = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(is_active_ZX.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["active", ""])
        self.assertEqual(exitZX, 0)
        #
        cmd = "{systemctl} stop zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        #
        is_active_ZX = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(is_active_ZX.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["inactive", ""])
        self.assertEqual(exitZX, 3)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def real_3061_is_failed_for_forking(self):
        self.test_3061_is_failed_for_forking(True)
    def test_3061_is_failed_for_forking(self, real = None):
        """ check that we can start forking services and have them is-failed"""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        bindir = os_path(root, "/usr/bin")
        testsleep = self.testname("sleep")
        self.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        cmd = "{systemctl} is-failed zzz.service {vv}"
        actZX, exitZX  = output2(cmd.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["unknown", ""])
        self.assertEqual(exitZX, 1)
        #
        cmd = "{systemctl} enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-failed zzz.service {vv}"
        actZX, exitZX  = output2(cmd.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["inactive", ""])
        self.assertEqual(exitZX, 1)
        #
        cmd = "{systemctl} start zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        is_active_ZX = "{systemctl} is-failed zzz.service {vv}"
        actZX, exitZX  = output2(is_active_ZX.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["active", ""])
        self.assertEqual(exitZX, 1)
        #
        cmd = "{systemctl} stop zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        #
        is_active_ZX = "{systemctl} is-failed zzz.service {vv}"
        actZX, exitZX  = output2(is_active_ZX.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["inactive", ""])
        self.assertEqual(exitZX, 1)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def real_3063_is_active_for_forking_delayed(self):
        self.test_3063_is_active_for_forking_delayed(True)
    def test_3063_is_active_for_forking_delayed(self, real = None):
        """ check that we can start forking services and have them is-active,
            even when the pid-file is created later because startup waits
            for its existance."""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        self.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                sleep 4
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               sleep 1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        cmd = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(cmd.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["unknown", ""])
        self.assertEqual(exitZX, 3)
        #
        cmd = "{systemctl} enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(cmd.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["inactive", ""])
        self.assertEqual(exitZX, 3)
        #
        cmd = "{systemctl} start zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        is_active_ZX = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(is_active_ZX.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["active", ""])
        self.assertEqual(exitZX, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/run/zzz.init.pid")))
        time.sleep(4)
        self.assertTrue(os.path.exists(os_path(root, "/var/run/zzz.init.pid")))
        #
        cmd = "{systemctl} stop zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        #
        is_active_ZX = "{systemctl} is-active zzz.service {vv}"
        actZX, exitZX  = output2(is_active_ZX.format(**locals()))
        self.assertEqual(actZX.split("\n"), ["inactive", ""])
        self.assertEqual(exitZX, 3)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def real_3080_two_service_starts_in_parallel(self):
        self.test_3063_two_service_starts_in_parallel(True)
    def test_3080_two_service_starts_in_parallel(self, real = None):
        """ consider a situation where a 'systemctl start <service>' is
            done from two programs at the same time. Ensure that there
            is a locking that disallow then to run in parallel."""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + realpath(_systemctl_py) + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        self.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               (
                mkdir -p {root}/var/log
                echo starting >{root}/var/log/zzz.log
                {bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
                echo started >>{root}/var/log/zzz.log
                sleep 2
                {systemctl} start zza.service >> {root}/var/log/zzz.log 2>&1 &
               ) &
               sleep 1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStartPre={bindir}/{testsleep}pre 5
            ExecStart={bindir}/{testsleep}now 10
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep+"pre"))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep+"now"))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        cmd = "{systemctl} start zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        logg.info("===== just started")
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        time.sleep(3)
        logg.info("===== after start")
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        logfile = os_path(root, "/var/log/zzz.log")
        if os.path.exists(logfile):
            logtext = open(logfile).read()
            logg.info("zzz.log => %s", logtext)
        else:
            logg.info("no zzz.log")
        #
        logg.info("====== start next")
        cmd = "{systemctl} start zza.service {vv}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        self.assertTrue(greps(err, "\\(1\\) systemctl locked by"))
        self.assertTrue(greps(err, "the service is already running on PID")) # FIXME: may not be?
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def test_3081_two_service_starts_in_parallel_with_lockfile_remove(self, real = None):
        """ consider a situation where a 'systemctl start <service>' is
            done from two programs at the same time. Ensure that there
            is a locking that disallows them to run in parallel. In this
            scenario we test what happens if the lockfile is deleted in between."""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + realpath(_systemctl_py) + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        self.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               (
                mkdir -p {root}/var/log
                echo starting >{root}/var/log/zzz.log
                {bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
                echo started >>{root}/var/log/zzz.log
                sleep 2
                {systemctl} start zza.service >> {root}/var/log/zzz.log 2>&1 &
               ) &
               sleep 1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStartPre={bindir}/{testsleep}pre 5
            ExecStart={bindir}/{testsleep}now 10
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep+"pre"))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep+"now"))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        cmd = "DEBUG_REMOVE=2 {systemctl} start zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        logg.info("===== just started")
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        time.sleep(3)
        logg.info("===== after start")
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        logfile = os_path(root, "/var/log/zzz.log")
        if os.path.exists(logfile):
            logtext = open(logfile).read()
            logg.info("zzz.log => %s", logtext)
        else:
            logg.info("no zzz.log")
        #
        logg.info("====== start next")
        cmd = "DEBUG_REMOVE=2 {systemctl} start zza.service {vv}"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        self.assertTrue(greps(err, "\\(1\\) systemctl locked by"))
        self.assertTrue(greps(err, "the service is already running on PID"))
        self.assertTrue(greps(err, "lock got deleted, trying again"))
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def real_3102_mask_service_creates_empty_file(self):
        self.test_3102_mask_service_creates_empty_file(True)
    def test_3102_mask_service_creates_empty_file(self, real = False):
        """ check that a service can be masked """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        vv = "-vv"
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        text_file(os_path(root, "/usr/lib/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/usr/lib/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        cmd = "{systemctl} status zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "enabled"))
        # .........................................
        cmd = "{systemctl} mask zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} status zzb.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "enabled"))
        self.assertTrue(greps(out, "masked"))
        if real: self.assertTrue(greps(out, "/dev/null"))
        else: self.assertTrue(greps(out, "None, "))
        mask_file = os_path(root, "/etc/systemd/system/zzb.service")
        self.assertTrue(os.path.islink(mask_file))
        target = os.readlink(mask_file)
        self.assertEqual(target, "/dev/null")
        cmd = "{systemctl} show zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "LoadState=masked"))
        self.assertTrue(greps(out, "UnitFileState=masked"))
        self.assertTrue(greps(out, "Id=zzb.service"))
        self.assertTrue(greps(out, "Names=zzb.service"))
        cmd = "{systemctl} is-active zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if real: self.assertTrue(greps(out, "inactive"))
        cmd = "{systemctl} is-enabled zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "masked"))
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def real_3104_unmask_service_removes_empty_file(self):
        self.test_3104_unmask_service_removes_empty_file(True)
    def test_3104_unmask_service_removes_empty_file(self, real = False):
        """ check that a service can be unmasked """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir, real)
        vv = "-vv"
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        self.rm_zzfiles(root)
        #
        text_file(os_path(root, "/usr/lib/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/usr/lib/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            ExecStart=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/zzb.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        cmd = "{systemctl} status zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "enabled"))
        # .........................................
        cmd = "{systemctl} mask zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} status zzb.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "enabled"))
        self.assertTrue(greps(out, "masked"))
        if real: self.assertTrue(greps(out, "/dev/null"))
        else: self.assertTrue(greps(out, "None, "))
        mask_file = os_path(root, "/etc/systemd/system/zzb.service")
        self.assertTrue(os.path.islink(mask_file))
        target = os.readlink(mask_file)
        self.assertEqual(target, "/dev/null")
        cmd = "{systemctl} show zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "LoadState=masked"))
        self.assertTrue(greps(out, "UnitFileState=masked"))
        self.assertTrue(greps(out, "Id=zzb.service"))
        self.assertTrue(greps(out, "Names=zzb.service"))
        # .................................................
        cmd = "{systemctl} unmask zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} status zzb.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "enabled"))
        self.assertFalse(greps(out, "masked"))
        mask_file = os_path(root, "/etc/systemd/system/zzb.service")
        self.assertFalse(os.path.exists(mask_file))
        cmd = "{systemctl} show zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "LoadState=loaded"))
        self.assertTrue(greps(out, "Id=zzb.service"))
        self.assertTrue(greps(out, "Names=zzb.service"))
        self.rm_zzfiles(root)
        self.rm_testdir()
        self.coverage()
    def test_3201_missing_environment_file_makes_service_ignored(self):
        """ check that a missing EnvironmentFile spec makes the service to be ignored"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            EnvironmentFile=/foo.conf
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        start_service = "{systemctl} start zzz.service -vv"
        end = sx____(start_service.format(**locals()))
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        self.assertGreater(end, 0)
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        end = sx____(stop_service.format(**locals()))
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        self.assertGreater(end, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3211_environment_files_are_included(self):
        """ check that environment specs are read correctly"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            EnvironmentFile=/etc/sysconfig/zzz.conf
            Environment=CONF4=dd4
            ExecStart={bindir}/zzz.sh
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            echo "WITH CONF1=$CONF1" >> {logfile}
            echo "WITH CONF2=$CONF2" >> {logfile}
            echo "WITH CONF3=$CONF3" >> {logfile}
            echo "WITH CONF4=$CONF4" >> {logfile}
            {bindir}/{testsleep} 4
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.conf"),"""
            CONF1=aa1
            CONF2="bb2"
            CONF3='cc3'
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(bindir, "zzz.sh"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_file(os_path(testdir, "zzz.conf"), os_path(root, "/etc/sysconfig/zzz.conf"))
        #
        start_service = "{systemctl} start zzz.service -vv"
        end = sx____(start_service.format(**locals()))
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        self.assertEqual(end, 0)
        #
        log = lines(open(logfile))
        logg.info("LOG \n| %s", "\n| ".join(log))
        self.assertTrue(greps(log, "WITH CONF1=aa1"))
        self.assertTrue(greps(log, "WITH CONF2=bb2"))
        self.assertTrue(greps(log, "WITH CONF3=cc3"))
        self.assertTrue(greps(log, "WITH CONF4=dd4"))
        os.remove(logfile)
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        end = sx____(stop_service.format(**locals()))
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        #
        self.rm_testdir()
        self.coverage()
    def test_3240_may_expand_environment_variables(self):
        """ check that different styles of environment
            variables get expanded."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        print_sh = os_path(root, "/usr/bin/print.sh")
        logfile = os_path(root, "/var/log/print_sh.log")
        text_file(os_path(root, "/etc/sysconfig/b.conf"),"""
            DEF1='def1'
            DEF2="def2 def3"
            DEF4="$DEF1 ${DEF2}"
            DEF5="$DEF1111 def5 ${DEF2222}"
            """)
        text_file(os_path(root, "/etc/systemd/system/zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Environment=DEF2=foo
            EnvironmentFile=/etc/sysconfig/b.conf
            ExecStart=/usr/bin/sleep 3
            ExecStartPost=%s A $DEF1 $DEF2
            ExecStartPost=%s B ${DEF1} ${DEF2}
            ExecStartPost=%s C $DEF1$DEF2
            ExecStartPost=%s D ${DEF1}${DEF2}
            ExecStartPost=%s E ${DEF4}
            ExecStartPost=%s F ${DEF5}
            [Install]
            WantedBy=multi-user.target""" 
            % (print_sh, print_sh, print_sh, print_sh, 
               print_sh, print_sh,))
        text_file(logfile, "")
        shell_file(print_sh, """
            #! /bin/sh
            logfile='{logfile}'
            echo "'$1' '$2' '$3' '$4' '$5'" >> "$logfile"
            """.format(**locals()))
        cmd = "{systemctl} environment zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^DEF1=def1"))
        self.assertTrue(greps(out, r"^DEF2=def2 def3"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        log = lines(open(logfile))
        logg.info("LOG \n%s", log)
        A="'A' 'def1' 'def2' 'def3' ''"   # A $DEF1 $DEF2
        B="'B' 'def1' 'def2 def3' '' ''"  # B ${DEF1} ${DEF2}
        C="'C' 'def1def2' 'def3' '' ''"   # C $DEF1$DEF2
        D="'D' 'def1def2 def3' '' '' ''"  # D ${DEF1}${DEF2} ??TODO??
        E="'E' 'def1 def2 def3' '' '' ''" # E ${DEF4}
        F="'F' ' def5 ' '' '' ''"         # F ${DEF5}
        self.assertIn(A, log)
        self.assertIn(B, log)
        self.assertIn(C, log)
        self.assertIn(D, log)
        self.assertIn(E, log)
        self.assertIn(F, log)
        #
        self.rm_testdir()
        self.coverage()
    def test_3250_may_expand_special_variables(self):
        """ check that different flavours for special
            variables get expanded."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        print_sh = os_path(root, "/usr/bin/print.sh")
        logfile = os_path(root, "/var/log/print_sh.log")
        service_file = os_path(root, "/etc/systemd/system/zzb zzc.service")
        text_file(service_file,"""
            [Unit]
            Description=Testing B
            [Service]
            Environment=X=x1
            Environment="Y=y2 y3"
            ExecStart=/usr/bin/sleep 3
            ExecStartPost=%s A %%N $X ${Y}
            ExecStartPost=%s B %%n $X ${Y}
            ExecStartPost=%s C %%f $X ${Y}
            ExecStartPost=%s D %%t $X ${Y}
            ExecStartPost=%s E %%P $X ${Y}
            ExecStartPost=%s F %%p $X ${Y}
            ExecStartPost=%s G %%I $X ${Y}
            ExecStartPost=%s H %%i $X ${Y} $FOO
            ExecStartPost=%s Z %%Z $X ${Y} ${FOO}
            [Install]
            WantedBy=multi-user.target""" 
            % (print_sh, print_sh, print_sh, print_sh,
               print_sh, print_sh, print_sh, print_sh,
               print_sh,))
        text_file(logfile, "")
        shell_file(print_sh, """
            #! /bin/sh
            logfile='{logfile}'
            echo "'$1' '$2' '$3' '$4' '$5'" >> "$logfile"
            """.format(**locals()))
        #
        cmd = "{systemctl} start 'zzb zzc.service' -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        log = lines(open(logfile))
        logg.info("LOG \n%s", log)
        A="'A' 'zzb' 'zzc.service' 'x1' 'y2 y3'"  # A %%N
        B="'B' 'zzb zzc.service' 'x1' 'y2 y3' ''" # B %%n
        C="'C' '%s' 'x1' 'y2 y3' ''" % service_file           # C %%f
        D="'D' '%s' 'x1' 'y2 y3' ''" % os_path(root, "/var")  # D %%t
        E="'E' 'zzb' 'zzc' 'x1' 'y2 y3'"  # E %%P
        F="'F' 'zzb zzc' 'x1' 'y2 y3' ''" # F %%p
        G="'G' 'x1' 'y2 y3' '' ''" # G %%I
        H="'H' '' 'x1' 'y2 y3' ''" # H %%i
        Z="'Z' '' 'x1' 'y2 y3' ''" # Z %%Z
        self.assertIn(A, log)
        self.assertIn(B, log)
        self.assertIn(C, log)
        self.assertIn(D, log)
        self.assertIn(E, log)
        self.assertIn(F, log)
        self.assertIn(G, log)
        self.assertIn(H, log)
        self.assertIn(Z, log)
        #
        self.rm_testdir()
        self.coverage()
    def test_3270_may_override_environment_from_commandline(self):
        """ check that --extra-vars can be given on the commandline
            to override settings in Environment= and EnvironmentFile=."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        print_sh = os_path(root, "/usr/bin/print.sh")
        logfile = os_path(root, "/var/log/print_sh.log")
        service_file = os_path(root, "/etc/systemd/system/zzb zzc.service")
        env_file = "/etc/sysconfig/my.conf"
        extra_vars_file = "/etc/sysconfig/extra.conf"
        env_text_file = os_path(root, env_file)
        extra_vars_text_file = os_path(root, extra_vars_file)
        text_file(env_text_file,"""
            M="emm a"
            N='enn i'
        """)
        text_file(extra_vars_text_file,"""
            R="rob o"
            Y='knew it'
        """)
        text_file(service_file,"""
            [Unit]
            Description=Testing B
            [Service]
            Environment=X=x1
            Environment="Y=y2 y3"
            EnvironmentFile=%s
            ExecStart=/usr/bin/sleep 3
            ExecStartPost=%s X: $X ${X}
            ExecStartPost=%s Y: $Y ${Y}
            ExecStartPost=%s M: $M ${M}
            ExecStartPost=%s N: $N ${N}
            ExecStartPost=%s R: $R ${R}
            ExecStartPost=%s S: $S ${S}
            ExecStartPost=%s T: $T ${T}
            [Install]
            WantedBy=multi-user.target""" 
            % (env_file, print_sh, print_sh, print_sh,
               print_sh, print_sh, print_sh, print_sh, ))
        text_file(logfile, "")
        shell_file(print_sh, """
            #! /bin/sh
            logfile='{logfile}'
            echo "'$1' '$2' '$3' '$4' '$5'" >> "$logfile"
            """.format(**locals()))
        #
        cmd = "{systemctl} start 'zzb zzc.service' -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        log = lines(open(logfile))
        logg.info("LOG \n%s", log)
        X="'X:' 'x1' 'x1' '' ''"  #
        Y="'Y:' 'y2' 'y3' 'y2 y3' ''" 
        M="'M:' 'emm' 'a' 'emm a' ''" 
        N="'N:' 'enn' 'i' 'enn i' ''" 
        R="'R:' '' '' '' ''"
        S="'S:' '' '' '' ''"
        T="'T:' '' '' '' ''"
        self.assertIn(X, log)
        self.assertIn(Y, log)
        self.assertIn(M, log)
        self.assertIn(N, log)
        self.assertIn(R, log)
        self.assertIn(S, log)
        self.assertIn(T, log)
        #
        cmd = "{systemctl} stop 'zzb zzc.service'"
        out, end = output2(cmd.format(**locals()))
        time.sleep(1)
        cmd = "{systemctl} start 'zzb zzc.service' -vv -e X=now --environment 'M=more N=from' --extra-vars @" + extra_vars_file
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        log = lines(open(logfile))
        logg.info("LOG \n%s", log)
        X="'X:' 'now' 'now' '' ''"  #
        Y="'Y:' 'knew' 'it' 'knew it' ''" 
        M="'M:' 'more' 'more' '' ''" 
        N="'N:' 'from' 'from' '' ''" 
        R="'R:' 'rob' 'o' 'rob o' ''"
        S="'S:' '' '' '' ''"
        T="'T:' '' '' '' ''"
        self.assertIn(X, log)
        self.assertIn(Y, log)
        self.assertIn(M, log)
        self.assertIn(N, log)
        self.assertIn(R, log)
        self.assertIn(S, log)
        self.assertIn(T, log)
        #
        self.rm_testdir()
        self.coverage()
    def test_3301_service_config_show(self):
        """ check that a named service config can show its properties"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} show zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "Id=zzs.service"))
        self.assertTrue(greps(data, "Names=zzs.service"))
        self.assertTrue(greps(data, "Description=Testing"))
        self.assertTrue(greps(data, "MainPID=0"))
        self.assertTrue(greps(data, "SubState=dead"))
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertTrue(greps(data, "LoadState=loaded"))
        self.assertTrue(greps(data, "UnitFileState=disabled"))
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "Id=zzs.service"))
        self.assertTrue(greps(data, "Names=zzs.service"))
        self.assertTrue(greps(data, "Description=Testing"))
        self.assertTrue(greps(data, "MainPID=0"))
        self.assertTrue(greps(data, "SubState=dead"))
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertTrue(greps(data, "LoadState=loaded"))
        self.assertTrue(greps(data, "UnitFileState=enabled")) # <<<
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "Id=zzs.service"))
        self.assertTrue(greps(data, "Names=zzs.service"))
        self.assertTrue(greps(data, "Description=Testing"))
        self.assertTrue(greps(data, "MainPID=[123456789][1234567890]*")) # <<<<
        self.assertTrue(greps(data, "SubState=running")) # <<<
        self.assertTrue(greps(data, "ActiveState=active")) # <<<<
        self.assertTrue(greps(data, "LoadState=loaded"))
        self.assertTrue(greps(data, "UnitFileState=enabled")) 
        self.assertEqual(end, 0)
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3302_service_config_show_single_properties(self):
        """ check that a named service config can show a single properties"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} show zzs.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=active"))
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv -p 'MainPID'"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "MainPID=[123456789][1234567890]*")) # <<<<
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3303_service_config_show_single_properties_plus_unknown(self):
        """ check that a named service config can show a single properties"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} show zzs.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service other.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=active"))
        self.assertEqual(len(data), 1)
        #
        cmd = "{systemctl} show zzs.service other.service -vv -p 'MainPID'"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "MainPID=[123456789][1234567890]*")) # <<<<
        self.assertEqual(len(data), 1)
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3401_service_status_show(self):
        """ check that a named service config can show its status"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} status zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: inactive"))
        self.assertTrue(greps(data, "[(]dead[)]"))
        self.assertTrue(greps(data, "disabled[)]"))
        #
        cmd = "{systemctl} enable zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} status zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: active"))
        self.assertTrue(greps(data, "[(]running[)]"))
        self.assertTrue(greps(data, "enabled[)]"))
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3403_service_status_show_plus_unknown(self):
        """ check that a named service config can show its status"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} status zzs.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: inactive"))
        self.assertTrue(greps(data, "[(]dead[)]"))
        self.assertTrue(greps(data, "disabled[)]"))
        #
        cmd = "{systemctl} enable zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} status zzs.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: active"))
        self.assertTrue(greps(data, "[(]running[)]"))
        self.assertTrue(greps(data, "enabled[)]"))
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3530_systemctl_py_default_workingdirectory_is_root(self):
        """ check that services without WorkingDirectory start in / """
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/zzz.sh
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertIn(root, log) # <<<<<<<<<< CHECK
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3531_systemctl_py_simple_in_workingdirectory(self):
        """ check that we can start simple services with a WorkingDirectory"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        workingdir = "/var/testsleep"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            WorkingDirectory={workingdir}
            ExecStart={bindir}/zzz.sh
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        os.makedirs(os_path(root, workingdir))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertIn(os_path(root,workingdir), log) # <<<<<<<<<< CHECK
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3532_systemctl_py_with_bad_workingdirectory(self):
        """ check that we can start simple services with a bad WorkingDirectory"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        workingdir = "/var/testsleep"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            WorkingDirectory={workingdir}
            ExecStart={bindir}/zzz.sh
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        # os.makedirs(os_path(root, workingdir)) <<<
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertNotIn(os_path(root,workingdir), log) # <<<<<<<<<< CHECK
        self.assertIn(root, log)
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3533_systemctl_py_with_bad_workingdirectory(self):
        """ check that we can start simple services with a bad WorkingDirectory with '-'"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        workingdir = "/var/testsleep"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            WorkingDirectory=-{workingdir}
            ExecStart={bindir}/zzz.sh
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        # os.makedirs(os_path(root, workingdir)) <<<
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertNotIn(os_path(root,workingdir), log) # <<<<<<<<<< CHECK
        self.assertIn(root, log)
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3601_non_absolute_ExecStopPost(self):
        """ check that we get a strong warning when not using absolute paths in ExecCommands"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            ExecStop=/usr/bin/killall {testsleep}
            ExecStopPost=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        self.assertTrue(greps(err, "Exec is not an absolute"))
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3602_non_absolute_ExecStop(self):
        """ check that we get a strong warning when not using absolute paths in ExecCommands"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            ExecStop=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        self.assertTrue(greps(err, "Exec is not an absolute"))
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3603_non_absolute_ExecReload(self):
        """ check that we get a strong warning when not using absolute paths in ExecCommands"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            ExecReload=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} reload zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        self.assertTrue(greps(err, "Exec is not an absolute"))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3604_non_absolute_ExecStartPost(self):
        """ check that we get a strong warning when not using absolute paths in ExecCommands"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            ExecStartPost=echo OK
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(err, "Exec is not an absolute"))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3605_non_absolute_ExecStartPre(self):
        """ check that we get a strong warning when not using absolute paths in ExecCommands"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStartPre=echo OK
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(err, "Exec is not an absolute"))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3606_non_absolute_ExecStart(self):
        """ check that we get a strong warning when not using absolute paths in ExecCommands"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=sleep 50
            TimeoutSec=10
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Exec is not an absolute"))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, err, out)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3901_service_config_cat(self):
        """ check that a name service config can be printed as-is"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} cat zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        orig = lines(open(os_path(root, "/etc/systemd/system/zzs.service")))
        data = lines(out)
        self.assertEqual(orig + [""], data)
        #
        self.rm_testdir()
        self.coverage()
    def test_3903_service_config_cat_plus_unknown(self):
        """ check that a name service config can be printed as-is"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} cat zzs.service unknown.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        orig = lines(open(os_path(root, "/etc/systemd/system/zzs.service")))
        data = lines(out)
        self.assertEqual(orig + [""], data)
        #
        self.rm_testdir()
        self.coverage()
    def test_4030_simple_service_functions(self):
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("testsleep")
        testscript = self.testname("testscript.sh")
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(logfile, "")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testscript} 50
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill -3 $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            ExecReload=/usr/bin/kill -10 $MAINPID
            KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscript),"""
            #! /bin/sh
            date +%T,enter > {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep}
              date +%T,stopped >> {logfile}
            {end}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 10
            date +%T,starting >> {logfile}
            {bindir}/{testsleep} $1 >> {logfile} 2>&1 &
            while kill -0 $!; do 
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10
            date +%T,leave >> {logfile}
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        # inspect the service's log
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertTrue(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        os.remove(logfile)
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        # inspect the service's log
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        os.remove(logfile)
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
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
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "reload"))
        os.remove(logfile)
        #
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertFalse(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertFalse(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertTrue(greps(log, "reload"))
        os.remove(logfile)
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # no PID known so 'kill $MAINPID' fails
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will NOT restart an is-active service (with ExecReload)")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4032_forking_service_functions(self):
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
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
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
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
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4035_notify_service_functions(self):
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        if not os.path.exists("/usr/bin/socat"):
            self.skipTest("missing /usr/bin/socat")
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,args
            {end}
            stop() {begin}
                killall {testsleep}
            {end}
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
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
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
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4036_notify_service_functions_with_reload(self):
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        if not os.path.exists("/usr/bin/socat"):
            self.skipTest("missing /usr/bin/socat")
        # self.skipTest("unfinished (bad functionality?)") # TODO
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,args
            {end}
            stop() {begin}
                killall {testsleep}
            {end}
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
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
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
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
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
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is the same PID for the service process (if ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")  #TODO#
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.rm_testdir()
        self.coverage()
    def test_4037_oneshot_service_functions(self):
        """ check that we manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/usr/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/usr/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "backup"), os_path(root, "/usr/bin/backup"))
        text_file(os_path(root, "/var/tmp/test.0"), """..""")
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        is_active = "{systemctl} is-active zzz.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vvvv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4038_oneshot_and_unknown_service_functions(self):
        """ check that we manage multiple services even when some
            services are not actually known. Along with oneshot serivce
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart / we have only different exit-code."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/usr/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/usr/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "backup"), os_path(root, "/usr/bin/backup"))
        text_file(os_path(root, "/var/tmp/test.0"), """..""")
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        is_active = "{systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = "{systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3) 
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")        
        cmd = "{systemctl} reload-or-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4039_sysv_service_functions(self):
        """ check that we manage SysV services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
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
            sleeptime=50
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} $sleeptime 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
               cat "RUNNING `cat {root}/var/run/zzz.init.pid`"
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
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
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/etc/init.d/zzz"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
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
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
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
        logg.info("== 'reload-or-restart' may restart a service that is-active")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps6 = find_pids(top6, testsleep)
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()

    def test_4050_forking_service_failed_functions(self):
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            checking the executions when some part fails."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        fail = os_path(root, "/tmp/fail")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
            echo "run-$1" >> $logfile
            if test -f {fail}$1; then
               echo "fail-$1" >> $logfile
               exit 1
            fi
            case "$1" 
            in start)
               echo "START-IT" >> $logfile
               start >> $logfile 2>&1
               echo "started" >> $logfile
            ;; stop)
               echo "STOP-IT" >> $logfile
               stop >> $logfile 2>&1
               echo "stopped" >> $logfile
            ;; restart)
               echo "RESTART-IT" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               echo "restarted" >> $logfile
            ;; reload)
               echo "RELOAD-IT" >> $logfile
               echo "...." >> $logfile 2>&1
               echo "reloaded" >> $logfile
            ;; start-pre)
               echo "START-PRE" >> $logfile
            ;; start-post)
               echo "START-POST" >> $logfile
            ;; stop-post)
               echo "STOP-POST" >> $logfile
            ;; esac 
            echo "done$1" >&2
            if test -f {fail}after$1; then
               echo "fail-after-$1" >> $logfile
               exit 1
            fi
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStartPre={root}/usr/bin/zzz.init start-pre
            ExecStart={root}/usr/bin/zzz.init start
            ExecStartPost={root}/usr/bin/zzz.init start-post
            ExecStop={root}/usr/bin/zzz.init stop
            ExecStopPost={root}/usr/bin/zzz.init stop-post
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, ["created"])
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started",
           "run-start-post", "START-POST"])
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-stop", "STOP-IT", "stopped",
           "run-stop-post", "STOP-POST"])
        #
        text_file(fail+"start", "")
        #
        logg.info("== 'start' returns to stopped if the main call fails ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "fail-start",
           "run-stop-post", "STOP-POST"])
        #
        logg.info("== 'stop' on stopped service does not do much ")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log[:2], [
           "run-stop", "STOP-IT" ])
        self.assertEqual(log[-2:], [
           "run-stop-post", "STOP-POST"])
        #
        logg.info("== 'restart' on a stopped item remains stopped if the main call fails ")
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "fail-start",
           "run-stop-post", "STOP-POST"])
        #
        os.remove(fail+"start")
        text_file(fail+"stop", "")
        #
        logg.info("== 'start' that service ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' may have a failed item ")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        # 'active' because the PIDFile process was not killed
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started",
           "run-start-post", "START-POST",
           "run-stop", "fail-stop"])
        #
        os.remove(fail+"stop")
        text_file(fail+"afterstop", "")
        #
        logg.info("== 'start' that service ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' may have a failed item ")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started",
           "run-start-post", "START-POST",
           "run-stop", "STOP-IT", "stopped", "fail-after-stop",
           "run-stop-post", "STOP-POST"])
        #
        os.remove(fail+"afterstop")
        text_file(fail+"afterstart", "")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started", "fail-after-start",
           "run-stop-post", "STOP-POST"])
        #
        self.rm_testdir()
        self.coverage()
    def test_4060_oneshot_truncate_old_status(self):
        """ check that we manage a service that has some old .status
            file being around. That is a reboot has occurred and the
            information is not relevant to the current system state."""
        self.rm_testdir()
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=oneshot
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStopPost=/usr/bin/rm {root}/var/tmp/test.1
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        text_file(os_path(root, "/var/tmp/test.0"), """..""")
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        is_active = "{systemctl} is-active zzz.service other.service {vv}"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = "{systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3) 
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        #
        logg.info("== 'restart' shall start a service that NOT is-active\n")        
        cmd = "{systemctl} restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        #
        logg.info("== mark the status file as being too old")
        status_file = os_path(root, "/var/run/zzz.service.status")
        self.assertTrue(os.path.exists(status_file))
        sh____("LANG=C stat {status_file} | grep Modify:".format(**locals()))
        sh____("LANG=C stat /proc/1/status | grep Modify:".format(**locals()))
        sh____("touch -r /proc/1/status {status_file}".format(**locals()))
        sh____("LANG=C stat {status_file} | grep Modify:".format(**locals()))
        #
        logg.info("== the next is-active shall then truncate it")
        old_size = os.path.getsize(status_file)
        is_activeXX = "{systemctl} is-active zzz.service other.service {vv} {vv}"
        act, end = output2(is_activeXX.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        new_size = os.path.getsize(status_file)
        logg.info("status-file size: old %s new %s", old_size, new_size)
        self.assertGreater(old_size, 0)
        self.assertEqual(new_size, 0)
        #
        logg.info("== 'stop' shall cleanup a service that was not inactive")
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        # and the status_file is also cleaned away
        self.assertFalse(os.path.exists(status_file))
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4065_simple_truncate_old_pid(self):
        """ check that we manage a service that has some old .pid
            file being around. That is a reboot has occurred and the
            information is not relevant to the current system state."""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service -vv"
        sh____(cmd.format(**locals()))
        is_active = "{systemctl} is-active zzz.service other.service {vv}"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = "{systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3) 
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        #
        logg.info("== 'restart' shall start a service that NOT is-active\n")        
        cmd = "{systemctl} restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 3)
        #
        time.sleep(2)
        logg.info("== mark the status file as being too old")
        status_file = os_path(root, "/var/run/zzz.service.status")
        self.assertTrue(os.path.exists(status_file))
        sh____("LANG=C stat {status_file} | grep Modify:".format(**locals()))
        sh____("LANG=C stat /proc/1/status | grep Modify:".format(**locals()))
        sh____("touch -r /proc/1/status {status_file}".format(**locals()))
        sh____("LANG=C stat {status_file} | grep Modify:".format(**locals()))
        #
        pid_file = os_path(root, "/var/run/zzz.service.pid")
        #+ self.assertTrue(os.path.exists(pid_file))
        #+ sh____("LANG=C stat {pid_file} | grep Modify:".format(**locals()))
        #+ sh____("LANG=C stat /proc/1/status | grep Modify:".format(**locals()))
        #+ sh____("touch -r /proc/1/status {pid_file}".format(**locals()))
        #+ sh____("LANG=C stat {pid_file} | grep Modify:".format(**locals()))
        #
        logg.info("== the next is-active shall then truncate it")
        old_status = os.path.getsize(status_file)
        #+ old_pid = os.path.getsize(pid_file)
        is_activeXX = "{systemctl} is-active zzz.service other.service {vv} {vv}"
        act, end = output2(is_activeXX.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        new_status = os.path.getsize(status_file)
        #+ new_pid = os.path.getsize(pid_file)
        logg.info("status-file size: old %s new %s", old_status, new_status)
        self.assertGreater(old_status, 0)
        self.assertEqual(new_status, 0)
        #+ logg.info("pid-file size: old %s new %s", old_pid, new_pid)
        #+ self.assertGreater(old_pid, 0)
        #+ self.assertEqual(new_pid, 0)
        #
        logg.info("== 'stop' shall cleanup a service that was not inactive")
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 3)
        logg.info("== and the status_file / pid_file is also cleaned away")
        self.assertFalse(os.path.exists(status_file))
        self.assertFalse(os.path.exists(pid_file))
        #
        self.rm_testdir()
        self.coverage()
    def real_4090_simple_service_RemainAfterExit(self):
        self.test_4090_simple_service_RemainAfterExit(True)
    def test_4090_simple_service_RemainAfterExit(self, real = None):
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc where
            RemainAfterExit=yes says the service is okay even
            when ExecStart has finished."""
        vv = "-vv"
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir, real)
        systemctl = _cov + _systemctl_py + " --root=" + root
        if real: vv, systemctl = "", "/usr/bin/systemctl"
        testsleep = self.testname("testsleep")
        testfail = self.testname("testfail.sh")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testsleep} 20
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zze.service"),"""
            [Unit]
            Description=Testing E
            [Service]
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testsleep} 3
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzf.service"),"""
            [Unit]
            Description=Testing F
            [Service]
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testfail} 3
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzr.service"),"""
            [Unit]
            Description=Testing R
            [Service]
            Type=simple
            RemainAfterExit=yes
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testsleep} 3
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzx.service"),"""
            [Unit]
            Description=Testing X
            [Service]
            Type=simple
            RemainAfterExit=yes
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testfail} 3
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "testfail.sh"),"""
            #! /bin/sh
            {bindir}/{testsleep} $1
            exit 2
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "testfail.sh"), os_path(bindir, testfail))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_file(os_path(testdir, "zze.service"), os_path(root, "/etc/systemd/system/zze.service"))
        copy_file(os_path(testdir, "zzf.service"), os_path(root, "/etc/systemd/system/zzf.service"))
        copy_file(os_path(testdir, "zzr.service"), os_path(root, "/etc/systemd/system/zzr.service"))
        copy_file(os_path(testdir, "zzx.service"), os_path(root, "/etc/systemd/system/zzx.service"))
        sh____("{systemctl} daemon-reload".format(**locals()))
        #
        cmd = "{systemctl} is-active zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "unknown")
        #
        cmd = "{systemctl} enable zzz.service {vv}"
        sh____(cmd.format(**locals()))
        cmd = "{systemctl} is-active zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a normal service ")
        cmd = "{systemctl} start zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(4)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a normal service")
        cmd = "{systemctl} stop zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        cmd = "{systemctl} enable zze.service {vv}"
        sh____(cmd.format(**locals()))
        #
        logg.info("== 'start' will run a later exiting service ")
        cmd = "{systemctl} start zze.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(4)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zze.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' shall clean an already exited service")
        cmd = "{systemctl} stop zze.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if not real: self.assertEqual(end, 1) # TODO real = 0
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zze.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        if not real: self.assertEqual(out.strip(), "inactive") # TODO real "failed"

        #
        cmd = "{systemctl} enable zzf.service {vv}"
        sh____(cmd.format(**locals()))
        #
        logg.info("== 'start' will run a later failing service ")
        cmd = "{systemctl} start zzf.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(4)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzf.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'reset-failed' shall clean an already failed service")
        cmd = "{systemctl} reset-failed zzf.service {vv} {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzf.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive") 
        #
        logg.info("== 'stop' shall clean an already failed service")
        cmd = "{systemctl} stop zzf.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if not real: self.assertEqual(end, 1) ## TODO real = 0
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzf.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        self.assertEqual(out.strip(), "inactive")
        #
        #
        cmd = "{systemctl} enable zzr.service {vv}"
        sh____(cmd.format(**locals()))
        #
        logg.info("== 'start' will have a later exiting service as remaining active")
        cmd = "{systemctl} start zzr.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(4)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzr.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active") # <<<<<<<<<<< here's the new functionality
        #
        logg.info("== 'stop' shall clean an exited but remaining service")
        cmd = "{systemctl} stop zzr.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if not real: self.assertEqual(end, 1) # TODO real 0
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzr.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        if not real: self.assertEqual(end, 3) # TODO real 0
        if not real: self.assertEqual(out.strip(), "inactive") # TODO real "failed"

        #
        cmd = "{systemctl} enable zzx.service {vv}"
        sh____(cmd.format(**locals()))
        #
        #
        logg.info("== 'start' will have a later failing service remaining but failed")
        cmd = "{systemctl} start zzx.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        time.sleep(4)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzx.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        ## if not real: self.assertEqual(end, 3)  # TODO real = 0
        ## if not real: self.assertEqual(out.strip(), "failed") # TODO real = "active"
        self.assertEqual(end, 0) 
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall clean an already failed remaining service")
        cmd = "{systemctl} stop zzx.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        if not real: self.assertEqual(end, 1) ## TODO real = 0
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzx.service {vv}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 3)
        if not real: self.assertEqual(out.strip(), "inactive") # TODO real "failed"
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.rm_zzfiles(root)
        self.coverage()
    def test_4101_systemctl_py_kill_basic_behaviour(self):
        """ check systemctl_py kill basic behaviour"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepB} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepC} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "killall {testsleepB}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "killall {testsleepC}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # already down
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # nothing to kill
        #
        time.sleep(1)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        self.rm_testdir()
        self.coverage()
    def test_4105_systemctl_py_kill_in_stop(self):
        """ check systemctl_py kill from ExecStop"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        bindir = os_path(root, "/usr/bin")
        rundir = os_path(root, "/var/run")
        begin="{"
        end="}"
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepB} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepC} 50
            ExecStop=/usr/bin/kill ${begin}MAINPID{end}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(rundir)
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} stop zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        # self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #TODO# self.assertTrue(greps(out, "zzb.service.pid"))
        #TODO# self.assertTrue(greps(out, "zzc.service.pid"))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #TODO# self.assertFalse(greps(out, "zzb.service.pid"))
        #TODO# self.assertTrue(greps(out, "zzc.service.pid"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #TODO# self.assertTrue(greps(out, "zzb.service.pid"))
        #TODO# self.assertTrue(greps(out, "zzc.service.pid"))
        #
        cmd = "killall {testsleepB}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "killall {testsleepC}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # already down
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # nothing to kill
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #TODO# self.assertFalse(greps(out, "zzb.service.pid")) # issue #13
        #TODO# self.assertTrue(greps(out, "zzc.service.pid")) # TODO ?
        #
        time.sleep(1)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        self.rm_testdir()
        self.coverage()
    def test_4120_systemctl_kill_ignore_behaviour(self):
        """ systemctl kill ignore behaviour"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("testsleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        testscriptB = self.testname("testscriptB.sh")
        testscriptC = self.testname("testscriptC.sh")
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(logfile, "")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testscriptB} 50
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill -3 $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            ExecReload=/usr/bin/kill -10 $MAINPID
            # KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscriptB),"""
            #! /bin/sh
            date +%T,enter > {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep}
              date +%T,stopped >> {logfile}
            {end}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {end}
            ignored () {begin}
              date +%T,ignored >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 10
            trap "ignored" 15
            date +%T,starting >> {logfile}
            {bindir}/{testsleepB} $1 >> {logfile} 2>&1 &
            while kill -0 $!; do 
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 15
            date +%T,leave >> {logfile}
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testscriptB))
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} kill zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testscriptB))
        self.assertFalse(greps(top, testsleepB)) # kills children as well
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertTrue(greps(log, "ignored"))
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        cmd = "killall {testsleepB}"
        sx____(cmd.format(**locals())) # cleanup before check
        self.assertFalse(greps(top, testsleepB))
        #
        self.rm_testdir()
        self.coverage()
    def test_4121_systemctl_kill_ignore_nokill_behaviour(self):
        """ systemctl kill ignore and nokill behaviour"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("testsleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        testscriptB = self.testname("testscriptB.sh")
        testscriptC = self.testname("testscriptC.sh")
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(logfile, "")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre=/bin/echo %n
            ExecStart={bindir}/{testscriptB} 50
            ExecStartPost=/bin/echo started $MAINPID
            ExecStop=/usr/bin/kill -3 $MAINPID
            ExecStopPost=/bin/echo stopped $MAINPID
            ExecStopPost=/usr/bin/sleep 2
            ExecReload=/usr/bin/kill -10 $MAINPID
            # KillSignal=SIGQUIT
            SendSIGKILL=no
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscriptB),"""
            #! /bin/sh
            date +%T,enter > {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep}
              date +%T,stopped >> {logfile}
            {end}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {end}
            ignored () {begin}
              date +%T,ignored >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 10
            trap "ignored" 15
            date +%T,starting >> {logfile}
            {bindir}/{testsleepB} $1 >> {logfile} 2>&1 &
            while kill -0 $!; do 
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 15
            date +%T,leave >> {logfile}
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testscriptB))
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} kill zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # actually killed
        #
        time.sleep(1) # kill is asynchronous
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testscriptB)) 
        self.assertFalse(greps(top, testsleepB)) # and it kills children
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertTrue(greps(log, "ignored"))
        #
        time.sleep(1) # kill is asynchronous
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        cmd = "killall {testsleepB}"
        sx____(cmd.format(**locals())) # cleanup before check
        self.assertFalse(greps(top, testscriptB))
        self.assertFalse(greps(top, testsleepB))
        #
        self.rm_testdir()
        self.coverage()

    def test_4201_systemctl_py_dependencies_plain_start_order(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps  = output(list_dependencies.format(**locals()))
        logg.info("deps \n%s", deps)
        #
        cmd = "{systemctl} start zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "start-A")
        self.assertEqual(log[1], "start-B")
        self.assertEqual(log[2], "start-C")
        os.remove(logfile)
        #
        cmd = "{systemctl} stop zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "stop-A")
        self.assertEqual(log[1], "stop-B")
        self.assertEqual(log[2], "stop-C")
        os.remove(logfile)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4211_systemctl_py_dependencies_basic_reorder(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            After=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            After=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps  = output(list_dependencies.format(**locals()))
        logg.info("deps \n%s", deps)
        #
        cmd = "{systemctl} start zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "start-B")
        self.assertEqual(log[1], "start-A")
        self.assertEqual(log[2], "start-C")
        os.remove(logfile)
        #
        cmd = "{systemctl} stop zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "stop-C")
        self.assertEqual(log[1], "stop-A")
        self.assertEqual(log[2], "stop-B")
        os.remove(logfile)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4301_systemctl_py_list_dependencies_with_after(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            After=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            After=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service\t(Requested)")
        self.assertEqual(len(deps), 1)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4302_systemctl_py_list_dependencies_with_wants(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Wants=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Wants=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Wants)")
        self.assertEqual(deps[1], "zza.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Requested)")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service\t(Wants)")
        self.assertEqual(deps[1], "zzc.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4303_systemctl_py_list_dependencies_with_requires(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Requires=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Requires)")
        self.assertEqual(deps[1], "zza.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Requested)")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service\t(Requires)")
        self.assertEqual(deps[1], "zzc.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4401_systemctl_py_list_dependencies_with_after(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            After=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            After=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service:")
        self.assertEqual(len(deps), 1)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4402_systemctl_py_list_dependencies_with_wants(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Wants=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Wants=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service:")
        self.assertEqual(deps[1], "| zzb.service: wanted to start")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service:")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzc.service:")
        self.assertEqual(deps[1], "| zza.service: wanted to start")
        self.assertEqual(deps[2], "| | zzb.service: wanted to start")
        self.assertEqual(len(deps), 3)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4403_systemctl_py_list_dependencies_with_requires(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Requires=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service:")
        self.assertEqual(deps[1], "| zzb.service: required to start")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service:")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzc.service:")
        self.assertEqual(deps[1], "| zza.service: required to start")
        self.assertEqual(deps[2], "| | zzb.service: required to start")
        self.assertEqual(len(deps), 3)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4900_unreadable_files_can_be_handled(self):
        """ a file may exist but it is unreadable"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=simple
            ExecStart=/usr/bin/sleep 10
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zza.service
            disable zzb.service""")
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        os.chmod(os_path(root, "/etc/systemd/system/zza.service"), 0222)
        #
        cmd = "{systemctl} start zza"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{systemctl} start zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} stop zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} try-restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload-or-restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload-or-try-restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} kill zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        #
        cmd = "{systemctl} is-active zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        self.assertTrue(greps(out, "unknown"))
        cmd = "{systemctl} is-failed zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, "unknown"))
        #
        cmd = "{systemctl} status zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertTrue(greps(out, "zza.service - NOT-FOUND"))
        #
        cmd = "{systemctl} show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # shows not-found state ok
        self.assertTrue(greps(out, "LoadState=not-loaded"))
        #
        cmd = "{systemctl} cat zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertTrue(greps(out, "Unit zza.service is not-loaded"))
        #
        cmd = "{systemctl} list-dependencies zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # always succeeds
        #
        cmd = "{systemctl} enable zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        cmd = "{systemctl} disable zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # ok
        #
        cmd = "{systemctl} preset zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        cmd = "{systemctl} preset-all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # always succeeds
        #
        self.rm_testdir()
        self.coverage()
    def test_4901_unsupported_run_type_for_service(self):
        """ a service file may exist but the run type is not supported"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=foo
            ExecStart=/usr/bin/sleep 10
            ExecStop=/usr/bin/kill $MAINPID
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        cmd = "{systemctl} start zza"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} start zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} stop zza.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.rm_testdir()
        self.coverage()

    def test_5001_systemctl_py_inside_container(self):
        """ check that we can run systemctl.py inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        python = _python
        systemctl_py = _systemctl_py
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.assertTrue(greps(out, "systemctl.py"))
        #
        self.rm_testdir()
    def test_5002_systemctl_py_enable_in_container(self):
        """ check that we can enable services in a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl list-unit-files"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.assertTrue(greps(out, "zza.service.*static"))
        self.assertTrue(greps(out, "zzb.service.*disabled"))
        self.assertTrue(greps(out, "zzc.service.*enabled"))
        #
        self.rm_testdir()
    def test_5003_systemctl_py_default_services_in_container(self):
        """ check that we can enable services in a docker container to have default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        list_units_systemctl = "docker exec {testname} systemctl --all default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.assertTrue(greps(out2, "zzb.service"))
        self.assertTrue(greps(out2, "zzc.service"))
        self.assertEqual(len(lines(out2)), 2)
        self.assertTrue(greps(out3, "zzb.service"))
        self.assertTrue(greps(out3, "zzc.service"))
        # self.assertGreater(len(lines(out2)), 2)
        #
        self.rm_testdir()
    def test_5030_systemctl_py_start_simple(self):
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            ExecStop=/usr/bin/killall testsleep
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5031_systemctl_py_start_extra_simple(self):
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5032_systemctl_py_start_forking(self):
        """ check that we can start forking services in a container w/ PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
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
               (testsleep 50 0<&- &>/dev/null &
                echo $! > /var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,args
            ;; stop)
               killall testsleep
            ;; esac 
            echo "done$1" >&2
            exit 0""")
        text_file(os_path(testdir, "zzz.service"),"""
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
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sx____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5033_systemctl_py_start_forking_without_pid_file(self):
        """ check that we can start forking services in a container without PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               (testsleep 50 0<&- &>/dev/null &) &
               wait %1
               ps -o pid,ppid,args >&2
            ;; stop)
               killall testsleep
               echo killed all testsleep >&2
               sleep 1
            ;; esac 
            echo "done$1" >&2
            exit 0""")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sx____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5035_systemctl_py_start_notify_by_timeout(self):
        """ check that we can start simple services in a container w/ notify timeout"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=notify
            ExecStart=/usr/bin/testsleep 50
            ExecStop=/usr/bin/killall testsleep
            TimeoutSec=4
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vvvv"
        sx____(cmd.format(**locals())) # returncode = 1
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5100_systemctl_py_run_default_services_in_container(self):
        """ check that we can enable services in a docker container to be run as default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "docker exec {testname} systemctl default -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5120_systemctl_py_run_default_services_from_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        images = IMAGES
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"--init\",\"default\",\"-vv\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5130_systemctl_py_run_default_services_from_simple_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        images = IMAGES
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD \"/usr/bin/systemctl\"'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5133_systemctl_py_run_default_services_from_single_service_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        images = IMAGES
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker stop {testname}x" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_6000_precheck_coverage_install(self):
        """ Allow to have a coverage tool be installed."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        if package == "zypper":
            cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
            sh____(cmd.format(**locals()))
            ## https://github.com/openSUSE/docker-containers/issues/64
            #cmd = "docker exec {testname} {package} rr oss-update"
            #sh____(cmd.format(**locals()))
            #cmd = "docker exec {testname} {package} ar -f http://download.opensuse.org/update/leap/42.3/oss/openSUSE:Leap:42.3:Update.repo"
            #sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} {package} install -y {python_coverage}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_6130_systemctl_py_run_default_services_from_simple_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD \"/usr/bin/systemctl\"'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            okay_coverage = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(okay_coverage.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6133_systemctl_py_run_default_services_from_single_service_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker stop {testname}x" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            okay_coverage = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(okay_coverage.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6180_systemctl_py_halt_to_exit_container(self):
        """ check that we can 'halt' in a docker container to stop the service
            and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python = _python
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if package == "zypper":
            cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
            sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python}"
            sh____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(2)
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 50"))
        #
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv status check now
        cmd = "docker inspect {testname}x"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = "docker exec {testname}x systemctl halt"
        sh____(cmd.format(**locals()))
        InitLoopSleep = 5
        waits = InitLoopSleep + 2
        logg.info("waits %ss for the zombie-reaper to have cleaned up", waits)
        time.sleep(waits)
        #
        cmd = "docker inspect {testname}x"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        logg.info("ExitCode = %s", state["ExitCode"])
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = "docker stop {testname}x" # <<< this is a no-op now
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            okay_coverage = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(okay_coverage.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6190_systemctl_py_stop_last_service_to_exit_container(self):
        """ check that we can 'stop <service>' in a docker container to stop the service
            being the last service and to exit the PID 1 as the last part of the service."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python = _python
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if package == "zypper":
            cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
            sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python}"
            sh____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(2)
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker inspect {testname}x"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        self.assertTrue(state["Running"])
        self.assertEqual(state["Status"], "running")
        #
        cmd = "docker exec {testname}x systemctl stop zzc.service" # <<<<<<<<<<<<<<<<<<<<<
        sh____(cmd.format(**locals()))
        InitLoopSleep = 5
        waits = InitLoopSleep + 2
        logg.info("waits %ss for the zombie-reaper to have cleaned up", waits)
        time.sleep(waits)
        #
        cmd = "docker inspect {testname}x"
        inspected = output(cmd.format(**locals()))
        state = json.loads(inspected)[0]["State"]
        logg.info("Status = %s", state["Status"])
        logg.info("ExitCode = %s", state["ExitCode"])
        self.assertFalse(state["Running"])
        self.assertEqual(state["Status"], "exited")
        #
        cmd = "docker stop {testname}x" # <<< this is a no-op now
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            okay_coverage = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(okay_coverage.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6200_systemctl_py_switch_users_is_possible(self):
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python = _python
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            User=user1
            Group=root
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            User=user1
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            Group=group2
            ExecStart=/usr/bin/testsleep 60
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 150"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        elif True:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
                cmd = "docker exec {testname} {package} install -y {python}"
                sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        if COVERAGE:
            cmd = "docker exec {testname} touch /.coverage"
            sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} chmod 777 /.coverage"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname} groupadd group2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} useradd user1 -g group2"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start zzb.service -v"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start zzc.service -v"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start zzd.service -v"
        sh____(cmd.format(**locals()))
        #
        # first of all, it starts commands like the service specs without user/group
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        # but really it has some user/group changed
        top_container = "docker exec {testname} ps -eo user,group,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "user1 .*root .*testsleep 40"))
        self.assertTrue(greps(top, "user1 .*group2 .*testsleep 50"))
        self.assertTrue(greps(top, "root .*group2 .*testsleep 60"))
        # and the pid file has changed as well
        cmd = "docker exec {testname} ls -l /var/run/zzb.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        #TODO# self.assertTrue(greps(out, "user1 .*root .*zzb.service.pid"))
        cmd = "docker exec {testname} ls -l /var/run/zzc.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        #TODO# self.assertTrue(greps(out, "user1 .*group2 .*zzc.service.pid"))
        cmd = "docker exec {testname} ls -l /var/run/zzd.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        #TODO# self.assertTrue(greps(out, "root .*group2 .*zzd.service.pid"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6201_systemctl_py_switch_users_is_possible_from_saved_container(self):
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python = _python
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            User=user1
            Group=root
            ExecStart=/usr/bin/testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            User=user1
            ExecStart=/usr/bin/testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            Group=group2
            ExecStart=/usr/bin/testsleep 60
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        elif True:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
                cmd = "docker exec {testname} {package} install -y {python}"
                sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname} groupadd group2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} useradd user1 -g group2"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(5)
        #
        # first of all, it starts commands like the service specs without user/group
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        self.assertTrue(greps(top, "testsleep 60"))
        # but really it has some user/group changed
        top_container2 = "docker exec {testname}x ps -eo user,group,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "user1 .*root .*testsleep 40"))
        self.assertTrue(greps(top, "user1 .*group2 .*testsleep 50"))
        self.assertTrue(greps(top, "root .*group2 .*testsleep 60"))
        # and the pid file has changed as well
        cmd = "docker exec {testname}x ls -l /var/run/zzb.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        #TODO# self.assertTrue(greps(out, "user1 .*root .*zzb.service.pid"))
        cmd = "docker exec {testname}x ls -l /var/run/zzc.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        #TODO# self.assertTrue(greps(out, "user1 .*group2 .*zzc.service.pid"))
        cmd = "docker exec {testname}x ls -l /var/run/zzd.service.pid"
        out = output(cmd.format(**locals()))
        logg.info("found %s", out.strip())
        #TODO# self.assertTrue(greps(out, "root .*group2 .*zzd.service.pid"))
        #
        cmd = "docker stop {testname}x" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        self.assertFalse(greps(top, "testsleep 60"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6210_switch_users_and_workingdir_coverage(self):
        """ check that we can put workingdir and setuid/setgid definitions in a service
            and code parts for that are actually executed (test case without fork before) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        systemctl_sh = os_path(testdir, "systemctl.sh")
        testsleep_sh = os_path(testdir, "testsleep.sh")
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        shell_file(testsleep_sh,"""
            #! /bin/sh
            logfile="/tmp/testsleep-$1.log"
            date > $logfile
            echo "pwd": `pwd` >> $logfile
            echo "user:" `id -un` >> $logfile
            echo "group:" `id -gn` >> $logfile
            testsleep $1
            """.format(**locals()))
        text_file(os_path(testdir, "zz4.service"),"""
            [Unit]
            Description=Testing 4
            [Service]
            Type=simple
            User=user1
            Group=root
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 4
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zz5.service"),"""
            [Unit]
            Description=Testing 5
            [Service]
            Type=simple
            User=user1
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 5
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zz6.service"),"""
            [Unit]
            Description=Testing 6
            [Service]
            Type=simple
            Group=group2
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 6
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testsleep_sh} {testname}:/usr/bin/testsleep.sh"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} chmod 755 /usr/bin/testsleep.sh"
        sh____(cmd.format(**locals()))
        if package == "zypper":
            cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
            sh____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        else:
            cmd = "docker exec {testname} bash -c 'ls -l /usr/bin/python || {package} install -y python'"
            sx____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        if COVERAGE:
            cmd = "docker exec {testname} touch /.coverage"
            sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} chmod 777 /.coverage"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname} groupadd group2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} useradd user1 -g group2"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zz4.service {testname}:/etc/systemd/system/zz4.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zz5.service {testname}:/etc/systemd/system/zz5.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zz6.service {testname}:/etc/systemd/system/zz6.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl __exec_start_unit zz4.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} cp .coverage .coverage.{testname}.4"
        sx____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl __exec_start_unit zz5.service -vv"
        sh____(cmd.format(**locals())) 
        cmd = "docker exec {testname} cp .coverage .coverage.{testname}.5"
        sx____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl __exec_start_unit zz6.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} cp .coverage .coverage.{testname}.6"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker cp {testname}:/tmp/testsleep-4.log {testdir}/"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/tmp/testsleep-5.log {testdir}/"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/tmp/testsleep-6.log {testdir}/"
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
        self.assertTrue(greps(log4, "user: user1"))
        self.assertTrue(greps(log5, "user: user1"))
        self.assertTrue(greps(log5, "group: group2"))
        self.assertTrue(greps(log6, "group: group2"))
        self.assertTrue(greps(log6, "user: root"))
        #
        if COVERAGE:
            cmd = "docker cp {testname}:/.coverage.{testname}.4 ."
            sh____(cmd.format(**locals()))
            cmd = "docker cp {testname}:/.coverage.{testname}.5 ."
            sh____(cmd.format(**locals()))
            cmd = "docker cp {testname}:/.coverage.{testname}.6 ."
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}.4"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}.5"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}.6"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6600_systemctl_py_can_reap_zombies_in_a_container(self):
        """ check that we can reap zombies in a container managed by systemctl.py"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        package = "yum"
        python_coverage = _python_coverage
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
            if greps(open("/etc/issue"), "openSUSE"):
                image = self.local_image(OPENSUSE)
                package = "zypper"
        systemctl_py = realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        user = self.user()
        testsleep = self.testname("sleep")
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               (/usr/bin/{testsleep} 50 0<&- &>/dev/null &) &
               wait %1
               # ps -o pid,ppid,args >&2
            ;; stop)
               killall {testsleep}
               echo killed all {testsleep} >&2
               sleep 1
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
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
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/{testsleep}"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        cmd = "docker exec {testname}x ps -eo state,pid,ppid,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        # testsleep is running with parent-pid of '1'
        self.assertTrue(greps(top, " 1 /usr/bin/.*sleep 50"))
        # and the pid '1' is systemctl (actually systemctl.py)
        self.assertTrue(greps(top, " 1 .* 0 .*systemctl"))
        # and let's check no zombies around so far:
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< no zombie yet
        #
        # check the subprocess
        m = re.search(r"(?m)^(\S+)\s+(\d+)\s+(\d+)\s+(\S+.*sleep 50.*)$", top)
        if m:
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
        cmd = "docker exec {testname}x kill {pid}"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname}x ps -eo state,pid,ppid,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "Z .*sleep.*<defunct>")) # <<< we have zombie!
        time.sleep(4)
        #
        cmd = "docker exec {testname}x ps -eo state,pid,ppid,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< and it's gone!
        time.sleep(1)
        #
        cmd = "docker stop {testname}x"
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_7001_centos_httpd(self):
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
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testport=self.testport()
        name="centos-httpd"
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        # WHEN
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {testport}:80 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        cmd = "sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{testport}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_7002_centos_postgres(self):
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
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testport=self.testport()
        name="centos-postgres"
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        psql = PSQL_TOOL
        PG = "/var/lib/pgsql/data"
        # WHEN
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y postgresql-server postgresql-utils"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} postgresql-setup initdb"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c \"sed -i -e 's/.*listen_addresses.*/listen_addresses = '\\\"'*'\\\"'/' {PG}/postgresql.conf\""
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'sed -i -e \"s/.*host.*ident/# &/\" {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'echo \"host all all 0.0.0.0/0 md5\" >> {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'sleep 5; ps -ax'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c \"echo 'CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.11'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c \"echo 'CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.OK'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable postgresql"
        sh____(cmd.format(**locals()))
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {testport}:5432 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sleep 5"
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
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_7011_centos_httpd_socket_notify(self):
        """ WHEN using an image for a systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            and in the systemctl.debug.log we can see NOTIFY_SOCKET
            messages with Apache sending a READY and MAINPID value."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        ## commit_container = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"-vv\"]'  {testname} {images}:{testname}"
        ## sh____(commit_container.format(**locals()))
        ## stop_container = "docker rm --force {testname}"
        ## sx____(stop_container.format(**locals()))
        ## start_container = "docker run --detach --name {testname} {images}:{testname} sleep 200"
        ## sh____(start_container.format(**locals()))
        ## time.sleep(3)
        #
        container = self.ip_container(testname)
        cmd = "docker exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl status httpd"
        sx____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        # CHECK
        self.assertEqual(len(greps(open(testdir+"/systemctl.debug.log"), " ERROR ")), 0)
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "use NOTIFY_SOCKET="))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "read_notify.*READY=1.*MAINPID="))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "notify start done"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "stop '/bin/kill' '-WINCH'"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "wait [$]NOTIFY_SOCKET"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "wait for PID .* is done"))
        self.rm_testdir()
    def test_7020_ubuntu_apache2_with_saved_container(self):
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
        testname = self.testname()
        port=self.testport()
        images = IMAGES
        image = "ubuntu:16.04"
        python_base = os.path.basename(_python)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, port, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} apt-get update"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} apt-get install -y apache2 {python_base}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable apache2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        # .........................................
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {port}:80 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        cmd = "sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{port}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_7502_centos_postgres_user_mode_container(self):
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
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testport=self.testport()
        name="centos-postgres"
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        psql = PSQL_TOOL
        PG = "/var/lib/pgsql/data"
        # WHEN
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y postgresql-server postgresql-utils"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} postgresql-setup initdb"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c \"sed -i -e 's/.*listen_addresses.*/listen_addresses = '\\\"'*'\\\"'/' {PG}/postgresql.conf\""
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'sed -i -e \"s/.*host.*ident/# &/\" {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'echo \"host all all 0.0.0.0/0 md5\" >> {PG}/pg_hba.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c 'sleep 5; ps -ax'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c \"echo 'CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.11'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sh -c \"echo 'CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD '\\\"'Testuser.OK'\\\" | runuser -u postgres /usr/bin/psql\""
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop postgresql -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable postgresql"
        sh____(cmd.format(**locals()))
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {testport}:5432 --name {testname} -u postgres {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sleep 5"
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
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        # sx____(cmd.format(**locals()))
        self.rm_testdir()
    # @unittest.expectedFailure
    def test_8001_issue_1_start_mariadb_centos_7_0(self):
        """ issue 1: mariadb on centos 7.0 does not start"""
        # this was based on the expectation that "yum install mariadb" would allow
        # for a "systemctl start mysql" which in fact it doesn't. Double-checking
        # with "yum install mariadb-server" and "systemctl start mariadb" shows
        # that mariadb's unit file is buggy, because it does not specify a kill
        # signal that it's mysqld_safe controller does not ignore.
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        # image= "centos:centos7.0.1406" # <<<< can not yum-install mariadb-server ?
        # image= "centos:centos7.1.1503"
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        # mariadb has a TimeoutSec=300 in the unit config:
        cmd = "docker run --detach --name={testname} {image} sleep 400"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y mariadb"
        sh____(cmd.format(**locals()))
        if False:
            # expected in bug report but that one can not work:
            cmd = "docker exec {testname} systemctl enable mysql"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertFalse(greps(out,"mysqld"))
        #
        cmd = "docker exec {testname} yum install -y mariadb-server"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out,"mariadb.service"))
        #
        cmd = "docker exec {testname} systemctl start mariadb -vv"
        sh____(cmd.format(**locals()))
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "mysqld "))
        had_mysqld_safe = greps(top, "mysqld_safe ")
        #
        # NOTE: mariadb-5.5.52's mysqld_safe controller does ignore systemctl kill
        # but after a TimeoutSec=300 the 'systemctl kill' will send a SIGKILL to it
        # which leaves the mysqld to be still running -> this is an upstream error.
        cmd = "docker exec {testname} systemctl stop mariadb -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        # self.assertFalse(greps(top, "mysqld "))
        if greps(top, "mysqld ") and had_mysqld_safe:
            logg.critical("mysqld still running => this is an uptream error!")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8002_issue_2_start_rsyslog_centos7(self):
        """ issue 2: rsyslog on centos 7 does not start"""
        # this was based on a ";Requires=xy" line in the unit file
        # but our unit parser did not regard ";" as starting a comment
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y rsyslog"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out,"rsyslog.service.*enabled"))
        #
        cmd = "docker exec {testname} systemctl start rsyslog -vv"
        sh____(cmd.format(**locals()))
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "/usr/sbin/rsyslog"))
        #
        cmd = "docker exec {testname} systemctl stop rsyslog -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "/usr/sbin/rsyslog"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8011_centos_httpd_socket_notify(self):
        """ start/restart behaviour if a httpd has failed - issue #11 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 600"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        cmd = "docker exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl status httpd"
        #
        # CRASH
        cmd = "docker exec {testname} bash -c 'cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.orig'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo foo > /etc/httpd/conf/httpd.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # start failed
        cmd = "docker exec {testname} systemctl status httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "docker exec {testname} systemctl restart httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # restart failed
        #
        cmd = "docker exec {testname} bash -c 'cat /etc/httpd/conf/httpd.conf.orig > /etc/httpd/conf/httpd.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl restart httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        cmd = "docker exec {testname} systemctl stop httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = "docker exec {testname} systemctl status httpd"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        #
        self.rm_testdir()
    def test_8031_centos_nginx_restart(self):
        """ start/restart behaviour if a nginx has failed - issue #31 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 600"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y epel-release"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y nginx"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable nginx"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} rpm -q --list nginx"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /usr/share/nginx/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        cmd = "docker exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start nginx"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status nginx"
        sh____(cmd.format(**locals()))
        #
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "nginx"))
        #
        cmd = "docker exec {testname} systemctl restart nginx"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "nginx"))
        #
        cmd = "docker exec {testname} systemctl status nginx"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop nginx"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = "docker exec {testname} systemctl status nginx"
        sx____(cmd.format(**locals()))
        top = output(_top_recent)
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "nginx"))
        #
        cmd = "docker cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        #
        self.rm_testdir()

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
       epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v","--verbose", action="count", default=0,
       help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
       help="systemctl.py file to be tested (%default)")
    _o.add_option("-p","--python", metavar="EXE", default=_python,
       help="use another python execution engine [%default]")
    _o.add_option("-a","--coverage", action="count", default=0,
       help="gather coverage.py data (use -aa for new set) [%default]")
    _o.add_option("-l","--logfile", metavar="FILE", default="",
       help="additionally save the output log to a file [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
       help="capture results as a junit xml file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    _python_version = output(_python + " --version 2>&1")
    if "Python 3" in _python_version:
        _cov_run = _cov3run
        _cov_cmd = _cov3cmd
        _python_coverage = _python3coverage
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
           os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
           os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    #
    if opt.coverage:
        COVERAGE = True
        _cov = _cov_run
        if opt.coverage > 1:
            if os.path.exists(".coverage"):
                logg.info("rm .coverage")
                os.remove(".coverage")
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = [ "test_*" ]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if arg.startswith("_"): arg = arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    if not logfile:
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
            Runner(xmlresults).run(suite)
        else:
            Runner = unittest.TextTestRunner
            Runner(verbosity=opt.verbose).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
        Runner(logfile.stream, verbosity=opt.verbose).run(suite)
    if opt.coverage:
        print(" " + _cov_cmd + " combine")
        print(" " + _cov_cmd + " report " + _systemctl_py)
        print(" " + _cov_cmd + " annotate " + _systemctl_py)
