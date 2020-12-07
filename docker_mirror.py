#! /usr/bin/python3
# from __future__ import print_function

__copyright__ = "(C) 2020 Guido Draheim"
__contact__ = "https://github.com/gdraheim/docker-mirror-packages-repo"
__license__ = "CC0 Creative Commons Zero (Public Domain)"
__version__ = "1.6.2491"

from collections import OrderedDict, namedtuple
import os.path
import sys
import re
import json
import logging
import subprocess

if sys.version[0] != '2':
   xrange = range
   basestring = str

logg = logging.getLogger("mirror")
DOCKER = "docker"
ADDHOSTS = False

UBUNTU_VERSIONS = { "12.04": "precise", "14.04": "trusty", "16.04": "xenial", "17.10": "artful",
                    "18.04": "bionic", "18.10": "cosmic", "19.04": "disco", "19.10": "eoan",
                    "20.04": "focal", "20.10": "groovy" }
CENTOS_VERSIONS = { "7.0": "7.0.1406", "7.1": "7.1.1503", "7.2": "7.2.1511", "7.3": "7.3.1611",
                    "7.4": "7.4.1708", "7.5": "7.5.1804", "7.6": "7.6.1810", "7.7": "7.7.1908",
                    "8.0": "8.0.1905", "8.1": "8.1.1911", "8.2": "8.2.2004" }

def decodes(text):
    if text is None: return None
    return decodes_(text)
def decodes_(text):
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try: 
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def output3(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.debug("run: %s", cmd)
    else:
        logg.debug("run: %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return decodes_(out), decodes_(err), run.returncode

class DockerMirror:
    def __init__(self, cname, image, hosts):
        self.cname = cname # name of running container
        self.image = image # image used to start the container
        self.hosts = hosts # domain names for the container

class DockerMirrorPackagesRepo:
    def __init__(self, image = None):
        self._image = image
    def image(self):
        """ when a function has no image argument then a default
            is used - either explict from _init_ or local system. """
        if self._image:
            return self._image
        return self.host_system_image()
    def host_system_image(self):
        """ returns the docker image name which corresponds to the 
            operating system distribution of the host system. This
            image name is the key for the other mirror functions. """
        distro, version = "", ""
        if os.path.exists("/etc/os-release"):
            # rhel:7.4 # VERSION="7.4 (Maipo)" ID="rhel" VERSION_ID="7.4"
            # centos:7.3  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # centos:7.4  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # centos:7.7.1908  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # opensuse:42.3 # VERSION="42.3" ID=opensuse VERSION_ID="42.3"
            # opensuse/leap:15.0 # VERSION="15.0" ID="opensuse-leap" VERSION_ID="15.0"
            # ubuntu:16.04 # VERSION="16.04.3 LTS (Xenial Xerus)" ID=ubuntu VERSION_ID="16.04"
            # ubuntu:18.04 # VERSION="18.04.1 LTS (Bionic Beaver)" ID=ubuntu VERSION_ID="18.04"
            for line in open("/etc/os-release"):
                key, value = "", ""
                m = re.match('^([_\\w]+)=([^"].*).*', line.strip())
                if m:
                    key, value = m.group(1), m.group(2)
                m = re.match('^([_\\w]+)="([^"]*)".*', line.strip())
                if m:
                    key, value = m.group(1), m.group(2)
                # logg.debug("%s => '%s' '%s'", line.strip(), key, value)
                if key in ["ID"]:
                    distro = value.replace("-","/")
                if key in ["VERSION_ID"]:
                    version = value
        if os.path.exists("/etc/redhat-release"):
            for line in open("/etc/redhat-release"):
                m = re.search("release (\\d+[.]\\d+).*", line)
                if m:
                    distro = "rhel"
                    version = m.group(1)
        if os.path.exists("/etc/centos-release"):
            # CentOS Linux release 7.5.1804 (Core)
            for line in open("/etc/centos-release"):
                m = re.search("release (\\d+[.]\\d+).*", line)
                if m:
                    distro = "centos"
                    version = m.group(1)
        logg.info(":%s:%s host system image detected", distro, version)
        if distro and version:
            return "%s:%s" % (distro, version)
        return ""
    def get_docker_mirror(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            return self.get_centos_docker_mirror(version)
        if image.startswith("opensuse/leap:"):
            version = image[len("opensuse/leap:"):]
            return self.get_opensuse_docker_mirror(version)
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            return self.get_opensuse_docker_mirror(version)
        if image.startswith("ubuntu:"):
            version = image[len("ubuntu:"):]
            return self.get_ubuntu_docker_mirror(version)
        return None
    def get_docker_mirrors(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        mirrors = []
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            mirrors = self.get_centos_docker_mirrors(version)
        if image.startswith("opensuse/leap:"):
            version = image[len("opensuse/leap:"):]
            mirrors = self.get_opensuse_docker_mirrors(version)
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            mirrors = self.get_opensuse_docker_mirrors(version)
        if image.startswith("ubuntu:"):
            version = image[len("ubuntu:"):]
            mirrors = self.get_ubuntu_docker_mirrors(version)
        logg.info(" %s -> %s", image, " ".join([mirror.cname for mirror in mirrors]))
        return mirrors
    def get_ubuntu_docker_mirror(self, ver):
        """ detects a local ubuntu mirror or starts a local
            docker container with a ubunut repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000/mirror-packages"
        rep = "ubuntu-repo"
        if "." not in ver:
            latest = ""
            for version in UBUNTU_VERSIONS:
                codename = UBUNTU_VERSIONS[version]
                if codename.startswith(ver):
                    if version > latest:
                       latest = version
                elif version.startswith(ver):
                    if version > latest:
                       latest = version
            ver = latest or ver
        return self.docker_mirror(rmi, rep, ver, "archive.ubuntu.com", "security.ubuntu.com")
    def get_ubuntu_docker_mirrors(self, ver):
        main = self.get_ubuntu_docker_mirror(ver)
        return [ main ]
    def get_centos_docker_mirror(self, ver):
        """ detects a local centos mirror or starts a local
            docker container with a centos repo mirror. It
            will return the setting for extrahosts"""
        rmi = "localhost:5000/mirror-packages"
        rep = "centos-repo"
        if "." not in ver:
            latest = ""
            for version in CENTOS_VERSIONS:
               if version.startswith(ver):
                   fullversion = CENTOS_VERSIONS[version]
                   if fullversion > latest:
                       latest = fullversion
            ver = latest or ver
        if ver in CENTOS_VERSIONS:
           ver = CENTOS_VERSIONS[ver]
        return self.docker_mirror(rmi, rep, ver, "mirrorlist.centos.org")
    def get_centos_docker_mirrors(self, ver):
        main = self.get_centos_docker_mirror(ver)
        return [ main ]
    def get_opensuse_docker_mirror(self, ver):
        """ detects a local opensuse mirror or starts a local
            docker container with a centos repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000/mirror-packages"
        rep = "opensuse-repo"
        return self.docker_mirror(rmi, rep, ver, "download.opensuse.org")
    def get_opensuse_docker_mirrors(self, ver):
        main = self.get_opensuse_docker_mirror(ver)
        return [ main ]
    def docker_mirror(self, rmi, rep, ver, *hosts):
        image = "{rmi}/{rep}:{ver}".format(**locals())
        cname = "{rep}-{ver}".format(**locals())
        return DockerMirror(cname, image, list(hosts))
    #
    def ip_container(self, name):
        docker = DOCKER
        cmd = "{docker} inspect {name}"
        out, err, rc = output3(cmd.format(**locals()))
        if rc:
            logg.info("%s : %s", cmd, err)
            logg.debug("no address for %s", name)
            return None
        values = json.loads(out)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        addr =  values[0]["NetworkSettings"]["IPAddress"]
        assert isinstance(addr, basestring)
        logg.debug("address %s for %s", addr, name)
        return addr
    def start_containers(self, image):
        mirrors = self.get_docker_mirrors(image)
        done = {}
        for mirror in mirrors:
            addr = self.start_container(mirror.image, mirror.cname)
            done[mirror.cname] = addr
        return done
    def start_container(self, image, container):
        docker = DOCKER
        cmd = "{docker} inspect {image}"
        out, err, ok = output3(cmd.format(**locals()))
        image_found = json.loads(out)
        if not image_found:
            logg.info("image not found: %s", image)
            return None
        cmd = "{docker} inspect {container}"
        out, err, rc = output3(cmd.format(**locals()))
        container_found = json.loads(out)
        if not rc and container_found:
            container_status = container_found[0]["State"]["Status"]
            logg.info("::: %s -> %s", container, container_status)
            latest_image_id = image_found[0]["Id"]
            container_image_id = container_found[0]["Image"]
            if latest_image_id != container_image_id or container_status not in ["running"]:
                cmd = "{docker} rm --force {container}"
                out, err, rc = output3(cmd.format(**locals()))
                if rc:
                    logg.debug("%s : %s", cmd, err)
                container_found = []
        if not container_found:
            cmd = "{docker} run --rm=true --detach --name {container} {image}"
            out, err, rc = output3(cmd.format(**locals()))
            if rc:
                logg.error("%s : %s", cmd, err)
        addr = self.ip_container(container)
        logg.info("%s : %s", container, addr)
        return addr
    def stop_containers(self, image):
        mirrors = self.get_docker_mirrors(image)
        done = {}
        for mirror in mirrors:
            info = self.stop_container(mirror.image, mirror.cname)
            done[mirror.cname] = info
        return done
    def stop_container(self, image, container):
        docker = DOCKER
        cmd = "{docker} inspect {container}"
        out, err, rc = output3(cmd.format(**locals()))
        container_found = json.loads(out)
        if not rc and container_found:
            cmd = "{docker} rm --force {container}"
            out, err, ok = output3(cmd.format(**locals()))
            status = container_found[0].get("State", {})
            started = status.get("StartedAt", "(was not started)")
            assert isinstance(started, basestring)
            return started
        return "(did not exist)"
    def info_containers(self, image):
        mirrors = self.get_docker_mirrors(image)
        done = {}
        for mirror in mirrors:
            info = self.info_container(mirror.image, mirror.cname)
            done[mirror.cname] = info
        return done
    def info_container(self, image, container):
        addr = self.ip_container(container)
        return addr
    def get_containers(self, image):
        mirrors = self.get_docker_mirrors(image)
        done = []
        for mirror in mirrors:
            done.append(mirror.cname)
        return done
    def inspect_containers(self, image):
        mirrors= self.get_docker_mirrors(image)
        docker = DOCKER
        done = OrderedDict()
        for mirror in mirrors:
            addr = self.ip_container(mirror.cname)
            done[mirror.cname] = addr
        return done
    #
    def add_hosts(self, image, done = {}):
        mirrors = self.get_docker_mirrors(image)
        args = []
        for mirror in mirrors:
            name = mirror.cname
            if name in done:
                addr = done[name]
                if addr:
                    for host in mirror.hosts:
                        args += ["--add-host", "%s:%s" % (host, addr) ]
        return args
    def helps(self):
        return """helper to start/stop mirror-container with the packages-repo
        help             this help screen
        image|detect     the image name matching the local system
        facts [image]    the json data used to start or stop the containers
        start [image]    starts the container(s) with the mirror-packages-repo
        stop  [image]    stops the containers(s) with the mirror-packages-repo
        addhosts [image] shows the --add-hosts string for the client container
"""
    def detect(self):
        image = self.host_system_image()
        return image
    def repo(self, image = None):
        image = image or self.image()
        mirrors = self.get_docker_mirrors(image)
        for mirror in mirrors:
            return mirror.image
        return ""
    def repos(self, image = None):
        image = image or self.image()
        mirrors = self.get_docker_mirrors(image)
        shown = ""
        for mirror in mirrors:
            shown = mirror.image + "\n"
        return ""
    def facts(self, image = None):
        image = image or self.image()
        mirrors = self.get_docker_mirrors(image)
        data = {}
        for mirror in mirrors:
            data[mirror.cname] = { "image": mirror.image, "name": mirror.cname,
                                   "hosts": mirror.hosts }
        return json.dumps(data, indent=2)
    def starts(self, image = None):
        image = image or self.image()
        done = self.start_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, done))
        else:
            return json.dumps(done, indent=2)
    def stops(self, image = None):
        image = image or self.image()
        done = self.stop_containers(image)
        if ADDHOSTS:
            names = sorted(done.keys())
            return " ".join(names)
        else:
            return json.dumps(done, indent=2)
    def infos(self, image = None):
        image = image or self.image()
        done = self.info_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, done))
        else:
            return json.dumps(done, indent=2)
    def containers(self, image = None):
        image = image or self.image()
        done = self.get_containers(image)
        if ADDHOSTS:
            return " ".join(done)
        else:
            return json.dumps(done, indent=2)
    def inspects(self, image = None):
        image = image or self.image()
        done = self.inspect_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, done))
        else:
            return json.dumps(done, indent=2)

if __name__ == "__main__":
    from argparse import ArgumentParser
    _o = ArgumentParser(description = """starts local containers representing mirrors of package repo repositories 
        which are required by a container type. Subsequent 'docker run' can use the '--add-hosts' from this
        helper script to divert 'pkg install' calls to a local docker container as the real source.""")
    _o.add_argument("-v", "--verbose", action="count", default=0, help="more logging")
    _o.add_argument("-a", "--add-hosts", "--add-host", action="store_true", default=ADDHOSTS, 
        help="show options for 'docker run'")
    commands = ["help","detect","image","repo","info","facts","start","stop"]
    _o.add_argument("command", nargs="?", default="detect", help="|".join(commands))
    _o.add_argument("image", nargs="?", default=None, help="defaults to image name of the local host system")
    opt = _o.parse_args()
    logging.basicConfig(level = max(0, logging.WARNING - opt.verbose * 10))
    ADDHOSTS = opt.add_hosts
    command = "detect"
    repo = DockerMirrorPackagesRepo()
    if opt.command in [ "?", "help"]:
        print(repo.helps())
    elif opt.command in [ "detect", "image" ]:
        print(repo.detect())
    elif opt.command in [ "repo", "from" ]:
        print(repo.repo(opt.image))
    elif opt.command in [ "repos", "for" ]:
        print(repo.repos(opt.image))
    elif opt.command in [ "facts" ]:
        print(repo.facts(opt.image))
    elif opt.command in [ "start", "starts" ]:
        print(repo.starts(opt.image))
    elif opt.command in [ "stop", "stops" ]:
        print(repo.stops(opt.image))
    elif opt.command in [ "show", "shows", "info", "infos" ]:
        print(repo.infos(opt.image))
    elif opt.command in [ "addhost", "add-host", "addhosts", "add-hosts" ]:
        ADDHOSTS = True
        print(repo.infos(opt.image))
    elif opt.command in [ "inspect" ]:
        print(repo.inspects(opt.image))
    elif opt.command in [ "containers" ]:
        print(repo.containers(opt.image))
    else:
        print("unknown command", opt.command)
        sys.exit(1)
