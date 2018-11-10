# INIT-DAEMON

By tradition a docker container is an enhanced version
of a chroot environment. Through remapping Process IDs 
it does however contain a new PID-1 where an init daemon 
would live.

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
is the case for many `*.service` definitions with a type
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
read the "WantedBy" of the referenced `*.service` script.
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
remaining processes in the container.

For system services those 10 seconds are way too short. Be
sure to increase that to atleast 100 seconds to allow the
normal service scripts to bring down the applications
completely. How to increase the timeout depends on the tool
however, for example:

    docker stop --time 100 running
    docker run --stop-timeout 100 --name running image
    docker-compose.yml: stop_grace_period: 100
