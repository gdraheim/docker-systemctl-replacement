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
test_%: ; ./testsuite.py $@ -vv
real_%: ; ./testsuite.py $@ -vv

15.0/test_%:  ; ./testsuite.py $(notdir $@) -vv --image=opensuse/leap:15.0
42.3/test_%:  ; ./testsuite.py $(notdir $@) -vv --image=opensuse:42.3
42.2/test_%:  ; ./testsuite.py $(notdir $@) -vv --image=opensuse:42.2
18.04/test_%: ; ./testsuite.py $(notdir $@) -vv --image=ubuntu:18.04
16.04/test_%: ; ./testsuite.py $(notdir $@) -vv --image=ubuntu:16.04
7.5/test_%:   ; ./testsuite.py $(notdir $@) -vv --image=centos:7.5.1804
7.4/test_%:   ; ./testsuite.py $(notdir $@) -vv --image=centos:7.4.1708
7.3/test_%:   ; ./testsuite.py $(notdir $@) -vv --image=centos:7.3.1611

check: check2018
	@ echo please run 'make checks' now
18 check2018: ; ./testsuite.py -vv --opensuse=15.0 --centos=7.5 --ubuntu=18.04
17 check2017: ; ./testsuite.py -vv --opensuse=42.3 --centos=7.4 --ubuntu=16.04
16 check2016: ; ./testsuite.py -vv --opensuse=42.2 --centos=7.3 --ubuntu=16.04

2/test_%:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv $(notdir $@) --sometime=666 \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python
3/test_%:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv $(notdir $@) --sometime=666 \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

check2:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python
check3:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

checks: 
	- rm .coverage* 
	$(MAKE) checks2_coverage
	for i in .coverage*; do mv $$i $$i.cov2; done
	$(MAKE) checks3_coverage
	for i in .coverage*; do mv $$i $$i.cov3; done
	coverage combine && coverage report && coverage annotate
	test -l tmp/systemctl.py,cover
checks2:  
	rm .coverage* ; $(MAKE) checks2_coverage
checks2_coverage:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv --coverage \
	   '--with=tmp/systemctl.py'
checks3: 
	rm .coverage* ; $(MAKE) checks3_coverage
checks3_coverage: 
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv --coverage \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3
coverage: coverage2
coverage2: 
	$(MAKE) tmp_systemctl_py_2
	rm .coverage* ; ./testsuite.py -vv --coverage test_1 test_2 test_3 test_4 test_6 \
	  '--with=tmp/systemctl.py'
coverage3:
	$(MAKE) tmp_systemctl_py_3
	rm .coverage* ; ./testsuite.py -vv --coverage test_1 test_2 test_3 test_4 test_6 \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

tmp_systemctl_py_2:
	@ test -d tmp || mkdir tmp
	@ cp files/docker/systemctl.py tmp/systemctl.py
tmp_systemctl_py_3:
	@ test -d tmp || mkdir tmp
	@ cp files/docker/systemctl.py tmp/systemctl.py
	@ sed -i -e "s|/usr/bin/python|/usr/bin/python3|" tmp/systemctl.py
st_%:
	$(MAKE) tmp_systemctl_py_3
	rm .coverage* ; ./testsuite.py -vv --coverage te$@ \
	   '--with=tmp/systemctl.py' --python=/usr/bin/python3

op opensuse: ; ./testsuite.py make_opensuse
ub ubuntu:   ; ./testsuite.py make_ubuntu
ce centos:   ; ./testsuite.py make_centos

clean:
	- rm .coverage*
	- rm -rf tmp/tmp.test_*
	- rm -rf tmp/systemctl.py

