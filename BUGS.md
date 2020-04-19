# Known Bugs and Peculiar Features


## Firefox

Firefox wants to connect to the DBUS. Instead of skipping
a missing service gracefully it just stops with a reference
to "/etc/machine-id" to not contain a 32-chars ID.

Firefox will however start if any such number is written.

    echo "012345678901234567890123456789012" > /etc/machine-id

Theoretically it should be available through docker but that
is not always the case, somehow.


## Ansible service module

Calling Ansible "service" with "enabled: yes" will fail with

    "no service or tool found for: my.service"

Although "my.service" is mentioned it really thinks that
the tool /usr/bin/systemctl does not exist - altough it does.
The reason is an additional sanity check whether systemd is
really managing the system - and it wants to fallback to
"chkconfig" otherwise. The test (seen in Ansible 2.1) can
be defeated by

    mkdir /run/systemd/system
    # or /dev/.run/systemd or /dev/.systemd

Sadly it must be done before calling ansible's "service" module
(and indrectly the systemctl replacement) so there is no help
to make this just on a temporary basis. If you have installed
the "initscripts" package then it will work without such a
workaround because chkconfig exists and handles the "enabled"
thing correctly (but only for the existing SysV style init.d
services).

## Restart=on-failure

Because the systemctl replacement script is not a daemon it
will not watch over the started applications. As such any
option in a service unit file like "Restart=on-failure" is
disregarded.

As a designer of a docker application container one should
take that as a warning - the process is buggy and it may
break. And so will your containered service. If you need a
fallback solutation then the container clould application
should monitor the docker container.

## The systemd package was updated

In the [docker-systemctl-images](https://github.com/gdraheim/docker-systemctl-images)
examples we have a number of occasions that the script needs
to be installed twice - before and after a package install.

    COPY files/docker/systemctl.py /usr/bin/systemctl
    RUN yum install -y postgresql-server postgresql-utils
    COPY files/docker/systemctl.py /usr/bin/systemctl

That's because the package install (e.g. postgresql-server)
has a dependency on the "systemd" package which will
implicitly get updated. That update will overwrite the
/usr/bin/systemctl path with the original systemd binary.

You will notice that when a systemctl command says that it
can not operate. Which means it is not systemctl.py but the
original systemd systemctl trying to talk to the systemd daemon:

    Failed to get D-Bus connection: Operation not permitted.
    System has not been booted with systemd as init system (PID 1). Cant' operate.
