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
