# docker systemctl replacement

This script may be used to overwrite "/usr/bin/systemctl".   
It will execute the systemctl commands without SystemD!

This is used to test deployment of services with a docker
container as the target host. Just as on a real machine you 
can use "systemctl start" and "systemctl enable" and other 
commands to bring up services for further configuration and 
testing.

This script can also be run as PID 1 of a docker container
(i.e. the main "CMD") where it will automatically bring up
all enabled services in the "multi-user.target" and where it 
will reap all zombies from background processes in the container.
When running a "docker stop" on such a container it will also 
bring down all configured services correctly before exit.

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
with docker containers.

See [SERVICE-MANAGER](SERVICE-MANAGER.md) for more details.

---

## Problems with PID 1 in Docker

The command listed as "CMD" in the docker image properties
or being given as docker-run argument will become the PID-1
of a new container. Actually it takes the place that would
traditionally be used by the /sbin/init process which has
a special functionality in unix'ish operating systems.

For one part, it is there to start up the system to a
specific runlevel. What is known as runlevel "5" in SysV
is the "multi-user.target" in SystemD. When the system is
halted it will send a stop to other processes giving them
a chance to shutdown cleanly.

The docker-stop command will send a SIGTERM to PID-1 in
the container - but NOT to any other process. If the CMD
is the actual application (java -jar whatever) then this
works fine as it will also clean up its subprocesses. If
you need multiple processes then most developers tend to 
write a shell script ("run.sh") to start them up but they 
forget to intercept the SIGTERM in the shell script including
a handler to shutdown started subprocesses. After a grace
period (of 10 seconds by default) the docker-stop will
turn to send SIGKILL to all remaining processes in the
container. So the application data is not ensured to be
clean at that point.

Another part of PID 1 is that it will adopt all background
processes where the parent has already died (or where the
process has explicitly "disown"ed the subprocess). This
is the case for many *.service definitions with a type
of "forking". In general these have use a PIDfile to know
how to send a SIGTERM signal to the background process. 
But without an init-process at PID-1 this will create 
zombie processes in the docker container that will
continue to exist forever.

As such one would need to implement a so-called "zombie reaper" 
functionality for the process at PID-1. This is not easy
to be done in a plain shell script. But there are number 
of implementations available already that can do it. And 
this script will also serve as a docker-init-replacement.

## The docker-init-replacement

When a "docker-stop" sends a SIGTERM to PID-1 then it may
expect that it indirectly runs "systemctl halt" to shut
down the running services. The docker-systemctl-replacement
does implement that function - so where "systemctl default"
will run a "systemctl start" on all "is-enabled" services, 
the inverse "system halt" command will run a "systemctl stop"
on all those services.

Of course it would be possible to write a second script to
implement the docker-init-replacement functionality but it
is integrated here. Just run the systemctl.py as the PID-1
process and it will implicitly call its functionality of
"systemctl -1 default", and upon receiving a SIGTERM from
docker-stop it will run its "systemctl halt" implementation.

Here "default" is the standard command to start all services 
in the multi-user target. The new option "--init" (or the command 
"init") will keep the script running as a zombie reaper. (NOTE: 
if it is not PID-1 then it defaults "systemctl list-units").

As a hint: the SystemD "systemctl enable" command will
read the "WantedBy" of the referenced *.service script.
For all the targets listed in there it will create a
symlink - for the common "multi-user.target" this will
be in /etc/systemd/system/multi-user.target.wants/.

The docker-systemctl-replacement knows about that and
it is used. And as another hint: if you run the script
as "systemctl.py init" then pressing Control-C will result
in an interpretation of "systemctl halt" as well, so
one can test the correct interpretion of the "wants".

## Installation as an init-replacement

For the systemctl-replacement it is best to overwrite
the original /usr/bin/systemctl because a number of
tools call that indirectly to start/stop services. This
is very true for Ansible's 'service' module.

For an init-replacement it may be placed anywhere in
the docker image, let's say it is /usr/bin/systemctl.py.
It will be activated by listing that path in the CMD
element of a Dockerfile.

If you do not use a Dockerfile (for example using an
Ansible script for deployment to a docker container) 
then you can add the attribute upon the next 
"docker commit" like this:

    docker commit -c "CMD ['/usr/bin/systemctl.py']" \
        -m "<comment>" <container> <new-image>

If the script is being installed as /usr/bin/systemctl
anyway then you may just want to reference that. (Left
for an excercise here). If only a specific set of
services shall be run then one can exchange the "default"
command with an explicit start list (and be sure to 
activate the continued execution as an init process):

    /usr/bin/systemctl.py init mongodb myapp

## Remember the stop grace timeout

Note that the docker daemon will send a SIGTERM to the PID 1
of a docker container that will result in the stop-behaviour
of the "systemctl init" loop. However the docker daemon will
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

---

## Testsuite and example images

There is an extensive testsuite in the project that allows
for a high line coverage of the tool. All the major functionality
of the systemctl.py is being tested so that its usage in 
continuous development pipeline will no break on updates of
the script. If the systemctl.py script has some important
changes in the implementation details it will be marked with
an update of the major version. 

Please run the `testsuite.py` or `make check` upon providing
a patch. It takes a couple of minutes because it may download
a number of packages during provisioning - with the help of the
scripting of the gdraheim/docker-centos-repo-mirror project this 
can be reduced a lot (it even runs without internet connection).

Some real world examples have been cut out into a seperate
project. This includes dockerfile and ansible based tests
to provide common applications like webservers, databases
and even a Jenkins application. You may want to have a look
at https://github.com/gdraheim/docker-systemctl-images

## Something is not implemented

Although this script has been developed for quite a while,
it does only implement a limited number of commands. And
it should still be considered in a Beta state. In all the
existing implementations the replacement should produce 
a similar output compared to SystemD's systemctl as a number 
of tools are interpreting the output.

Sadly the functionality of SystemD's systemctl is badly
documented so that much of the current implementation is
done by trial and fixing the errors. As most programmers
tend to write very simple *.service files it works in a
surprising number of cases however. But definitly not all.

I take patches. ;)

## The author

Guido Draheim is working as a freelance consultant for
multiple big companies in Germany. This script is related to 
the current surge of DevOps topics which often use docker 
as a lightweight replacement for cloud containers or even 
virtual machines. It makes it easier to test deployments
in the standard build pipelines of development teams.

