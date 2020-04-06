## TYPEHINTS

The systemctl.py 1.5 supports type hints along Python3 typing annotations.

In order to make this completely optional, the actual typing hints do
live in a seperate file called `types/systemctl3.pyi`

With the help of git@github.com:ambv/retype.git these are implanted
into files/docker/systemctl3.py to have an actualy 'mypy' check.

Use `make type` to run stubgen, retype, and mypy in one stop.

Adding type hints should only be done in systemctl3.pyi and not
on the actualy systemctl3.py source code. Remember that systemctl.py
and systemctl3.py are actual the same source code, so that patches
to python2 can be easily applied to python3 and vice versa.
