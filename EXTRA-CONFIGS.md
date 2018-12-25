# Extra Configs and Features

## DROP-IN FILES

The systemd service descriptors do already have the feature
of drop-in configurations. So when there is a docker container
with these files:

    /usr/lib/systemd/system/some.service
    /usr/lib/systemd/system/some.service.d/extra.conf
    /etc/systemd/system/some.service.d/override.conf

then ALL these files will be parsed. Therefore some `*.rpm`
program may instal the `some.service` file but you can always
override the settings with your `override.conf`.

In general the new lines will be added to the existing config
entries. So when you have

    # some.service
    [Service]
    Environment=A=1 B=2
    ExecStartPre=/usr/bin/somecheck
    
    # some.service.d/extra.conf
    [Service]
    Environment=C=2
    ExecStartPre=/usr/bin/morechecks

then both of these commands are being executed and the environment
contains A, B and C variables for all commands.

There is a feature where you can also replace the original settings
completely by giving an option with an empty argument:

    # some.service
    [Service]
    Environment=A=1 B=2
    ExecStart=/usr/bin/startup $A $B
    
    # some.service.d/override.conf
    [Service]
    Environment=C=2
    ExecStart=
    ExecStart=/usr/bin/startup $A $B $C

In the latter case, only one ExecStart command will be executed
having three arguments.

All these are standard features of systemd. In general they are
meant to be used by configuration programs that can add or change
some environment variables materializing the extra settings as
an extra.conf instead of changing the original service descriptor
file. However the way to append/replace a setting is completely 
generic - it is part of the parser and not of the interpreter for 
the service definitions. Thus it works also for the Exec-parts.

