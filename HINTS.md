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
