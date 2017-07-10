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

Shows the start-order of services. The first item is
started as the last item and the item on the bottom
is the first that will get a real "start <unit>".

Use -v debugging to see how the start-rank is computed
from the Before/After clauses in the unit files.

The reversed-order is based on the fact that initially
the Required items are added to the list at the end.
The real execution order on "start" must be inversed 
while upon "stop" it is run in the listed order.
