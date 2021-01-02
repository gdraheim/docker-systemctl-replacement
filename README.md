[![Build Status](https://dev.azure.com/gdraheim/gdraheim/_apis/build/status/gdraheim.docker-systemctl-replacement?branchName=develop)](https://dev.azure.com/gdraheim/gdraheim/_build/latest?definitionId=5&branchName=develop) . . . _(make checks : code coverage 93% from more than 400 test cases)_

# docker systemctl replacement

This script may be used to overwrite "/usr/bin/systemctl".
It will execute the systemctl commands without SystemD!

As a result you can start multiple systemd services in one
container just like they would be on a virtual machine.
This makes testing phases much more lightweight and it
allows code to be packaged in docker images which are not
prepared to run in containers or any container cloud. It
helps your organization to embrace a cloud-only strategy.

Here is an example of a LAMP stack (Linux, Apache, MySQL
and PHP) running in a single container. Note that the
systemctl3.py scripts runs on PID-1 (instead of /sbin/init)
which has spawned the processes of the two main services.
No changes to the original rpm/deb packages are needed and
no extra docker-entrypoint script is required. You can find
more real world scenarios in a seperate GitHub project
at [gdraheim/docker-systemctl-images](https://github.com/gdraheim/docker-systemctl-images).

    ## docker exec lamp-stack-container systemctl list-units --state=running
    httpd.service     loaded active running   The Apache HTTP Server
    mariadb.service   loaded active running   MariaDB database server
    
    ## docker exec lamp-stack-container pstree -ap
    systemctl,1 /usr/bin/systemctl
      |-httpd,7 -DFOREGROUND
      |   |-httpd,9 -DFOREGROUND
      |   |-httpd,10 -DFOREGROUND
      `-mysqld_safe,44 /usr/bin/mysqld_safe --basedir=/usr
          `-mysqld,187 --basedir=/usr --datadir=/var/lib/mysql
              |-{mysqld},191
              |-{mysqld},192

## Features

The systemctl replacement script is a service manager to
support start/stop/status as well as enable/disable commands.
The implementation is correct as much that the "ansible service"
module is happy. Hence ansible scripts written to deploy to a
a virtual machine may be reused to prepare a docker image 
instead. (Actually that was the original motivation).

* See [SERVICE-MANAGER](SERVICE-MANAGER.md) for more details.

The systemctl replacement script is an init daemon to support
booting services in a container and to propagate docker-stop
signals to the processes inside the container. Just like
the "systemd" daemon had replaced /sbin/init on PID-1 this
systemctl3.py script will replace those when set in the
CMD / ENTRYPOINT of a docker image. (That's how it makes
a docker-entrypoint script to be not needed).

* See [INIT-DAEMON](INIT-DAEMON.md) for more details.

The systemctl replacement supports an extra usermode setup
where the init daemon does not run as UID 0 (root) but with
a  normal user account (e.g. 1001). It will then limit the
commands to only start services with a matching `User=` in
the descriptor. That is a very good match for modern cloud
deployments which dislike UID 0 as to have better monitoring
and to enhance security with non-priviledged processes.

* See [USERMODE](USERMODE.md) for more details.

The systemctl replacement script can be used in parallel
with a real systemd daemon running a system. It does not
require a central daemon to be around. Instead it creates
some xy.service.status files to store runtime information.
As the "daemon-reload" command is a no-op it was reused to
analyze the service descriptors of the target system which
can show problems that the original systemd will not warn about.

* See [ARCHITECTURE](ARCHITECTURE.md) to see the differences.

The complete implementation is wrapped in a single file. That
makes it every easy to have it pushed to a target system or
to COPY it into a container image in some dockerfile script.
You can also just download the script directly to check your
current system for details. Try it out like this:

```bash
wget https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/systemctl3.py \
  --output-document /usr/bin/systemctl.py \
  --no-clobber
chmod +x /usr/bin/systemctl.py
systemctl.py list-units
```

## Examples

There is an extensive testsuite to show a lot of features of
systemd and to even compare the result of the replacement
script with the original implementation. Note however that no
full compatibility is intended and for the architecture 
differences it is not even possible.

* See [TESTSUITE](TESTUITE.md) for more details.

The testsuite is also an example to test setup code with package
installations (apt-get install / yum install / zypper install)
in an air-gap situation - with no internet access or without
the required bandwith to download rpm/deb packages. It makes
use of a package mirror wrapped again in a container for a
cloud-only approach.

* See [gdraheim/docker-mirror-packages-repo](https://github.com/gdraheim/docker-mirror-packages-repo) for details.

Note that the testsuite in this GitHub project uses mostly 
synthetic test cases (run `make check` for that). However 
the replacement script has been already used in a number of 
real world scenarios - have a look at the sister project to
see examples of that in [gdraheim/docker-systemctl-images](https://github.com/gdraheim/docker-systemctl-images).
To help with details you should use systemd extra-configs
instead of writing a docker-entrypoint script.

* See [EXTRA-CONFIGS](EXTRA-CONFIGS.md) for that option.

## Development

Although this script has been developed for quite a while,
it does only implement a limited number of commands. It
was created a number of problems that were encounted when
moving from a world of systemd in virtual machines to a
world with docker and containers.

* See [SYSTEMD-PROBLEMS](SYSTEMD-PROBLEMS.md) for an overview

The systemctl replacement script has a long [HISTORY](HISTORY.md)
now with [thousands of commits on github](https://github.com/gdraheim/docker-systemctl-replacement/tree/master)
the current implementation is done by trial and fixing the errors.
Some [BUGS](BUGS.md) are actually in other tools and need to be
circumvented. The choice of the [EUPL-LICENSE](EUPL-LICENSE.md) is
intentionally permissive to allow you to copy the script to your project.

* See the [RELEASENOTES](RELEASENOTES.md) for the latest achievements.

Sadly the functionality of SystemD's systemctl is badly documented.
As most programmers tend to write very simple `*.service` files
it works in a surprising number of cases however. But definitly
not all. So if there is a problem, use the
[github issue tracker](https://github.com/gdraheim/docker-systemctl-replacement/issues)
to make me aware of it.

And I take patches. ;)

## The author

Guido Draheim is working as a freelance consultant for
multiple big companies in Germany. This script is related to 
the current surge of DevOps topics which often use docker 
as a lightweight replacement for cloud containers or even 
virtual machines. It makes it easier to test deployments
in the standard build pipelines of development teams.
