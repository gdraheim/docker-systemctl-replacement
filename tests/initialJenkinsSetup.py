#! /usr/bin/python
"""
You must provide -f /var/lib/jenkins/secrets/initialAdminPasword pointing
to the actual location of the password file to be able to unlock the Jenkins 
that has just been installed and started up.
                                                                          .
By default it will create a first admin user named 'install' that can be used
for steps after unlocking Jenkins. The later steps will probably use the  API.
                                                                          .
If the scripts runs on a Cloudbees product then it can automatically acquire
a trial license - be sure to provide atleast a -T email@address to track the
instances that have been used so far.
"""

__copyright__ = " (C) Guido U. Draheim, licensed under the EUPL"
__version__ = "1.1.2177"

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import os.path
import time
import logging
from urlparse import urlparse
from fnmatch import fnmatch

logg = logging.getLogger("JenkinsSetup")

class Program:
    SELENIUM_REMOTE="http://localhost:4444/wd/hub"
    BASE_URL=""
    INITIAL_PASSWORD_FILE="" # new style
    INITIAL_PASSWORD="admin" # old style
    INITIAL_USERNAME="admin"
    USERNAME="install"
    PASSWORD="{username}.1A"
    FULLNAME="{username} user"
    EMAIL="{username}@{hostdomain}"
    BASE_URL="http://testingsystemctl2_serversystem_1:8080/linux"
    SCREENSHOT=""
    SLOW = 2
    LONGWAIT = 300
    LICENSE_FULLNAME = ""
    LICENSE_EMAIL = ""
    LICENSE_COMPANY = ""
    ref_manual_license="#btn-com_cloudbees_jenkins_plugins_license_ManualRegistrar"
    ref_trial_license="#btn-com_cloudbees_opscenter_server_license_OperationsCenterEvaluationRegistrar"
    ref_plugins=".install-recommended"
    ref_firstuser = ".save-first-user"
    ref_done = ".install-done"
    ref_done_restart = ".install-done-restart"
    def __init__(self):
        self.base_url = self.BASE_URL
        self.initial_password_file = self.INITIAL_PASSWORD_FILE
        self.initial_password = self.INITIAL_PASSWORD
        self.initial_username = self.INITIAL_USERNAME
        self.username = self.USERNAME
        self.password = self.PASSWORD
        self.fullname = ""
        self.email = ""
        self.description = "The {username} admin user is used by automation tools"
        self.screenshot = self.SCREENSHOT
        self.slow = int(self.SLOW)
        self.driver = None
    def sleep(self, seconds = None):
        time.sleep(seconds or self.SLOW)
    def exists_element_by(self, ref):
        if ref.startswith("#"):
            if 'id="%s"' % ref[1:] in self.driver.page_source:
                return True
            return False
        else:
            if self.find_elements_by(ref):
                return True
            return False
    def find_elements_by(self, ref):
        if " " in ref:
            search, pattern = ref.split(" ", 1)
            result = []
            for elem in self.find_elements_by(search):
                text = elem.text
                if fnmatch(text.strip(), pattern):
                    result.append(elem)
            logg.info("found %s for '%s'", len(result), ref)
            return result
        if ref.startswith("#"):
            return [ self.driver.find_element_by_name(ref[1:]) ]
        if ref.startswith("="):
            return self.driver.find_elements_by_name(ref[1:])
        if ref.startswith("."):
            return self.driver.find_elements_by_class_name(ref[1:])
        if ref.startswith(">"):
            return self.driver.find_elements_by_tag_name(ref[1:])
        logg.error("bad ref %s", ref)
        raise Exception("bad ref %s", ref)
    def find_element_by(self, ref):
        if " " in ref:
            result = self.find_elements_by(ref)
            if result: return result[0]
            logg.error("not matched: %s", ref)
        if ref.startswith("#"):
            return self.driver.find_element_by_id(ref[1:])
        if ref.startswith("="):
            return self.driver.find_element_by_name(ref[1:])
        if ref.startswith("."):
            return self.driver.find_element_by_class_name(ref[1:])
        if ref.startswith(">"):
            return self.driver.find_element_by_tag_name(ref[1:])
        logg.error("bad ref %s", ref)
        raise Exception("bad ref %s", ref)
    def run(self):
        self.do_begin()
        self.do_unlock()
        self.do_license
        self.do_plugins()
        self.do_firstuser()
        self.do_done()
        self.do_login()
        self.do_description()
        self.do_end()
    def do_begin(self):
        logg.info("selenium at %s", self.SELENIUM_REMOTE)
        # driver = webdriver.Firefox()
        firefox=DesiredCapabilities.FIREFOX.copy()
        self.driver = webdriver.Remote(
            command_executor=self.SELENIUM_REMOTE,
            desired_capabilities=firefox)
        logg.info("start at %s", self.base_url)
        self.driver.get(self.base_url)
        self.sleep()
        logg.debug("wait for browser to come up")
        self.sleep()
    def do_unlock(self):
        """ that's usually a blocker in the setup process """
        if self.initial_password_file:
            text = open(self.initial_password_file).read()
            initial_password = text.strip()
            initial_username = self.initial_username
        else:
            initial_password = self.initial_password
            initial_username = self.initial_username
        logg.info("check initialAdminPassword")
        self.sleep()
        if "initialAdminPassword" in self.driver.page_source:
            elem = self.find_element_by("#security-token")
            elem.clear()
            elem.send_keys(initial_password)
            elem = self.find_element_by(".set-security-key")
            elem.click()
            for x in xrange(10):
                self.sleep()
                if self.exists_element_by(self.ref_trial_license):
                    break
                if self.exists_element_by(self.ref_plugins):
                    break
                if self.exists_element_by(self.ref_firstuser):
                    break
                logg.info("waiting...")
    def do_license(self):
        """ you'll have that with Cloudbees EE / OC """
        logg.info("check license")
        self.sleep()
        if self.exists_element_by(self.ref_trial_license):
            for x in xrange(10):
                self.sleep()
                if "firstName" in self.driver.page_source:
                    break
                logg.info("waiting...")
            fullname = self.LICENSE_FULLNAME
            email = self.LICENSE_EMAIL
            company = self.LICENSE_COMPANY
            if not company and email:
                company = email.split("@")[1]
                if "." in company:
                    company = company.split(".")[-2]
                company = company.replace("-", " ").title()
            if not fullname and email:
                fullname = email.split("@")[0]
                if "." in fullname:
                    fullname = fullname.replace("."," ").title()
                else:
                    fullname = (fullname[0:1] + " " + fullname[1:]).title()
            elem = self.find_element_by(self.ref_trial_license)
            elem.click()
            self.sleep()
            elem = self.find_element_by("=firstName")
            elem.clear()
            elem.send_keys(fullname.rsplit(" ",1)[0])
            elem = self.find_element_by("=lastName")
            elem.clear()
            elem.send_keys(fullname.rsplit(" ",1)[1])
            elem = self.find_element_by("=email")
            elem.clear()
            elem.send_keys(email)
            elem = self.find_element_by("=company")
            elem.clear()
            elem.send_keys(company)
            elem = self.find_element_by("=subscribe")
            if elem.is_selected():
                logg.info("subscribe space")
                elem.send_keys(" ")
            if elem.is_selected():
                logg.info("subscribe click")
                elem.click()
            if elem.is_selected():
                logg.warning("subscribe still selected")
            elem = self.find_element_by("=agree")
            if not elem.is_selected():
                logg.info("agree space")
                elem.send_keys(" ")
            if not elem.is_selected():
                logg.info("agree click")
                elem.click()
            if not elem.is_selected():
                logg.warning("still not selected")
            elem = self.find_element_by(".btn-primary")
            # elem.click()
            for x in xrange(10):
                self.sleep()
                if self.exists_element_by(self.ref_plugins):
                    break
                if self.exists_element_by(self.ref_firstuser):
                    break
                logg.info("waiting...")
    def do_plugins(self):
        """ it does need internet access to download plugins """
        logg.info("check plugins")
        self.sleep()
        if self.exists_element_by(self.ref_plugins):
            elem = self.find_element_by(self.ref_plugins)
            elem.click()
            logg.info("done install-recommended - wait for admin user")
            for i in xrange((int(self.LONGWAIT) * 4)/ int(self.slow)):
                self.sleep()
                if self.exists_element_by(self.ref_firstuser):
                    self.sleep()
                    break
                logg.info("waiting...")
    def do_firstuser(self):
        """ create the admin user for later automated config steps """
        logg.info("check First Admin User")
        self.sleep()
        if self.exists_element_by(self.ref_firstuser):
            logg.info("ready for admin user")
            self.driver.switch_to.default_content()
            for iframe in self.find_elements_by(">iframe"):
                src = str(iframe.get_attribute("src"))
                logg.debug("check iframe src=%s", )
                if  "WizardFirstUser" in src:
                    logg.info("found iframe src=%s", src)
                    self.driver.switch_to_frame(iframe)
                    break
            # for default expansions
            url = urlparse(self.base_url)
            hostname = url.hostname
            hostdomain = hostname.split(".",1)[0]
            username = self.username
            password = self.password.format(**locals())
            fullname = self.fullname.format(**locals())
            email = self.email.format(**locals())
            if not email:
                email = username + "@example.test"
            if not fullname:
                email = (username + " user").title()
            elem = self.find_element_by("#username")
            elem.clear()
            elem.send_keys(username)
            elem = self.find_element_by("=password1")
            elem.clear()
            elem.send_keys(password)
            elem = self.find_element_by("=password2")
            elem.clear()
            elem.send_keys(password)
            elem = self.find_element_by("=fullname")
            elem.clear()
            elem.send_keys(fullname)
            elem = self.find_element_by("=email")
            elem.clear()
            elem.send_keys(email)
            #
            self.driver.switch_to.default_content()
            elem = self.find_element_by(".save-first-user")
            elem.click()
            self.sleep()
    def do_done(self):
        """ click away the message that we are done here. """
        logg.info("check for final screen")
        if self.exists_element_by(self.ref_done):
            self.sleep()
            elem = self.find_element_by(self.ref_done)
            elem.click()
            self.sleep()
        elif self.exists_element_by(self.ref_done_restart):
            self.sleep()
            elem = self.find_element_by(self.ref_done_restart)
            elem.click()
            self.sleep()
            self.do_waitlogin()
            self.do_login()
    def do_restart(self):
        """ optional: the Cloudbees products do it anyway. """
        logg.info("restart now")
        self.sleep()
        if True:
            base_url = self.base_url
            url= "{base_url}/restart".format(**locals())
            self.driver.get(url)
            elem = self.find_element_by("#yui-gen1-button")
            elem.click()
            self.sleep()
            self.do_waitlogin()
    def do_waitlogin(self):
        """ optional: only if you restart after unlock is done. """
        for x in xrange(100):
            if self.find_elements_by("=j_username"):
                break
            logg.info("waiting...")
            self.sleep()
    def do_login(self):
        """ check that the new admin user works. """
        username = self.username
        password = self.password.format(**locals())
        logg.info("check re-login")
        if self.find_elements_by("=j_username"):
            elem = self.find_element_by("=j_username")
            elem.clear()
            elem.send_keys(username)
            elem = self.find_element_by("=j_password")
            elem.clear()
            elem.send_keys(password)
            elem = self.find_element_by("#yui-gen1-button")
            elem.click()
            self.sleep()
    def do_description(self):
        """ and use it to update the user description. """
        logg.info("check user description")
        self.sleep()
        if "Manage Jenkins" in self.driver.page_source:
            logg.info("ready for screenshot")
            username = self.username
            description = self.description.format(**locals())
            base_url = self.base_url
            url= "{base_url}/user/{username}/configure".format(**locals())
            self.driver.get(url)
            elem = self.find_element_by("=_.description")
            elem.clear()
            elem.send_keys(description)
            self.sleep()
            if self.screenshot:
                logg.info("screenshot into %s", self.screenshot)
                self.driver.save_screenshot(self.screenshot)
            elem = self.find_element_by("#yui-gen3")
            elem.click()
        else:
            if self.screenshot:
                logg.info("screenshot into %s", self.screenshot)
                self.driver.save_screenshot(self.screenshot)
    def do_sleep(self):
        """ optional: just for testing to a look """
        self.sleep(self.LONGWAIT)
    def do_end(self):
        """ tears down the browser we used since 'begin' """
        logg.info("done - tear down")
        self.sleep(self.slow * 5)
        self.driver.close()
        self.driver.quit()
        self.driver = None


if __name__ == "__main__":
    import optparse
    _o = optparse.OptionParser("%prog [-f passwordfile", epilog=__doc__)
    _o.add_option("-B","--selenium", metavar="URL", default=Program.SELENIUM_REMOTE,
           help="selenium remote service [%default]")
    _o.add_option("-b","--base_url", metavar="URL", default=Program.BASE_URL,
           help="selenium target baseurl [%default]")
    _o.add_option("-f","--initpassfile", metavar="PASSWORDFILE", default=Program.INITIAL_PASSWORD_FILE,
           help="unlock user password file [%default]")
    _o.add_option("-u","--initusername", metavar="USERNAME", default=Program.INITIAL_USERNAME,
           help="unlock user username [%default]")
    _o.add_option("-p","--initpassword", metavar="PASSWORD", default=Program.INITIAL_PASSWORD,
           help="unlock user password [%default]")
    _o.add_option("-U","--username", metavar="USER", default=Program.USERNAME,
           help="admin user username [%default]")
    _o.add_option("-P","--password", metavar="PASS", default=Program.PASSWORD,
           help="admin user password [%default]")
    _o.add_option("-F","--fullname", metavar="USER", default=Program.FULLNAME,
           help="admin user fullname [%default]")
    _o.add_option("-E","--email", metavar="PASS", default=Program.EMAIL,
           help="admin user email [%default]")
    _o.add_option("-T","--license_email", metavar="PASS", default=Program.LICENSE_EMAIL,
           help="trial license user email [%default]")
    _o.add_option("--slow", metavar="SECONDS", default=Program.SLOW,
           help="slow next step after clicks/checks [%default]")
    _o.add_option("--screenshot", metavar="FILE", default=Program.SCREENSHOT,
           help="save a final screenshot [%default]")
    _o.add_option("--logfile", metavar="FILE", default="/var/log/initialJenkinsSetup.log",
           help="write log if exists [%default]")
    _o.add_option("-v","--verbose", action="count", default=0,
           help="increase debug output [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level = max(0,logging.WARNING - (10 * opt.verbose)))
    if opt.logfile and os.path.exists(opt.logfile):
       loggfile = logging.FileHandler(opt.logfile)
       loggfile.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
       logg.addHandler(loggfile)
       logg.setLevel(max(0, logging.INFO - 10 * opt.verbose))
    exe = Program()
    exe.selenium_remote = opt.selenium
    exe.base_url = opt.base_url
    exe.initial_password_file = opt.initpassfile
    exe.initial_password = opt.initpassword
    exe.initial_username = opt.initusername
    exe.username = opt.username
    exe.password = opt.password
    exe.fullname = opt.fullname
    exe.email = opt.email
    exe.slow = int(opt.slow)
    exe.screenshot = opt.screenshot
    exe.LICENSE_EMAIL = opt.license_email
    if not args:
        exe.run()
    else:
        for arg in args:
            func = getattr(exe, "do_"+arg)
            if callable(func):
                logg.info("====> %s", arg)
                func()
            else:
                logg.error("no such command: %s", arg)

