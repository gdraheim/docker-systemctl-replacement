# The Testsuite

Before any release "make check" should report no problems.

Some testcases are skipped as they are known bugs or they
point to missing features of systemctl.py. That's okay.

The testsuite is organized by four digit numbers. In all
documents (and issue tickets) only the number is used to
identify the relevant testcase. Four digits are used to
put related testcase into a common group, it is not 
related to the amount of testcases (other than having
enough free numbers in between the groups to allow for 
later addition of testcases into an existing group).

## running testcases by number

The standard python unittest.main() is not used. Instead there
is a slightly different frontend that allows to run testcases
by number in the style of "test_4032". So all the testcases do
have a number and a longer function name where the remainder
of the function name does not need to be used to run a test.

It may be easiest to say
* make test_4032

Actually the implementation is checking for the given testcase
by checking for test function names with that prefix. This 
will also allow to run a group of tests with a common prefix.
The number will ensure that they are being run in an expected
order, so that "make test_900" will run the (up to) ten
testcases of test_9000...test_9009 in that order.

## docker-container or subdir-root

The systemctl.py script supports a non-standard option '--root'
which will ensure that *.service files and other data are being
searched below that point. So with --root=/tmp/run2 you can
install a /tmp/run2/etc/systemd/system/zzc.service to be the
only file being interpreted by systemctl.py.

If there is no --root option being used then systemctl.py will
inspect the standard systemd locations on the disk. This can
be handy in some circumstance but for that test cases that is
only an option inside a docker container where one can control
the files that are being installed as test data.

Note that
* the testcases 1000...4999 are using a --root=subdir environment
* the testcases 5000...9999 will start a docker container to work.

Also remember that not all systemctl.py commands have been checked
to interpret the --root=subdir option correctly. Be wary when you
run systemctl.py outside of a docker container.

## python line coverage

There is an option --coverage on the testsuite which will use an
install pycoverage (in /usr/bin/coverage2) tool to gather the
testsuite coverage of the systemctl.py tool.

The result will be in files/docker/systemctl.py,cover !

You can use "make check" to simply start all testscases including
gathering the coverage. Note however that only the subdir-root
testcases count for the python coverage. (The pycoverage tool is
currently not installed into a docker container and its results
are not pulled out for being added to the general line coverage).

Therefore
* only the testcase 1000...4999 count for line coverage
* running sinle testcases like "make test_4032" has no coverage

## junit xml results

The script may also write a junit xml report instead of the 
standard python testcase results. However this is not part of
the source tree - you need to grab an "xmlrunner.py" copy and
install it to the place where "testsuite.py" shall be run.

That's because a junit xml report does only make sense along
with a Jenkins build server and/or a Sonar server setup where
the results should be gathered. That's not being used for the
opensource Github version at the moment.

