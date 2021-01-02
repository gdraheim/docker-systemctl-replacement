RELEASE 1.6

Just as with v1.5, Python 3 is the default variant now. Just as in the previous
release branches there is only one code basis for python2 and python3 but the
primary test target has changed. If you run "make test_1000" then you see
the result from systemctl3.py now, and "make 2" will derive systemctl.py
from it. The testsuite.py itself is also run by a python3 interpreter now.
And a types/systemctl3.pyi file provides optional strict type checking.

The v1.6 will be the last branch to support 2and3 code compatibility. A new
tool format3.py has been added to convert `format(**locals())` into proper
python3 f-strings for mypy checks. All debug-loggers were wrapped to use
format-strings as the input already. The next release branch will go to use
python3 f-strings and inline type hints using `strip-hints` to create a
python2 variant from it. Actually only the rhel/centos 7.x series may need
extended python2 support with an end-of-life by 2024. With older Ubuntu
and Opensuse support being discontinued we can assume Python 3.6 as the
minimal supported version by mid of 2021 in all common Linux distributions.

The biggest functional change in v1.6 is the service dependencies discovery.
Up to v1.5 the 'default-services' deduction was only based on the enabled
.service and .target which got a bit of complicated code in the range of
"works most of the time". The new style can see the full set of Wants and
Requires around - use "systemctl.py daemon-reload" to create a deps.cache
that makes the logic to see indirect relations like "Alias" and "PartOf"
entries in the service descriptor files.

While compatibility with an original systemd got a lot better by that, it
does also have the downside that startup time got slower. Also be aware
that missing "After" entries in the modules will lead to subtle problems 
with the start order. Remember that a "Wants" does not imply "After" and
that makes a dependency to be possibly be started later which is often
unintended. The original systemd seems to follow some undocumented heuristic
guidelines - please provide patches if you find another one.

The v1.6 will still not start dependencies automatically on "systemctl start"
but it will do it now on "systemctl default". It is not anymore required
to enable all dependencies for that case. But the .target unit support was
enhanced to changed to honour all dependencies (except for sysinit.arget 
and basic.target services). On the other hand, the socket support is still 
minimal as it has been in v1.6 so there is no change for that either.

Internally, there were quite some changes to support more "-c XyOption=yes"
variable which is in the process of changing the testsuite.py. The default
info/debug messages will consequently be lowered. Please remember that if
you are going to analyze problems as you may need to enable some DebugXY
channels to get more details as to what has gone wrong.

For some people it may count that the ActiveState support was extended
so that you can now see "starting" and "stopping" phases as well as the
is-system-ready to show more details. It comes with an internal cleanup
where seperate xy.lock files are not used anymore and the LockFile support 
was transferred to the xy.status files. These will be created more often 
and they will stay longer around - specifically "failed" services will 
show more information on the "status" screen about the exit code of the 
processes and steps involved. And remember to use "systemctl logs" as
a tool to find the partial journal implementation results more easily.

Last not least: the support for testing in an air-gap situation was 
enhanced with a copy of the new generation "docker_mirror.py" script
that comes from https://github.com/gdraheim/docker-mirror-packages-repo
