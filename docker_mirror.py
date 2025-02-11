#! /usr/bin/python3
# from __future__ import print_function

__copyright__ = "(C) 2025 Guido Draheim"
__contact__ = "https://github.com/gdraheim/docker-mirror-packages-repo"
__license__ = "CC0 Creative Commons Zero (Public Domain)"
__version__ = "1.7.7034"

from collections import OrderedDict, namedtuple
import os.path
import sys
import re
import json
import logging
import subprocess
import tempfile
import shutil
import socket
import time
import configparser

if sys.version[0] == '2': # pragma: nocover
    range = xrange # pylint: disable=redefined-builtin, used-before-assignment, undefined-variable
    stringtypes = basestring # pylint: disable=undefined-variable
else:
    stringtypes = str

logg = logging.getLogger("mirror")
IMAGESREPO = "localhost:5000/mirror-packages"
DOCKER = "docker"
ADDHOSTS = False
ADDEPEL = False
UPDATES = False
UNIVERSE = False
LOCAL = False

MAXWAIT = 6
WAXWAIT = ""

BASE = {}
BASE["8.5.2111"] = "8.5"
BASE["8.4.2105"] = "8.4"
BASE["8.3.2011"] = "8.3"
BASE["8.2.2004"] = "8.2"
BASE["8.1.1911"] = "8.1"
BASE["8.0.1905"] = "8.0"
BASE["7.9.2009"] = "7.9"
BASE["7.8.2003"] = "7.8"
BASE["7.7.1908"] = "7.7"
BASE["7.6.1810"] = "7.6"
BASE["7.5.1804"] = "7.5"
BASE["7.4.1708"] = "7.4"
BASE["7.3.1611"] = "7.3"
BASE["7.2.1511"] = "7.2"
BASE["7.1.1503"] = "7.1"
BASE["7.0.1406"] = "7.0"

ALMA = {}
ALMA["8.8-20230524"] = "8.8"
ALMA["8.8-20230718"] = "8.8"
ALMA["8.9-20231124"] = "8.9"
ALMA["8.9-20240410"] = "8.9"
ALMA["8.10-20240528"] = "8.10"
ALMA["9.0-20220706"] = "9.0"
ALMA["9.0-20220901"] = "9.0"
ALMA["9.0-20221001"] = "9.0"
ALMA["9.0-20221102"] = "9.0"
ALMA["9.1-20221117"] = "9.1"
ALMA["9.1-20221201"] = "9.1"
ALMA["9.1-20230222"] = "9.1"
ALMA["9.1-20230407"] = "9.1"
ALMA["9.2-20230512"] = "9.2"
ALMA["9.2-20230718"] = "9.2"
ALMA["9.3-20231124"] = "9.3"
ALMA["9.3-20240410"] = "9.3"
ALMA["9.4-20240506"] = "9.4"
ALMA["9.4-20240530"] = "9.4"

DIST = {}
DIST["12.04"] = "precise"  # Precise Pangolin
DIST["12.10"] = "quantal"  # Quntal Quetzal
DIST["14.04"] = "trusty"   # Trusty Tahr LTS    (April 2022)
DIST["14.10"] = "utopic"   # Utopic Unicorn
DIST["16.04"] = "xenial"   # Xenial Xerus LTS   (April 2024)
DIST["16.10"] = "yaketty"  # Yaketty Yak
DIST["17.10"] = "artful"   # Artful Aardvark
DIST["18.04"] = "bionic"   # Bionic Beaver LTS  (April 2028)
DIST["18.10"] = "cosmic"   # Cosmic Cuttlefish  (x)
DIST["19.04"] = "disco"    # Disco Dingo
DIST["19.10"] = "eoan"     # Eoan Ermine
DIST["20.04"] = "focal"    # Focal Fossa LTS    (April 2030)
DIST["20.10"] = "groovy"   # Groovy Gorilla
DIST["21.04"] = "hirsute"  # Hirsute Hippo
DIST["21.10"] = "impish"   # Impish Indri
DIST["22.04"] = "jammy"    # Jammy Jellyfish    (April 2027)
DIST["22.10"] = "kinetic"  # Kinetic Kudu
DIST["23.04"] = "lunatic"  # Lunatic Lobster
DIST["23.10"] = "mantic"   # Mantic Minotaur
DIST["24.04"] = "noble"    # Noble Numbat       (April 2029)

OPENSUSE = {}
OPENSUSE["13.2"] = "opensuse"  # no docker image
OPENSUSE["42.2"] = "opensuse/leap"  # docker image removed
OPENSUSE["42.3"] = "opensuse/leap"
OPENSUSE["15.0"] = "opensuse/leap"
OPENSUSE["15.1"] = "opensuse/leap"
OPENSUSE["15.2"] = "opensuse/leap"
OPENSUSE["15.3"] = "opensuse/leap"
OPENSUSE["15.4"] = "opensuse/leap"
OPENSUSE["15.5"] = "opensuse/leap"
OPENSUSE["15.6"] = "opensuse/leap"
OPENSUSE["16.0"] = "opensuse/leap"

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", "~/.config")
DOCKER_MIRROR_CONFIG = os.environ.get("DOCKER_MIRROR_CONFIG", os.path.join(XDG_CONFIG_HOME, "docker_mirror.ini"))

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
def output3(cmd, shell=True, debug=True):
    if isinstance(cmd, stringtypes):
        if debug: logg.debug("run: %s", cmd)
    else:
        if debug: logg.debug("run: %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return decodes_(out), decodes_(err), run.returncode

def major(version):
    if len(version) > 2:
        if version[1] == ".":
            return version[0]
        else:
            return version[:2]
    return version
def majorminor(version):
    if version.count(".") > 2:
        ver = version.split(".")
        return ver[0] + "." + ver[1]
    if version.count("-") > 0:
        ver = version.split("-")
        return ver[0]
    return version
def onlyversion(image):
    if ":" in image:
        return image.split(":")[-1]
    return image

class DockerMirror:
    def __init__(self, cname, image, hosts, mount=""):
        self.cname = cname  # name of running container
        self.image = image  # image used to start the container
        self.hosts = hosts  # domain names for the container
        self.mount = mount  # mounting as data to serve
    def __str__(self):
        return "(cname='%s',image='%s',hosts=%s,mount='%s')" % (self.cname, self.image, self.hosts, self.mount)

class DockerMirrorPackagesRepo:
    def __init__(self, image=None):
        self._image = image
    def host_system_image(self):
        """ returns the docker image name which corresponds to the 
            operating system distribution of the host system. This
            image name is the key for the other mirror functions. """
        distro, version = self.detect_etc_image("/etc")
        logg.info(":%s:%s host system image detected", distro, version)
        if distro and version:
            return "%s:%s" % (distro, version)
        return ""
    def detect_etc_image(self, etc):
        distro, version = "", ""
        os_release = os.path.join(etc, "os-release")
        if os.path.exists(os_release):
            # rhel:7.4 # VERSION="7.4 (Maipo)" ID="rhel" VERSION_ID="7.4"
            # centos:7.3  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # centos:7.4  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # centos:7.7.1908  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # opensuse:42.3 # VERSION="42.3" ID=opensuse VERSION_ID="42.3"
            # opensuse/leap:15.0 # VERSION="15.0" ID="opensuse-leap" VERSION_ID="15.0"
            # ubuntu:16.04 # VERSION="16.04.3 LTS (Xenial Xerus)" ID=ubuntu VERSION_ID="16.04"
            # ubuntu:18.04 # VERSION="18.04.1 LTS (Bionic Beaver)" ID=ubuntu VERSION_ID="18.04"
            for line in open(os_release):
                key, value = "", ""
                m = re.match('^([_\\w]+)=([^"].*).*', line.strip())
                if m:
                    key, value = m.group(1), m.group(2)
                m = re.match('^([_\\w]+)="([^"]*)".*', line.strip())
                if m:
                    key, value = m.group(1), m.group(2)
                # logg.debug("%s => '%s' '%s'", line.strip(), key, value)
                if key in ["ID"]:
                    distro = value.replace("-", "/")
                if key in ["VERSION_ID"]:
                    version = value
        redhat_release = os.path.join(etc, "redhat-release")
        if os.path.exists(redhat_release):
            for line in open(redhat_release):
                m = re.search("release (\\d+[.]\\d+).*", line)
                if m:
                    distro = "rhel"
                    version = m.group(1)
        centos_release = os.path.join(etc, "centos-release")
        if os.path.exists(centos_release):
            # CentOS Linux release 7.5.1804 (Core)
            for line in open(centos_release):
                m = re.search("release (\\d+[.]\\d+).*", line)
                if m:
                    distro = "centos"
                    version = m.group(1)
        return distro, version
    def detect_base_image(self, image):
        """ returns the docker image name which corresponds to the 
            operating system distribution of the image provided. This
            image name is the key for the other mirror functions. """
        docker = DOCKER
        distro, version = "", ""
        cname = "docker_mirror_detect." + os.path.basename(image).replace(":", ".")
        cmd = "{docker} rm -f {cname}"
        out, err, end = output3(cmd.format(**locals()))
        cmd = "{docker} create --name={cname} {image}"
        out, err, end = output3(cmd.format(**locals()))
        if end:
            logg.info("%s --name %s : %s", image, cname, err.strip())
        tempdir = tempfile.mkdtemp("docker_mirror_detect")
        try:
            distro, version = self.detect_base_image_from(cname, tempdir)
            logg.info(":%s:%s base image detected", distro, version)
            if distro and version:
                return "%s:%s" % (distro, version)
        finally:
            shutil.rmtree(tempdir)
            cmd = "{docker} rm {cname}"
            out, err, end = output3(cmd.format(**locals()))
        return image
    def detect_base_image_from(self, cname, tempdir):
        debug = False
        docker = DOCKER
        cmd = "{docker} cp {cname}:/usr/lib/os-release {tempdir}/os-release"
        out, err, end = output3(cmd.format(**locals()), debug=debug)
        if not end:
            logg.debug("get: /usr/lib/os-release copied")
        else:
            logg.debug("get: /usr/lib/os-release: %s", err.strip().replace(cname, "{cname}"))
            cmd = "{docker} cp {cname}:/etc/os-release {tempdir}/os-release"
            out, err, end = output3(cmd.format(**locals()), debug=debug)
            if not end:
                logg.debug("get: /etc/os-release copied")
            else:
                logg.debug("get: /etc/os-release: %s", err.strip().replace(cname, "{cname}"))
        cmd = "{docker} cp {cname}:/etc/redhat-release {tempdir}/redhat-release"
        out, err, end = output3(cmd.format(**locals()), debug=debug)
        if not end:
            logg.debug("get: /etc/redhat-release copied")
        else:
            logg.debug("get: /etc/redhat-release: %s", err.strip().replace(cname, "{cname}"))
        cmd = "{docker} cp {cname}:/etc/centos-release {tempdir}/centos-release"
        out, err, end = output3(cmd.format(**locals()), debug=debug)
        if not end:
            logg.debug("get: /etc/centos-release copied")
        else:
            logg.debug("get: /etc/centos-release: %s", err.strip().replace(cname, "{cname}"))
        return self.detect_etc_image(tempdir)
    def get_docker_latest_image(self, image):
        """ converts a shorthand version into the version string used on an image name. """
        if image.startswith("centos:"):
            return self.get_centos_latest(image)
        if image.startswith("almalinux:"):
            return self.get_centos_latest(image)
        if image.startswith("opensuse/leap:"):
            return self.get_opensuse_latest(image)
        if image.startswith("opensuse:"):
            return self.get_opensuse_latest(image)
        if image.startswith("ubuntu:"):
            return self.get_ubuntu_latest(image)
        return ""
    def get_docker_latest_version(self, image):
        """ converts a shorthand version into the version string used on an image name. """
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            return self.get_centos_latest_version(version)
        if image.startswith("almalinux:"):
            version = image[len("almalinux:"):]
            return self.get_centos_latest_version(version)
        if image.startswith("opensuse/leap:"):
            version = image[len("opensuse/leap:"):]
            return self.get_opensuse_latest_version(version)
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            return self.get_opensuse_latest_version(version)
        if image.startswith("ubuntu:"):
            version = image[len("ubuntu:"):]
            return self.get_ubuntu_latest_version(version)
        return ""
    def get_docker_mirror(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if image.startswith("centos:"):
            return self.get_centos_docker_mirror(image)
        if image.startswith("almalinux:"):
            return self.get_centos_docker_mirror(image)
        if image.startswith("opensuse/leap:"):
            return self.get_opensuse_docker_mirror(image)
        if image.startswith("opensuse:"):
            return self.get_opensuse_docker_mirror(image)
        if image.startswith("ubuntu:"):
            return self.get_ubuntu_docker_mirror(image)
        return None
    def get_docker_mirrors(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        logg.info("mirrors for %s", image)
        mirrors = []
        config = configparser.ConfigParser()
        configfile = os.path.expanduser(DOCKER_MIRROR_CONFIG)
        if os.path.exists(configfile):
            config.read(configfile)
        if image.startswith("centos:"):
            mirrors = self.get_centos_docker_mirrors(image)
            if ADDEPEL:
                mirrors += self.get_epel_docker_mirrors(image)
        if image.startswith("almalinux:"):
            mirrors = self.get_centos_docker_mirrors(image)
            if ADDEPEL:
                mirrors += self.get_epel_docker_mirrors(image)
        if image.startswith("opensuse/leap:"):
            mirrors = self.get_opensuse_docker_mirrors(image)
        if image.startswith("opensuse:"):
            mirrors = self.get_opensuse_docker_mirrors(image)
        if image.startswith("ubuntu:"):
            mirrors = self.get_ubuntu_docker_mirrors(image)
        if ":" in image:
            if image in config.sections():
                cname1 = config[image].get("cname", "")
                image1 = config[image].get("image", "")
                hosts1 = [x.strip() for x in config[image].get("hosts", "").split(",") if x.strip()]
                mount1 = config[image].get("mount", "")
                logg.info("config [%s]\n\tcname=%s\n\timage=%s\n\thosts=%s\n\tmount=%s",
                          image, cname1, image1, hosts1, mount1)
                if len(mirrors) > 0:
                    if cname1:
                        mirrors[0].cname = cname1
                    if image1:
                        mirrors[0].image = image1
                    if hosts1:
                        logg.info("hosts1=%s", hosts1)
                        mirrors[0].hosts = hosts1
                    if mount1:
                        mirrors[0].mount = mount1
                elif image1:
                    if not hosts1:
                        hosts1 = [image1.split(":", 1)[0] + ".org"]
                    mirrors = [DockerMirror(self.containername(image1), image1, hosts1)]
        logg.info("     mirrors for %s -> %s", image, " ".join([mirror.cname for mirror in mirrors]))
        return mirrors
    def get_ubuntu_latest(self, image, default=None):
        if image.startswith("ubuntu:"):
            distro = "ubuntu"
            version = image[len("ubuntu:"):]
            latest = self.get_ubuntu_latest_version(version)
            if latest:
                return "{distro}:{latest}".format(**locals())
        if default is not None:
            return default
        return image
    def get_ubuntu_latest_version(self, version):
        """ allows to use 'ubuntu:18' or 'ubuntu:bionic' """
        ver = version
        if ver in ["latest"]:
            ver = ""
        if "." not in ver:
            latest = ""
            for release in DIST:
                codename = DIST[release]
                if len(ver) >= 3 and ver.startswith(codename):
                    logg.debug("release (%s) %s", release, codename)
                    if latest < release:
                        latest = release
                elif release.startswith(ver):
                    logg.debug("release %s (%s)", release, codename)
                    if latest < release:
                        latest = release
            if latest:
                ver = latest
        return ver or version
    def get_ubuntu_docker_mirror(self, image):
        """ detects a local ubuntu mirror or starts a local
            docker container with a ubunut repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = IMAGESREPO
        rep = "ubuntu-repo"
        if UPDATES: rep = "ubuntu-repo/updates"
        if UNIVERSE: rep = "ubuntu-repo/universe"
        ver = self.get_ubuntu_latest_version(onlyversion(image))
        return self.docker_mirror(rmi, rep, ver, "archive.ubuntu.com", "security.ubuntu.com")
    def get_ubuntu_docker_mirrors(self, image):
        main = self.get_ubuntu_docker_mirror(image)
        return [main]
    def get_centos_latest(self, image, default=None):
        if image.startswith("centos:"):
            distro = "centos"
            version = image[len("centos:"):]
            latest = self.get_centos_latest_version(version)
            if latest:
                return "{distro}:{latest}".format(**locals())
        if image.startswith("almalinux:"):
            distro = "almalinux"
            version = image[len("almalinux:"):]
            latest = self.get_centos_latest_version(version)
            if latest:
                return "{distro}:{latest}".format(**locals())
        if default is not None:
            return default
        return image
    def get_centos_latest_version(self, version):
        """ allows to use 'centos:7' or 'centos:7.9' making 'centos:7.9.2009' """
        ver = version
        if ver in ["latest"]:
            ver = ""
        if "." not in ver:
            latest = ""
            for release in BASE:
                if release.startswith(ver):
                    mainrelease = BASE[release]
                    logg.debug("release %s (%s)", release, mainrelease)
                    if latest < release:
                        latest = release
            for release in ALMA:
                if release.startswith(ver):
                    mainrelease = BASE[release]
                    logg.debug("release %s (%s)", release, mainrelease)
                    if latest < mainrelease:
                        latest = mainrelease
            if latest:
                ver = latest
        if ver in BASE:
            ver = BASE[ver]
        if version in ALMA:
            ver = version # ALMA.keys() are long version
        elif version in ALMA.values():
            ver = max([os for os in ALMA if ALMA[os] == version])
        logg.debug("latest version %s for %s", ver, version)
        return ver or version
    def get_centos_docker_mirror(self, image):
        """ detects a local centos mirror or starts a local
            docker container with a centos repo mirror. It
            will return the setting for extrahosts"""
        if ":" in image:
            distro, ver = image.split(":", 1)
        else:
            distro, ver = "centos", image
        rmi = IMAGESREPO
        rep = F"{distro}-repo"
        version = self.get_centos_latest_version(onlyversion(image))
        ver = majorminor(version)
        logg.debug("    mirror for %s (%s)", ver, image)
        if "alma" in distro:
            return self.docker_mirror(rmi, rep, ver, "mirrors.almalinux.org")
        else:
            return self.docker_mirror(rmi, rep, ver, "mirrorlist.centos.org")
    def get_centos_docker_mirrors(self, image):
        main = self.get_centos_docker_mirror(image)
        return [main]
    def get_opensuse_latest(self, image, default=None):
        if image.startswith("opensuse/leap:"):
            distro = "opensuse/leap"
            version = image[len("opensuse/leap:"):]
            latest = self.get_opensuse_latest_version(version)
            if latest:
                if latest in OPENSUSE:
                    distro = OPENSUSE[latest]
                return "{distro}:{latest}".format(**locals())
        if image.startswith("opensuse:"):
            distro = "opensuse"
            version = image[len("opensuse:"):]
            latest = self.get_opensuse_latest_version(version)
            if latest:
                if latest in OPENSUSE:
                    distro = OPENSUSE[latest]
                return "{distro}:{latest}".format(**locals())
        if default is not None:
            return default
        return image
    def get_opensuse_latest_version(self, version):
        """ allows to use 'opensuse:42' making 'opensuse:42.3' """
        ver = version
        if ver in ["latest"]:
            ver = ""
        if "." not in ver:
            latest = ""
            for release in OPENSUSE:
                if release.startswith(ver):
                    logg.debug("release %s", release)
                    # opensuse:42.0 was before opensuse/leap:15.0
                    release42 = release.replace("42.", "14.")
                    latest42 = latest.replace("42.", "14.")
                    if latest42 < release42:
                        latest = release
            ver = latest or ver
        return ver or version
    def get_opensuse_docker_mirror(self, image):
        """ detects a local opensuse mirror or starts a local
            docker container with a centos repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = IMAGESREPO
        rep = "opensuse-repo"
        ver = self.get_opensuse_latest_version(onlyversion(image))
        return self.docker_mirror(rmi, rep, ver, "download.opensuse.org")
    def get_opensuse_docker_mirrors(self, image):
        main = self.get_opensuse_docker_mirror(image)
        return [main]
    def docker_mirror(self, rmi, rep, ver, *hosts):
        req = rep.replace("/", "-")
        image = "{rmi}/{rep}:{ver}".format(**locals())
        cname = "{req}-{ver}".format(**locals())
        return DockerMirror(cname, image, list(hosts))
    def containername(self, image):
        x = image.rfind("/")
        if x > 0:
            return image[x + 1:].replace(":", "-")
        else:
            return image.replace(":", "-")
    #
    def get_extra_mirrors(self, image):
        mirrors = []
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            mirrors = self.get_epel_docker_mirrors(version)
        return mirrors
    def get_epel_docker_mirrors(self, image):
        main = self.get_epel_docker_mirror(image)
        return [main]
    def get_epel_docker_mirror(self, image):
        """ detects a local epel mirror or starts a local
            docker container with a epel repo mirror. It
            will return the setting for extrahosts"""
        docker = DOCKER
        rmi = IMAGESREPO
        rep = "epel-repo"
        ver = onlyversion(image)
        version = self.get_centos_latest_version(ver)
        logg.debug("detect epel refdate from '%s'", version)
        # cut the yymm date part from the almalinux release
        yymm = re.match("\\d+[.]\\d+-\\d\\d(\\d\\d\\d\\d)\\d*", version)
        if yymm:
            released = yymm.group(1)
        # cut the yymm date part from the centos release
        elif version.count(".") == 2:
            released = version.split(".")[-1]
        else:
            logg.error("can not get epel refdate from %s", version)
            raise ValueError("can not get epel refdate")
        logg.debug("      detected %s -> epel refdate %s", version, released)
        later = ""
        before = ""
        epelimages = self.get_epel_docker_mirror_images(rep)
        diskrepos = self.get_epel_docker_mirror_disks(rep, "mirrors.fedoraproject.org")
        epelrepos = epelimages + list(diskrepos.keys())
        logg.debug("select %s from images %s", released, epelrepos)
        for image in epelrepos:
            tagline = re.sub(".*:", "", image)
            tagname = re.sub(" .*", "", tagline)
            created = tagname.split(".")[-1]
            accepts = tagname.startswith(major(version))
            logg.debug(": %s (%s) (%s) %s:%s", image, created, released, major(version), accepts and "x" or "ignore")
            if created >= released and accepts:
                if not later or later > tagname:
                    later = tagname
            elif created < released and accepts:
                if not before or before < tagname:
                    before = tagname
        if later:
            ver = later
        elif before:
            ver = before
        logg.debug("image ver %s <- epel refdate %s", ver, released)
        mirror = self.docker_mirror(rmi, rep, ver, "mirrors.fedoraproject.org")
        if F"{rep}:{ver}" in diskrepos:
            mirror = diskrepos[ F"{rep}:{ver}"]
            logg.info("replace %s:%s by disk %s", rep, ver, mirror.mount)
        return mirror
    def get_epel_docker_mirror_images(self, rep):
        docker = DOCKER
        rmi = IMAGESREPO
        cmd = docker + " images --format '{{.Repository}}:{{.Tag}}'"
        out, err, end = output3(cmd)
        if end:
            logg.error("docker images [%s]\n\t%s", end, cmd)
            return []
        found = []
        for line in out.split("\n"):
            if not line.startswith(rmi):
                continue
            if F"/{rep}:" not in line:
                continue
            found.append(line.rstrip())
        return found
    def get_epel_docker_mirror_disks(self, rep, *hosts):
        rep = rep or "epel-repo"
        found = {}
        config = configparser.ConfigParser()
        configfile = os.path.expanduser(DOCKER_MIRROR_CONFIG)
        if os.path.exists(configfile):
            config.read(configfile)
        for sec in config.sections():
            if sec.startswith(rep+":"):
                cname = sec.replace(":","-")
                mirror = DockerMirror(cname, config[sec]["image"], hosts, config[sec]["mount"])
                logg.info("found epel disk %s", mirror)
                found[sec] = mirror
        return found

    #
    def ip_container(self, name):
        docker = DOCKER
        cmd = "{docker} inspect {name}"
        out, err, rc = output3(cmd.format(**locals()))
        if rc:
            logg.info("%s : %s", cmd, err)
            logg.debug("no addr for %s", name)
            return None
        values = json.loads(out)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        addr = values[0]["NetworkSettings"]["IPAddress"]
        assert isinstance(addr, stringtypes)
        logg.debug("::::                %s -> %s", name, addr)
        return addr
    def start_containers(self, image):
        mirrors = self.get_docker_mirrors(image)
        done = {}
        for mirror in mirrors:
            logg.debug(" START --name %s %s [%s]", mirror.cname, mirror.image, mirror.mount)
            addr = self.start_container(mirror.image, mirror.cname, mirror.mount)
            done[mirror.cname] = addr
        return done
    def start_container(self, image, container, mount):
        docker = DOCKER
        cmd = "{docker} inspect {image}"
        out, err, ok = output3(cmd.format(**locals()))
        image_found = json.loads(out)
        if not image_found:
            logg.info("    image not found: %s", image)
            return None
        cmd = "{docker} inspect {container}"
        out, err, rc = output3(cmd.format(**locals()))
        container_found = json.loads(out)
        if not rc and container_found:
            container_status = container_found[0]["State"]["Status"]
            logg.debug("::::                %s -> %s", container, container_status)
            latest_image_id = image_found[0]["Id"]
            container_image_id = container_found[0]["Image"]
            if latest_image_id != container_image_id or container_status not in ["running"]:
                cmd = "{docker} rm --force {container}"
                out, err, rc = output3(cmd.format(**locals()))
                if rc:
                    logg.debug("%s : %s", cmd, err)
                container_found = []
        if not container_found:
            cmd = "{docker} run --rm=true --detach"
            if mount and os.path.isdir(mount):
                cmd += " -v {mount}:/srv/repo"
            elif mount:
                logg.warning("no such volume %s", mount)
            else:
                logg.debug("no extra volume given")
            cmd += " --name {container} {image}"
            out, err, rc = output3(cmd.format(**locals()))
            if rc:
                logg.error("%s : %s", cmd, err)
            else:
                logg.info("%s : %s", cmd, "OK")
        addr = self.ip_container(container)
        logg.info(" ---> %s : %s", container, addr)
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
            assert isinstance(started, stringtypes)
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
        mirrors = self.get_docker_mirrors(image)
        docker = DOCKER
        done = OrderedDict()
        for mirror in mirrors:
            addr = self.ip_container(mirror.cname)
            done[mirror.cname] = addr
        return done
    #
    def add_hosts(self, image, done={}):
        mirrors = self.get_docker_mirrors(image)
        args = []
        for mirror in mirrors:
            name = mirror.cname
            logg.debug(" repo container %s   (%s)", name, done)
            if name in done:
                addr = done[name]
                if addr:
                    for host in mirror.hosts:
                        args += ["--add-host", "%s:%s" % (host, addr)]
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
    def detect(self, image=None):
        if not image and self._image:
            image = self._image
        if not image or image in ["host", "system"]:
            return self.host_system_image()
        latest = self.get_docker_latest_image(image)
        if latest:
            return latest
        else:
            # actually create a container and look into it
            return self.detect_base_image(image)
    def epel(self, image=None):
        image = self.detect(image)
        mirrors = self.get_extra_mirrors(image)
        for mirror in mirrors:
            return mirror.image
        return ""
    def repo(self, image=None):
        image = self.detect(image)
        mirrors = self.get_docker_mirrors(image)
        for mirror in mirrors:
            if ADDHOSTS:
                refer = mirror.image
                host = mirror.hosts[0]
                return "--add-host={host}:({refer})".format(**locals())
            else:
                return mirror.image
        return ""
    def repos(self, image=None):
        image = self.detect(image)
        mirrors = self.get_docker_mirrors(image)
        shown = ""
        for mirror in mirrors:
            if ADDHOSTS:
                if shown: shown += " "
                for host in mirror.hosts:
                    refer = mirror.image
                    shown += "--add-host={host}:({refer})".format(**locals())
            else:
                shown += mirror.image + "\n"
        return shown
    def facts(self, image=None):
        image = self.detect(image)
        mirrors = self.get_docker_mirrors(image)
        data = {}
        for mirror in mirrors:
            data[mirror.cname] = {"image": mirror.image, "name": mirror.cname,
                                  "hosts": mirror.hosts}
        return json.dumps(data, indent=2)
    def starts(self, image=None):
        image = self.detect(image)
        logg.debug("starts image = %s", image)
        mirrors = self.start_containers(image)
        if LOCAL:
            notfound = [mirror for mirror, addr in mirrors.items() if addr is None]
            if notfound:
                logg.error("   no docker mirror image for %s" % (" ".join(notfound)))
                sys.exit(1)
        self.wait_mirrors(mirrors)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, mirrors))
        else:
            return json.dumps(mirrors, indent=2)
    def stops(self, image=None):
        image = self.detect(image)
        mirrors = self.stop_containers(image)
        if ADDHOSTS:
            names = sorted(mirrors.keys())
            return " ".join(names)
        else:
            return json.dumps(mirrors, indent=2)
    def wait_mirrors(self, hosts):
        results = {}
        started = time.monotonic()
        for url, addr in hosts.items():
            if not addr:
                continue
            results[url] = 0
            if "alma" in url or "epel" in url:
                logg.debug("wait %s:443 (%ss)", url, MAXWAIT)
                for attempt in range(max(1, MAXWAIT)):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        sock.connect((addr, 443))
                        results[url] = 0
                        break
                    except ConnectionRefusedError as e:
                        logg.debug("wait %s:443 = %s", url, e)
                        results[url] += 1
                        time.sleep(1)
            else:
                logg.debug("wait %s:80 (%ss)", url, MAXWAIT)
                for attempt in range(max(1, MAXWAIT - 2)):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        sock.connect((addr, 80))
                        results[url] = 0
                        break
                    except ConnectionRefusedError as e:
                        logg.debug("wait %s:80 = %s", url, e)
                        results[url] += 1
                        time.sleep(1)
            if attempt:
                logg.debug("wait %s:80 - OK", url)
        took = time.monotonic() - started
        if took > 1.1:
            logg.debug("wait %3.3f sec", took)
        return sum(results.values())
    def infos(self, image=None):
        image = self.detect(image)
        mirrors = self.info_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, mirrors))
        else:
            return json.dumps(mirrors, indent=2)
    def containers(self, image=None):
        image = self.detect(image)
        mirrors = self.get_containers(image)
        if ADDHOSTS:
            return " ".join(mirrors)
        else:
            return json.dumps(mirrors, indent=2)
    def inspects(self, image=None):
        image = self.detect(image)
        mirrors = self.inspect_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, mirrors))
        else:
            return json.dumps(mirrors, indent=2)
    def from_dockerfile(self, dockerfile, defaults=None):
        if os.path.isdir(dockerfile):
            dockerfile = os.path.join(dockerfile, "Dockerfile")
        for line in open(dockerfile):
            found = re.match(r"(?:FROM|from)\s+(\w\S+)(.*)", line)
            if found:
                return found.group(1)
        return defaults

def repo_scripts():
    me = os.path.dirname(sys.argv[0])
    dn = os.path.join(me, "scripts")
    if os.path.isdir(dn): return dn
    dn = os.path.join(me, "docker_mirror/scripts")
    if os.path.isdir(dn): return dn
    dn = os.path.join(me, "../docker_mirror/scripts")
    if os.path.isdir(dn): return dn
    dn = os.path.join(me, "../share/docker_mirror/scripts")
    if os.path.isdir(dn): return dn
    return "scripts"

if __name__ == "__main__":
    from argparse import ArgumentParser, HelpFormatter
    cmdline = ArgumentParser(formatter_class=lambda prog: HelpFormatter(prog, max_help_position=36, width=81),  # type: ignore[arg-type]
                             description="""starts local containers representing mirrors of package repo repositories 
        which are required by a container type. Subsequent 'docker run' can use the '--add-hosts' from this
        helper script to divert 'pkg install' calls to a local docker container as the real source.""")
    cmdline.add_argument("-v", "--verbose", action="count", default=0, help="more logging")
    cmdline.add_argument("-a", "--add-hosts", "--add-host", action="store_true", default=ADDHOSTS,
                         help="show addhost options for 'docker run' [%(default)s]")
    cmdline.add_argument("-D", "--docker", metavar="EXE", default=DOCKER,
                         help="use other docker exe or podman [%(default)s]")
    cmdline.add_argument("--imagesrepo", metavar="PREFIX", default=IMAGESREPO,
                         help="set $IMAGESREPO [%(default)s]")
    cmdline.add_argument("--epel", action="store_true", default=ADDEPEL,
                         help="addhosts for epel as well [%(default)s]")
    cmdline.add_argument("--updates", "--update", action="store_true", default=UPDATES,
                         help="addhosts using updates variant [%(default)s]")
    cmdline.add_argument("--universe", action="store_true", default=UNIVERSE,
                         help="addhosts using universe variant [%(default)s]")
    cmdline.add_argument("-f", "--file", metavar="DOCKERFILE", default=None,
                         help="default to image FROM the dockerfile [%(default)s]")
    cmdline.add_argument("-l", "--local", "--localmirrors", action="count", default=0,
                         help="fail if a local mirror was not found [%(default)s]")
    cmdline.add_argument("-C", "--configfile", metavar="FILE", default=DOCKER_MIRROR_CONFIG,
                         help="overrides in [%(default)s]")
    commands = ["help", "detect", "image", "repo", "info", "facts", "start", "stop"]
    cmdline.add_argument("command", nargs="?", default="detect", help="|".join(commands))
    cmdline.add_argument("image", nargs="?", default=None, help="defaults to image name matching the local host system")
    opt = cmdline.parse_args()
    logging.basicConfig(level=max(0, logging.WARNING - opt.verbose * 10))
    DOCKER = opt.docker
    IMAGESREPO = opt.imagesrepo
    ADDHOSTS = opt.add_hosts
    ADDEPEL = opt.epel  # centos epel-repo
    # UPDATES = opt.updates
    UNIVERSE = opt.universe  # ubuntu universe repo
    LOCAL = opt.local
    DOCKER_MIRROR_CONFIG = opt.configfile
    command = opt.command or "detect"
    repo = DockerMirrorPackagesRepo()
    if not opt.image and opt.file:
        opt.image = repo.from_dockerfile(opt.file)
    if command in ["?", "help"]:
        print(repo.helps())
    elif command in ["detect", "image"]:
        print(repo.detect(opt.image))
    elif command in ["repo", "from"]:
        print(repo.repo(opt.image))
    elif command in ["repos", "for"]:
        print(repo.repos(opt.image))
    elif command in ["latest"]:
        print(repo.get_docker_latest_version(opt.image))
    elif command in ["epel"]:
        print(repo.epel(opt.image))
    elif command in ["facts"]:
        print(repo.facts(opt.image))
    elif command in ["start", "starts"]:
        print(repo.starts(opt.image))
    elif command in ["stop", "stops"]:
        print(repo.stops(opt.image))
    elif command in ["show", "shows", "info", "infos"]:
        print(repo.infos(opt.image))
    elif command in ["addhost", "add-host", "addhosts", "add-hosts"]:
        ADDHOSTS = True
        print(repo.infos(opt.image))
    elif command in ["inspect"]:
        print(repo.inspects(opt.image))
    elif command in ["containers"]:
        print(repo.containers(opt.image))
    elif command in ["scripts"]:
        print(repo_scripts())
    else:
        print("unknown command", opt.command)
        sys.exit(1)
