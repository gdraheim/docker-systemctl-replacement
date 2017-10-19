# Tricks and Hints

## The --now internals

The option "--now" is only used for a very low number
of systemctl commands. In the systemctl.py variant
it is (ab)used to run an alternative method.

## systemctl.py list-unit-files --now

Shows the list of files found on the disk. Those are
not parsed and they are not check for an enabled-link.
It is just what is there as a first step after scanning
for systemd-relevant unit information.

## systemctl.py list-dependencies --now

Shows the start-order of services. Use -v debugging to 
see how the start-rank is computed from the Before/After 
clauses in the unit files.

Note that upon a "<stop> operation" the start order is
run through in reverse order.

The current 'default' target does not filter the list.
Instead it only uses Before/After on the units in the
'multi-user.target' but it does not process any of
its required units.

# Implementation helpers

## docker images --filter

https://github.com/moby/moby/blob/10c0af083544460a2ddc2218f37dc24a077f7d90/docs/reference/commandline/images.md#filtering

    docker images --filter dangling=true || dangling=false
    docker images --filter label=<key> || label=<key>=<value>

whereas filter by name is just an argument "docker images <name>"

## docker images --format

    docker images --format "{{.ID}}: {{.Repository}}\t{{.Size}}"
    and "{{.Tag}} {{.Digest}} {{.CreatedSince}} {{.CreatedAt}}"

## IPv4 -vs- IPv6

For java / tomcat applications one can add a java-option to use ipv4

    -Djava.net.preferIPv4Stack=true

For docker-compose 2.1+ one can add a sysctl to disable ipv6.

    sysctls:
       - net.ipv6.conf.eth0.disable_ipv6=1
       - net.ipv6.conf.all.disable_ipv6=1

And there is an option to disable '::1 localhost' with systemctl.py

    systemctl.py --ipv4 daemon-reload

## oneshoot services

https://www.freedesktop.org/software/systemd/man/systemd.service.html

There is a note that after "start unit" the unit is considered to be
active. A second "start unit" shall NOT run the execs again.

Indirectly it hints to the detail that a "start unit" does not run
any execs when "is-active unit" true. See issue #6.

## system specifies

https://www.freedesktop.org/software/systemd/man/systemd.unit.html

* "%n" Full unit name
* "%N" Unescaped full unit name = Same as "%n", but with escaping undone
* "%p" Prefix name = For instantiated units, this refers to the string before the "@" character of the unit name. For non-instantiated units, this refers to the name of the unit with the type suffix removed.
* "%P" Unescaped prefix name = Same as "%p", but with escaping undone
* "%i" Instance name = For instantiated units: this is the string between the "@" character and the suffix of the unit name.
* "%I" Unescaped instance name = Same as "%i", but with escaping undone
* "%f" Unescaped filename = This is either the unescaped instance name (if applicable) with / prepended (if applicable), or the unescaped prefix name prepended with /.
* "%t" Runtime directory = This is either /run (for the system manager) or the path "$XDG_RUNTIME_DIR" resolves to (for user managers).
* "%u" User name = This is the name of the user running the service manager instance. In case of the system manager this resolves to "root".
* "%U" User UID  = This is the numeric UID of the user running the service manager instance. In case of the system manager this resolves to "0".
* "%h" User home directory  = This is the home directory of the user running the service manager instance. In case of the system manager this resolves to "/root".
* "%s" User shell = This is the shell of the user running the service manager instance. In case of the system manager this resolves to "/bin/sh".
* "%m" Machine ID = The machine ID of the running system, formatted as string. See machine-id(5) for more information.
* "%b" Boot ID = The boot ID of the running system, formatted as string. See random(4) for more information.
* "%H" Host name = The hostname of the running system at the point in time the unit configuration is loaded.
* "%v" Kernel release = Identical to uname -r output
* "%%" Single percent sign = Use "%%" in place of "%" to specify a single percent sign.

## KillMode with SendSIGKILL and SendSIGHUP

When grepping through existing *.service files one can see a number
of references to those two options
* SendSIGKILL=no / postgresql + plymouth-start
* SendSIGHUP=yes / getty + console + journal-service

For a docker container one can safely exclude the latter but the
usage for postgresql makes it an importation option being in use.
In both cases the option changes the behaviour of "systemctl kill".

https://www.freedesktop.org/software/systemd/man/systemd.kill.html

As one can already guess, the default for SendSIGHUP is "no" and it
means that after the "KillSignal=" it should immediately send an
addtional SIGHUP - which is defined to also be forwarded to the
children of a program. 

One can also guess the default for SendSIGKILL to be "yes". Here it
is defined to work only after a timeout - as it shall send a KILL
to all remaining processes(!) of a service that are still around.

The third signal in use is a SIGTERM which is the default that is
sometimes overridden as "KillSignal=SIGHUP". Obviously it does
not make sense to mix Kill-SIGHUP and SendSIGHUP and there is no
such thing to exist in real service systemd files.

Last not least, there is also a "KillMode=control-group" default.
Which effectivly means that the specified sequences of Signals
(SIGTERM + SIGHUP & SIGKILL) should be sent to all processes.

As it is implemented for systemctl.py 1.0 there are some differences
in the handling - a "systemctl.py stop" will only execute ExecStop
but no implicit "systemctl kill" after that (KillMode=none). And
the SIGTERM & SIGKILL will only go the $MAINPID of a service as far
as we know about it (KillMode=process). If there is NO ExecStop
then there is a fallback from "signal stop" to "signal kill".

## Start Exec-Mode

It may be a little known detail from the systemd specs but in
reality one should NOT have multiple ExecStart lines in a spec
file. (quoting from specs: "Unless Type= is oneshot, exactly 
one command must be given.")

Instead the systemd specification has a number of prefixes for
the ExecStart line that modify the behaviour that are somewhat
related to the call of fork+execve.

https://www.freedesktop.org/software/systemd/man/systemd.service.html#ExecStart=

* a "-" prefix is the most obvious: ignore the return value
* a "@" prefix allows to have argv[0] to be not the called program
* a "+" prefix makes for a priviledged services process which
  basically means that User/Group changes should NOT be made
  (User/Group would affect ExecStart/ExecStop otherwise)
* and some unintelligible description of "!" and "!!" prefixes
  the seem to be alterations of a "+"

Moreover, "-" and "@" and "+" may be combined and the prefix
characters may occur in any order. Phew!

And just for another thing - one might expect that along with
ExecStart / ExecStop / ExecReload there also Exec-statements
for other frontend commands - including ExecXyPre/ExecXyPost
statements for each of them. But this is not the case - 
specifically there exists NO ExecRestart statement in the
systemd specs. Only these are valid:

* ExecStartPre
* ExecStart
* ExecStartPost
* ExecReload
* ExecStop
* ExecStopPost

On top of that, if any of the ExecStopPre, ExecStart, ExecStopPost
commands fails then you will also see that the original systemd 
daemon will execute the ExecStopPost lines to cleanup the system.
(and it will NOT run the ExecStop lines in that case). In order
for ExecStopPost to know the reason why it has been called there
are additional environment variables around

* $SERVICE_RESULT = "success", "timeout", "exit-code", "signal"..
* $EXIT_CODE = "exited", "killed" (the most relevant styles)
* $EXIT_STATUS - the exit-code of $MAINPID .. and for the
  combination of "success" + "exited" this is always 0.

That's a bit tricky to follow and "systemctl.py" does not do it.
One can assume that there is hardly any programmer to have taken
advantage of that - it sounds a bit like wizardry around.

As for the hint of "only one ExecStart" - while the script after
ExecStart is NOT run in a shell you can still use multiple
commands by having them seperated with "{space}{semicolon}{space}".
And a stray semicolon may instead be escaped with "\;". Phew!


