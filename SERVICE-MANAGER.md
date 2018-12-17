# Service Manager

The systemctl-replacement script is not really a replacement for SystemD itself.
Instead it covers enough functionality that one does not need to run a SystemD
daemon in a docker container in order to start/stop/run services in it.

In an operating system that is based on SystemD, the older unix scripts like 
"service xx start" and "service xx stop" are diverted to run "systemctl start xx"
and "systemctl stop xx". Additionally deployment tools like Ansible will ask
for the status of a service by executing the "systemctl" tool. Hence overwriting
/usr/bin/systemctl is sufficient to intercept all service management requests.

## Problems with SystemD in Docker

The background for this script is the inability to run a
SystemD daemon easily inside a docker container. There have
been multiple workarounds with varying complexity and actual
functionality. The systemd-nsspawn tool is supposed to help 
with  running systemd in a container - but only rkt with 
its CoreOs is using it so far.

Most people have come to take the easy path and to create a
startup shell script for the docker container that will
bring up the service processes one by one. Essentially one would
read the documentation or the SystemD `*.service` scripts of the
application to see how that would be done. By using this
replacement script a programmer can skip that step.

As a historic background this script was born when the
deployment targets shifted from RHEL6 (with initscripts)
to RHEL7 (with SystemD) and suddenly even a simple call
to "service app start" would result in errors from a missing
SystemD-daemon. By using this docker systemctl replacment
script one could continue with the original installers.

Please note that this systemctl replacement will also
read and interpret initscripts in /etc/init.d/. As such
you can also deploy older applications with a classic 
SysV-style start/stop script and they are handled similar 
to how SystemD would care for them.

## Usage along with Ansible

This script has been tested often along with deployments
using Ansible. As of version 2.0 and later Ansible is
able to connect to docker containers directly without the
help of a ssh-daemon in the container and a known-ip of 
the container. Just make your inventory look like

    [frontend]
    my_frontend_1 ansible_connection=docker

With a local docker container the turnaround times of
testing a deployment script are a lot shorter. If there
is an error it is much faster to get a fresh target host 
and to have the basic deployment parts run on it.

With the help of docker-compose one can bring up a
number of hosts as docker containers and to use Ansible
to orchestrate the deployment. Some of the containers
will actually be interconnected with each other and the
deployed services will only work with some other service
of another container to be running.

This is the main difference over Dockerfiles which can
only build one container. And a Dockerfile is extremely
limited if the deployment includes the configuration of
services using their http-based API. Not so with a
deployment tool like Ansible.

## Installation as a systemctl-replacement

Simply overwrite /usr/bin/systemctl - but remember that
any package installation may update the real 'systemd'
so that you have to do the overwrite after every major
package installation. Or just do it firsthand.

    - name: update systemd
      package: name="systemd" state="latest"
      when: ansible_connection == 'docker'
    - name: install systemctl.py
      copy: src="files/docker/systemctl.py" dest="/usr/bin/systemctl"
      when: ansible_connection == 'docker'

Note that such a setup will also work when using Ansible's 
service module to start/stop/enable services on a target host.
On a systemd-controlled operating system the old "service" 
script will delegate commands to systemctl anyway.

## Diverted commands

When the systemctl-replacement has been installed as /usr/bin/systemctl
then it is also executed when then following commands are run

    service xx start   =>  systemctl start xx
    service xx stop    =>  systemctl stop xx
    service xx status  =>  systemctl status xx
    service xx reload  =>  systemctl reload xx
    chkconfig xx       =>  systemctl is-enabled xx
    chkconfig xx on    =>  systemctl enable xx
    chkconfig xx off   =>  systemctl disable xx

You can see that when enabling the implicit logging for systemctl.py by
doing a `touch /var/log/systemctl.log`

## Python Installation

At the time that systemctl.py was started all the docker images of the
established Linux distros (redhat/centos, ubuntu, opensuse) had Python
preinstalled - just as on the real machines where these distros are 
installed, as Python is used heavily in configuration scripts for these
operating systems.

However Python has since been removed in later versions of the official
docker images of these Linux distros in an attempt to lower the size of
the images used to build application containers. As such you need to
extend the initial setup steps for systemctl.py - in order to make it
work, you need to overwrite /usr/bin/systemctl and to install Python.

    - name: install systemctl.py
      copy: src="files/docker/systemctl.py" dest="/usr/bin/systemctl"
      when: ansible_connection == 'docker'
    - name: install python for systemctl.py
      package: name=python
      when: ansible_connection == 'docker'

You can also use `systemctl3.py` along with `python3` for the same effect.
