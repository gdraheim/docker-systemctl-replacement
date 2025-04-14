#! /usr/bin/env python3
""" Testcases for docker-systemctl-replacement functionality """

# pylint: disable=line-too-long,too-many-lines,too-many-locals,too-many-statements,too-many-branches,too-many-arguments,too-many-positional-arguments,too-many-return-statements,too-many-nested-blocks,too-many-public-methods
# pylint: disable=bare-except,broad-exception-caught,pointless-statement,multiple-statements,f-string-without-interpolation,import-outside-toplevel,no-else-return
# pylint: disable=missing-function-docstring,unused-variable,unused-argument,unspecified-encoding,redefined-outer-name,using-constant-test,invalid-name
# pylint: disable=fixme,consider-using-with,consider-using-get,condition-evals-to-constant,chained-comparison
__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.0.1151"

from typing import List, Tuple, Iterator, Union, Optional, TextIO, Mapping

import subprocess
import os
import os.path
import time
import datetime
import unittest
import shutil
import inspect
import string
import random
import logging
import re
import sys
from fnmatch import fnmatchcase as fnmatch
import json

string_types = (str, bytes)

logg = logging.getLogger("TESTING")
_sed = "sed"
_docker = "docker"
_python = "/usr/bin/python3"
_python2 = "/usr/bin/python"
_systemctl_py = "src/systemctl3.py"
_strip_python3_src = "../strip_python3/src"
SKIP = True
TODO = False
KEEP = 0
LONGER = 2
KILLWAIT = 20

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

SAVETO = "localhost:5000/systemctl"
IMAGES = "localhost:5000/systemctl/testing"
IMAGE = ""
LOCAL = 0
CENTOS = "almalinux:9.4"
UBUNTU = "ubuntu:24.04"
OPENSUSE = "opensuse/leap:15.6"
IMAGEDEF = OPENSUSE # was CENTOS but almalinux does not have python2 anymore
SOMETIME = ""

QUICK = "-c MAXTIMEOUT=9"
DOCKER_SOCKET = "/var/run/docker.sock"

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")

realpath = os.path.realpath

def package_tool(image: str, checks: bool = False) -> str:
    if "opensuse" in image:
        if not checks:
            # --gpgcheck-strict / --no-gpg-checks
            # --gpgcheck-allow-unsigned( --gpgcheck-allow-unsigned-repo --gpgcheck-allow-unsigned-package)
            # return "zypper --gpgcheck-allow-unsigned-repo"
            return "zypper"
        return "zypper"
    if "ubuntu" in image:
        # sources.list:
        # deb [ allow-insecure=yes ] # disables but keeps warning
        # deb [ trusted=yes ] # disables GPG
        # --allow-unauthenticated
        # -o APT::Get::AllowUnauthenticated=true
        # -o Acquire::Check-Valid-Until=false
        # -o APT::Ignore::gpg-pubkey
        # -o Acquire::AllowInsecureRepositories=true
        # -o Acquire::AllowDowngradeToInsecureRepositories=true
        if not checks:
            return "apt-get -o Acquire::AllowInsecureRepositories=true"
        return "apt-get"
    if not checks:
        return "yum --setopt=repo_gpgcheck=false"
    return "yum"
def refresh_tool(image: str, checks: bool = False) -> str:
    # https://github.com/openSUSE/docker-containers/issues/64
    #  {package} rr oss-update"
    #  {package} ar -f http://download.opensuse.org/update/leap/42.3/oss/openSUSE:Leap:42.3:Update.repo"
    if "opensuse:42.3" in image:
        cmds = [
            "zypper mr --no-gpgcheck oss-update",
            "zypper refresh"]
        return "bash -c '%s'" % (" && ".join(cmds))  # pylint: disable=consider-using-f-string
    if "opensuse/leap:15." in image:
        cmds = [
            "zypper mr --no-gpgcheck --all",
            "zypper refresh"]
        return "bash -c '%s'" % (" && ".join(cmds))  # pylint: disable=consider-using-f-string
    if "opensuse" in image:
        return "zypper refresh"
    if "ubuntu" in image:
        if not checks:
            return "apt-get -o Acquire::AllowInsecureRepositories=true update"
        return "apt-get update"
    if "almalinux" in image:
        cmds = ["echo sslverify=false >> /etc/yum.conf"]
        return "bash -c '%s'" % (" && ".join(cmds))  # pylint: disable=consider-using-f-string
    return "true"
def python_package(python: str, image: Optional[str] = None) -> str:
    package = os.path.basename(python)
    if "python2" in package:
        if image and "centos:8" in image:
            return package
        if image and "almalinux:9" in image:
            return package
        if image and "ubuntu:2" in image:
            return package
        return package.replace("python2", "python")
    return package.replace(".", "") # python3.11 => python311

def q_str(part: Union[str, int, None]) -> str:
    if part is None:
        return ""
    if isinstance(part, int):
        return str(part)
    return "'%s'" % part  # pylint: disable=consider-using-f-string
def decodes(text: Union[str, bytes, None]) -> str:
    if text is None: return ""
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def sh____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd: Union[str, List[str]], shell: bool = True) -> int:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> str:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out)
def output2(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> Tuple[str, int]:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd: Union[str, List[str]], shell: bool = True, env: Optional[Mapping[str, str]] = None) -> Tuple[str, str, int]:
    if isinstance(cmd, string_types):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join([q_str(item) for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode

def reads(filename: str) -> str:
    return decodes(open(filename, "rb").read())
def _lines4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    if isinstance(textlines, string_types):
        linelist = decodes(textlines).split("\n")
        if len(linelist) and linelist[-1] == "":
            linelist = linelist[:-1]
        return linelist
    return list(textlines)
def lines4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    linelist = []
    for line in _lines4(textlines):
        linelist.append(line.rstrip())
    return linelist
def sorted4(textlines: Union[str, List[str], Iterator[str], TextIO]) -> List[str]:
    return list(sorted(_lines4(textlines)))
def each_grep(pattern: str, textlines: Union[str, List[str], TextIO]) -> Iterator[str]:
    for line in _lines4(textlines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def grep(pattern: str, textlines: Union[str, List[str], TextIO]) -> List[str]:
    return list(each_grep(pattern, textlines))
def greps(textlines: Union[str, List[str], TextIO], pattern: str) -> List[str]:
    return list(each_grep(pattern, textlines))
def running(textlines: Union[str, List[str]]) -> List[str]:
    return list(each_non_runuser(each_non_defunct(textlines)))
def each_non_defunct(textlines: Union[str, List[str], Iterator[str]]) -> Iterator[str]:
    for line in _lines4(textlines):
        if '<defunct>' in line:
            continue
        yield line
def each_non_runuser(textlines: Union[str, List[str], Iterator[str]]) -> Iterator[str]:
    for line in _lines4(textlines):
        if 'runuser -u' in line:
            continue
        yield line
def each_clean(textlines: Union[str, List[str]]) -> Iterator[str]:
    for line in _lines4(textlines):
        if '<defunct>' in line:
            continue
        if 'runuser -u' in line:
            continue
        if 'ps -eo pid,' in line:
            continue
        yield line
def clean(textlines: Union[str, List[str]]) -> str:
    return " " + "\n ".join(each_clean(textlines))

def i2(part: str, indent: str = "  ") -> str:
    if isinstance(part, string_types):
        if "\n" in part.strip():
            lines = part.strip().split("\n")
            text = indent
            newline = "\n" + indent
            text += newline.join(lines)
            if part.endswith("\n"):
                text += "\n"
            return text
    return part
def o22(part: str, maxlines: int =22) -> str:
    return only22(part, maxlines=maxlines)
def oi22(part: str, maxlines: int = 22) -> str:
    return only22(part, indent="  ", maxlines=maxlines)
def only22(part: str, indent: str = "", maxlines: int = 22) -> str:
    if isinstance(part, string_types):
        if "\n" in part.strip():
            lines = part.strip().split("\n")
            if len(lines) <= maxlines:
                return indent+part.replace("\n", "\n"+indent)
            skipped = len(lines) - maxlines + 3
            lastlines = maxlines - 5 - 3
            real = lines[:5] + ["...", F"... ({skipped} lines skipped)", "..."] + lines[-lastlines:]
            text = indent
            newline = "\n" + indent
            text += newline.join(real)
            if part.endswith("\n"):
                text += "\n"
            return text
    if isinstance(part, string_types):
        if len(part) <= maxlines:
            return part
        return part[:5] + "..." + part[-14:]
    if isinstance(part, list):
        if len(part) <= maxlines:
            return part
        skipped = len(part) - maxlines + 3
        lastlines = maxlines - 5 - 3
        return part[:5] + ["...", F"... ({skipped} lines skipped)", "..."] + part[-lastlines:]
    return part

def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
    logg.info("::: made %s", filename)
def shell_file(filename: str, content: str) -> None:
    text_file(filename, content)
    os.chmod(filename, 0o775)
def copy_file(filename: str, target: str) -> None:
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename: str, target: str) -> None:
    copy_file(filename, target)
    os.chmod(target, 0o755)
def get_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back  # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]
# def os_path(root: Optional[str], path: Optional[str]) -> Optional[str]:
def os_path(root: Optional[str], path: str) -> str:
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(root, path)
def os_getlogin() -> str:
    """ NOT using os.getlogin() """
    import pwd
    return pwd.getpwuid(os.geteuid()).pw_name
def os_remove(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
def get_runtime_dir() -> str:
    explicit = os.environ.get("XDG_RUNTIME_DIR", "")
    if explicit: return explicit
    user = os_getlogin()
    return "/tmp/run-"+user
def docname(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

SYSTEMCTL_DEBUG_LOG = "{LOG}/systemctl.debug.log"
SYSTEMCTL_EXTRA_LOG = "{LOG}/systemctl.log"

############ local mirror helpers #############
def ip_container(name: str) -> str:
    docker = _docker
    values = output(F"{docker} inspect {name}")
    values = json.loads(values)
    if not values or "NetworkSettings" not in values[0]:
        logg.critical(" %s inspect %s => %s ", docker, name, values)
    return values[0]["NetworkSettings"]["IPAddress"] # type: ignore
def detect_local_system() -> str:
    """ checks the controller host (a real machine / your laptop)
        and returns a matching image name for it (docker style) """
    docker = _docker
    mirror = _mirror
    cmd = F"{mirror} detect"
    out = output(cmd)
    return decodes(out).strip()

############ the real testsuite ##############

class DockerSystemctlReplacementTest(unittest.TestCase):
    """ testcases for systemctl.py """
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str] = None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self) -> int:
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 4000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname: Optional[str] = None, keep: bool = False) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir) and not keep:
            shutil.rmtree(newdir)
        if not os.path.isdir(newdir):
            os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            if not KEEP:
                shutil.rmtree(newdir)
        return newdir
    def rm_docker(self, testname: str) -> None:
        docker = _docker
        if not KEEP:
            sx____(F"{docker} stop -t 6 {testname}")
            sx____(F"{docker} rm -f {testname}")
    def root(self, testdir: str, real: bool = False) -> str:
        if real: return "/"
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def newpassword(self) -> str:
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
    def ip_container(self, name: str) -> str:
        values = output("docker inspect "+name)
        values = json.loads(values)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"] # type: ignore
    def local_image(self, image: str) -> str:
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if os.environ.get("NONLOCAL", ""):
            return image
        add_hosts = self.start_mirror(image)
        if add_hosts:
            return F"{add_hosts} {image}"
        return image
    def start_mirror(self, image: str) -> str:
        docker = _docker
        mirror = _mirror
        local = " --localmirrors" if LOCAL else ""
        cmd = F"{mirror} start {image} --add-hosts{local}"
        out = output(cmd)
        return decodes(out).strip()
    def drop_container(self, name: str) -> None:
        docker = _docker
        sx____(F"{docker} rm --force {name}")
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
        docker = _docker
        self.drop_container(name)
        local_image = self.local_image(image)
        cmd = F"{docker} run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd)
        print(F"                 # {local_image}")
        print(F"  {docker} exec -it {name} bash")
    def begin(self) -> str:
        self._started = time.monotonic() # pylint: disable=attribute-defined-outside-init
        logg.info("[[%s]]", datetime.datetime.fromtimestamp(self._started).strftime("%H:%M:%S"))
        return "-vv"
    def end(self, maximum: int = 99) -> None:
        runtime = time.monotonic() - self._started
        self.assertLess(runtime, maximum * LONGER)
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    #
    def test_81000_systemctl_py_inside_container(self) -> None:
        """ check that we can run systemctl.py inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        if _python.endswith("python3") and "centos:7" in image:
            if SKIP: self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} sed -i 's:/usr/bin/env python.*:/usr/bin/env {python}:' /usr/bin/systemctl"
        sh____(cmd)
        cmd = F"{docker} exec {testname} systemctl --version"
        sh____(cmd)
        out = output(cmd)
        logg.info("\n>\n%s", out)
        #
        self.rm_docker(testname)
        self.rm_testdir()
        #
        self.assertTrue(greps(out, "systemctl.py"))
    def test_85000_systemctl_py_inside_container(self) -> None:
        """ check that we can run systemctl.py inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        image = self.local_image(IMAGE or IMAGEDEF)
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} {refresh}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c 'ls -l /usr/bin/{python} || {package} install -y {python_x}'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} bash -c '{package} install -y {python_x}-pip {python_x}-setuptools {python_x}-wheel make'"
        sx____(cmd)
        cmd = F"{docker} exec {testname} mkdir /setup"
        sh____(cmd)
        cmd = F"{docker} cp src {testname}:/setup/"
        sh____(cmd)
        cmd = F"{docker} cp Makefile {testname}:/setup/"
        sh____(cmd)
        cmd = F"{docker} cp README.md {testname}:/setup/"
        sh____(cmd)
        cmd = F"{docker} cp pyproject.toml {testname}:/setup/"
        sh____(cmd)
        cmd = F"{docker} cp tests {testname}:/"
        sh____(cmd)
        cmd = F"{docker} cp {_strip_python3_src} {testname}:/strip"
        sh____(cmd)
        cmd = F"{docker} exec {testname} make -C setup ins PYTHON3={python} PYTHON39={python} STRIP_PYTHON3=/strip/strip_python3.py"
        sh____(cmd)
        out = output(F"{docker} exec {testname} make -C setup show PYTHON3={python} PYTHON39={python}")
        logg.info("make show\n%s", out)
        self.assertTrue(greps(out, F"Location:.*/{python}/site-packages"))
        self.assertTrue(greps(out, "journalctl3.py"))
        self.assertTrue(greps(out, "systemctl3.py"))
        self.assertTrue(greps(out, "systemctl.py"))
        self.assertTrue(greps(out, "systemctl-stubs/__init__.pyi"))
        self.assertTrue(greps(out, "bin/systemctl.py"))
        self.assertTrue(greps(out, "bin/systemctl3"))
        self.assertTrue(greps(out, "bin/journalctl3"))
        #
        out = output(F"{docker} exec {testname} bash -c 'PATH=\\$PATH:~/.local/bin;systemctl3 --version'")
        logg.info("systemctl3 --version\n%s", out)
        self.assertTrue(greps(out, "via systemctl.py"))
        #
        out = output(F"{docker} commit {testname} {images}:{testname}")
        self.rm_docker(testname)
        self.rm_testdir()
    def test_85010_mypy_inside_container(self) -> None:
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        images = IMAGES
        imagedef = IMAGE or IMAGEDEF
        image = self.local_image(F"{images}:test_85000")
        testname = self.testname()
        testdir = self.testdir()
        docker = _docker
        package = package_tool(image)
        refresh = refresh_tool(image)
        python = os.path.basename(_python)
        python_x = python_package(_python, image)
        systemctl_py = _systemctl_py
        sometime = SOMETIME or 188
        #
        cmd = F"{docker} rm --force {testname}"
        sx____(cmd)
        cmd = F"{docker} run --detach --name={testname} {image} sleep {sometime}"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c '{package} install -y {python_x}-mypy'"
        sx____(cmd)
        out = output(F"{docker} exec {testname} {python} -m mypy --version")
        logg.info("{python3} -m mypy --version\n%s", out)
        if not greps(out, "mypy 1"):
            self.skipTest(F"no mypy available - {imagedef} - {python}")
        cmd = F"{docker} exec {testname} bash -c '{{ echo \"import systemctl\"; echo \"systemctl.main()\"; }} > testsystemctl.py'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c '{python} -m mypy --strict testsystemctl.py'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c '{{ echo \"import systemctl3\"; echo \"systemctl3.main()\"; }} > testsystemctl3.py'"
        sh____(cmd)
        cmd = F"{docker} exec {testname} bash -c '{python} -m mypy --strict testsystemctl3.py --follow-imports=silent --disable-error-code=import-untyped'"
        sh____(cmd)
        self.rm_docker(testname)
        self.rm_testdir()
        #


    def test_89999_drop_local_mirrors(self) -> None:
        """ a helper when using images from https://github.com/gdraheim/docker-mirror-packages-repo"
            which create containers according to self.local_image(IMAGE) """
        docker = _docker
        containers = output(F"{docker} ps -a")
        for line in lines4(containers):
            found = re.search("\\b(opensuse-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____(F"{docker} rm -f {container}")
            found = re.search("\\b(centos-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____(F"{docker} rm -f {container}")
            found = re.search("\\b(ubuntu-repo-\\d[.\\d]*)\\b", line)
            if found:
                container = found.group(1)
                logg.info("     ---> drop %s", container)
                sx____(F"{docker} rm -f {container}")

if __name__ == "__main__":
    from optparse import OptionParser  # pylint: disable=deprecated-module
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
                  help="systemctl.py file to be tested (%default)")
    _o.add_option("-D", "--docker", metavar="EXE", default=_docker,
                  help="use another docker container tool [%default]")
    _o.add_option("-p", "--python", metavar="EXE", default=_python,
                  help="use another python execution engine [%default]")
    _o.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    _o.add_option("--keep", action="count", default=KEEP,
                  help="keep tempdir and other data after testcase [%default]")
    _o.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    _o.add_option("--sometime", metavar="SECONDS", default=SOMETIME,
                  help="SOMETIME=%default (use 666)")
    _o.add_option("--todo", action="store_true", default=TODO,
                  help="enable TODO outtakes [%default])")
    _o.add_option("-f", "--force", action="store_true", default=False,
                  help="enable the skipped IMAGE and PYTHON versions [%default])")
    _o.add_option("-C", "--chdir", metavar="PATH", default="",
                  help="change directory before running tests {%default}")
    _o.add_option("--local", "--localmirrors", action="count", default=LOCAL,
                  help="fail if local mirror was not found [%default]")
    _o.add_option("--opensuse", metavar="NAME", default=OPENSUSE,
                  help="OPENSUSE=%default")
    _o.add_option("--ubuntu", metavar="NAME", default=UBUNTU,
                  help="UBUNTU=%default")
    _o.add_option("--centos", metavar="NAME", default=CENTOS,
                  help="CENTOS=%default")
    _o.add_option("--image", metavar="NAME", default=IMAGE,
                  help="IMAGE=%default (or CENTOS)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    SKIP = not opt.force
    TODO = opt.todo
    KEEP = opt.keep
    #
    LOCAL = int(opt.local)
    OPENSUSE = opt.opensuse
    UBUNTU = opt.ubuntu
    CENTOS = opt.centos
    IMAGE = opt.image
    if ":" not in CENTOS:
        CENTOS = "centos:" + CENTOS
    if ":" not in OPENSUSE and "42" in OPENSUSE:
        OPENSUSE = "opensuse:" + OPENSUSE
    if ":" not in OPENSUSE:
        OPENSUSE = "opensuse/leap:" + OPENSUSE
    if ":" not in UBUNTU:
        UBUNTU = "ubuntu:" + UBUNTU
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    _docker = opt.docker
    #
    if opt.chdir:
        os.chdir(opt.chdir)
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
    if not args: args = ["test_*"]
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
                if len(arg) > 2 and arg[1] == "_":
                    arg = "test" + arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    if not logfile:
        if xmlresults:
            import xmlrunner # type: ignore[import-error] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore
    if not testresult.wasSuccessful():
        sys.exit(1)
