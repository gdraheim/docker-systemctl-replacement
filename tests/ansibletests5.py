#! /usr/bin/env python3
# pylint: disable=line-too-long,too-many-lines,multiple-statements,unspecified-encoding,import-outside-toplevel,deprecated-module,invalid-name,bare-except
# pylint: disable=unused-argument,unused-variable,possibly-unused-variable,missing-function-docstring,missing-class-docstring,consider-using-f-string,logging-format-interpolation
""" Testcases for docker-systemctl-replacement functionality """

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.0.1144"

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
_systemctl_py = "files/docker/systemctl3.py"
_top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* ' | grep -v -e ' ps ' -e ' grep ' -e 'kworker/'"
_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"

SAVETO = "localhost:5000/systemctl"
IMAGES = "localhost:5000/systemctl/image"
CENTOS7 = "centos:7.7.1908"
CENTOS = "almalinux:9.1"
UBUNTU = "ubuntu:22.04"
OPENSUSE = "opensuse/leap:15.5"
NIX = ""

_curl = "curl"
_curl_timeout4 = "--max-time 4"
_docker = "docker"
DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"
PLAYBOOK_TOOL = "/usr/bin/ansible-playbook"
RUNTIME = "/tmp/run-"

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")
_password = ""

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

SYSTEMCTL=""
_src_systemctl_py = "../files/docker/systemctl3.py" # pylint: disable=invalid-name
_tmp_systemctl2_py = "tmp/systemctl2.py"  # pylint: disable=invalid-name
_tmp_systemctl3_py = "tmp/systemctl3.py"  # pylint: disable=invalid-name
STRIP_PYTHON3 = "../strip_python3/src/strip_python3.py"
STRIPPED3 = False

def tmp_systemctl3(stripped: Optional[bool]=None) -> str:
    stripped = stripped if stripped is not None else STRIPPED3
    if SYSTEMCTL:
        return SYSTEMCTL
    if stripped:
        tmp_systemctl2(_tmp_systemctl3_py)  # testing stripped python with a python3 interpreter
    else:
        if  (not os.path.exists(_tmp_systemctl3_py) or os.path.exists(F"{_tmp_systemctl3_py}i")
            or os.path.getmtime(_tmp_systemctl3_py) < os.path.getmtime(_src_systemctl_py)):
            tmpdir = os.path.dirname(_tmp_systemctl3_py)
            if "/" in _tmp_systemctl3_py and not os.path.isdir(tmpdir):
                os.makedirs(tmpdir)
            shutil.copy2(_src_systemctl_py, _tmp_systemctl3_py)
    return _systemctl_py

def tmp_systemctl2(systemctl2: str = NIX) -> str:
    systemctl2 = systemctl2 if systemctl2 else _tmp_systemctl2_py
    if  (not os.path.exists(_tmp_systemctl3_py) or not os.path.exists(F"{_tmp_systemctl3_py}i")
        or os.path.getmtime(_tmp_systemctl3_py) < os.path.getmtime(_src_systemctl_py)):
        sh____(F"{STRIP_PYTHON3} {_src_systemctl_py} -o {_tmp_systemctl3_py}")
        assert os.path.exists(F"{_tmp_systemctl3_py}i")
    return _systemctl_py

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
        extras = extras or ""
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
    def test_53487_centos7_postgres_playbook(self) -> None:
        """ WHEN using a playbook for systemd-enabled CentOS 7 and python2,
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        self.skipTest("TODO")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-postgres"
        playbook = "centos7-postgres-docker.yml"
        savename = docname(playbook)
        saveto = SAVETO
        images = saveto + "/postgres"
        psql = PSQL_TOOL
        runtime = RUNTIME
        password = self.newpassword()
        testpass = "Pass." + password
        # WHEN
        users = "-e postgres_testuser=testuser_11 -e postgres_testpass={testpass} -e postgress_password={password}"
        cmd = "ansible-playbook {playbook} " + users + " -e tagrepo={saveto} -e tagversion={testname} -v"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
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
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_58407_centos_elasticsearch_setup(self) -> None:
        """ Check setup of ElasticSearch on CentOs via ansible docker connection"""
        # note that the test runs with a non-root 'ansible' user to reflect
        # a real deployment scenario using ansible in the non-docker world.
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        self.skipTest("TODO")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        setupfile = "centos7-elasticsearch-setup.yml"
        savename = docname(setupfile)
        basename = CENTOS7
        saveto = SAVETO
        images = IMAGES
        image = self.local_image(basename)
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {image} sleep infinity"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo sslverify=false >> /etc/yum.conf'" # almalinux https
        sh____(cmd.format(**locals()))
        prepare = " --limit {testname} -e ansible_user=root"
        cmd = "ansible-playbook -i centos7-elasticsearch-setup.ini ansible-deployment-user.yml -vv" + prepare
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} grep __version__ /usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "ansible-playbook -i centos7-elasticsearch-setup.ini centos7-elasticsearch-setup.yml -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} grep __version__ /usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD /usr/bin/systemctl' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in range(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        for attempt in range(3):
            cmd = "{docker} exec {testname} systemctl is-active elasticsearch"
            out, end = output2(cmd.format(**locals()))
            logg.info("elasticsearch {out}".format(**locals()))
            if out.strip() == "active": break
            time.sleep(1)
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    @unittest.expectedFailure # can not find role in Ansible 2.9
    def test_58607_centos_elasticsearch_image(self) -> None:
        """ Check setup of ElasticSearch on CentOs via ansible playbook image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        self.skipTest("TODO")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch-image.yml"
        basename = CENTOS7  # "centos:7.3.1611"
        tagrepo = SAVETO
        tagname = "elasticsearch"
        #
        cmd = "ansible-playbook {playbook} -e base_image='{basename}' -e tagrepo={tagrepo} -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {tagrepo}/{tagname}:latest"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in range(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        self.rm_testdir()
    def test_58707_centos_elasticsearch_deploy(self) -> None:
        """ Check setup of ElasticSearch on CentOs via ansible docker connection"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        self.skipTest("TODO")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch-deploy.yml"
        savename = docname(playbook)
        basename = CENTOS7
        saveto = SAVETO
        images = IMAGES
        image = self.local_image(basename)
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {image} sleep infinity"
        sh____(cmd.format(**locals()))
        prepare = " --limit {testname} -e ansible_user=root"
        cmd = "ansible-playbook {playbook} -e container1={testname} -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD /usr/bin/systemctl' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in range(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_58807_centos_elasticsearch_docker(self) -> None:
        """ Check setup of ElasticSearch on CentOs via ansible playbook image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        self.skipTest("TODO")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch-docker.yml"
        basename = CENTOS7  # "centos:7.3.1611"
        tagrepo = SAVETO
        tagname = "elasticsearch"
        #
        cmd = "ansible-playbook {playbook} -e base_image='{basename}' -e tagrepo={tagrepo} -e tagversion={testname} -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {tagrepo}/{tagname}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in range(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        self.rm_testdir()
    def test_58907_centos_elasticsearch_docker_playbook(self) -> None:
        """ Check setup of ElasticSearch on CentOs via ansible playbook image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        self.skipTest("TODO")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch.docker.yml"
        basename = CENTOS7  # "centos:7.3.1611"
        tagrepo = SAVETO
        tagname = "elasticsearch"
        #
        cmd = "ansible-playbook {playbook} -e base_image='{basename}' -e tagrepo={tagrepo} -e tagversion={testname} -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {tagrepo}/{tagname}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in range(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        self.rm_testdir()

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
                  help="systemctl.py file to be tested (%default)")
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
    _o.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    _python2 = opt.python2
    _python3 = opt.python3
    _epel7 = opt.epel7
    _mirror = opt.mirror
    _docker = opt.docker
    _password = opt.password
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
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    #
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = ["test_*"]
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
            Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
        Runner(logfile.stream, verbosity=opt.verbose).run(suite)
