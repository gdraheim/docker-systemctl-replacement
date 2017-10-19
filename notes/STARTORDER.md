# Start/Stop ordering and Dependencies

There is a lot of confusion what the various definitions
for dependencies After/Wants/Requires will actually do.

Note that the list of Requires/etc services comes from
multiple Requires/etc text-lines and on each text-line 
one may define multiple names of dependencies.

The entry point for reading should be:

https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Requires=

## Dependencies

### Requires

It says >>Configures requirement dependencies on other units. If this unit 
gets activated, the units listed here will be activated as well.<< / >>Note 
that requirement dependencies do not influence the order in which services 
are started or stopped. This has to be configured independently with the 
After= or Before= options.<<

So actually, if there is a Requires but no After then the current service
and its required dependency service may be started in parallel.

Additionally >>If one of the other [Requires] units gets deactivated or its 
activation fails, this unit will be deactivated.<< /  >>Often, it is a 
better choice to use Wants= instead of Requires= in order to achieve a system 
that is more robust when dealing with failing services.<<

So theoretically, if we have a phpadmin service then if there is a call to
"systemctl stop mariadb" then it should automatically do some "systemctl
stop phpadmin". However if the mariadb-service fails and it just goes into
an inactive-state then the phpadmin service continues to run. >>Use the 
BindsTo= dependency type together with After= to ensure that a unit may 
never be in active state without a specific other unit also in active 
state<<

### Wants

We have >>A weaker version of Requires=. Units listed in this option will 
be started if the configuring unit is. However, if the listed units fail 
to start or cannot be added to the transaction, this has no impact on the 
validity of the transaction as a whole. This is the recommended way to hook 
start-up of one unit to the start-up of another unit.<<

So just like "Requires" when "systemctl start phpadmin" then it will also
execute "systemctl start mariadb" (possibly in parallel). However mariadb
might not be installed or it is "systemctl mask"ed, in which case there is
not start-action attempted for it.

### Requisite / BindsTo / PartOf / PropagateReloadTo

For Bindsto we have >>When used in conjunction with After= on the same 
unit the behaviour of BindsTo= is even stronger. In this case, the unit 
bound to strictly has to be in active state for this unit to also be in 
active state.<< More importantly, this is completely transitive.

For Requisite we have >>Similar to Requires=. However, if the units listed 
here are not started already, they will not be started and the transaction 
will fail immediately.<< In other words, "systemctl start phpadmin" will
not run "systemctl start mariadb" but when mariadb is inactive then the
call to start-phpadmin will fail.

And for PartOf we have >>Configures dependencies similar to Requires=, but 
limited to stopping and restarting of units. When systemd stops or restarts 
the units listed here, the action is propagated to this unit.<<

And for PropagatesReloadTo=, ReloadPropagatedFrom= we have >>Issuing a 
reload request on a unit will automatically also enqueue a reload request 
on all units that the reload request shall be propagated to via these two 
settings.<<

### Conflicts

This is an exclusive-mark, so if service A is started then it should
stop service B and vice versa.

## systemctl.py

As there is no parallism in systemctl we can actually ignore anything that
looks like After/Before.

### start logic

Without a global dependency graph we would do:

GIVEN <phpadmin> Requires / BindsTo <mariadb> AND <mariadb> EXISTS.
ON "start <phpadmin> THEN 
  IF inactive <mariadb> THEN do "start <mariadb>" and wait for result.
     AND mark a "dependency-start <mariadb>"
  IF active <mariadb> THEN do not wait.
  AFTER wait IF active <mariadb> THEN do "start <phadmin>". BUT...
  AFTER wait IF inactive <mariadb> THEN fail "start <phpadmin>".

GIVEN <phpadmin> Requires / BindsTo <mariadb> AND <mariadb> MISSING.
ON "start <phpadmin>" THEN fail "start <phpadmin>".

GIVEN <phpadmin> Wants <mariadb> AND <mariadb> EXISTS.
ON "start <phpadmin> THEN 
: IF inactive <mariadb> THEN do "start <mariadb>" and wait for result.
::    AND mark a "dependency-start <mariadb>"
: IF active <mariadb> THEN do not wait.
: AFTER wait IF active <mariadb> THEN do "start <phadmin>".
: AFTER wait IF inactive <mariadb> THEN do "start <phpadmin>".

GIVEN <phpadmin> Wants <mariadb> AND <mariadb> MISSING.
ON "start <phpadmin>" THEN do "start <phpadmin>".

GIVEN <phpadmin> Requisite <mariadb> AND <mariadb> EXISTS.
ON "start <phpadmin> THEN 
: IF inactive <mariadb> THEN fail "start <phpadmin>"
: IF active <mariadb> THEN do "start <phpadmin>"

GIVEN <phpadmin> Conflicts <phpadmin5> AND <phpadmin5> EXISTS.
ON "start <phpadmin>" THEN
   IF active <phpadmin5> THEN do "stop <phpadmin5>"

### stop logic

There is no explanatation whether a dependency that was
indirectly started should also be stopped when the original
script is being stopped.

Without a global dependency graph we would do:

GIVEN <phpadmin> Requires / BindsTo / Wants <mariadb> AND <mariadb> EXISTS.
: IF active <mariadb> AND "dependency-start <mariadb>"
: THEN do "stop <mariadb>" and drop dependency-start mark

### restart logic

Without a global dependency graph we would do:

Nothing is propagated

### reload logic

Without a global dependency graph we would do:

GIVEN <phpadmin> PropagatesTo <mariadb> AND <mariadb> EXISTS.
: IF active <mariadb> THEN do "reload <mariadb>"

## .wants directories

The list of Wants may be extended by symlinks in a directory
for the service file. So if there is a file 'phpadmin.service'
then there MAY be a directory 'phpadmin.service.wants/'.

The list of Requires may be extended by symlinks in directory
for the service file. So if there is a file 'phpadmin.service'
then there MAY be a directory 'phpadmin.service.requires/'.

No other types of directory wants/requires are defined.

### After / Before

Each service may have a list of dependencies. The order of
their start is determined by the After and Before clauses
within their files.

Theoretically this should be transitive. So if a dependency
does have other dependencies then their order should be
looked up as well.

### list-dependencies

There is a "systemctl list-dependencies"

That one will also show dependencies of dependencies.

Note that we only check the dependencies in the "[Unit]"
section and not in the "[Install]" section. The install
section will tell the "enable <unit>" command where to
set a symlink in a .wants/.requires directory.

As such, after an enable-ment it should pop up as a
dependency.
