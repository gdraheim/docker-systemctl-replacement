#! /usr/bin/env python

""" Testcases for docker-systemctl-replacement functionality """

__copyright__ = "(C) Guido Draheim, for free use (CC-BY,GPL) """
__version__ = "0.6.1135"

import subprocess
import os.path
import time
import datetime
import unittest
import shutil
import logging
from fnmatch import fnmatchcase as fnmatch

logg = logging.getLogger("tests")

def sh____(cmd, shell=True):
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd, shell=True):
    return subprocess.call(cmd, shell=shell)

class DockerSystemctlReplacementTest(unittest.TestCase):
    def testdir(self, testname):
        newdir = "tests/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
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
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag localhost:5000/tests:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} localhost:5000/tests:{name}"
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
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag localhost:5000/tests:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:5432 --name {name} localhost:5000/tests:{name}"
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
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag localhost:5000/tests:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} localhost:5000/tests:{name}"
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
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag localhost:5000/tests:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} localhost:5000/tests:{name}"
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
        # WHEN
        build_new_image = "docker build . -f tests/{dockerfile} --tag localhost:5000/tests:{name}"
        sh____(build_new_image.format(**locals()))
        drop_old_container = "docker rm --force {name}"
        start_as_container = "docker run -d -p {port}:80 --name {name} localhost:5000/tests:{name}"
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
    def test_9002_ansible_restart_docker_build_compose(self):
        """ bring up the build-step deployment containers """
        drop_old_containers = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        make_new_containers = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml up -d"
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
    def test_9003_ansible_run_build_step_playbooks(self):
        """ run the build-playbook (using ansible roles) """
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
    def test_9005_ansible_restart_docker_start_compose(self):
        """ bring up the start-step runtime containers from the new images"""
        drop_old_build_step = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        drop_old_containers = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml down"
        make_new_containers = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml up -d"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
    def test_9006_ansible_unlock_jenkins(self):
        """ unlock jenkins as a post-build config-example using selenium-server """
        inventory = "tests/docker-start-compose.ini"
        playbooks = "tests/docker-start-playbook.yml"
        variables = "-e LOCAL=yes -e j_username=installs -e j_password=installs.11"
        vartarget = "-e j_url=http://serversystem:8080/buildserver"
        ansible = "ansible-playbook -i {inventory} {variables} {vartarget} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        # TEST
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
        time.sleep(4)
        drop_old_build_step = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        drop_old_start_step = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml down"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_start_step}".format(**locals()))


if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
       epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v","--verbose", action="count", default=0,
       help="increase logging level (%default)")
    _o.add_option("-l","--logfile", metavar="FILE", default="",
       help="additionally save the output log to a file (%default)")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
       help="capture results as a junit xml file (%default)")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
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
