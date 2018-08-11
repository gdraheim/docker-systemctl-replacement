# The User Mode

Be warned, the systemctl.py user-mode is not identical with the systemd user-manager behaviour.

Both concepts can be explicitly selected when running "systemctl --user" however.
For systemctl.py it enables the user-mode while for systemd it opens the socket
to send commands to the user-manager. Such a user-manager exists when you have
a graphical desktop running.

In reality, the user-manager feature has been scarcily used. The systemd guys do even
think about droppping the 'systemctl --user' level altogether. Even when you are not 
root, all commands default to "systemctl --system" anyway, assuming a systemd controlled
operating system.

Anyway, the distinction of user/system level is the reason that most developers will need
to install their new *.service files into a subdirectory of /etc/systemd or /usr/lib/systemd.
If you look closer then you will see that there are two subdirectories, and there are actually 
service files in your /usr/lib/systemd/user/ directory. Did you ever think about why the
*.service install directory is named /usr/lib/systemd/system/.? Well, here's why.

Let's get back to systemctl.py. It does behave similar to systemd's systemctl in that
it will only search x/systemd/system directories when in system-mode. It ignores any
files in x/systemd/user directories. However if in user-mode then x/systemd/user
directories are searched - and just like the systemd user-manager it will also find
*.service files under the user's home directory at `"~/.config/systemd/user"`
and `"~.local/share/systemd/user"`.

So when running "systemctl --user list-units" you will get a very different list
of services. That accounts for both systemctl.py and systemd systemctl. Give it a try.

## User Containers

The existance of a user-level would have been totally irrelevant if it would not have
been for a rule from OpenShift in that processes in a container must not try to be run
as a virtual root user. In fact, all docker containers are started with an explicit
"docker run --user=foo" value. So when systemctl.py is registered as the CMD of the
container then it will not have root permissions.

Now that can make for a problem when you consider that services may want to read/write
global /var/xyz directories. If systemctl.py is started in a user container then it
can not start services that expect to be run with root permissions. It just does not
make sense.

Luckily, most modern *.service files do name an explicit "User=target". So in a user
container, systemctl.py can start them when the target user is the same as the
container has been started under. Effectivly, when systemctl.py is running as PID-1
it will filter all *.service files to the current user of the container.

Theoretically you can still start multiple enabled services through systemctl.py in
a single container. Practically it does not happen very often as a tomcat.service 
has "User=tomcat" and a postgresql.service has "User=postgres". There is no way to
run them both in a user container at the same time. Unless of course you change 
those lines while preparing such a docker image to have the same "User=target".

## User Mode

The systemctl.py user-mode is automatically selected when it runs as PID-1 and it
finds itself to be not root (the re-mapped virtual root of course). As described 
above, only systemd/system files with the same running user may be started/stopped. 
The systemctl default-services list of enabled services will only show those.

Adding to that, systemctl.py will also offer to start/stop systemd/user services
as they are naturally designed to be started as non-root processes. And that's
the basic difference between systemd's user-manager and systemctl.py user-mode -
when you select "systemctl.py --user" then it will allow operations on all 
systemd/user services plus all systemd/system services with a matching "User=target".
The systemd's systemctl will however only offer systemd/user services.

Having systemd/user services in user-mode allows a developer to explicitly
prepare a service to be run under a user-manager. In fact one can find a
lot of examples that were meant to be run as user containers where the actually
application is deployed to a virtual /home/foo in the container image. When
taking advantage of systemctl.py then a developer can just as well add a
/home/foo/.config/systemd/user/foo.service file. Such a deployment script
will not only allow such an application to be run in a user-container but
it will also work in a classic virtual machine with a user-manager.

## Other Paths

In the general case, developers do not need to think about that too much.
Just deploy a systemd/system service and when there is a "User=target" line
in the configuration then the docker image can be started as a user
container. You can use systemctl.py just like with classic containers.

When a developer takes advantage of deploying to /home/foo then you need
to be aware however that some other directories are searched for these
user services. And the special variables like %t in a *.service file may 
in fact point to a different directory. The freedeskop standard for XDG 
directories has the details what to think about.

## User Images

The sister project https://github.com/gdraheim/docker-systemctl-images
has examples where systemctl.py is used to help creating docker images.
Not only are there classic images where systemctl.py will run as PID-1
in root mode - there are also docker images which have a user-mode
configuration.

In fact, the Dockerfile "USER foo" directive is meant to force an image
into be run as a user container by default. So any of those images will
have systemctl.py in user-mode.

Naturally, the docker-systemctl-images can show user-mode images for
single applications like Apache and MariaDB. But having a full LAMP
stack in single container is not possible for user-mode.

Anyway, it just works - you can use systemctl.py even for user 
containers. No need write special docker-entrypoint scripts, just 
install the service, enable it, name the "USER target" in the 
Dockerfile, and then you can run the container.
