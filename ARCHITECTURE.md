# ARCHITECTURE

The implementation of the systemctl replacement script does
not follow the model of systemd. Systemd was designed to work
as a central daemon in the first place while the systemctl
script does not use a daemon at all to provide its
functionality. While the result may be very similar there are
differences in detail.

## communication sockets

The systemd's systemctl program is actually a dumb tool. It
does mostly have no function at all other than looking for
a communication channel to talk to the systemd daemon. You
can ask the systemd daemon to open a TCP port but the default
is to use a unix file socket on `/var/run/systemd/private`.
So when you run a `systemctl start xy.service` then it will
simply send a message on that socket to the systemd daemon
which is running on PID-1 of your system (or the docker
container created by systemd-nsspawn).

Even when running the systemctl replacement script as PID-1
it does  not open such a file socket, and none of the calls
to `systemctl.py start xy.service` will try to find that kind
of socket. Each instance will run on its own. This includes
the requirement to open another file socket named
`/var/run/systemd/notify` which is used for the services
of `Type=notify`. The notify-services are essentially
forking-services but instead of assuming that a service
is state=active as soon as the xy-start.sh comes back the
tool needs to wait till the service has sent a message
that startup is complete. Apache is one prominent example
of a notify-service.

The systemctl replacement's notify-socket will only be
created as soon as the systemctl replacment script runs
a "start xy.service" and it is closed as soon as the
startup-wait has completed. Now what if there are multiple
`systemctl.py start` calls that run in parallel? Well, that
would lead into problems - so there is some mutex locking
needed. Only one systemctl script instance may be running
a service-start at a time.

This startup locking has been optimized meanwhile. For
one thing there is not one notify-socket but each
service gets its own. In systemctl script controlled
environment you will find a
`/var/run/systemd/notify.httpd.service` (or a similar
thing in the user-directory for user services). All
programs of Type=notify are supposed to watch for the
environment variable `$NOTIFY_SOCKET` and while this
will be always the same path in a systemd controlled
environment it is a different one when a program is
started through the systemctl replacement. It works.

## lock files

The optimization of per-service notify-sockets has
brought about the optimization that the mutex locking
for systemctl script actions is not global anymore. In
an early version of the systemctl replacement script
only one systemctl.py instance was allowed to run but
in later versions all the systemctl script instances
may run in parallel as long as they try to start/stop
a different xy.service.

So just like with the notify-socket files there are
multiple service-lock files around. They are created
just next to notify-socket files, so you can see them
popping up as `/var/run/systemd/httpd.service.lock`.
There is nothing similar with the original systemd
daemon as all actions are run by the single process
on PID-1 which can do the serialisation through its
own internal event loop.

When the systemctl replacement script runs as the
init-daemon on PID-1 it does not change its behaviour.
It will look for the enabled services and for each of
the services a lock-file is created on startup. As soon 
as the startup is complete they are unlocked. Actually 
it was a real-life observation when some xy.service
was calling a "systemctl start foo.service" during
its own startup phase, so the per-service locking
is a definite requirement.

As the service-locking is somewhat granular, a lot
of actions of the systemctl script do not run guarded
by an active lock. Obviously `systemctl cat xy.service`
does not need a lock at all. At the moment not even
`systemctl status xy.service` will ask for a mutex
locking although that could theoretically lead into
problems when a pid-file is removed midway of the
status detection. So far it just works fine.

## optional daemon-reload

So far you should have understood that all instances
of the systemctl script run independently and the 
behaviour does not change when the systemctl 
replacement script is the init-daemon on PID-1. When
the systemctl script on PID-1 has started all the 
services, it will basically sit silent with doing no
more actions other than reaping zombies reassigned by
the unix kernel. (And waiting for a SIGTERM to go for
the shutdown process but that's another topic).

For the systemd daemon however the one instance on
PID-1 is all there is. So when you make any changes
to the xy.service files on disk then it will not
have any effect on the next start/stop. You need to
initiate some `systemctl daemon-reload` to ask the
PID-1 process to scan for changes to the service
files. (There is a debug mode where the systemd
daemon will watch for that automatically but let's
disregard that here as it is not normally enabled).

The systemctl replacement script however will scan 
the service descriptors on each execution. Actually 
it will not only scan the `xy.service` descriptor 
file for the service that you like to start/stop but 
it will always scan all the descriptor files. That's
because any file may declare a requirement for another
service, especially in the `Requires=`, the `After=`
and the `Conflicts=` rules where the latter will say
that you need to stop another service before you are
allowed to start the current service.

Now `Conflicts` is not implemented at the time of
writing so that one could optimize to scan only one
descriptor file. But the saved time is not worth it.
The scanning of the service files is quick enough
that you won't even notice that it took a few
milliseconds more than systemd systemctl would need
for an action. The only thing is that a syntax error
in any service descriptor on the disk will result
in a warning message flashing by on every call to
the systemctl replacement script. The actions on 
the correctly declared services will not be hampered 
however.

## overwriting /usr/bin/systemctl

The systemctl replacement script is generally shipped
as the python implemention of it, named "systemctl.py".
You can use the non-installed script right away which is
no different than the usage of the installed bin/systemctl
replacement. So `systemctl.py start xy.service` and
a bin-path replacement `systemctl start xy.service` do
work exactly the same. While an installation as
/usr/bin/systemctl.py would work fine that is not a
good choice however. The reason for that is that other
programs will only know about running the `systemctl`
tool as the tool is named in the systemd world.
That's strictly the case for tools like Ansible/Puppet
which will check the target system running "systemctl"
commands. You can not tell them to do it different
just because of the systemctl.py script invention.

There are however occasions where you do run the the
systemctl replacement script actions without having it
installed in the  system as /usr/bin/systemctl. During
the development  it is even the normal case in the
testsuite. Remember that every systemctl script instance
runs independently, so it does not matter if one uses
the version installed in the /usr/bin directory or the
version that comes directly from the git workspace.

You can run the systemctl script actions even in a system
that is currently controlled by a systemd daemon. That
allows you to inspect service descriptor files without 
running a "system-reload" on the system's systemd daemon.
Starting/stopping is actually possible as well in parallel
with systemd but I would not recommend that. And that's
due to the way status information is stored.

## status files

In a systemd controlled environment all status information
is kept in memory. The systemd init daemon will start a
service program, it will possibly wait for a notify-message,
and it can see when a child process dies so that it can be
restarted. Essentially, all service programs are child
processes of the systemd daemon (disregarding the fact here
that service programs may detach but when the systemd
daemon is on PID-1 then they will be reattached to it
right away).

In a systemctl script controlled environment all status
information is kept on disk. When the systemctl replacement
script starts a service program then it will run the
Exec-steps, it will possibly wait for a notify-message,
and then it will exit. So the started program will
implicitly run unattached. No systemctl script will be
on the process table anymore in a docker container (it
used to be different in the past - and in some occasions
where the execve() has replaced the original process you
can see the 'systemctl start' command in the process table
but the underlying binary is actually the application).

Detecting the 'is-active' status of a service works somewhat
different for systemd and the systemctl script. It is only
the same  when a `PIDFile=` has been declared because both
the systemd daemon and the systemctl replacement will read the
PID from that file and they will check if the PID is active.
A dead process may result in either an "inactive" or "failed"
service status depending on whether the service was started
or stopped.

In the very first versions of the systemctl replacement the
script was inventing pid-files when the service descriptor
was not declaring one. Especially a `Type=simple` service
does not need a PIDFile declaration as it is supposed to run
attached  as child process of the systemd daemon. With the
systemctl replacement however a pid-file was written on
`systemctl start xy` and the next call to `systemctl status xy`
will look for the invented pid-file, read the PID and check
on the status. So here are much more pid-files around in a
systemctl script controlled environment than in systemd
daemon controlled one.

In later versions of the systemctl replacement script 
(including the current one at the time of writing) that 
has changed. That's because a `RemainActiveAfterExit` and 
other modes require a more detailed knowledge of whether 
a service was supposed to be running, and that a dead 
process is not problem (it is rendered 'active' on RemainActive). 
So the systemctl replacement script needs more information 
bits than just the  PID of the started process.

Because of that there are `/var/run/xy.service.status`
files around. They will almost always contain the PID.
But is just a standard json file so it can contain more
information bits about a service. When checking a service
through the systemctl replacement then it will look for 
those files. Because the systemd daemon does not write 
those files a systemctl replacement script call may 
return a very different status when poking at a service 
started through it.

In a docker container it is usually the case that all
services are started through the systemctl replacement
script (either from the command line or through the one
on PID-1 on docker container start). That allows the
status info returned to be the same as in a systemd
controlled environment. There are however subtle
differences - mostly that's just room for improvement
to align the way how a "failed" service is called out.
The "active" state is always reported correctly however.
That's because deployment tools like Ansible/Puppet will
stop execution when not - but these tools do not care
much if a service in an unexpected stopped status
through a mark as "failed" or "inactive". Whatever.

## boot time check

Because of the importance of the status files on disk
there is a situation that you may have saved a container
to an image with some status files being still around.
When you do start a container from the image then the
status files will refere to processes from an earlier
incarnation.

While a PID rollover is only a theoretic threat in a
standard unix system it is the normal case for a such
a docker container - it is very probable that an old
status file remembers a PID that can be detected as
running ... but it may be a completely different
application binary from a whole different command.

Therefore the systemctl replacement script implements 
a check on the  boot time of container (or a real system) 
by checking for some files in /proc with hopefully 
/proc/1 to be around. If any status file has a timestamp 
that is older than the timestamp of the boot PID then these
status files are truncated to zero. Effectivly, any
old PID that was saved in an image will be disregarded
in a new container.

Surely, if there are subtle problems with the system
clock then you will bump into mysterious problems
on service starts through the systemctl replacement
script. And some docker versions did really weird 
things to /proc/1 for unknown reasons - it came back 
to normal on the next version of docker. It is just 
that the docker guys don't expect a tool like the 
systemctl replacement script to be around which is 
very picky on the timestamps.
