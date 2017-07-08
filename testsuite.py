#! /usr/bin/env python

""" Testcases for docker-systemctl-replacement functionality """

__copyright__ = "(C) Guido Draheim, for free use (CC-BY,GPL) """
__version__ = "0.7.0"

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

logg = logging.getLogger("tests")
_systemctl_py = "files/docker/systemctl.py"

IMAGES = "localhost:5000/testingsystemctl"

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
    return _lines(text)
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
    def testname(self):
        return self.caller_testname()
    def caller_testname(self):
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tests/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def root(self, testdir):
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
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
    def test_1002_systemctl_version(self):
        cmd = "%s --version" % _systemctl_py
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, "systemd 0"))
        self.assertTrue(greps(out, "[(]systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_1003_systemctl_help(self):
        cmd = "%s --help" % _systemctl_py
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, "--root=PATH"))
        self.assertTrue(greps(out, "--verbose"))
        self.assertTrue(greps(out, "--init"))
        self.assertTrue(greps(out, "for more information"))
        self.assertFalse(greps(out, "reload-or-try-restart"))
        cmd = "%s help" % _systemctl_py
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertFalse(greps(out, "--init"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
    def test_1004_systemctl_daemon_reload(self):
        """ daemon-reload always succeeds (does nothing) """
        cmd = "%s daemon-reload" % _systemctl_py
        out,end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
    def test_1005_systemctl_daemon_reload_root_ignored(self):
        """ daemon-reload always succeeds (does nothing) """
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "%s --root=%s daemon-reload" % (_systemctl_py, root)
        out,end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
    def test_1010_systemctl_force_ipv4(self):
        """ we can force --ipv4 for /etc/hosts """
        testdir = self.testdir()
        root = self.root(testdir)
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
        cmd = "%s --root=%s --ipv4 daemon-reload" % (_systemctl_py, root)
        out,end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertFalse(greps(hosts, "::1.*localhost "))
    def test_1011_systemctl_force_ipv6(self):
        """ we can force --ipv6 for /etc/hosts """
        testdir = self.testdir()
        root = self.root(testdir)
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
        cmd = "%s --root=%s --ipv6 daemon-reload" % (_systemctl_py, root)
        out,end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertFalse(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
    def test_2001_can_create_test_services(self):
        """ check that two unit files can be created for testing """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
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
    def test_2002_list_units(self):
        """ check that two unit files can be found for 'list-units' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "%s --root=%s list-units" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"b.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertIn("loaded units listed.", out)
        self.assertIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "%s --root=%s --no-legend list-units" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"b.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertNotIn("loaded units listed.", out)
        self.assertNotIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 2)
    def test_2003_list_unit_files(self):
        """ check that two unit service files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "%s --root=%s --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "%s --root=%s --no-legend --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
    def test_2004_list_unit_files_wanted(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "%s --root=%s --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "%s --root=%s --no-legend --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
    def test_2013_list_unit_files_common_targets(self):
        """ check that some unit target files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "%s --root=%s --no-legend --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertFalse(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        cmd = "%s --root=%s --no-legend --type=target list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertFalse(greps(out, r"a.service\s+static"))
        self.assertFalse(greps(out, r"b.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertGreater(len(lines(out)), 10)
        num_targets = len(lines(out))
        cmd = "%s --root=%s --no-legend list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), num_targets + 2)
    def test_2014_list_unit_files_now(self):
        """ check that 'list-unit-files --now' presents a special debug list """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "%s --root=%s --no-legend --now list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+SysD\s+.*systemd/system/a.service"))
        self.assertTrue(greps(out, r"b.service\s+SysD\s+.*systemd/system/b.service"))
        self.assertFalse(greps(out, r"multi-user.target"))
        self.assertFalse(greps(out, r"enabled"))
        self.assertEqual(len(lines(out)), 2)
    def test_2020_show_unit_is_parseable(self):
        """ check that 'show UNIT' is machine-readable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "%s --root=%s show a.service" % (_systemctl_py, root)
        out = output(cmd)
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
        cmd = "%s --root=%s --all show a.service" % (_systemctl_py, root)
        out = output(cmd)
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
    def test_2021_show_unit_can_be_restricted_to_one_property(self):
        """ check that 'show UNIT' may return just one value if asked for"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "%s --root=%s show a.service --property=Description" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "%s --root=%s show a.service --property=Description --all" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "%s --root=%s show a.service --property=PIDFile" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "%s --root=%s show a.service --property=PIDFile --all" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        self.assertEqual(lines(out), [ "PIDFile=" ])
    def test_2025_show_unit_for_multiple_matches(self):
        """ check that the result of 'show UNIT' for multiple services is 
            concatenated but still machine readable. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "%s --root=%s show a.service" % (_systemctl_py, root)
        out = output(cmd)
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
        cmd = "%s --root=%s show b.service" % (_systemctl_py, root)
        out = output(cmd)
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
        cmd = "%s --root=%s show a.service b.service" % (_systemctl_py, root)
        out = output(cmd)
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
    def test_3002_enable_service_creates_a_symlink(self):
        """ check that a service can be enabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "%s --root=%s enable b.service" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
    def test_3003_disable_service_removes_the_symlink(self):
        """ check that a service can be enabled and disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "%s --root=%s enable b.service" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        cmd = "%s --root=%s disable b.service" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
    def test_3004_list_unit_files_when_enabled(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "%s --root=%s --no-legend --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "%s --root=%s --no-legend enable b.service" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        #
        cmd = "%s --root=%s --no-legend --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "%s --root=%s --no-legend disable b.service" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "%s --root=%s --no-legend --type=service list-unit-files" % (_systemctl_py, root)
        out = output(cmd)
        logg.info("\n> %s\n%s", cmd, out)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertEqual(len(lines(out)), 2)
    def test_3005_is_enabled_result_when_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "%s --root=%s is-enabled a.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "%s --root=%s is-enabled b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "%s --root=%s --no-legend enable b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s is-enabled b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s --no-legend disable b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s is-enabled b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
    def test_3006_is_enabled_is_true_when_any_is_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
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
        cmd = "%s --root=%s is-enabled a.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "%s --root=%s is-enabled b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "%s --root=%s is-enabled c.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "%s --root=%s is-enabled b.service c.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 1)
        cmd = "%s --root=%s is-enabled a.service b.service c.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 3)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s --no-legend enable b.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s is-enabled b.service c.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s is-enabled b.service a.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "%s --root=%s is-enabled c.service a.service" % (_systemctl_py, root)
        out, end = output2(cmd)
        logg.info("\n> %s\n%s\n**%s", cmd, out, end)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
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
    def test_6006_centos_elasticsearch_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can setup a specific ElasticSearch version 
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
        testname="test_6006"
        port=6006
        name="centos-elasticsearch"
        dockerfile="centos-elasticsearch.dockerfile"
        images = IMAGES
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:9200 --name {name} {images}:{name} sleep 9999"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        make_info_log = "touch /var/log/systemctl.log"
        start_elasticsearch = "systemctl start elasticsearch"
        sh____("docker exec {name} {make_info_log}".format(**locals()))
        sh____("docker exec {name} {start_elasticsearch}".format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        read_index_html = "sleep 5; wget -O {tmp}/{name}.txt http://127.0.0.1:{port}/?pretty"
        grep_index_html = "grep 'You Know, for Search' {tmp}/{name}.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # STOP
        status_elasticsearch = "systemctl status elasticsearch"
        stop_elasticsearch = "systemctl stop elasticsearch"
        sh____("docker exec {name} {status_elasticsearch}".format(**locals()))
        sh____("docker exec {name} {stop_elasticsearch}".format(**locals()))
        sh____("docker cp {name}:/var/log/systemctl.log {tmp}/systemctl.log".format(**locals()))
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        # CHECK
        self.assertEqual(len(greps(open(tmp+"/systemctl.log"), " ERROR ")), 1)
        self.assertTrue(greps(open(tmp+"/systemctl.log"), "ERROR chdir .* '/home/elasticsearch': .* No such file or directory"))
        self.assertTrue(greps(open(tmp+"/systemctl.log"), "done simple PID"))
        self.assertTrue(greps(open(tmp+"/systemctl.log"), "stop kill PID .*elasticsearch.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.log"), "stopped PID .* EXIT 143"))
    def test_6011_centos_httpd_socket_notify(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            and in the systemctl.debug.log we can see NOTIFY_SOCKET
            messages with Apache sending a READY and MAINPID value."""
        testname="test_6011"
        port=6011
        name="centos-httpd"
        dockerfile="centos-httpd.dockerfile"
        images = IMAGES
        # WHEN
        # test_6001: build_new_image = "docker build . -f tests/{dockerfile} --tag {images}:{name}"
        # test_6001: sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} {images}:{name} sleep 9999"
        sx____(drop_old_container.format(**locals()))
        sh____(start_as_container.format(**locals()))
        make_info_log = "touch /var/log/systemctl.debug.log"
        start_httpd = "systemctl start httpd"
        sh____("docker exec {name} {make_info_log}".format(**locals()))
        sh____("docker exec {name} {start_httpd}".format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        read_index_html = "sleep 5; wget -O {tmp}/{name}.txt http://127.0.0.1:{port}"
        grep_index_html = "grep OK {tmp}/{name}.txt"
        sh____(read_index_html.format(**locals()))
        sh____(grep_index_html.format(**locals()))
        # STOP
        status_elasticsearch = "systemctl status httpd"
        stop_elasticsearch = "systemctl stop httpd"
        sh____("docker exec {name} {status_elasticsearch}".format(**locals()))
        sh____("docker exec {name} {stop_elasticsearch}".format(**locals()))
        sh____("docker cp {name}:/var/log/systemctl.debug.log {tmp}/systemctl.debug.log".format(**locals()))
        stop_new_container = "docker stop {name}"
        drop_new_container = "docker rm --force {name}"
        sh____(stop_new_container.format(**locals()))
        sh____(drop_new_container.format(**locals()))
        # CHECK
        self.assertEqual(len(greps(open(tmp+"/systemctl.debug.log"), " ERROR ")), 0)
        self.assertTrue(greps(open(tmp+"/systemctl.debug.log"), "use NOTIFY_SOCKET="))
        self.assertTrue(greps(open(tmp+"/systemctl.debug.log"), "read_notify.*READY=1.*MAINPID="))
        self.assertTrue(greps(open(tmp+"/systemctl.debug.log"), "done notify"))
        self.assertTrue(greps(open(tmp+"/systemctl.debug.log"), "stop /bin/kill"))
        self.assertTrue(greps(open(tmp+"/systemctl.debug.log"), "wait [$]NOTIFY_SOCKET"))
        self.assertTrue(greps(open(tmp+"/systemctl.debug.log"), "dead PID"))
    def test_9000_ansible_test(self):
        """ FIXME: "-p testing_systemctl" makes containers like "testingsystemctl_<service>_1" ?! """
        sh____("ansible-playbook --version | grep ansible-playbook.2") # atleast version2
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
        self.assertGreater(len(greps(open(tmp+"/systemctl.server.log"), " INFO ")), 22)
        self.assertGreater(len(greps(open(tmp+"/systemctl.desktop.log"), " INFO ")), 22)
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl daemon-reload"))
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl status jenkins.service"))
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
       help="increase logging level (%default)")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
       help="systemctl.py file to be tested (%default)")
    _o.add_option("-l","--logfile", metavar="FILE", default="",
       help="additionally save the output log to a file (%default)")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
       help="capture results as a junit xml file (%default)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
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
