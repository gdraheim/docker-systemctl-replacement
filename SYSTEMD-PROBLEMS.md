## Problems with SystemD in Docker

The background for this script is the inability to run a
SystemD daemon easily inside a docker container. There have
been multiple workarounds with varying complexity and actual
functionality. (The systemd-nsspawn tool is supposed to help 
with  running systemd in a container but only rkt with CoreOs 
is using it so far).

Most people have come to take the easy path and to create a
startup shell script for the docker container that will
bring up the service processes one by one. Essentially one would
read the documentation or the SystemD `*.service` scripts of the
application to see how that would be done. By using this
replacement script a programmer can skip that step.

## Service Manager

The systemctl-replacement script does cover the functionality
of a service manager where commands like `systemctl start xx`
are executed. This is achieved by parsing the `*.service`
files that are installed by the standard application packages 
(rpm, deb) in the container. These service unit descriptors
define the actual commands to start/stop a service in their
ExecStart/ExecStop settings.

When installing systemctl.py as /usr/bin/systemctl in a
container then it provides enough functionality that
deployment scripts for virtual machines continue to
work unchanged when trying to start/stop, enable/disable
or mask/unmask a service in a container.

This is also true for deployment tools like Ansible. As of 
version 2.0 and later Ansible is able to connect to docker 
containers directly without the help of a ssh-daemon in 
the container. Just make your inventory look like

    [frontend]
    my_frontend_1 ansible_connection=docker

Based on that `ansible_connection` one can enable the
systemctl-replacement to intercept subsequent calls
to `"service:"` steps. Effectivly Ansible scripts that 
shall be run on real virtual machines can be tested 
with docker containers. However in newer centos/ubuntu
images you need to check for python first.

    - copy: src="files/docker/systemctl.py" dest="/usr/bin/systemctl"
    - package: name="python"
    - file: name="/run/systemd/system/" state="directory"
    - service: name="dbus.service" state="stopped"

See [SERVICE-MANAGER](SERVICE-MANAGER.md) for more details.

---

## Problems with PID 1 in Docker

The command listed as "CMD" in the docker image properties
or being given as docker-run argument will become the PID-1
of a new container. Actually it takes the place that would
traditionally be used by the /sbin/init process which has
a special functionality in unix'ish operating systems.

The docker-stop command will send a SIGTERM to PID-1 in
the container - but NOT to any other process. If the CMD
is the actual application (exec java -jar whatever) then 
this works fine as it will also clean up its subprocesses. 
In many other cases it is not sufficient leaving 
[zombie processes](https://www.howtogeek.com/119815/) 
around.

Zombie processes may also occur when a master process does 
not do a `wait` for its children or the children were
explicitly "disown"ed to run as a daemon themselves. The
systemctl replacment script can help here as it implements 
the "zombie reaper" functionality that the standard unix
init daemon would provide. Otherwise the zombie PIDs would
continue to live forever (as long as the container is
running) filling also the process table of the docker host
as the init daemon of the host does not reap them.

## Init Daemon

Another function of the init daemon is to startup the
default system services. What has been known as runlevel
in SystemV is now "multi-user.target" or "graphical.target"
in a SystemD environment.

Let's assume that a system has been configured with some
"systemctl enable xx" services. When a virtual machine
starts then these services are started as well. The
systemctl-replacement script does provide this functionality
for a docker container, thereby implementing
"systemctl default" for usage in inside a container.

The "systemctl halt" command is also implemented
allowing to stop all services that are found as
"is-enabled" services that have been run upon container
start. It does execute all the "systemctl stop xx"
commands to bring down the enabled services correctly.

This is most useful when the systemctl replacement script 
has been run as the entrypoint of a container - so when a 
"docker stop" sends a SIGTERM to the container's PID-1 then 
all the services are shut down before exiting the container.
This can be permanently achieved by registering the
systemctl replacement script  as the CMD attribute of an 
image, perhaps by a "docker commit" like this:

    docker commit -c "CMD ['/usr/bin/systemctl']" \
        -m "<comment>" <container> <new-image>

After all it allows to use a docker container to be
more like a virtual machine with multiple services
running at the same time in the same context.

See [INIT-DAEMON](INIT-DAEMON.md) for more details.
