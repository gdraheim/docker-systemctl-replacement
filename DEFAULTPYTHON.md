## Default Python

Docker was shipped with RHEL 7.0 since 2014, and openSUSE adopted it in the same year.
Docker was dropped in RHEL 8.0 to be replaced by 'podman' which is mostly compatible.

centos:7.3.1611
* does not have /usr/libexec/platform-python
* python = python2
* python2 : installed (2.7.5)
* python3 : yum install --enablerepo=base -y python3 (3.6.8)

centos:7.4.1708
* does not have /usr/libexec/platform-python
* python = python2 
* python2 : installed (2.7.5)
* python3 ; yum install --enablerepo=base -y python3 (3.6.8)

centos:7.5.1804
* does not have /usr/libexec/platform-python
* python = python2 
* python2 : installed (2.7.5)
* python3 ; yum install --enablerepo=base -y python3 (3.6.8)

centos:7.6.1810
* /usr/libexec/platform-python = python2
* /usr/libexec/platform-python : installed (2.7.5)
* python = python2 
* python2 : installed (2.7.5)
* python3 ; yum install --enablerepo=base -y python3 (3.6.8)

centos:7.7.1908
* /usr/libexec/platform-python = python2
* /usr/libexec/platform-python : installed (2.7.5)
* python = python2 
* python2 : installed (2.7.5)
* python3 ; yum install --enablerepo=base -y python3 (3.6.8)
* /usr/libexec/platform-python : (n/a)

centos:8.0.1905
* /usr/libexec/platform-python = python3
* /usr/libexec/platform-python : installed (3.6.8)
* python2 : yum install --enablerepo=AppStream -y python2 (2.7.16)
* python2 = does not setup 'python'
* python3 ; yum install --enablerepo=BaseOS -y python3 (3.6.8)
* python2 = does not setup 'python'

centos:8.1.1911
* /usr/libexec/platform-python = python3
* /usr/libexec/platform-python : installed (3.6.8)
* python2 : yum install --enablerepo=AppStream -y python2 (2.7.16)
* python2 = does not setup 'python'
* python3 ; yum install --enablerepo=BaseOS -y python3 (3.6.8)
* python2 = does not setup 'python'

almalinux:9.3 (2023.11)
* /usr/libexec/platform-python = python3
* /usr/libexec/platform-python : installed (3.9.18)
* python2 = does not exist (yum install python does install python3)
* python3 ; yum install --enablerepo=BaseOS -y python3 (3.9.18)
* python3 = python python3.9

opensuse:42.2 (2016.11)
* zypper is not python anymore
* python2 : zypper install -r OSS -y python2 (2.7.13)
* python2 = with 'python' (actually package 'python' provides 'python2')
* python3 : zypper install -r OSS -y python3 (3.4.6)
* python3 = does not setup 'python'

opensuse:42.3 (2017.07)
* zypper is not python anymore
* python2 : zypper install -r OSS -y python2 (2.7.13)
* python2 = with 'python' (actually package 'python' provides 'python2')
* python3 : zypper install -r OSS -y python3 (3.4.6)
* python3 = does not setup 'python'

opensuse/leap:15.0 (2018.05)
* zypper is binary
* python2 : zypper install -r repo-oss -y python2 (2.7.14)
* python2 = with 'python' (actually package 'python-base' provides 'python2')
* python3 : zypper install -r repo-oss -y python3 (3.6.5)
* python3 = does not setup 'python'

opensuse/leap:15.1 (2019.05)
* zypper is binary
* python2 : zypper install -r repo-oss -y python2 (2.7.14)
* python2 = with 'python' (actually package 'python-base' provides 'python2')
* python3 : zypper install -r repo-oss -y python3 (3.6.5)
* python3 = does not setup 'python'

opensuse/leap:15.2 (2020.05)
* zypper is binary
* python2 : zypper install -r repo-oss -y python2 (2.7.17)
* python2 = with 'python' (actually package 'python-base' provides 'python2')
* python3 : zypper install -r repo-oss -y python3 (3.6.10)
* python3 = does not setup 'python'

opensuse/leap:15.4 (2022.06)
* zypper is binary
* python2 : zypper install -r repo-oss -y python2 (2.7.18)
* python2 = with 'python' (actually package 'python-base' provides 'python2')
* python3 : zypper install -r repo-oss -y python3 (3.6.15)
* python3 = does not setup 'python'
* python310 : zypper install python310 (3.10.13)
* python310 = python3.10
* python311 : zypper install python311 (3.11.5)

opensuse/leap:15.5 (2023.06)
* zypper is binary
* python2 : zypper install -r repo-oss -y python2 (2.7.18)
* python3 : zypper install -r repo-oss -y python3 (3.6.15)
* python3 = does not setup 'python'
* python310 : zypper install python310 (3.10.13)
* python310 = python3.10
* python311 : zypper install python311 (3.11.5)

ubuntu:16.04
* apt is binary
* python2 : apt-get install -y python (2.7.12)
* python2 = with 'python' (note that there is no package 'python2')
* python3 : apt-get install -y python3 (3.5.2)
* python3 = does not setup 'python'

ubuntu:18.04
* apt is binary
* python2 : apt-get install -y python (2.7.17)
* python2 = with 'python' (note that there is no package 'python2')
* python3 : apt-get install -y python3 (3.6.9)
* python3 = does not setup 'python'

ubuntu:20.04
* apt is binary
* python2 : apt-get install -y python (2.7.17)
* python2 = with 'python' (python installs package 'python2')
* python3 : apt-get install -y python3 (3.8.2)
* python3 = python3.8 # does not setup 'python' (python3 installs package 'python3.8')
* python3.9 : apt-get install -y python3.9 (3.9.5)
* python3.9 = python3.9 # does not setup 'python' nor 'python3'

ubuntu:22.04
* apt is binary
* python2 : apt-get install -y python2 (2.7.18)
* python2 = does not setup 'python'
* python3 : apt-get install -y python3 (3.10.6)
* python3 = python3.10 # does not setup 'python' (python3 installs package 'python3.10')
* python311 : apt-get install -y python3.11 (3.11.0)
* python311 = python3.11 # does not setup 'python' nor 'python3'

ubuntu:24.04
* apt is binary
* python2 = does not exist (yum install python does not even install python3)
* python3 : apt-get install -y python3 (3.11.7)
* python3 = python3.11 # does not setup 'python' (python3 installs package 'python3.11')
* python312 : apt-get install -y python3.12 (3.12.1)
* python312 = python3.12 # does not setup 'python' nor 'python3'
