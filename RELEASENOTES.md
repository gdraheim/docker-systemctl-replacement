RELEASE 1.5 - now switching to 1.7

The release branch 1.4 has been stable for a long time. Nethertheless there
is still much room for improvement which is also shown by the hundreds of
commits that went into this release.

Most prominently, Python 3 is the default variant now. Just as in the previous
release branch there is only one code basis for python2 and python3 but the
primary test target has changed. If you run "make test_1000" then you see
the result from systemctl3.py now, and "make 2" will derive systemctl.py
from it. The testsuite.py itself is also run by a python3 interpreter now.

The systemctl3.py script is accompanied by a systemctl3.pyi script with type 
hints to allow for strict type checking. Static code analysis is a big
advantage. Not only for nullable types but also for mere typos that can not 
be missed anymore when the testsuite does not touch that line. Still the 
testsuite has a line code coverage of 94% for this release.

There are some breaking changes though. Especially the variable expansion 
has changed which was wrong in 1.4 but some scripts may already rely on the
way it worked. Some of the root/user directories have changed in their real
locations as well. And the computation for the default-services and starting
order has been improved as well.

The new socket support may be a reason for problems in old code as well.
Actually, the release 1.5 does only implement non-accept units where the
xy.service is directly started when the xy.socket is started. The
accept-listeners code can be tested with "-c TestAccept=yes" as seen in
the testsuite, and the listeners themselves have a "systemctl listen"
command. But it is incomplete beyond repair. In the real world however
it was all sufficient to support sshd and cvsd in containers.

As a consequence, the support for xy.target units was improved as well,
and multi instance template services have much wider support in their
features. The logging features implement a number of redirects for the
service stdout/stderr as well. Because of that, check the JournalFilePath
property when looking for the place where the logs from the service go.

As mentioned already, there is a new commandline feature in the 1.5 
release branch which did not exist in 1.4: you can enable/disable internal
options and defaults via "--config Feature=xy" on the commandline. Some of
the environment variables are still supported (atleast when the 
original systemd does as well) but a "-c DefaultUnit=your.target" 
will override them. Any global variable in the systemctl3.py code is 
generically accessible through that commandline option.

You will need those when you like to finetune the support for service
that can automatically restart themselves when they fail. The timeout
variables have a default so that it is not enabled by default - but 
some services have explicit values in their unit file which will promptly
enable that feature now. Note however that only very simple strategies
are supported here and we ask you to use the HealthCheck features of 
your docker environment to get things right.

Internally, there are a number of changes as well. One important thing
was the original start of the 1.5 branch where the exit-code of the
program is not derived from just the return value of a function but
it also checks for the ".error" bitmask. That's in preparation of some
C99 implementation in the feature/cplusplus branch of this project. It 
will not be merged soon but the foundation is there where the Python code
and C/C++ code represent the same logic with the same variables and
the same function names and types.

RELEASE 1.7

Python2 can not be installed on Ubuntu24.04 and AlmaLinux 9.3 (202311). 
The RHEL7 distribution runs out of support by June 2024 (with some
extended support till 2026). As such the Python2 development in this
project will be mostly dropped after 2024. The developments for a 2.x
version in 2025 were never released however. Instead the project picked 
up some of the changes in 2025 merging them into a 1.7 release 
series (version 1.6 is another branch that was never released). 

The release 1.7 is taking advantage of the strip_python3 project 
that had been developed during 2025 as a side-project. The
strip_python3 tool allows to use modern python3 features (syntax and
library parts) during development replacing them with compatible older 
features for shipping to pypi.org. That way systemctl.py can be installed 
on very old systems. Additionally, a back-to-python2 output script can 
be tested on the developer side to actually work as expected. As such
python2 does still get minimal support - the easiest way to get a
python2 systemctl.py is by dowloading the pypi package using "pip".

As a consequence, the systemctl3.pyi typehints file is gone, just as 
the systemctl.py python2 script has been removed from the git repo. 
Instead there is only systemctl3.py that includes typehints - that makes 
for a minimum  python version of python3.6 if systemctl3.py is being used 
unmodified  (not handled by strip_python3). By 2026 even python3.9 has 
been out of maintenance, so expect that features up to that version will
picked up.
