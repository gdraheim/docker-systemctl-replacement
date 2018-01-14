F= files/docker/systemctl.py
B= 2016

version1:
	@ grep -l __version__ */*.??* */*/*.??* | { while read f; do echo $$f; done; } 

version:
	@ grep -l __version__ */*.??* */*/*.??* *.py | { while read f; do : \
	; Y=`date +%Y` ; X=$$(expr $$Y - $B); D=`date +%W%u` ; sed -i \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $B-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep ^__version__ files/*/*.??*

help:
	python files/docker/systemctl.py help
3:
	cp -v files/docker/systemctl.py files/docker/systemctl3.py
	sed -i -e "s|/usr/bin/python|/usr/bin/python3|" files/docker/systemctl3.py
	diff -U1 files/docker/systemctl.py files/docker/systemctl3.py || true

alltests: CH CP UA DJ
.PHONY: tests
tests: alltests

CH centos-httpd.dockerfile: ; ./testsuite.py test_6001
CP centos-postgres.dockerfile: ; ./testsuite.py test_6002
UA ubuntu-apache2.dockerfile: ; ./testsuite.py test_6005
DJ docker-jenkins: ; ./testsuite.py test_900*

COVERAGE=--coverage
est_%: ; rm .coverage* ; ./testsuite.py t$@ -vv --coverage
coverage: ; rm .coverage* ; ./testsuite.py -vv --coverage test_1 test_2 test_3 test_4 test_6
check: ; rm .coverage* ; ./testsuite.py -vv --coverage
test_%: ; ./testsuite.py $@ -vv
real_%: ; ./testsuite.py $@ -vv

9: test_9001 test_9002 test_9003 test_9004 test_9005 test_9006

st_%:
	$(MAKE) tmp/systemctl.py
	rm .coverage* ; ./testsuite.py -vv --coverage te$@ \
	   '--with=tmp/systemctl.py' --python=/usr/bin/python3
check3:
	$(MAKE) tmp/systemctl.py
	rm .coverage* ; ./testsuite.py -vv --coverage \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3
coverage3:
	$(MAKE) tmp/systemctl.py
	rm .coverage* ; ./testsuite.py -vv --coverage test_1 test_2 test_3 test_4 test_6 \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

tmp/systemctl.py : files/docker/systemctl.py
	test -d tmp || mkdir tmp
	cp files/docker/systemctl.py tmp/systemctl.py
	sed -i -e "s|/usr/bin/python|/usr/bin/python3|" tmp/systemctl.py

op opensuse: ; ./testsuite.py make_opensuse
ub ubuntu:   ; ./testsuite.py make_ubuntu
ce centos:   ; ./testsuite.py make_centos

clean:
	- rm .coverage*
	- rm -rf tmp/tmp.test_*
