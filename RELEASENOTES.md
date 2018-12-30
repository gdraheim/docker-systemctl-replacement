RELEASE 1.4

Additional features have been put into the 1.4 series of systemctl.py. The
commands of "mask"/"unmask"/"set-default"/"get-default" have been implemented
where the "default" runlevel is only modified by not checked by systemctl.py.
The PID-1 will now assemble all journal logs of services and print them from
the init_loop to stdout so that "docker logs" shows the status logs of all
the services currently running.

Changes include that /var/run/systemd/notify is not the default notify_socket
anymore but instead each service has its own ../notify.A.service channel.
Along with the A.service.lock behaviour one may safely run many systemctl.py
in parallel that will not overlap in getting text. 

The switch to fork/execve in 1.3 had been allowing some process to leave zombies 
or even block the  master systemctl.py which has been resolved now. After all, 
the service.pid parts are completely gone with the MainPID register in the
service.status files now. Checking the (non)active status has been stabilized
from these changes.

The support for usermode containers had been already present in the 1.3 series
but is now tested and documented. The docker-systemctl-images sister project
will show a number of examples of it where the PID-1 of a container is not
run as root but as a specific user - only allowing to start services with the
same user association.

The testsuite has been expanded a lot to support testing usermode containers
which can not be done just by running systemctl --root=path. Additionally the
testing times do increase from testing various pairs of python version and
linux distributions and their versions. Thus --python and --image can be used
to get to the details of compatibility. After all, the coverage is now at 92%.

The question of how to let a PID-1 systemctl.py exit the container has been
put into a new state. When running "systemctl.py init A B" then PID-1 will
end when both A and B have turned to a non-active status. When running a plain
"systemctl.py" then it is the same as "systemctl.py init" which is the same as 
"systemctl.py --init default", all of which will never stop. So this PID-1 is
identical with /sbin/init that keeps it up.

However PID-1 will not run forever in that "init" mode. You can always send a
SIGQUIT, SIGINT, SIGTERM to PID-1. Upon SIGQUIT the PID-1 systemctl.py will wait 
for all processed in the container to have ended. The other signals will make
it leave.

Last not least there are some minor adjustement like adding to the list of
expanded special vars like "%t" runtime. And it was interesting to see how
"postgresql-setup initdb" runs "systemctl show -p Environment" expecting to
get a list of settings in one line. Also when using "User=" then the started
services should also get the default group of that system user.

RELEASE 1.4.2456

There a couple of bugfixes and little enhancements asking for an intermediate
patch release. Be sure to update any 1.4 script to this version soon.

Some of the `%x` special vars were not expanded, and some of the environment
variables like `$HOME` were not present or incorrect. Functionality of the
`mask` command has been improved as well.

The release does also include the extension of the testsuite that was otherwise
intended for RELEASE 1.5 where different versions of common distro images are
included in the nighrun tests. It did uncover a bug in ubuntu `kill` by the
way that may got unnoticed by some application packages so far.

RELEASE 1.4.3000

There are a couple of bugfixes. The most prominent one is the proper support
of drop-in overide configs. This can be very useful in scenarios where one
wants to install a `*.rpm` from an upstream distributor adding some additional
parts only in the case of a docker container image. That has been described
more prominently in [EXTRA-CONFIGS.md].

The general README itself contains an easier introduction with a hint on how
a multi-service container looks like from the inside. That should make some
visual impression on everyone who has already worked with containers so far.




