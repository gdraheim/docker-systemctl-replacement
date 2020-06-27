#! /usr/bin/python

__copyright__ = "(C) 2020 Guido Draheim"
__contact__ = "https://github.com/gdraheim/docker-mirror-packages-repo"
__license__ = "CC0 Creative Commons Zero (Public Domain)"
__version__ = "1.5.2256"

from collections import OrderedDict, namedtuple
import os.path
import sys
import re
import json
import logging
import subprocess

logg = logging.getLogger("mirror")
DOCKER = "docker"
ADDHOSTS = False

def decodes(text):
    if text is None: return None
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
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode

class DockerMirrorPackagesRepo:
    def local_system(self):
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
        logg.info(":: local_system %s:%s", distro, version)
        if distro and version:
            return "%s:%s" % (distro, version)
        return ""
    def get_local_mirror(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        hosts = {}
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            hosts = self.get_local_centos_mirror(version)
        if image.startswith("opensuse/leap:"):
            version = image[len("opensuse/leap:"):]
            hosts = self.get_local_opensuse_mirror(version)
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            hosts = self.get_local_opensuse_mirror(version)
        if image.startswith("ubuntu:"):
            version = image[len("ubuntu:"):]
            hosts = self.get_local_ubuntu_mirror(version)
        return hosts
    def get_local_ubuntu_mirror(self, ver = None):
        """ detects a local ubuntu mirror or starts a local
            docker container with a ubunut repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000/mirror-packages"
        rep = "ubuntu-repo"
        ver = ver or UBUNTU.split(":")[1]
        return self.get_local(rmi, rep, ver, "archive.ubuntu.com", "security.ubuntu.com")
    def get_local_centos_mirror(self, ver = None):
        """ detects a local centos mirror or starts a local
            docker container with a centos repo mirror. It
            will return the setting for extrahosts"""
        rmi = "localhost:5000/mirror-packages"
        rep = "centos-repo"
        ver = ver or CENTOS.split(":")[1]
        return self.get_local(rmi, rep, ver, "mirrorlist.centos.org")
    def get_local_opensuse_mirror(self, ver = None):
        """ detects a local opensuse mirror or starts a local
            docker container with a centos repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000/mirror-packages"
        rep = "opensuse-repo"
        ver = ver or OPENSUSE.split(":")[1]
        return self.get_local(rmi, rep, ver, "download.opensuse.org")
    def get_local(self, rmi, rep, ver, *hosts):
        image = "{rmi}/{rep}:{ver}".format(**locals())
        container = "{rep}-{ver}".format(**locals())
        data = OrderedDict()
        containers = [ { "name": container, "image": image }]
        addhosts = []
        for hostname in hosts:
            addhosts.append( { "name": container, "host": hostname })
        return { "containers": containers, "addhosts": addhosts }
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
        logg.debug("address %s for %s", addr, name)
        return addr
    def start_containers(self, image):
        data = self.get_local_mirror(image)
        done = {}
        for container in data["containers"]:
            image = container["image"]
            name = container["name"]
            addr = self.start_container(image, name)
            done[name] = addr
        return done
    def start_container(self, image, container):
        docker = DOCKER
        cmd = "{docker} inspect {image}"
        out, err, ok = output3(cmd.format(**locals()))
        image_found = json.loads(out)
        if not image_found:
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
        return addr
    def stop_containers(self, image):
        data = self.get_local_mirror(image)
        done = {}
        for container in data["containers"]:
            image = container["image"]
            name = container["name"]
            info = self.stop_container(image, name)
            done[name] = info
        return done
    def stop_container(self, image, container):
        docker = DOCKER
        done = []
        cmd = "{docker} inspect {container}"
        out, err, rc = output3(cmd.format(**locals()))
        container_found = json.loads(out)
        if not rc and container_found:
            cmd = "{docker} rm --force {container}"
            out, err, ok = output3(cmd.format(**locals()))
            status = container_found[0].get("State", {})
            started = status.get("StartedAt", "(was not started)")
            return started
        return "(did not exist)"
    def info_containers(self, image):
        data = self.get_local_mirror(image)
        done = {}
        for container in data["containers"]:
            image = container["image"]
            name = container["name"]
            info = self.info_container(image, name)
            done[name] = info
        return done
    def info_container(self, image, container):
        addr = self.ip_container(container)
        return addr
    def get_containers(self, image):
        data = self.get_local_mirror(image)
        done = []
        for container in data["containers"]:
            done.append(container["name"])
        return done
    def inspect_containers(self, image):
        data = self.get_local_mirror(image)
        docker = DOCKER
        done = []
        for container in data["containers"]:
            image = container["image"]
            name = container["name"]
            addr = self.ip_container(name)
            item = {}
            item["name"] = name
            item["image"] = image
            item["addr"] = addr or ""
            done.append(item)
        return done
    #
    def add_hosts(self, image, done = {}):
        data = self.get_local_mirror(image)
        args = []
        for addhosts in data["addhosts"]:
            host = addhosts["host"]
            name = addhosts["name"]
            if name in done:
                addr = done[name]
                if addr:
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
        image = self.local_system()
        return image
    def facts(self, image = None):
        if not image:
            image = self.local_system()
        data = self.get_local_mirror(image)
        return json.dumps(data, indent=2)
    def starts(self, image = None):
        if not image:
            image = self.local_system()
        done = self.start_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, done))
        else:
            return json.dumps(done, indent=2)
    def stops(self, image = None):
        if not image:
            image = self.local_system()
        done = self.stop_containers(image)
        if ADDHOSTS:
            names = sorted(done.keys())
            return " ".join(names)
        else:
            return json.dumps(done, indent=2)
    def infos(self, image = None):
        if not image:
            image = self.local_system()
        done = self.info_containers(image)
        if ADDHOSTS:
            return " ".join(self.add_hosts(image, done))
        else:
            return json.dumps(done, indent=2)
    def containers(self, image = None):
        if not image:
            image = self.local_system()
        done = self.get_containers(image)
        if ADDHOSTS:
            return " ".join(done)
        else:
            return json.dumps(done, indent=2)
    def inspects(self, image = None):
        if not image:
            image = self.local_system()
        done = self.inspect_containers(image)
        if ADDHOSTS:
            return " ".join(done)
        else:
            return json.dumps(done, indent=2)

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [-options] help|detect|image|info|facts|start|stop [image]")
    _o.add_option("-v", "--verbose", action="count", default=0, help="more logging")
    _o.add_option("-a", "--add-hosts", "--add-host", action="store_true", default=ADDHOSTS, 
        help="show options for 'docker run'")
    opt, args = _o.parse_args()
    logging.basicConfig(level = max(0, logging.WARNING - opt.verbose * 10))
    ADDHOSTS = opt.add_hosts
    command = "detect"
    arg = ""
    if len(args) >= 1:
        command = args[0]
    if len(args) >= 2:
        arg = args[1]
    repo = DockerMirrorPackagesRepo()
    if command in [ "?", "help"]:
        print repo.helps()
    elif command in [ "detect", "image" ]:
        print repo.detect()
    elif command in [ "facts" ]:
        print repo.facts(arg)
    elif command in [ "start" ]:
        print repo.starts(arg)
    elif command in [ "stop" ]:
        print repo.stops(arg)
    elif command in [ "show", "info", "infos" ]:
        print repo.infos(arg)
    elif command in [ "addhost", "add-host", "addhosts", "add-hosts" ]:
        ADDHOSTS = True
        print repo.infos(arg)
    elif command in [ "inspect" ]:
        print repo.inspects(arg)
    elif command in [ "containers" ]:
        print repo.containers(arg)
