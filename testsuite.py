#! /usr/bin/env python

""" Testcases for docker-systemctl-replacement functionality """

__copyright__ = "(C) Guido Draheim, for free use (CC-BY,GPL) """
__version__ = "0.8.1401"

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
import logging
import re
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json

logg = logging.getLogger("TESTING")
_systemctl_py = "files/docker/systemctl.py"
_cov = ""
_coverage = "coverage2 run -a "
_cov_cmd = "coverage2"

IMAGES = "localhost:5000/testingsystemctl"
CENTOS = "centos:7.3.1611"
UBUNTU = "ubuntu:14.04"
OPENSUSE = "opensuse:42.2"

def sh____(cmd, shell=True):
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd, shell=True):
    return subprocess.call(cmd, shell=shell)
def output(cmd, shell=True):
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out
def output2(cmd, shell=True):
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out, run.returncode
def _lines(lines):
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def lines(text):
    return list(_lines(text))
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
        newdir = "tests/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tests/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    def root(self, testdir):
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def user(self):
        import getpass
        getpass.getuser()
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
        ver = ver or "7.3.1611"
        find_repo_image = "docker images {rmi}/{rep}:{ver}"
        images = output(find_repo_image.format(**locals()))
        running = output("docker ps")
        if greps(images, rep) and not greps(running, rep+ver):
            stop_repo = "docker rm --force {rep}{ver}"
            sx____(stop_repo.format(**locals()))
            start_repo = "docker run --detach --name {rep}{ver} {rmi}/{rep}:{ver}"
            logg.info("!! %s", start_repo.format(**locals()))
            sh____(start_repo.format(**locals()))
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
        ver = ver or "42.2"
        find_repo_image = "docker images {rmi}/{rep}:{ver}"
        images = output(find_repo_image.format(**locals()))
        running = output("docker ps")
        if greps(images, rep) and not greps(running, rep+ver):
            stop_repo = "docker rm --force {rep}{ver}"
            sx____(stop_repo.format(**locals()))
            start_repo = "docker run --detach --name {rep}{ver} {rmi}/{rep}:{ver}"
            logg.info("!! %s", start_repo.format(**locals()))
            sh____(start_repo.format(**locals()))
        running = output("docker ps")
        if greps(running, rep+ver):
            ip_a = self.ip_container(rep+ver)
            logg.info("%s%s => %s", rep, ver, ip_a)
            result = "download.opensuse.org:%s" % ip_a
            logg.info("--add-host %s", result)
            return result
        return ""
    def local_image(self, image):
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
        stop = "docker rm --force {name}"
        sx____(stop.format(**locals()))
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
        start = "docker run --detach --name {name} {local_image} sleep 1000"
        sh____(start.format(**locals()))
        print "                 # " + local_image
        print "  docker exec -it "+name+" bash"
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_1000(self):
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
    def test_1002_systemctl_version(self):
        systemctl = _cov + _systemctl_py 
        cmd = "{systemctl} --version"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, "systemd 0"))
        self.assertTrue(greps(out, "[(]systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_1003_systemctl_help(self):
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} --help"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, "--root=PATH"))
        self.assertTrue(greps(out, "--verbose"))
        self.assertTrue(greps(out, "--init"))
        self.assertTrue(greps(out, "for more information"))
        self.assertFalse(greps(out, "reload-or-try-restart"))
        cmd = "{systemctl} help" 
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertFalse(greps(out, "--verbose"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
    def test_1004_systemctl_daemon_reload(self):
        """ daemon-reload always succeeds (does nothing) """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
    def test_1005_systemctl_daemon_reload_root_ignored(self):
        """ daemon-reload always succeeds (does nothing) """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            ExecStart=/usr/bin/sleep 3
        """)
        cmd = "{systemctl} daemon-reload"
        out,end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        self.rm_testdir()
    def test_1010_systemctl_force_ipv4(self):
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
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertFalse(greps(hosts, "::1.*localhost "))
        self.rm_testdir()
    def test_1011_systemctl_force_ipv6(self):
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
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertFalse(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        self.rm_testdir()
    def test_1020_systemctl_with_systemctl_log(self):
        """ when /var/log/systemctl.log exists then print INFO messages into it"""
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/systemctl.log")
        text_file(logfile,"")
        #
        cmd = "{systemctl} daemon-reload"
        sh____(cmd.format(**locals()))
        self.assertEqual(len(greps(open(logfile), " INFO ")), 2)
        self.assertEqual(len(greps(open(logfile), " DEBUG ")), 0)
        self.rm_testdir()
    def test_1021_systemctl_with_systemctl_debug_log(self):
        """ when /var/log/systemctl.debug.log exists then print DEBUG messages into it"""
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/systemctl.debug.log")
        text_file(logfile,"")
        #
        cmd = "{systemctl} daemon-reload"
        sh____(cmd.format(**locals()))
        self.assertEqual(len(greps(open(logfile), " INFO ")), 2)
        self.assertEqual(len(greps(open(logfile), " DEBUG ")), 3)
        self.rm_testdir()
    def test_2001_can_create_test_services(self):
        """ check that two unit files can be created for testing """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        textB = file(os_path(root, "/etc/systemd/system/b.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textA)
        self.assertIn("\nDescription", textB)
        self.rm_testdir()
    def test_2002_list_units(self):
        """ check that two unit files can be found for 'list-units' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} list-units"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"b.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertIn("loaded units listed.", out)
        self.assertIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend list-units"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"b.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertNotIn("loaded units listed.", out)
        self.assertNotIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
    def test_2003_list_unit_files(self):
        """ check that two unit service files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
    def test_2004_list_unit_files_wanted(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
    def test_2013_list_unit_files_common_targets(self):
        """ check that some unit target files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertFalse(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        cmd = "{systemctl} --no-legend --type=target list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertFalse(greps(out, r"a.service\s+static"))
        self.assertFalse(greps(out, r"b.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertGreater(len(lines(out)), 10)
        num_targets = len(lines(out))
        cmd = "{systemctl} --no-legend list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), num_targets + 2)
        self.rm_testdir()
    def test_2014_list_unit_files_now(self):
        """ check that 'list-unit-files --now' presents a special debug list """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --no-legend --now list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+SysD\s+.*systemd/system/a.service"))
        self.assertTrue(greps(out, r"b.service\s+SysD\s+.*systemd/system/b.service"))
        self.assertFalse(greps(out, r"multi-user.target"))
        self.assertFalse(greps(out, r"enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
    def test_2020_show_unit_is_parseable(self):
        """ check that 'show UNIT' is machine-readable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "{systemctl} show a.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
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
        cmd = "{systemctl} --all show a.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
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
    def test_2021_show_unit_can_be_restricted_to_one_property(self):
        """ check that 'show UNIT' may return just one value if asked for"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "{systemctl} show a.service --property=Description"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show a.service --property=Description --all"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show a.service --property=PIDFile"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show a.service --property=PIDFile --all"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        self.assertEqual(lines(out), [ "PIDFile=" ])
        self.rm_testdir()
    def test_2025_show_unit_for_multiple_matches(self):
        """ check that the result of 'show UNIT' for multiple services is 
            concatenated but still machine readable. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} show a.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
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
        cmd = "{systemctl} show b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
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
        cmd = "{systemctl} show a.service b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
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
    def test_3002_enable_service_creates_a_symlink(self):
        """ check that a service can be enabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} enable b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        self.rm_testdir()
    def test_3003_disable_service_removes_the_symlink(self):
        """ check that a service can be enabled and disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} enable b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        cmd = "{systemctl} disable b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        self.rm_testdir()
    def test_3004_list_unit_files_when_enabled(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} --no-legend disable b.service"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out = output(cmd.format(**locals()))
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        self.rm_testdir()
    def test_3005_is_enabled_result_when_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend disable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
    def test_3006_is_enabled_is_true_when_any_is_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled b.service c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled a.service b.service c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 3)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled c.service a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        self.rm_testdir()
    def test_3010_check_list_of_preset_files(self):
        """ check that 'is-enabled' reports correctly for presets """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} __load_preset_files"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^our.preset"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} __get_preset_of_unit a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        # self.assertTrue(greps(out, r"^our.preset"))
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} __get_preset_of_unit b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^enable"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} __get_preset_of_unit c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disable"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset-all" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
    def test_3020_default_services(self):
        """ check the 'default-services' to know the enabled services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        self.assertFalse(greps(out, "a.service"))
        self.assertTrue(greps(out, "b.service"))
        self.assertTrue(greps(out, "c.service"))
        #
        self.rm_testdir()
    def test_3021_default_services(self):
        """ check that 'default-services' skips some known services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/mount-disks.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/network.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable mount-disks.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable network.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services --all"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 3)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services --all --force"
        out, end = output2(cmd.format(**locals()))
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(len(lines(out)), 4)
        self.assertEqual(end, 0)
        #
        self.rm_testdir()
    def test_3030_systemctl_py_start_simple(self):
        """ check that we can start simple services with root env"""
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
        enable_service = "{systemctl} enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "{systemctl} --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "{systemctl} default-services -vv"
        sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
    def test_3031_systemctl_py_start_extra_simple(self):
        """ check that we can start extra simple services with root env"""
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
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        enable_service = "{systemctl} enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "{systemctl} --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "{systemctl} default-services -vv"
        sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
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
            ExceStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        enable_service = "{systemctl} enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "{systemctl} --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "{systemctl} default-services -vv"
        sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
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
        enable_service = "{systemctl} enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "{systemctl} --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "{systemctl} default-services -vv"
        sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
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
        enable_service = "{systemctl} enable zzb.service"
        sh____(enable_service.format(**locals()))
        enable_service = "{systemctl} enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "{systemctl} --version"
        sh____(version_systemctl.format(**locals()))
        list_services = "{systemctl} default-services -vv"
        out = output(list_services.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzb.service"))
        self.assertEqual(len(lines(out)), 2)
        #
        start_services = "{systemctl} default -vv"
        sh____(start_services.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        self.assertTrue(greps(top, testsleep+" 50"))
        #
        stop_services = "{systemctl} halt -vv"
        sh____(stop_services.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)        
        self.assertFalse(greps(top, testsleep))
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()

    def test_3050_systemctl_py_check_is_active_in_testenv(self):
        """ check is_active behaviour in local testenv env"""
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
        is_active_A = "{systemctl} is-active zza.service"
        is_active_B = "{systemctl} is-active zzb.service"
        is_active_C = "{systemctl} is-active zzc.service"
        is_active_D = "{systemctl} is-active zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "inactive")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertNotEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertNotEqual(exitD, 0)
        #
        start_service_B = "{systemctl} start zzb.service -vv"
        sh____(start_service_B.format(**locals()))
        #
        is_active_A = "{systemctl} is-active zza.service"
        is_active_B = "{systemctl} is-active zzb.service"
        is_active_C = "{systemctl} is-active zzc.service"
        is_active_D = "{systemctl} is-active zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
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
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        start_service_C = "{systemctl} start zzc.service -vv"
        sh____(start_service_C.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertEqual(exitBC, 0)         ## all is-active => return 0
        #
        start_service_C = "{systemctl} stop zzb.service zzc.service -vv"
        sh____(start_service_C.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["inactive", "inactive", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
    def test_3051_systemctl_py_check_is_failed_in_testenv(self):
        """ check is_failed behaviour in local testenv env"""
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
        is_active_A = "{systemctl} is-failed zza.service"
        is_active_B = "{systemctl} is-failed zzb.service"
        is_active_C = "{systemctl} is-failed zzc.service"
        is_active_D = "{systemctl} is-failed zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "inactive")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertNotEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertNotEqual(exitD, 0)
        #
        start_service_B = "{systemctl} start zzb.service -vv"
        sh____(start_service_B.format(**locals()))
        #
        is_active_A = "{systemctl} is-failed zza.service"
        is_active_B = "{systemctl} is-failed zzb.service"
        is_active_C = "{systemctl} is-failed zzc.service"
        is_active_D = "{systemctl} is-failed zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "active")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertNotEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertNotEqual(exitD, 0)
        #
        logg.info("== checking combinations of arguments")
        is_active_BC = "{systemctl} is-failed zzb.service zzc.service "
        is_active_CD = "{systemctl} is-failed zzc.service zzd.service"
        is_active_BD = "{systemctl} is-failed zzb.service zzd.service"
        is_active_BCD = "{systemctl} is-failed zzb.service zzc.service zzd.service"
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
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        start_service_C = "{systemctl} start zzc.service -vv"
        sh____(start_service_C.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["failed", "failed", ""])
        self.assertEqual(exitBC, 0)         ## all is-failed => return 0
        #
        start_service_C = "{systemctl} stop zzb.service zzc.service -vv"
        sh____(start_service_C.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["inactive", "inactive", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
    def test_4030_simple_service_functions(self):
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        self.skipTest("not implemented correctly")
        # the shellscript is blocking on its testsleep child
        # in such a way that it does not compute the signals.
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
            ExecStart={bindir}/{testscript} 50
            ExecStop=killall -3 {testscript}
            ExecStop=sleep 4
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscript),"""
            #! /bin/sh
            date > {logfile}
            echo "begin" >> {logfile}
            stops () {begin}
              date >> {logfile}
              echo "stopping" >> {logfile}
              killall {testsleep}
              exit 0
            {end}
            reload () {begin}
              date >> {logfile}
              echo "reloads" >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 5
            date >> {logfile}
            echo "start" >> {logfile}
            {bindir}/{testsleep} $1 >> {logfile} 2>&1
            date >> {logfile}
            echo "ended" >> {logfile}
            trap - 1 5
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        enable_service = "{systemctl} enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "{systemctl} --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "{systemctl} default-services -vv"
        sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
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
        is_active = "{systemctl} is-active zzz.service -vv"
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        restart_service = "{systemctl} restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        restart_service = "{systemctl} restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        restart_service = "{systemctl} reload zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        restart_service = "{systemctl} reload-or-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        restart_service = "{systemctl} kill zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        restart_service = "{systemctl} stop zzz.service -vv"
        sh____(restart_service.format(**locals()))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        restart_service = "{systemctl} reload-or-try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        restart_service = "{systemctl} reload-or-try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        restart_service = "{systemctl} reload-or-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        restart_service = "{systemctl} reload-or-try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        restart_service = "{systemctl} try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        is_active = "{systemctl} is-active zzz.service -vv"
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        start_service = "{systemctl} start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        stop_service = "{systemctl} stop zzz.service -vv"
        sh____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        restart_service = "{systemctl} restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        restart_service = "{systemctl} restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        restart_service = "{systemctl} reload zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
        restart_service = "{systemctl} reload-or-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        restart_service = "{systemctl} stop zzz.service -vv"
        sh____(restart_service.format(**locals()))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        restart_service = "{systemctl} reload-or-try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        restart_service = "{systemctl} reload-or-try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        restart_service = "{systemctl} reload-or-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        restart_service = "{systemctl} reload-or-try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        top6 = top
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        restart_service = "{systemctl} try-restart zzz.service -vv"
        sh____(restart_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        act = output(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
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
    def test_5001_systemctl_py_inside_container(self):
        """ check that we can run systemctl.py inside a docker container """
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        out = output(version_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        sx____(stop_container.format(**locals()))
        self.assertTrue(greps(out, "systemctl.py"))
        #
        self.rm_testdir()
    def test_5002_systemctl_py_enable_in_container(self):
        """ check that we can enable services in a docker container """
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
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_service = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl list-unit-files"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        sx____(stop_container.format(**locals()))
        self.assertTrue(greps(out, "zza.service.*static"))
        self.assertTrue(greps(out, "zzb.service.*disabled"))
        self.assertTrue(greps(out, "zzc.service.*enabled"))
        #
        self.rm_testdir()
    def test_5003_systemctl_py_default_services_in_container(self):
        """ check that we can enable services in a docker container to have default-services"""
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
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_service = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzb.service"
        sh____(enable_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        list_units_systemctl = "docker exec {testname} systemctl --all default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        sx____(stop_container.format(**locals()))
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
            ExecStart=testsleep 50
            ExecStop=killall testsleep
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_systemctl = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_systemctl.format(**locals()))
        install_killall = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(install_killall.format(**locals()))
        install_service = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "docker exec {testname} systemctl start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        start_service = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_5031_systemctl_py_start_extra_simple(self):
        """ check that we can start simple services in a container"""
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_systemctl = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_systemctl.format(**locals()))
        install_service = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "docker exec {testname} systemctl start zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        start_service = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_5032_systemctl_py_start_forking(self):
        """ check that we can start forking services in a container w/ PIDFile"""
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
            ExceStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_systemctl = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_systemctl.format(**locals()))
        install_killall = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(install_killall.format(**locals()))
        install_service = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(install_service.format(**locals()))
        install_initscript = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(install_initscript.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "docker exec {testname} systemctl start zzz.service -vv"
        sx____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        start_service = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_5033_systemctl_py_start_forking_without_pid_file(self):
        """ check that we can start forking services in a container without PIDFile"""
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
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_testsleep = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_testsleep.format(**locals()))
        install_killall = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(install_killall.format(**locals()))
        install_service = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(install_service.format(**locals()))
        install_initscript = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(install_initscript.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "docker exec {testname} systemctl start zzz.service -vv"
        sx____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        start_service = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_5035_systemctl_py_start_notify_by_timeout(self):
        """ check that we can start simple services in a container w/ notify timeout"""
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
            ExecStart=testsleep 50
            ExceStop=killall testsleep
            TimeoutSec=4
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_systemctl = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_systemctl.format(**locals()))
        install_killall = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(install_killall.format(**locals()))
        install_service = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzz.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        start_service = "docker exec {testname} systemctl start zzz.service -vvvv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        start_service = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_5041_systemctl_py_run_default_services_in_container(self):
        """ check that we can enable services in a docker container to be run as default-services"""
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
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_testsleep = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_testsleep.format(**locals()))
        install_service = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzb.service"
        sh____(enable_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        list_units_systemctl = "docker exec {testname} systemctl default -vvvv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        list_units_systemctl = "docker exec {testname} systemctl halt -vvvv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_5042_systemctl_py_run_default_services_from_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
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
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_testsleep = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_testsleep.format(**locals()))
        install_service = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzb.service"
        sh____(enable_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -v"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        commit_container = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"--init\",\"default\",\"-vv\"]'  {testname} {images}:{testname}"
        sh____(commit_container.format(**locals()))
        stop_container2 = "docker rm --force {testname}x"
        sx____(stop_container2.format(**locals()))
        start_container2 = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(start_container2.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        list_units_systemctl = "docker exec {testname} systemctl halt -vvvv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        sx____(stop_container.format(**locals()))
        sx____(stop_container2.format(**locals()))
        drop_image_container = "docker rmi {images}:{testname}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_5043_systemctl_py_run_default_services_from_simple_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
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
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_testsleep = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_testsleep.format(**locals()))
        install_service = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzb.service"
        sh____(enable_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -v"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        commit_container = "docker commit -c 'CMD \"/usr/bin/systemctl\"'  {testname} {images}:{testname}"
        sh____(commit_container.format(**locals()))
        stop_container2 = "docker rm --force {testname}x"
        sx____(stop_container2.format(**locals()))
        start_container2 = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(start_container2.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        list_units_systemctl = "docker exec {testname} systemctl halt -vvvv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        sx____(stop_container.format(**locals()))
        sx____(stop_container2.format(**locals()))
        drop_image_container = "docker rmi {images}:{testname}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_5044_systemctl_py_run_default_services_from_single_service_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
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
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_testsleep = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(install_testsleep.format(**locals()))
        install_service = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(install_service.format(**locals()))
        install_service = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(install_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzb.service"
        sh____(enable_service.format(**locals()))
        enable_service = "docker exec {testname} systemctl enable zzc.service"
        sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -v"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        commit_container = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(commit_container.format(**locals()))
        stop_container2 = "docker rm --force {testname}x"
        sx____(stop_container2.format(**locals()))
        start_container2 = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(start_container2.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 50"))
        #
        list_units_systemctl = "docker stop {testname}x" # <<<
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        sx____(stop_container.format(**locals()))
        sx____(stop_container2.format(**locals()))
        drop_image_container = "docker rmi {images}:{testname}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_6001_centos_httpd_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        testname="test_6001"
        port=6001
        name="centos-httpd"
        dockerfile="centos-httpd.dockerfile"
        images = IMAGES
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} {images}:{name}"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        read_index_html = "sleep 5; wget -O {tmp}/{name}.txt http://127.0.0.1:{port}"
        grep_index_html = "grep OK {tmp}/{name}.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # CLEAN
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        drop_image_container = "docker rmi {images}:{name}"
        ## sx____(drop_image_container.format(**locals())) # TODO: still needed for test_6011
        self.rm_testdir()
    def test_6002_centos_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        testname="test_6002"
        port=6002
        name="centos-postgres"
        dockerfile="centos-postgres.dockerfile"
        images = IMAGES
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:5432 --name {name} {images}:{name}"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        read_index_html = "sleep 5; {login}; psql -p {port} -h 127.0.0.1 -d postgres -c '{query}' > {tmp}/{name}.txt"
        grep_index_html = "grep testuser_ok {tmp}/{name}.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # CLEAN
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        drop_image_container = "docker rmi {images}:{name}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_6003_centos_lamp_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an full LAMP stack 
                 as systemd services being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the services have started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see the start page of PHP MyAdmin
            because the test script has enabled access to 
            that web page on our test port. """
        self.skipTest("=> replaced by test_6013")
        testname="test_6003"
        port=6003
        name="centos-lamp"
        dockerfile="centos-lamp.dockerfile"
        images = IMAGES
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} {images}:{name}"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        read_php_admin_html = "sleep 5; wget -O {tmp}/{name}.txt http://127.0.0.1:{port}/phpMyAdmin"
        grep_php_admin_html = "grep '<h1>.*>phpMyAdmin<' {tmp}/{name}.txt"
        sh____(read_php_admin_html.format(**locals()))
        sh____(grep_php_admin_html.format(**locals()))
        # CLEAN
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        drop_image_container = "docker rmi {images}:{name}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_6004_opensuse_lamp_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled OpenSUSE, 
            THEN we can create an image with an full LAMP stack 
                 as systemd services being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the services have started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see the start page of PHP MyAdmin
            because the test script has enabled access to 
            that web page on our test port. """
        self.skipTest("=> replaced by test_6014")
        testname="test_6004"
        port=6004
        name="opensuse-lamp"
        dockerfile="opensuse-lamp.dockerfile"
        images = IMAGES
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} {images}:{name}"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        read_php_admin_html = "sleep 5; wget -O {tmp}/{name}.txt http://127.0.0.1:{port}/phpMyAdmin"
        grep_php_admin_html = "grep '<h1>.*>phpMyAdmin<' {tmp}/{name}.txt"
        sh____(read_php_admin_html.format(**locals()))
        sh____(grep_php_admin_html.format(**locals()))
        # CLEAN
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        drop_image_container = "docker rmi {images}:{name}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_6005_ubuntu_apache2_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Ubuntu, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        testname="test_6005"
        port=6005
        name="ubuntu-apache2"
        dockerfile="ubuntu-apache2.dockerfile"
        images = IMAGES
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} {images}:{name}"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        read_index_html = "sleep 5; wget -O {tmp}/{name}.txt http://127.0.0.1:{port}"
        grep_index_html = "grep OK {tmp}/{name}.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # CLEAN
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        drop_image_container = "docker rmi {images}:{name}"
        sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_6011_centos_httpd_socket_notify(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            and in the systemctl.debug.log we can see NOTIFY_SOCKET
            messages with Apache sending a READY and MAINPID value."""
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 200"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_software = "docker exec {testname} yum install -y httpd httpd-tools"
        sh____(install_software.format(**locals()))
        enable_software = "docker exec {testname} systemctl enable httpd"
        sh____(enable_software.format(**locals()))
        push_result = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(push_result.format(**locals()))
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
        make_info_log = "docker exec {testname} touch /var/log/systemctl.debug.log"
        start_httpd = "docker exec {testname} systemctl start httpd"
        sh____(make_info_log.format(**locals()))
        sh____(start_httpd.format(**locals()))
        # THEN
        time.sleep(5)
        read_index_html = "wget -O {testdir}/result.txt http://{container}:80"
        grep_index_html = "grep OK {testdir}/result.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # STOP
        status_software = "docker exec {testname} systemctl status httpd"
        stop_software = "docker exec {testname} systemctl stop httpd"
        sh____(status_software.format(**locals()))
        sh____(stop_software.format(**locals()))
        fetch_systemctl_log = "docker cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(fetch_systemctl_log.format(**locals()))
        stop_new_container = "docker stop {testname}"
        drop_new_container = "docker rm --force {testname}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        # CHECK
        self.assertEqual(len(greps(open(testdir+"/systemctl.debug.log"), " ERROR ")), 0)
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "use NOTIFY_SOCKET="))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "read_notify.*READY=1.*MAINPID="))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "ntfy start done"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "stop '/bin/kill' '-WINCH'"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "wait [$]NOTIFY_SOCKET"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "dead PID"))
        self.rm_testdir()
    def test_6012_centos_elasticsearch(self):
        """ WHEN we can setup a specific ElasticSearch version 
                 as being downloaded from the company.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see the ok-status from elastic."""
        base_url = "https://download.elastic.co/elasticsearch/elasticsearch"
        filename = "elasticsearch-1.7.3.noarch.rpm"
        into_dir = "Software/ElasticSearch"
        download(base_url, filename, into_dir)
        self.assertTrue(greps(os.listdir("Software/ElasticSearch"), filename))
        #
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 200"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_java = "docker exec {testname} yum install -y java" # required
        sh____(install_java.format(**locals()))
        install_extras = "docker exec {testname} yum install -y which" # TODO: missing requirement of elasticsearch
        sh____(install_extras.format(**locals()))
        uploads_software = "docker cp Software/ElasticSearch {testname}:/srv/"
        sh____(uploads_software.format(**locals()))
        install_software = "docker exec {testname} bash -c 'yum install -y /srv/ElasticSearch/*.rpm'"
        sh____(install_software.format(**locals()))
        enable_software = "docker exec {testname} systemctl enable elasticsearch"
        sh____(enable_software.format(**locals()))
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
        logg.info("========================>>>>>>>>")
        make_info_log = "docker exec {testname} touch /var/log/systemctl.log"
        sh____(make_info_log.format(**locals()))
        start_software = "docker exec {testname} systemctl start elasticsearch -vvv"
        sh____(start_software.format(**locals()))
        # THEN
        testdir = self.testdir(testname)
        read_index_html = "sleep 5; wget -O {testdir}/result.txt http://{container}:9200/?pretty"
        grep_index_html = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # STOP
        status_elasticsearch = "docker exec {testname} systemctl status elasticsearch"
        stop_elasticsearch = "docker exec {testname} systemctl stop elasticsearch"
        sh____(status_elasticsearch.format(**locals()))
        sh____(stop_elasticsearch.format(**locals()))
        fetch_systemctl_log = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(fetch_systemctl_log.format(**locals()))
        stop_container = "docker stop {testname}"
        drop_container = "docker rm --force {testname}"
        sh____(stop_container.format(**locals()))
        sh____(drop_container.format(**locals()))
        # CHECK
        systemctl_log = open(testdir+"/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 1)
        self.assertTrue(greps(systemctl_log, "ERROR chdir .* '/home/elasticsearch': .* No such file or directory"))
        self.assertTrue(greps(systemctl_log, "simp start done PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID .*elasticsearch.service"))
        self.assertTrue(greps(systemctl_log, "stopped PID .* EXIT 143"))
        #
        ## drop_image_container = "docker rmi {images}:{name}"
        ## sx____(drop_image_container.format(**locals()))
        self.rm_testdir()
    def test_6013_centos_lamp_stack(self):
        """ Check setup of Linux/Mariadb/Apache/Php on CentOs"""
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 200"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_epel = "docker exec {testname} yum install -y epel-release"
        sh____(install_epel.format(**locals()))
        install_repos = "docker exec {testname} yum repolist"
        sh____(install_repos.format(**locals()))
        install_lamp = "docker exec {testname} yum install -y httpd httpd-tools mariadb-server mariadb php phpmyadmin"
        sh____(install_lamp.format(**locals()))
        #
        WEB_CONF="/etc/httpd/conf.d/phpMyAdmin.conf"
        INC_CONF="/etc/phpMyAdmin/config.inc.php"
        INDEX_PHP="/var/www/html/index.php"
        push_result = "docker exec {testname} bash -c 'echo \"<?php phpinfo(); ?>\" > {INDEX_PHP}'"
        push_connect = "docker exec {testname} sed -i 's|ip 127.0.0.1|ip 172.0.0.0/8|' {WEB_CONF}"
        sh____(push_result.format(**locals()))
        sh____(push_connect.format(**locals()))
        start_db = "docker exec {testname} systemctl start mariadb -vvv"
        sh____(start_db.format(**locals()))
        rootuser_db = "docker exec {testname} mysqladmin -uroot password 'N0.secret'"
        text_file(os_path(testdir,"testuser.sql"), "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'")
        testuser_sql = "docker cp {testdir}/testuser.sql {testname}:/srv/testuser.sql" 
        testuser_db = "docker exec {testname} bash -c 'cat /srv/testuser.sql | mysql -uroot -pN0.secret'"
        sh____(rootuser_db.format(**locals()))
        sh____(testuser_sql.format(**locals()))
        sh____(testuser_db.format(**locals()))
        testuser_username = "docker exec {testname} sed -i -e \"/'user'/s|=.*;|='testuser_OK';|\" {INC_CONF}"
        testuser_password = "docker exec {testname} sed -i -e \"/'password'/s|=.*;|='Testuser.OK';|\" {INC_CONF}"
        sh____(testuser_username.format(**locals()))
        sh____(testuser_password.format(**locals()))
        enable_software = "docker exec {testname} systemctl start httpd"
        sh____(enable_software.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        read_php_admin_html = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        grep_php_admin_html = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(read_php_admin_html.format(**locals()))
        sh____(grep_php_admin_html.format(**locals()))
        # CLEAN
        stop_container = "docker stop {testname}"
        drop_container = "docker rm --force {testname}"
        sh____(stop_container.format(**locals()))
        sh____(drop_container.format(**locals()))
        #
        self.rm_testdir()
    def test_6014_opensuse_lamp_stack(self):
        """ Check setup of Linux/Mariadb/Apache/Php" on Opensuse"""
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(OPENSUSE)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 200"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_python = "docker exec {testname} zypper install -r oss -y python"
        sh____(install_python.format(**locals()))
        install_lamp = "docker exec {testname} zypper install -r oss -y apache2 apache2-utils mariadb-server mariadb-tools php5 phpMyAdmin"
        sh____(install_lamp.format(**locals()))
        #
        WEB_CONF="/etc/apache2/conf.d/phpMyAdmin.conf"
        INC_CONF="/etc/phpMyAdmin/config.inc.php"
        INDEX_PHP="/srv/www/htdocs/index.php"
        push_result = "docker exec {testname} bash -c 'echo \"<?php phpinfo(); ?>\" > {INDEX_PHP}'"
        push_connect = "docker exec {testname} sed -i 's|ip 127.0.0.1|ip 172.0.0.0/8|' {WEB_CONF}"
        sh____(push_result.format(**locals()))
        sh____(push_connect.format(**locals()))
        start_db = "docker exec {testname} systemctl start mysql -vvv"
        sh____(start_db.format(**locals()))
        rootuser_db = "docker exec {testname} mysqladmin -uroot password 'N0.secret'"
        text_file(os_path(testdir,"testuser.sql"), "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'")
        testuser_sql = "docker cp {testdir}/testuser.sql {testname}:/srv/testuser.sql" 
        testuser_db = "docker exec {testname} bash -c 'cat /srv/testuser.sql | mysql -uroot -pN0.secret'"
        sh____(rootuser_db.format(**locals()))
        sh____(testuser_sql.format(**locals()))
        sh____(testuser_db.format(**locals()))
        testuser_username = "docker exec {testname} sed -i -e \"/'user'/s|=.*;|='testuser_OK';|\" {INC_CONF}"
        testuser_password = "docker exec {testname} sed -i -e \"/'password'/s|=.*;|='Testuser.OK';|\" {INC_CONF}"
        sh____(testuser_username.format(**locals()))
        sh____(testuser_password.format(**locals()))
        enable_software = "docker exec {testname} systemctl start apache2"
        sh____(enable_software.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        read_php_admin_html = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        grep_php_admin_html = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(read_php_admin_html.format(**locals()))
        sh____(grep_php_admin_html.format(**locals()))
        # CLEAN
        stop_container = "docker stop {testname}"
        drop_container = "docker rm --force {testname}"
        sh____(stop_container.format(**locals()))
        sh____(drop_container.format(**locals()))
        #
        self.rm_testdir()
    # @unittest.expectedFailure
    def test_8001_issue_1_start_mariadb_centos_7_0(self):
        """ issue 1: mariadb on centos 7.0 does not start"""
        # this was based on the expectation that "yum install mariadb" would allow
        # for a "systemctl start mysql" which in fact it doesn't. Double-checking
        # with "yum install mariadb-server" and "systemctl start mariadb" shows
        # that mariadb's unit file is buggy, because it does not specify a kill
        # signal that it's mysqld_safe controller does not ignore.
        testname = self.testname()
        testdir = self.testdir()
        # image= "centos:centos7.0.1406" # <<<< can not yum-install mariadb-server ?
        # image= "centos:centos7.1.1503"
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        # mariadb has a TimeoutSec=300 in the unit config:
        start_container = "docker run --detach --name={testname} {image} sleep 400"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_software = "docker exec {testname} yum install -y mariadb"
        sh____(install_software.format(**locals()))
        if False:
            # expected in bug report but that one can not work:
            enable_service = "docker exec {testname} systemctl enable mysql"
            sh____(enable_service.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_unit_files = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(list_unit_files.format(**locals()))
        out = output(list_unit_files.format(**locals()))
        self.assertFalse(greps(out,"mysqld"))
        #
        install_software2 = "docker exec {testname} yum install -y mariadb-server"
        sh____(install_software2.format(**locals()))
        list_unit_files = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(list_unit_files.format(**locals()))
        out = output(list_unit_files.format(**locals()))
        self.assertTrue(greps(out,"mariadb.service"))
        #
        start_service = "docker exec {testname} systemctl start mariadb -vv"
        sh____(start_service.format(**locals()))
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
        start_service = "docker exec {testname} systemctl stop mariadb -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        # self.assertFalse(greps(top, "mysqld "))
        if greps(top, "mysqld ") and had_mysqld_safe:
            logg.critical("mysqld still running => this is an uptream error!")
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_8002_issue_2_start_rsyslog_centos7(self):
        """ issue 2: rsyslog on centos 7 does not start"""
        # this was based on a ";Requires=xy" line in the unit file
        # but our unit parser did not regard ";" as starting a comment
        testname = self.testname()
        testdir = self.testdir()
        image= self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        stop_container = "docker rm --force {testname}"
        sx____(stop_container.format(**locals()))
        start_container = "docker run --detach --name={testname} {image} sleep 50"
        sh____(start_container.format(**locals()))
        install_systemctl = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(install_systemctl.format(**locals()))
        install_software = "docker exec {testname} yum install -y rsyslog"
        sh____(install_software.format(**locals()))
        version_systemctl = "docker exec {testname} systemctl --version"
        sh____(version_systemctl.format(**locals()))
        list_unit_files = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(list_unit_files.format(**locals()))
        out = output(list_unit_files.format(**locals()))
        self.assertTrue(greps(out,"rsyslog.service.*enabled"))
        #
        start_service = "docker exec {testname} systemctl start rsyslog -vv"
        sh____(start_service.format(**locals()))
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "/usr/sbin/rsyslog"))
        #
        start_service = "docker exec {testname} systemctl stop rsyslog -vv"
        sh____(start_service.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "/usr/sbin/rsyslog"))
        #
        sx____(stop_container.format(**locals()))
        self.rm_testdir()
    def test_9000_ansible_test(self):
        """ FIXME: "-p testing_systemctl" makes containers like "testingsystemctl_<service>_1" ?! """
        sh____("ansible-playbook --version | grep ansible-playbook.2") # atleast version2
        new_image1 = "localhost:5000/testingsystemctl:serversystem"
        new_image2 = "localhost:5000/testingsystemctl:virtualdesktop"
        rmi_commit1 = 'docker rmi "{new_image1}"'
        rmi_commit2 = 'docker rmi "{new_image2}"'
        sx____(rmi_commit1.format(**locals()))
        sx____(rmi_commit2.format(**locals()))
        if False:
            self.test_9001_ansible_download_software()
            self.test_9002_ansible_restart_docker_build_compose()
            self.test_9003_ansible_run_build_step_playbooks()
            self.test_9004_ansible_save_build_step_as_new_images()
            self.test_9005_ansible_restart_docker_start_compose()
            self.test_9006_ansible_unlock_jenkins()
            self.test_9006_ansible_check_jenkins_login()
            self.test_9008_ansible_stop_all_containers()
    def test_9001_ansible_download_software(self):
        """ download the software parts (will be done just once) """
        sh____("cd tests && ansible-playbook download-jenkins.yml -vv")
        sh____("cd tests && ansible-playbook download-selenium.yml -vv")
        sh____("cd tests && ansible-playbook download-firefox.yml -vv")
        # CHECK
        self.assertTrue(greps(os.listdir("Software/Jenkins"), "^jenkins.*[.]rpm"))
        self.assertTrue(greps(os.listdir("Software/Selenium"), "^selenium-.*[.]tar.gz"))
        self.assertTrue(greps(os.listdir("Software/Selenium"), "^selenium-server.*[.]jar"))
        self.assertTrue(greps(os.listdir("Software/CentOS"), "^firefox.*[.]centos[.]x86_64[.]rpm"))
    def test_9002_ansible_restart_docker_build_compose(self):
        """ bring up the build-step deployment containers """
        drop_old_containers = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        make_new_containers = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml up -d"
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
        # CHECK
        self.assertTrue(greps(output("docker ps"), " testingsystemctl1_virtualdesktop_1$"))
        self.assertTrue(greps(output("docker ps"), " testingsystemctl1_serversystem_1$"))
    def test_9003_ansible_run_build_step_playbooks(self):
        """ run the build-playbook (using ansible roles) """
        testname = "test_9003"
        # WHEN environment is prepared
        make_files_dir = "test -d tests/files || mkdir tests/files"
        make_script_link = "cd tests/files && ln -sf ../../files/docker"
        sh____(make_files_dir)
        sh____(make_script_link)
        make_logfile_1 = "docker exec testingsystemctl1_serversystem_1 bash -c 'touch /var/log/systemctl.log'"
        make_logfile_2 = "docker exec testingsystemctl1_virtualdesktop_1 bash -c 'touch /var/log/systemctl.log'"
        sh____(make_logfile_1)
        sh____(make_logfile_2)
        # THEN ready to run the deployment playbook
        inventory = "tests/docker-build-compose.ini"
        playbooks = "tests/docker-build-playbook.yml"
        variables = "-e LOCAL=yes -e jenkins_prefix=/buildserver"
        ansible = "ansible-playbook -i {inventory} {variables} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        # CLEAN
        drop_files_dir = "rm tests/files/docker"
        sh____(drop_files_dir)
        #
        # CHECK
        tmp = self.testdir(testname)
        read_logfile_1 = "docker cp testingsystemctl1_serversystem_1:/var/log/systemctl.log {tmp}/systemctl.server.log"
        read_logfile_2 = "docker cp testingsystemctl1_virtualdesktop_1:/var/log/systemctl.log {tmp}/systemctl.desktop.log"
        sh____(read_logfile_1.format(**locals()))
        sh____(read_logfile_2.format(**locals()))
        self.assertFalse(greps(open(tmp+"/systemctl.server.log"), " ERROR "))
        self.assertFalse(greps(open(tmp+"/systemctl.desktop.log"), " ERROR "))
        self.assertGreater(len(greps(open(tmp+"/systemctl.server.log"), " INFO ")), 10)
        self.assertGreater(len(greps(open(tmp+"/systemctl.desktop.log"), " INFO ")), 10)
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl daemon-reload"))
        # self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl status jenkins.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "--property=ActiveState")) # <<< new
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl show jenkins.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl show xvnc.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl enable xvnc.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl enable selenium.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl is-enabled selenium.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl daemon-reload"))
    def test_9004_ansible_save_build_step_as_new_images(self):
        # stop the containers but keep them around
        inventory = "tests/docker-build-compose.ini"
        playbooks = "tests/docker-build-stop.yml"
        variables = "-e LOCAL=yes"
        ansible = "ansible-playbook -i {inventory} {variables} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        message = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        startup = "CMD '/usr/bin/systemctl'"
        container1 = "testingsystemctl1_serversystem_1"
        new_image1 = "localhost:5000/testingsystemctl:serversystem"
        container2 = "testingsystemctl1_virtualdesktop_1"
        new_image2 = "localhost:5000/testingsystemctl:virtualdesktop"
        commit1 = 'docker commit -c "{startup}" -m "{message}" {container1} "{new_image1}"'
        commit2 = 'docker commit -c "{startup}" -m "{message}" {container2} "{new_image2}"'
        sh____(commit1.format(**locals()))
        sh____(commit2.format(**locals()))
        # CHECK
        self.assertTrue(greps(output("docker images"), IMAGES+".* serversystem "))
        self.assertTrue(greps(output("docker images"), IMAGES+".* virtualdesktop "))
    def test_9005_ansible_restart_docker_start_compose(self):
        """ bring up the start-step runtime containers from the new images"""
        drop_old_build_step = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        drop_old_containers = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml down"
        make_new_containers = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml up -d"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
        time.sleep(2) # sometimes the container dies early
        # CHECK
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_serversystem_1$"))
        self.assertTrue(greps(output("docker ps"), " testingsystemctl2_virtualdesktop_1$"))
        self.assertTrue(greps(output("docker ps"), " testingsystemctl2_serversystem_1$"))
    def test_9006_ansible_unlock_jenkins(self):
        """ unlock jenkins as a post-build config-example using selenium-server """
        inventory = "tests/docker-start-compose.ini"
        playbooks = "tests/docker-start-playbook.yml"
        variables = "-e LOCAL=yes -e j_username=installs -e j_password=installs.11"
        vartarget = "-e j_url=http://serversystem:8080/buildserver"
        ansible = "ansible-playbook -i {inventory} {variables} {vartarget} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        # CHECK
        test_screenshot = "ls -l tests/*.png"
        sh____(test_screenshot)
    def test_9007_ansible_check_jenkins_login(self):
        """ check jenkins runs unlocked as a testcase result """
        tmp = self.testdir("test_9007")
        webtarget = "http://localhost:8080/buildserver/manage"
        weblogin = "--user installs --password installs.11 --auth-no-challenge"
        read_jenkins_html = "wget {weblogin} -O {tmp}/page.html {webtarget}"
        grep_jenkins_html = "grep 'Manage Nodes' {tmp}/page.html"
        sh____(read_jenkins_html.format(**locals()))
        sh____(grep_jenkins_html.format(**locals()))
    def test_9008_ansible_stop_all_containers(self):
        """ bring up the start-step runtime containers from the new images"""
        time.sleep(3)
        drop_old_build_step = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        drop_old_start_step = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml down"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_start_step}".format(**locals()))
        # CHECK
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_serversystem_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl2_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl2_serversystem_1$"))

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
       epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v","--verbose", action="count", default=0,
       help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
       help="systemctl.py file to be tested (%default)")
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
    #
    if opt.coverage:
        _c = _coverage
        if opt.coverage > 1:
            if os.path.exists(".coverage"):
                os.remove(".coverage")
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
        _cov = _coverage
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
        print " " + _cov_cmd + " report " + _systemctl_py
        print " " + _cov_cmd + " annotate " + _systemctl_py
