# RESTART POLICY

Finally, the systemctl replacement InitLoop can check for Restart of failed modules.
But at first you should know that you can disable the feature right way to be 
backward compatible with older versions (before v1.5). Just say

    systemctl.py -c RESTART_FAILED_UNITS=no

## LimitBurst

The defaults for the LimitBurst implementation are just as in the standard SystemD:

   StartLimitBurst = 5x
   StartLimitIntervalSec = 10s

With a default of `InitLoopSleep=5` seconds it means that the LimitBurst will never
be activated. If you have a lower InitLoopSleep (see below) then it might happen
that a module restart was done too often - and the module gets an ActiveState=error.
In that state it will never be restarted again - so the container is effectivly dead
in terms of that service unit.

You can heal the situation explicitly by saying 'systemctl.py reset-failed [unit]'.
That's because the ActiveState is a part of the unit.service.status file which gets
deleted with that command. It matches with the original definition of the behaviour
of SystemD.

## RestartSec

The DefaultRestartSec is set at 100ms just like it is in SystemD. However this has
no effect on the systemctl behaviour as the InitLoopSleep is at 5 seconds. The
implementation of the Restart behaviour is done so that it does check for failed
services - and then they are scheduled for restart in the future. So effectivly
it is `StartTime = now + RestartSec`. But because of the InitLoop the next check
may be far away - so instead of with 100ms it gets the real restart of the failed
service after 5000ms.

In order to help with configuration of a shorter restart interval, the implementation
will check for the "RestartSec" in the unit service descriptors. If it is atleast
1 second but lower than InitLoopSleep then InitLoopSleep is shortened to that time.
For example if you do have a service unit with a "Restart=2s" then you can expect
that the real restart from failure will haben about 2 seconds after the failed state
was detected - which is again within a time frame of 2 seconds after the failure
has occured. As a result, a restart can happens far as 4 seconds after a unit failure.

A "RestartSec=0" is a special value - it will be increased to an InitLoop interval 
of 1 second but it has no further delay, so that a restart occurs within 1 second
after a unit failure. The current InitLoop of the docker systemctl replacement
code can not offer any better.

## InitLoopSleep

Using "RestartSec" you can easily build docker containers with a shorter InitLoop
interval - that comes from the [EXTRA-CONFIGS](EXTRA-CONFIGS.md) feature provided
by standard SystemD. Suppose you have service unit "my.service" then you are going
to create a "my.service.d/restart.conf" like this:

    # /usr/lib/systemd/system/my.service"
    mkdir /usr/lib/systemd/system/my.service.d
    echo >/usr/lib/systemd/system/my.service.d/restart.conf" <<EOF
    [Service]
    RestartSec=2s
    EOF

That will override the global default and any other setting in the my.service
descriptor.

## Existing Values

The RestartSec value is usually quite big if it is set at all - and in the vast
majority of cases it set to zero. So there is no delay after the detection of
a failed status. That's what you can use as well with systemctl.py but it will
keep the InitLoop interval quite high.

    /etc/systemd/system/dbus-org.freedesktop.network1.service:Restart=on-failure
    /etc/systemd/system/dbus-org.freedesktop.network1.service:RestartSec=0
    /usr/lib/systemd/system/autovt@.service-Restart=always
    /usr/lib/systemd/system/autovt@.service:RestartSec=0
    /usr/lib/systemd/system/autovt@.service-Restart=always
    /usr/lib/systemd/system/autovt@.service:RestartSec=0
    /usr/lib/systemd/system/dbus-org.freedesktop.login1.service-Restart=always
    /usr/lib/systemd/system/dbus-org.freedesktop.login1.service:RestartSec=0
    /usr/lib/systemd/system/getty@.service-Restart=always
    /usr/lib/systemd/system/getty@.service:RestartSec=0
    /usr/lib/systemd/system/ntpd.service:RestartSec=11min
    /usr/lib/systemd/system/ntpd.service-Restart=always
    /usr/lib/systemd/system/systemd-journald.service-Restart=always
    /usr/lib/systemd/system/systemd-journald.service:RestartSec=0
    /usr/lib/systemd/system/systemd-logind.service-Restart=always
    /usr/lib/systemd/system/systemd-logind.service:RestartSec=0
    /usr/lib/systemd/system/systemd-networkd.service-Restart=on-failure
    /usr/lib/systemd/system/systemd-networkd.service:RestartSec=0
    /usr/lib/systemd/system/systemd-udevd.service-Restart=always
    /usr/lib/systemd/system/systemd-udevd.service:RestartSec=0

## on-failure

Note that the implementation of the systemctl replacement script does not really
check the restart policy - so that Restart=on-failure and Restart=always are
actually the same thing. That's because the systemctl replacement script does
not know about an exit code of a unit file anyway.

On the other that, there are two settings which disable the restarting behaviour
for a service module: either "Restart=no" or "Restart=on-success" will keep the
service offline if it comes into a "failed" state. No restart is attempted. All 
other "Restart=x" settings will try to restart correspondingly.








