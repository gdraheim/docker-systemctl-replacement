#! /usr/bin/python
__copyright__ = " (C) Guido U. Draheim, for free use (CC-BY,GPL,BSD)"
__version__ = "1.0"

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import logging

logg = logging.getLogger("JenkinsSetup")

BASEURL="http://testingsystemctl2_serversystem_1:8080/linux"
USERNAME="install"
PASSWORD="install.1A"

def run(initialpassword, username = USERNAME, password = PASSWORD, baseurl = BASEURL):
    # driver = webdriver.Firefox()
    firefox=DesiredCapabilities.FIREFOX.copy()
    driver = webdriver.Remote(
        command_executor='http://127.0.0.1:4444/wd/hub',
        desired_capabilities=firefox)
    driver.get(baseurl)
    time.sleep(3)
    logg.info("check initialAdminPassword")
    time.sleep(2)
    if "initialAdminPassword" in driver.page_source:
        elem = driver.find_element_by_id("security-token")
        elem.clear()
        elem.send_keys(initialpassword)
        elem = driver.find_element_by_class_name("set-security-key")
        elem.click()
        time.sleep(15)
    logg.info("check install-recommended")
    time.sleep(2)
    if "install-recommended" in driver.page_source:
        elem = driver.find_element_by_class_name("install-recommended")
        elem.click()
        logg.info("done install-recommended - wait for admin user")
        for i in xrange(100):
           time.sleep(10)
           if "Create First Admin User" in driver.page_source:
               break
    logg.info("check First Admin User")
    time.sleep(2)
    if "Create First Admin User" in driver.page_source:
        logg.info("ready for admin user")
        elem = driver.find_element_by_name("username")
        elem.clear()
        elem.send_keys(username)
        elem = driver.find_element_by_name("password1")
        elem.clear()
        elem.send_keys(password)
        elem = driver.find_element_by_name("password2")
        elem.clear()
        elem.send_keys(password)
        elem = driver.find_element_by_name("fullname")
        elem.clear()
        elem.send_keys(username + " user")
        elem = driver.find_element_by_name("email")
        elem.clear()
        elem.send_keys(username + "@example.test")
        elem = driver.find_element_by_class_name("save-first-user")
        elem.click()
        time.sleep(5)
        elem = driver.find_element_by_class_name("install-done")
        elem.click()
        time.sleep(15)
    logg.info("check re-login")
    time.sleep(2)
    if driver.find_elements_by_class_name("login"):
        elem = driver.find_element_by_name("j_username")
        elem.clear()
        elem.send_keys(username)
        elem = driver.find_element_by_name("j_password")
        elem.clear()
        elem.send_keys(password)
        elem = driver.find_element_by_id("yui-gen1-button")
        elem.click()
        time.sleep(5)
    logg.info("check user description")
    time.sleep(2)
    if "Manage Jenkins" in driver.page_source:
        url= "%s/user/%s/configure" % (baseurl, username)
        driver.get(url)
        elem = driver.find_element_by_name("_.description")
        elem.clear()
        elem.send_keys("The install admin user is used by automation tools")
        time.sleep(5)
        driver.save_screenshot("initalJenkinsSetup.png")
        elem = driver.find_element_by_id("yui-gen3")
        elem.click()
    time.sleep(15)
    driver.close()
    driver.quit()


if __name__ == "__main__":
    import optparse
    _o = optparse.OptionParser("%prog [-f passwordfile")
    _o.add_option("-f","--passfile", metavar="PASSWORDFILE")
    _o.add_option("-b","--baseurl", metavar="URL", default=BASEURL)
    _o.add_option("-u","--username", metavar="USER", default=USERNAME)
    _o.add_option("-p","--password", metavar="PASS", default=PASSWORD)
    _o.add_option("-v","--verbose", action="count", default=0)
    opt, args = _o.parse_args()
    logging.basicConfig(level = max(0,logging.WARNING - (10 * opt.verbose)))
    if opt.passfile:
        initialpassword = open(opt.passfile).read()
    else:
        initialpassword = "admin"
    run(initialpassword, opt.username, opt.password, opt.baseurl)
