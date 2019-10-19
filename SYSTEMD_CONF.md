# SYSTEMD ENVS

The systemd daemon will look for a number of variables in the environment.

* https://www.freedesktop.org/software/systemd/man/systemd.unit.html

When the variable $SYSTEMD_UNIT_PATH is set, the contents of this variable overrides the unit load path. If $SYSTEMD_UNIT_PATH ends with an empty component (":"), the usual unit load path will be appended to the contents of the variable.

Load path when running in system mode (--system).

    /etc/systemd/system
    /run/systemd/system
    /usr/local/lib/systemd/system
    /usr/lib/systemd/system

Load path when running in user mode (--user).

    $XDG_CONFIG_HOME/systemd/user or $HOME/.config/systemd/user
    /etc/systemd/user
    $XDG_RUNTIME_DIR/systemd/user
    /run/systemd/user
    $XDG_DATA_HOME/systemd/user or $HOME/.local/share/systemd/user
    $dir/systemd/user for each $dir in $XDG_DATA_DIRS
    $dir/systemd/user for each $dir in $XDG_DATA_DIRS
    /usr/local/lib/systemd/user
    /usr/lib/systemd/user

* https://www.freedesktop.org/software/systemd/man/systemctl.html

    SYSTEMD_EDITOR
    SYSTEMD_PAGER
    SYSTEMD_LESS

* https://www.freedesktop.org/software/systemd/man/systemd.html

$SYSTEMD_LOG_LEVEL - systemd reads the log level from this environment variable. This can be overridden with --log-level=.

$SYSTEMD_LOG_TARGET - systemd reads the log target from this environment variable. This can be overridden with --log-target=.

$SYSTEMD_LOG_COLOR - Controls whether systemd highlights important log messages. This can be overridden with --log-color=.

$SYSTEMD_LOG_LOCATION - Controls whether systemd prints the code location along with log messages. This can be overridden with --log-location=.

$XDG_CONFIG_HOME, $XDG_CONFIG_DIRS, $XDG_DATA_HOME, $XDG_DATA_DIRS - The systemd user manager uses these variables in accordance to the XDG Base Directory specification to find its configuration.

$SYSTEMD_UNIT_PATH - Controls where systemd looks for unit files.

$SYSTEMD_SYSVINIT_PATH - Controls where systemd looks for SysV init scripts.

$SYSTEMD_SYSVRCND_PATH - Controls where systemd looks for SysV init script runlevel link farms.

$SYSTEMD_COLORS - The value must be a boolean. Controls whether colorized output should be generated. This can be specified to override the decision that systemd makes based on $TERM and what the console is connected to.

$SYSTEMD_URLIFY - The value must be a boolean. Controls whether clickable links should be generated in the output for terminal emulators supporting this. This can be specified to override the decision that systemd makes based on $TERM and other conditions.

$LISTEN_PID, $LISTEN_FDS, $LISTEN_FDNAMES - Set by systemd for supervised processes during socket-based activation. See sd_listen_fds(3) for more information.

$NOTIFY_SOCKET - Set by systemd for supervised processes for status and start-up completion notification. See sd_notify(3) for more information.


## CONF

    /etc/systemd/system.conf, /etc/systemd/system.conf.d/*.conf, /run/systemd/system.conf.d/*.conf, /usr/lib/systemd/system.conf.d/*.conf
  
    /etc/systemd/user.conf, /etc/systemd/user.conf.d/*.conf, /run/systemd/user.conf.d/*.conf, /usr/lib/systemd/user.conf.d/*.conf



* https://www.freedesktop.org/software/systemd/man/system.conf.d.html

All options are configured in the "[Manager]" section:

LogLevel=, LogTarget=, LogColor=, LogLocation=, DumpCore=yes, CrashChangeVT=no, CrashShell=no, CrashReboot=no, ShowStatus=yes, DefaultStandardOutput=journal, DefaultStandardError=inherit

CtrlAltDelBurstAction=

CPUAffinity=

NUMAPolicy=

RuntimeWatchdogSec=, RebootWatchdogSec=, KExecWatchdogSec=

WatchdogDevice=

CapabilityBoundingSet=

NoNewPrivileges=

SystemCallArchitectures=

TimerSlackNSec=

StatusUnitFormat=

DefaultTimerAccuracySec=

DefaultTimeoutStartSec=, DefaultTimeoutStopSec=, DefaultTimeoutAbortSec=, DefaultRestartSec=

DefaultStartLimitIntervalSec=, DefaultStartLimitBurst=

DefaultEnvironment=

DefaultCPUAccounting=, DefaultBlockIOAccounting=, DefaultMemoryAccounting=, DefaultTasksAccounting=, DefaultIOAccounting=, DefaultIPAccounting=

DefaultTasksMax=

DefaultLimitCPU=, DefaultLimitFSIZE=, DefaultLimitDATA=, DefaultLimitSTACK=, DefaultLimitCORE=, DefaultLimitRSS=, DefaultLimitNOFILE=, DefaultLimitAS=, DefaultLimitNPROC=, DefaultLimitMEMLOCK=, DefaultLimitLOCKS=, DefaultLimitSIGPENDING=, DefaultLimitMSGQUEUE=, DefaultLimitNICE=, DefaultLimitRTPRIO=, DefaultLimitRTTIME=

DefaultOOMPolicy=

