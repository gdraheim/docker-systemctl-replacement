    #! /usr/bin/env python3
# pylint: disable=line-too-long,too-many-lines,too-many-statements,too-many-locals,too-many-public-methods,too-many-return-statements
# pylint: disable=multiple-statements,unspecified-encoding,import-outside-toplevel,deprecated-module,invalid-name,bare-except
# pylint: disable=unused-argument,unused-variable,possibly-unused-variable,missing-function-docstring,missing-class-docstring,consider-using-f-string,logging-format-interpolation
# pylint: disable=consider-using-with,chained-comparison
""" Testcases for docker-systemctl-replacement functionality """

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.1.1066"

# NOTE:
# The testcases 1000...4999 are using a --root=subdir environment
# The testcases 5000...9999 will start a docker container to work.

from typing import Optional, Union, List, Tuple, Iterator, Dict
import subprocess
import os.path
import time
import unittest
import shutil
import inspect
import string
import random
import logging
import re
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json
import sys

logg = logging.getLogger("BUILD")
_epel7 = False
_opensuse14 = False
_python2 = "/usr/bin/python"
_python3 = "/usr/bin/python3"
_python = ""
_systemctl_py = ""
_systemctl3_py = "files/docker/systemctl3.py"
_top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* ' | grep -v -e ' ps ' -e ' grep ' -e 'kworker/'"
_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"

SAVETO = "localhost:5000/systemctl2"
IMAGES = "localhost:5000/systemctl"
CENTOS = "almalinux:9.4"
UBUNTU = "ubuntu:22.04"
OPENSUSE = "opensuse/leap:15.5"
NIX = ""
NOCACHE = "--no-cache"
LATEST = NIX
TODO = False

_curl = "curl"
_curl_timeout4 = "--max-time 4"
_docker = "docker"
DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"
RUNTIME = "/tmp/run-"

LOCALPACKAGES = False
REMOTEPACKAGES = False
_maindir = os.path.abspath(os.path.dirname(__file__))
_mirror = os.path.join(_maindir, "docker_mirror.py")
_password = ""
_verbose = ""

def decodes(text: Union[str, bytes, None]) -> Optional[str]:
    if text is None: return None
    return decodes_(text)
def decodes_(text: Union[str, bytes]) -> str:
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def sh____(cmd: Union[str, List[str]], shell: bool=True) -> int:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd: Union[str, List[str]], shell: bool =True) -> int:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd: Union[str, List[str]], shell: bool=True) -> str:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return decodes_(out)
def output2(cmd: Union[str, List[str]], shell:bool=True) -> Tuple[str, int]:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return decodes_(out), run.returncode
def output3(cmd: Union[str, List[str]], shell:bool=True) -> Tuple[str, str, int]:
    if isinstance(cmd, str):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return decodes_(out), decodes_(err), run.returncode


def _lines4(lines: Union[str, List[str]]) -> List[str]:
    if isinstance(lines, str):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def lines4(text: Union[str, List[str]]) -> List[str]:
    lines = []
    for line in _lines4(text):
        lines.append(line.rstrip())
    return lines
def grep(pattern: str, lines: Union[str, List[str]]) -> Iterator[str]:
    for line in _lines4(lines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def greps(lines: Union[str, List[str]], pattern: str) -> List[str]:
    return list(grep(pattern, lines))

def download(base_url: str, filename: str, into: str) -> None:
    if not os.path.isdir(into):
        os.makedirs(into)
    if not os.path.exists(os.path.join(into, filename)):
        curl = _curl
        sh____("cd {into} && {curl} -O {base_url}/{filename}".format(**locals()))
def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        assert x
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line + "\n")
    else:
        f.write(content)
    f.close()
def shell_file(filename: str, content: str) -> None:
    text_file(filename, content)
    os.chmod(filename, 0o770)
def copy_file(filename: str, target: str) -> None:
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename: str, target: str) -> None:
    copy_file(filename, target)
    os.chmod(target, 0o750)

def get_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name # type: ignore[union-attr]
def os_path(root: Optional[str], path: str) -> str:
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(root, path)
def docname(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

def python_package(python: str, image: Optional[str] = None) -> str:
    package = os.path.basename(python)
    if "python2" in package or "python" == package:
        if image and "opensuse" in image:
            return "python-base"
        if image and "centos:8" in image:
            return "python2"
        if image and "almalinux" in image:
            return "python2"
        if image and "ubuntu" in image:
            return "python2"
        return "python"
    if "python3.6" in package:
        return "python3"
    return package.replace(".", "") # python3.11 => python311

SYSTEMCTL=""
_tmp_systemctl2_py = "tmp/systemctl.py"  # pylint: disable=invalid-name
_tmp_systemctl3_py = "tmp/systemctl3.py"  # pylint: disable=invalid-name

def tmp_systemctl3() -> Optional[str]:
    src_systemctl3_py = _systemctl3_py if _systemctl3_py else _systemctl_py
    if not src_systemctl3_py:
        return None
    if  (not os.path.exists(_tmp_systemctl3_py)) or (os.path.getmtime(_tmp_systemctl3_py) < os.path.getmtime(src_systemctl3_py)):
        tmpdir = os.path.dirname(_tmp_systemctl3_py)
        if "/" in _tmp_systemctl3_py and not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)
        shutil.copy2(src_systemctl3_py, _tmp_systemctl3_py)
    if os.path.exists(_tmp_systemctl3_py):
        return _tmp_systemctl3_py
    return None

def tmp_systemctl() -> Optional[str]:
    src_systemctl2_py = _systemctl_py # _systemctl_py is assumed to be a stripped variant (strip_python3 output)
    if not src_systemctl2_py:
        return None
    if  (not os.path.exists(_tmp_systemctl2_py)) or (os.path.getmtime(_tmp_systemctl2_py) < os.path.getmtime(src_systemctl2_py)):
        tmpdir = os.path.dirname(_tmp_systemctl2_py)
        if "/" in _tmp_systemctl2_py and not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)
        shutil.copy2(src_systemctl2_py, _tmp_systemctl2_py)
    if os.path.exists(_tmp_systemctl2_py):
        return _tmp_systemctl2_py
    return None

class DockerBuildTest(unittest.TestCase):
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1 + 1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str]=None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self) -> int:
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 5000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname: Optional[str]=None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str]=None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
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
    def rm_zzfiles(self, root: Optional[str]) -> None:
        for folder in self.real_folders():
            for item in glob(os_path(root, folder + "/zz*")):
                logg.info("rm %s", item)
                os.remove(item)
            for item in glob(os_path(root, folder + "/test_*")):
                logg.info("rm %s", item)
                os.remove(item)
    def root(self, testdir: str, real: Optional[bool]=None) -> str:
        if real: return "/"
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def newpassword(self) -> str:
        if _password:
            return _password
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
        import getpass
        return getpass.getuser()
    def ip_container(self, name: str) -> str:
        docker = _docker
        cmd = "{docker} inspect {name}"
        stdout = output(cmd.format(**locals()))
        values: List[Dict[str, Dict[str, str]]] = json.loads(stdout)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"]
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
    def local_addhosts(self, dockerfile: str, extras: Optional[str]=None) -> str:
        extras = "--local" if not extras and LOCALPACKAGES else ""
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
            return self.start_mirror(image, extras)
        return ""
    def start_mirror(self, image:str, extras: Optional[str]=None) -> str:
        extras = "--local" if not extras and LOCALPACKAGES else ""
        if REMOTEPACKAGES:
            return ""
        docker = _docker
        mirror = _mirror
        cmd = "{mirror} start {image} --add-hosts {extras}"
        out = output(cmd.format(**locals()))
        return decodes_(out).strip()
    def drop_container(self, name: str) -> None:
        docker = _docker
        cmd = "{docker} rm --force {name}"
        sx____(cmd.format(**locals()))
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
        self.drop_container(name)
        docker = _docker
        local_image = self.local_image(image)
        cmd = "{docker} run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd.format(**locals()))
        print("                 # " + local_image)
        print("  {docker} exec -it {name} bash".format(**locals()))
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_9001_systemctl_testfile(self) -> None:
        """ the systemctl.py file to be tested does exist """
        systemctl = tmp_systemctl()
        if not systemctl: self.skipTest("no python2 systemctl.py")
        if not os.path.exists("/usr/bin/python"): self.skipTest("no /usr/bin/python found")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s", root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(systemctl, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
    def test_9002_systemctl_testfile(self) -> None:
        """ the systemctl.py file to be tested does exist """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists("/usr/bin/python3"): self.skipTest("no /usr/bin/python3 found")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s", root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(systemctl, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
    def test_9003_systemctl_version(self) -> None:
        systemctl = tmp_systemctl()
        if not systemctl: self.skipTest("no python2 systemctl.py")
        if not os.path.exists("/usr/bin/python"): self.skipTest("no /usr/bin/python found")
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "systemd 219"))
        self.assertTrue(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_9004_systemctl_version(self) -> None:
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists("/usr/bin/python3"): self.skipTest("no /usr/bin/python3 found")
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "systemd 219"))
        self.assertTrue(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_9005_systemctl_help(self) -> None:
        """ the '--help' option and 'help' command do work """
        systemctl = tmp_systemctl()
        if not systemctl: self.skipTest("no python2 systemctl.py")
        if not os.path.exists("/usr/bin/python"): self.skipTest("no /usr/bin/python found")
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
    def test_9006_systemctl_help(self) -> None:
        """ the '--help' option and 'help' command do work """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists("/usr/bin/python3"): self.skipTest("no /usr/bin/python3 found")
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
    def test_9109_httpd_alma9_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        name = "httpd-alma9"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9110_httpd_alma9_not_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode
            THEN it fails."""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        name = "httpd-alma9-not-user"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest} sleep 300"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "{docker} exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit httpd.service not for --user mode"))
        cmd = "{docker} exec {testname} /usr/sbin/httpd -DFOREGROUND"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unable to open logs"))
        # self.assertTrue(greps(err, "could not bind to address 0.0.0.0:80"))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9111_httpd_alma9_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode.
            THEN it succeeds if modified"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        name = "httpd-alma9-user"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest} sleep 300"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 0)
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}:8080"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "apache.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9116_apache2_ubuntu16(self) -> None:
        """ WHEN using a dockerfile for systemd enabled Ubuntu 16 with python2
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl()
        if not systemctl: self.skipTest("no python2 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not TODO: self.skipTest("ubuntu-16 end of life")
        docker = _docker
        curl = _curl
        python = _python or _python2
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "apache2-ubuntu-16.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        latest = LATEST or os.path.basename(python)
        python1 = os.path.basename(python) if "python3" in python else "python2"
        python2 = python_package(python, dockerfile)
        if not _python:
            logg.info("python1 %s python2 %s", python1, python2)
            assert python1 == "python2" # exe
            assert python2 == "python" # pkg
            logg.fatal("addhosts %s", addhosts)
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest} --build-arg PYTHON={python1} --build-arg PYTHON2={python2}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9118_apache2_ubuntu18(self) -> None:
        """ WHEN using a dockerfile for systemd enabled Ubuntu 18 with python3
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        dockerfile = "apache2-ubuntu18.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        latest = LATEST or os.path.basename(python)
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9121_apache2_ubuntu22(self) -> None:
        """ WHEN using a dockerfile for systemd enabled Ubuntu 22 with python2
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl()
        if not systemctl: self.skipTest("no python2 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python2
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "apache2-ubuntu-22.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        latest = LATEST or os.path.basename(python)
        python1 = os.path.basename(python) if "python3" in python else "python2"
        python2 = python_package(python, dockerfile)
        if not _python:
            logg.info("python1 %s python2 %s", python1, python2)
            assert python1 == "python2"
            assert python2 == "python2"
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest} --build-arg PYTHON={python1} --build-arg PYTHON2={python2}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9122_apache2_ubuntu22(self) -> None:
        """ WHEN using a dockerfile for systemd enabled Ubuntu 22 with python3
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "apache2-ubuntu22.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        latest = LATEST or os.path.basename(python)
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9142_apache2_opensuse15_py2_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse and python2, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl()
        if not systemctl: self.skipTest("no python2 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python2
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        name = "apache2-opensuse15-py2"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        nocache = NOCACHE
        python1 = "python" if "python2" in python else os.path.basename(python)
        pythonpkg = python_package(python, dockerfile)
        if not _python:
            logg.info("python1 %s pythonpkg %s", python1, pythonpkg)
            # assert python1 == "python"
            # assert python2 == "python2"
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {nocache} {addhosts} --tag {images}/{testname}:{latest} --build-arg PYTHON={python1} --build-arg PYTHONPKG={pythonpkg}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9143_apache2_opensuse15_dockerfile(self) -> None:
        self.test_9145_apache2_opensuse15_dockerfile("python3.11")
    def test_9145_apache2_opensuse15_dockerfile(self, python: str = NIX) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = python or _python or _python3
        latest = LATEST or os.path.basename(python)
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        testname = self.testname()
        testdir = self.testdir()
        name = "apache2-opensuse15"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        nocache = NOCACHE
        pythonpkg = python_package(python, dockerfile)
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {nocache} {addhosts} --tag {images}/{testname}:{latest} --build-arg PYTHON={python} --build-arg PYTHONPKG={pythonpkg}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9195_nginx_opensuse15_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse and python3, 
            THEN we can create an image with an NGINX HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "nginx-opensuse15.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9209_postgres_alma9_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        name = "postgres-alma9"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9218_postgres_ubuntu18_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu 16.04 and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "postgres-ubuntu18.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9222_postgres_ubuntu22_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu 22.04 and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "postgres-ubuntu22.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9245_postgres_opensuse15_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "postgres-opensuse15.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Pass." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9299_postgres_alma9_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and python3,
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
             AND in this variant it runs under User=postgres right
               there from PID-1 started implicity in --user mode."""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        name = "postgres-alma9-user"
        dockerfile = "postgres-alma9-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        runtime = RUNTIME
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        uid = "postgres"
        cmd = "{docker} exec {testname} id -u {uid}"
        out = output(cmd.format(**locals()))
        if out: uid = decodes_(out).strip()
        cmd = "{docker} exec {testname} ls {runtime}{uid}/run"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'for i in 1 2 3 4 5 ; do wc -l {runtime}{uid}/run/postgresql.service.status && break; sleep 2; done'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:{runtime}{uid}/run/postgresql.service.status {testdir}/postgresql.service.status"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "postgres.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9309_redis_alma9_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-alma9.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            raise
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9311_redis_alma9_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-alma9-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            if TODO:
                raise
            self.skipTest("TODO: redis server is not running?")
        #
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9318_redis_ubuntu18_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-ubuntu18.dockerfile"
        addhosts = ""  # FIXME# self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest} --build-arg PASSWORD={password}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} -a {password} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            raise
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9324_redis_ubuntu18_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-ubuntu24.dockerfile"
        addhosts = ""  # FIXME# self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest} --build-arg PASSWORD={password}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} -a {password} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            raise
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9345_redis_opensuse15_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-opensuse15.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest} --build-arg PASSWORD={password}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} -a {password} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            raise
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9368_redis_ubuntu18_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-ubuntu18-user.dockerfile"
        addhosts = ""  # FIXME# self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            if TODO:
                raise
            self.skipTest("TODO: redis server is not running????")
        #
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9374_redis_ubuntu24_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-ubuntu24-user.dockerfile"
        addhosts = ""  # FIXME# self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        if attempt > 5:
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} -a {password} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            if TODO:
                raise
            self.skipTest("TODO: redis server is not running????")
        #
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9385_redis_opensuse15_user_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' 
            AND that AUTH works along with a USER process"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "redis-opensuse15-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} -a {password} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep PONG {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            if TODO:
                raise
            self.skipTest("TODO: redis server is not running????")
        # USER
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9418_mongod_ubuntu18_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and mongod,
            check that mongo can reply with a hostInfo."""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "mongod-ubuntu18.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --help"
        sh____(cmd.format(**locals()))
        # cmd = "mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep 'MongoDB server version' {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("mongo server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            if TODO:
                raise
            self.skipTest("TODO: mongo server is not running????")
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9445_mongod_opensuse15_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and mongod, 
            check that mongo can reply witha  hostInfo."""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "mongod-opensuse15.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}/{testname}:{latest} sleep 3"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --help"
        sh____(cmd.format(**locals()))
        # cmd = "mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep 'MongoDB server version' {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            logg.error("redis server is not running? %s", e)
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            raise
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9709_lamp_stack_alma9(self) -> None:
        """ Check setup of Linux/Apache/Mariadb/Php on Almalinux with python3"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name = "lamp-stack-alma9"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile, "--epel")
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        logg.info("THEN")
        for attempt in range(20):
            time.sleep(1)
            cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
            out, err, end = output3(cmd.format(**locals()))
            if "503 Service Unavailable" in err:
                logg.info("[%i] ..... 503 %s", attempt, greps(err, "503 "))
                continue
            if "200 OK" in err:
                logg.info("[%i] ..... 200 %s", attempt, greps(err, "200 "))
                break
            text = open("{testdir}/result.txt".format(**locals())).read()
            if "503 Service Unavailable" in text:
                logg.info("[%i] ..... 503 %s", attempt, greps(text, "503 "))
                continue
            if "<h1>" in text:
                break
            logg.info(" %s =>%s\n%s", cmd, end, out)
            logg.info(" %s ->\n%s", cmd, text)
        cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9745_lamp_stack_opensuse15_php7(self) -> None:
        """ Check setup of Linux/Apache/Mariadb/Php" on Opensuse later than 15.x"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name = "lamp-stack-opensuse15"
        dockerfile = F"{name}.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        latest = LATEST or os.path.basename(python)
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        phpmyadmin = "phpMyAdmin" # opensuse/leap:15.1
        # phpmyadmin = "phpmyadmin"
        for attempt in range(8):
            time.sleep(1)
            cmd = "{curl} -o {testdir}/result.txt http://{container}/{phpmyadmin}/"
            out, err, end = output3(cmd.format(**locals()))
            if "503 Service Unavailable" in err:
                logg.info("[%i] ..... 503 %s", attempt, greps(err, "503 "))
                continue
            if "200 OK" in err:
                logg.info("[%i] ..... 200 %s", attempt, greps(err, "200 "))
                break
            logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{curl} -o {testdir}/result.txt http://{container}/{phpmyadmin}/"
        sh____(cmd.format(**locals()))
        result = open(F"{testdir}/result.txt").read()
        # logg.info("result:\n%s", result)
        self.assertTrue(greps(result, '<h1>.*>phpMyAdmin<'))
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9829_tomcat_alma9_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux, 
            THEN we can create an image with an tomcat service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "tomcat-alma9.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        nocache = NOCACHE
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {nocache} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(8):
            if not sx____(F"{docker} exec {testname} systemctl is-system-running # {attempt}."):
                break
            time.sleep(1)
            continue
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        # THEN
        for attempt in range(10):
            cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/"
            out, err, end = output3(cmd.format(**locals()))
            logg.info("(%s)=> %s\n%s", attempt, out, err)
            filename = F"{testdir}/{testname}.txt"
            if os.path.exists(filename):
                txt = open(filename).read()
                if txt.strip():
                    logg.info("result:\n%s", txt)
                    break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/"
        sh____(cmd.format(**locals()))
        try:
            cmd = "grep Quick.Start {testdir}/{testname}.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            if TODO:
                raise
            self.skipTest("TODO: tomcat server is not running????")
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9849_cntlm_alma9_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux, 
            THEN we can create an image with an cntlm service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        max4 = _curl_timeout4
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "cntlm-alma9.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active cntlm"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "http_proxy={container}:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        # cmd = "sleep 5; http_proxy=127.0.0.1:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        sh____(cmd.format(**locals()))
        cmd = "grep '<img alt=.Google.' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9909_sshd_alma9_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Almalinux, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if not os.path.exists("/usr/bin/sshpass"): self.skipTest("sshpass tool missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using preinstalled python3 for almalinux:9")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "sshd-alma9.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASS={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active sshd"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        for attempt in range(8):
            cmd = "{docker} exec {testname} ps axu"
            sx____(cmd.format(**locals()))
            cmd = "{docker} exec {testname} systemctl is-system-running"
            if not sx____(cmd.format(**locals())):
                break
            time.sleep(2)
        v=F"{_verbose}"
        try:
            allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
            cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
            sh____(cmd.format(**locals()))
            cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            if TODO:
                raise
            self.skipTest("TODO: ssh server is not running????")
        try:
            allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
            cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
            sh____(cmd.format(**locals()))
            cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
            sh____(cmd.format(**locals()))
        except subprocess.CalledProcessError as e:
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.log")
            if TODO:
                raise
            self.skipTest("TODO: ssh server is not running??????")
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
        # logg.warning("centos-sshd is incomplete without .socket support in systemctl.py")
        # logg.warning("the scp call will succeed only once - the sshd is dead after that")
    def test_9918_sshd_ubuntu18_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu 18, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists("/usr/bin/sshpass"): self.skipTest("sshpass tool missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "sshd-ubuntu18.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASS={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active ssh"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        cmd = "sleep 2; {docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        v=F"{_verbose}"
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
        cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
        cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9924_sshd_ubuntu24_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled Ubuntu 24, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists("/usr/bin/sshpass"): self.skipTest("sshpass tool missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "sshd-ubuntu24.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASS={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        for x in range(1,2,3):
            container = self.ip_container(testname)
            if not container:
                time.sleep(1)
                continue
        logg.fatal("container=%s", container)
        if not container:
            cmd = "{docker} cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
            sh____(cmd.format(**locals()))
            sh____(F"cat {testdir}/systemctl.debug.log")
        assert container
        # THEN
        for attempt in range(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active ssh"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        cmd = "sleep 2; {docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        v=F"{_verbose}"
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
        cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
        cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_9945_sshd_opensuse15_dockerfile(self) -> None:
        """ WHEN using a dockerfile for systemd-enabled OpenSuse 15, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        systemctl = tmp_systemctl3()
        if not systemctl: self.skipTest("no python3 systemctl.py")
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if not os.path.exists("/usr/bin/sshpass"): self.skipTest("sshpass tool missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if "python3" not in python: self.skipTest("using python3 for systemctl3.py")
        latest = LATEST or os.path.basename(python)
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "sshd-opensuse15.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASS={password} --tag {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}/{testname}:{latest}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in range(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active sshd"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        cmd = "sleep 2; {docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        v=F"{_verbose}"
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
        cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no"
        cmd = "sshpass -p {password} scp {v} {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}/{testname}:{latest} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}/{testname}:{latest}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
        # logg.warning("centos-sshd is incomplete without .socket support in systemctl.py")
        # logg.warning("the scp call will succeed only once - the sshd is dead after that")

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("--with", "--systemctl", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
                  help="systemctl.py file to be tested (%default)")
    _o.add_option("--src", "--systemctl3", metavar="FILE", dest="systemctl3_py", default=_systemctl3_py,
                  help="systemctl3.py file to be tested (%default)")
    _o.add_option("--python3", metavar="EXE", default=_python3,
                  help="use another python2 execution engine [%default]")
    _o.add_option("--python2", metavar="EXE", default=_python2,
                  help="use another python execution engine [%default]")
    _o.add_option("-p", "--python", metavar="EXE", default=_python,
                  help="override the python execution engine [%default]")
    _o.add_option("-C", "--chdir", metavar="DIR", default=NIX,
                  help="change to directory before execution [%default]")
    _o.add_option("-7", "--epel7", action="store_true", default=_epel7,
                  help="enable testbuilds requiring epel7 [%default]")
    _o.add_option("-m", "--mirror", metavar="EXE", default=_mirror,
                  help="override the docker_mirror.py [%default]")
    _o.add_option("-D", "--docker", metavar="EXE", default=_docker,
                  help="override docker exe or podman [%default]")
    _o.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    _o.add_option("-P", "--password", metavar="PASSWORD", default="",
                  help="use a fixed password for examples with auth [%default]")
    _o.add_option("--cache", action="store_true", default=False,
                  help="never run docker build --no-cache [%default]")
    _o.add_option("--local", action="store_true", default=LOCALPACKAGES,
                  help="only use local package mirrors [%default]")
    _o.add_option("--remote", action="store_true", default=REMOTEPACKAGES,
                  help="only use remote package mirrors [%default]")
    _o.add_option("--latest", metavar="ver", default=LATEST,
                  help="define latest instead of python [%default]")
    _o.add_option("--todo", action="store_true", default=False,
                  help="Show tests with a different expected result [%default]")
    _o.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
    _systemctl3_py = opt.systemctl3_py
    _python = opt.python
    _python2 = opt.python2
    _python3 = opt.python3
    _epel7 = opt.epel7
    _mirror = opt.mirror
    _docker = opt.docker
    _password = opt.password
    _verbose = "-v" if opt.verbose else ""
    LOCALPACKAGES = opt.local
    REMOTEPACKAGES = opt.remote
    LATEST = opt.latest
    if opt.cache:
        NOCACHE = NIX
    #
    if opt.chdir:
        os.chdir(opt.chdir)
        if _systemctl_py and not _systemctl_py.startswith("/"):
            _systemctl_py = ("../" * (opt.chdir.count("/") +1)) +  _systemctl_py
        if _systemctl3_py and not _systemctl3_py.startswith("/"):
            _systemctl3_py = ("../" * (opt.chdir.count("/") +1)) +  _systemctl3_py
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    # unittest.main()
    suite = unittest.TestSuite()
    if not args:
        args = ["test_*"]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if arg.endswith("/"):
                    arg = arg[:-1]
                if "*" not in arg:
                    arg += "*"
                if arg.startswith("_"):
                    arg = arg[1:]
                if len(arg) > 2 and arg[1] == "_":
                    arg = "test_" + arg[2:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    Runner = unittest.TextTestRunner
    if not logfile:
        done = Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
        for skipped in done.skipped:
            logg.info("skipped %s", str(skipped).replace("__main__", "").replace("testMethod=",""))
    else:
        Runner(logfile.stream, verbosity=opt.verbose).run(suite)
