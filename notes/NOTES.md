# Not A Daemon

The real systemd environment is based on a central daemon that
the "systemctl" command talks to. That one loads the unit files
on disk into memory (hence "systemctl daemon-reload").

That one allows some features that "systemctl.py" can not
provide at all.

## Restart=on-failure

The daemon can watch over its spawned processes (especially with
Type=simple) which allows it to automatically restart them if
the user wants to.

    Restart=on-failure

    Restart=always
    RestartSec=3

These things will probably never be supported with "systemctl.py".
One would need to run some background program somehow. Perhaps it
would be an option when running as the init-process but it is
currently not a goal for the 1.0 release. 

## /var/run/unit.service.pid

The daemon will also know the PID of its spawned processes (again
with Type=simple) and the list is really just kept in memory. The
"systemctl.py" needs to store all operational information however
on disk. 

As such, every process that does not specify a "PIDFile=" in the
unit descriptor will nethertheless get a pid file on disk. By
convention it uses the filename of the unit descriptor with an
attached ".pid" and it is stored in /var/run where most services
will store their pid file anyway.

So when the is-active attribute is asked then "systemctl.py" will
really look into that pid-file and check if the pid is alive. It
is that simple. (If the unit file declares a PIDFile then the pid
from that one is read - hopefully in a format that one can 
understand.)

## /var/log/journal/etc.unit.service.log

Likewise one can just store the output of the child processes in
memory so the output is diverted into /var/log/journal/. That 
directory would also used by the systemd daemon but in a different
way. So far there is no need to adapt the format.

Looking at the style of journalctl is yet another thing that one
could think about for systemctl.py after the 1.0 release.

## new substate via NOTIFY_SOCKET

The current "systemctl.py" script has actually implemented a good
portion of the $NOTIFY_SOCKET sd_notify portion. However that one
is only used to implement a dynamic waiting time for the process
to start. So it creates a /var/run/systemd/notify socket and then
it reads from that socket until "READY=1" is seen.

As soon as READY is received, the systemctl.py will end and with
it the notify-socket is removed. A real notify-socket programm
may however send attributes to the running systemd-daemon - and
most importantly the substate can give an overview on the health
of a system.

Since the next notify-socket will only exist on Restart, there is
no chance for that with "systemctl.py"

# Not A Network

The "systemctl.py" script is commonly used in a docker container,
hence the project name "docker-systemctl-replacement". For a
docker container however all the network setup is managed on the
outside of the container - you do have an emulated "eth0" but
that's as much as you can do. And you should leave it alone anyway.

Quite a number of service unit files however declare dependencies
on some network feature. We do have to ignore them all. Likewise
any existing unit file relating to network stuff - including some
firewall rules - has to be disregarded compeletely.

This however follows some heuristic assumptions. Some unit files
are skipped.... but may be that will be found to be wrong in the
future. Or may be some other unit descriptor needs to be skipped
as well.

## Not A Volume Manager

The same applies to the management of volumes. That is a thing 
that the docker daemon will do for you. So any program with such
a feature needs to told to not do anything. That is most
importantly for applications handling backup operations.

Simply assume that no special disk operations can be done in a
container. And hopefully the application does not require selinux
to be present.

## No Remote SystemD

Quite a number of the options for a real "systemctl" are about
not connecting to the local system daemon, but pointing to
a different machine. Or to a systemd inside a container. Or to
a systemd subprocess for specific user.

That is not supported by "systemctl.py" and those options have
been removed completely from the commandline interface. Any
program trying to use these should fail early with our
docker-systemctl-replacement program.

# Usage Without Docker

Whereas the "systemctl.py" is commonly used to be run inside a
docker container, it does still have some good points in a
normal system - even in parallel with normal "systemctl".

That is because "systemctl.py" can check the validity of the
unit.service files around. It's internal logic does understand
quite a lot of the features that lie therein. And so if the
"systemctl.py" does  not like a thing that is probably also
wrong for a real system process.

## Check with --root=path

Most importantly that is used for its own testsuite.py - the first
half of the tests will create a tmp.xxxx subdirectory where some
generated x.service files are stored. Then the option --root=path
is used to inspect their content if they are okay as a whole.

Notably, the --root=path feature is also known to the real
"systemctl" program. But most people will not likely have used
it before - it is meant to configure a chroot-environment with
the general systemd daemon.

And if you run "systemctl.py" without a --root=path then it will 
just look at the current system as it is. Which may reveal some 
interesting things you have never noticed before.

