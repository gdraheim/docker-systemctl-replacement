# docker systemctl replacement

This script may be used to overwrite "/usr/bin/systemctl"   
It will execute the systemctl commands without SystemD!

This is used to test deployment of services with a docker
container as the target host. Just as on a real machine you 
can use "systemctl start" and "systemctl enable" and other 
commands to bring up services for further configuration and 
testing.

This is achieved by reading and interpreting "*.service"
files that have been deployed in the docker container. In
many cases those will be in /etc/systemd/system/. Not only
the "simple" but also "forking" service types are handled
correctly, with the referenced PIDfile used to tell whether 
the service is running fine.

This script can also be run as PID 1 of a docker container
(i.e. the main "CMD") where it will automatically bring up
all enabled services in the "multi-user.target" and where it 
will reap all zombies from background processes in the container.
When running a "docker stop" on such a container it will also 
bring down all configured services correctly before exit.

## Problems with SystemD

The background for this script is the inability to run a
SystemD daemon easily inside a docker container. There have
been multiple workarounds with varying complexity and actual
functionality.

Most people have come to take the easy path and to create a
startup shell script for the docker container that will
bring up the service processes one by one. Essentially one would
read the documentation or the SystemD *.service scripts of the
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

## Installation

Simply overwrite /usr/bin/systemctl - for an additional
benefit you could try to lock updates of the systemd
package so that no newer "systemctl" can be installed
through a system update.

    - name: docker files
      copy: src="files/docker" dest="files/"
      when: ansible_connection == 'docker'
    - name: docker lock systemd
      shell: |
           test -d /run/systemd/system || mkdir /run/systemd/system # defeat newer ansible
           yum update -y systemd; yum install -y yum-versionlock; yum versionlock systemd; 
    - name: docker override systemctl
      shell: |
           cat files/docker/systemctl.py >/usr/bin/systemctl
      become: yes
      when: ansible_connection == 'docker'


## The docker-init-replacement

The script was born as to only interpret *.service files
but it became soon obvious that some stopped service
applications would simply send a kill signal the background
worker process assuming that the "init" process would
adopt and reap them.

That is not the case for a docker container however with
zombie processes lying around from previous "systemctl stop"
commands. Well the problem of zombies in a docker container
is not limited to service-scripts - it has been discussed
multiple times how to create an "init" replacement to be
run as PID 1 in a container.

Based on that information the "systemctl" replacement script
will also work as an "init" replacement script. It will
automatically turn to that functionality if it is run without
arguments and if it finds itself to be PID 1.

If the script is run without arguments and it is NOT at PID 1
the it will run "list-units" as the default command.

The funcationality of the init-replacment can be forced by
saying "systemctl 1". This is the combination of two 
commands - the first is "systemctl default" which is a
standard command of SystemD's systemctl. The 'default' run
level is assumed to be "multi-user.target" here - have a
look at the *.system file if that is listed as a "WantedBy", 
and wether it "is-enabled" which will result in a symlink 
in /etc/systemd/system/multi-user.target.wants/

When the "default" services have been started, the functionality
of the init-replacement will turn to "systemctl wait" (a new
command here). It will periodically check the linux process table
in /proc for zombies and reap them. When it gets a Control-C
or a "docker stop" it will execute "systemctl halt" which 
mimics the standard behaviour in running "stop" on each of
the level's services.

## Check stop grace timeout

Note that the docker daemon will send a SIGTERM to the PID 1
of a docker container that will result in the stop-behaviour
of the "systemctl wait" loop. However the docker daemon will
only wait 10 seconds by default and when the container has
not stopped completely it will send a SIGKILL to all the
remaining process in the container.

For system services those 10 seconds are way too short. Be
sure to increase that to atleast 100 seconds to allow the
normal service scripts to bring down the applications
completely. How to increase the timeout depends on the tool
however, for example:

    docker stop --time 100 running
    docker run --stop-timeout 100 --name running image
    docker-compose.yml: stop_grace_period: 100

## Some not implemented

Only a limited number of commands are implemented. They
should produce a similar output compared to SystemD's
systemctl as a number of tools are interpreting the
output.

Sadly the functionality of SystemD's systemctl is badly
documented so that much of the current implementation is
done by trial and fixing the errors. As most programmers
tend to write very simple *.service files it works in a
surprising number of cases however. But definitly not all.

I take patches. ;)

## The author

Guido Draheim is working as a freelance consultant for
multiple big companies in Germany (please ignore references
in the Makefile relating them). This script is related to 
the current surge of DevOps topics which often use docker 
as a lightweight replacement for cloud containers or even 
virtual machines. It makes it easier to test deployments
in the standard build pipelines of development teams.






