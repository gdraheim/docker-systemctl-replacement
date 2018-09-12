# HISTORY

## ExecStart Wrapper

In the beginning there was no systemctl replacement idea. Instead of that 
there had been an observation that people did create docker-entrypoint.sh
scripts that were wrong - and if they are correct then they did look very
similar to the lines written in the ExecStart and ExecStop lines from the
systemd service descriptor from the upstream software vendor.

Have a look at "grep Exec /usr/lib/systemd/system/postfix.service"

    ExecStart=/usr/sbin/postfix start
    ExecReload=/usr/sbin/postfix reload
    ExecStop=/usr/sbin/postfix stop

In fact, many software vendors were shipping with systemd service descriptors
at the time that were simply relaying start/stop to the scripts also called 
from the sysv init.d script. That way one could easily support non-systemd 
and systemd controlled target environments.

So back in late 2015 and early 2016 there was a generic docker-entrypoint
shell script that was grepping for ExecStart in a given systemd x.service
script. This had two theoretical advantages:

 * changes in the ExecStart from the upstream software vendor would 
   automatically be picked up by every rebuild of a docker image.
 * it was possible to intercept the SIGTERM signal from "docker stop" to also
   run the ExecStop sequence from the same given systemd x.service

This worked good enough for Type=forking services with very simple 
ExecStart/ExecStop definitions. It did mark the start because instead 
of giving the full path to the systemd service descriptor file one could 
just let the script search the usual locations itself. Simply do 
"docker-start.sh postfix.service".

Supporting Type=simple is also possible that way as it does basically 
just boil down to check for ExecStart and to run a final shell 
"exec $ExecStart" to have a "docker stop" signal be delivered directly
to the process. Almost too simple.

## Unit Parser

It became soon apparent that the docker-entrypoint wrapper script does
only work for very simple systemd service descriptors. Especially one
could see EnvironmentFile parts to be required to start up a service
correctly, and it would be nice to support also definitions for doing
an ExecReload.

Also the changes from upstream vendors were not so simple as expected,
so a Python script was born to analyze the structure of the systemd
service descriptor. In the beginning that was just wrapping Python's
ConfigParser to read the ini-style descriptor files. However be aware
that a lot of service descriptor files may fail to load with that.

After all, a "UnitConfig" parser was started to get the format
correctly. It is still at the heart of the systemctl.py
replacement script - completely rewritten of course because the
service descriptors are not really `*.ini` files. If you ever want 
to analyze systemd files then you better take that as an example how 
to do it.

The rest is simple - at some point in May 2016 a systemctl.py
script was born that did understand start/stop/reload commands.
It was able to source EnvironmentFile parts and to run services
of Type=simple and Type=forking by running the ExecStart=parts
through calling a subprocess shell. (yes, a shell!)

By June 2016 an optionparser was added that would allow to get 
all commands of that systemctl could handle. Most of them were
not implemented however - they were just in the "systemctl help"
list. For your reference that script is the first version in
the github tree - just note that it did already have the 
invention to generate a pid-file when no explicit one was given
so that `is_active_from` can tell the correct status.

https://github.com/gdraheim/docker-systemctl-replacement/commit/883d7e2022fe81d1dcdf9b5ead9215eb1167bd5c

## Ansible Helper

The reason for the summer project came from using Ansible to
provision docker containers. There have been scripts around
that were already able to deploy to the labs virtual machines.
In some parts they were deploying a systemd service descriptor
and the following tasks would "enable" the service for the
next reboot.

Using docker instead of virtual machines would simply lower
the amount of resources needed to test deployment scripts.
Having a systemctl-replacement script around makes the
development turnaround times so much faster. And for a start
you do really only need to implement enable/disable/status
in addition to start/stop/reload.

When that is ready, just overwrite /usr/bin/systemctl in
the container and you can use the earlier Ansible scripts 
to work on them as if they are virtual machines.

It took however to early 2017 that a project came around
where one would not only target one container - but the
provision scripts were switching back and forth to get
the interconnections correctly configured. Using some
systemctl replacement did require it to work exactly
like systemd - no failure in restarting a service was
allowed anymore.

So essentially, the first script was around for a year
that the next iterations came along. And a lot of commits
happened after that time. Note how one of the first versions
starts to implement `show_unit` because that is how Ansible 
reads the systemd descriptor files as well as checking 
the current `active` status from the service in the container.

https://github.com/gdraheim/docker-systemctl-replacement/commit/b985e110946316d7e19258436cac1ea25a21c259

## Reap Zombies

The next mark comes from implementing "systemctl default" to
start all enabled services in a container after restart. In
a way that combines the original idea for a startup wrapper
serving as the docker-entrypoint with the start/stop commands
for single services.

One of the biggest inovations at that point was to also check
the zombie processes around. Because the Ansible deployments
did stop services quite a number of times leaving the killed
processes around. That called for a zombie reaper to be
implemented - something that /sbin/init would do normally but
there is no such thing in a docker container.

Having that in the code, the basic structure of the project
was ready - with the systemctl-replacement-script to be
really a service manager for docker containers that want to
be almost like virtual machines.

https://github.com/gdraheim/docker-systemctl-replacement/commit/3515f94bb6d1fdbede68b560ea47b403bc081dbd

## First Release

As there are three stages above, the first real version number
for the published code was set at `0.3`. As the systemctl.py
project became an independent project from the Ansible code
some finer versioning was needed with 0.3.1124 being the first
real github version number.

https://github.com/gdraheim/docker-systemctl-replacement/commit/d7bbdd13b86620a9e1eee70522862a868b9053fb

However that one was not officially tagged as a release. The
first release happend on the next day at version 0.4.1125. Note 
how the versioning scheme works - the four digits at the end 
represent a date value, while the two numbers in front are 
incremented manually. The date value is (Years from BASEYEAR,
week number of the year, day number of the week) and it is
updated by `make version`. The README.md created for this first
official release is basically the same as the one two years later.

https://github.com/gdraheim/docker-systemctl-replacement/releases/tag/v0.4.1125

## Testsuite

In the first release only a "Maketests" file did exist, covering
as much as three Dockerfiles. As it was inconvenient to switch
back and forth to the other project, some Ansible code was copied
over for testing in release 0.5. With more and more dockerfiles,
that became the testsuite for quite a while.

It took to release 0.7 that a testsuite.py file exists but that was
only a wrapper to run the old dockerfile builds and the old ansible 
scripts. Basically, the old test cases did get a number! Using
experiences from another project, the unittest.main loop is not 
used but a different cli where one can run a test case by the prefix
of its method name - for example `testsuite.py test_6001`. The old
file "Maketests" was replaced by that.

For release 0.8 the systemctl.py script was enhanced with an extra
option "--root=path" to be able to test functionality without 
starting a docker container (something that was required before).
For release 0.9 the testsuite.py was enhanced to use "coverage2"
when running sytemctl.py so that one could know how many testcases
were still needed. This was done with the intention that an upcoming 
release 1.0 should only be published with good coverage. In fact,
the dot-zero release had over 90% line coverage already.

## Bugs and Features

With release 1.0 to also know about reordering of services, the
systemctl.py replacement script was about feature complete. After
that time the changes are tracked using the GitHub issue list
as well as mentioning the changes in the release notes attached
to the git tags / github releases.

Be aware that systemctl.py does not want to mimic the systemd
behaviour in all detail. There had been always the expectation
that at some point the docker cluster managers will be able to
run containers with some systemd emulation themselves (atleast
rkt does). So essentially, systemctl.py would become obsolete
soon - however, years later the situation has not changed much
and the script is even used for other purposes by now.

So let's close this history wrapup with a final remark: most
Linux distributions are run by systemd at the time of writing
this text. But systemd is a flawed solution - not only because
it breaks the Unix Philosophy of "Do One Thing and Do It Well".
There are many quirks in the service descriptors and the whole
functionality is badly documented - we're all just lucky that 
it works at all. SystemD is a bug itself.
