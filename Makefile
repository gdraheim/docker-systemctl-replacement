F= files/docker/systemctl.py
B= 2016
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'

version1:
	@ grep -l __version__ */*.??* */*/*.??* | { while read f; do echo $$f; done; } 

version:
	@ grep -l __version__ */*.??* */*/*.??* *.py | { while read f; do : \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $B) \
	; D=`date +%W$(DAY) -d "$(FOR)"` ; sed -i \
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
	sed -i -e "s|the.*identical but for|this is just a copy from systemctl.py but for|" files/docker/systemctl3.py
	diff -U1 files/docker/systemctl.py files/docker/systemctl3.py || true
2:
	cp -v files/docker/systemctl.py files/docker/systemctl2.py
	sed -i -e "s|/usr/bin/python|/usr/bin/python2|" files/docker/systemctl2.py
	sed -i -e "s|the.*identical but for|this is just a copy from systemctl.py but for|" files/docker/systemctl2.py
	diff -U1 files/docker/systemctl.py files/docker/systemctl2.py || true

alltests: CH CP UA DJ

CH centos-httpd.dockerfile: ; ./testsuite.py test_6001
CP centos-postgres.dockerfile: ; ./testsuite.py test_6002
UA ubuntu-apache2.dockerfile: ; ./testsuite.py test_6005
DJ docker-jenkins: ; ./testsuite.py test_900*

COVERAGE=--coverage
est_%: ; rm .coverage* ; ./testsuite.py "t$@" -vv --coverage
test_%: ; ./testsuite.py "$@" -vv
real_%: ; ./testsuite.py "$@" -vv
test: ; $(MAKE) "test_[1234]"
st_%: ; $(MAKE) 3 && ./testsuite.py "te$@" -vv $(WITH3)

WITH3 = --python=/usr/bin/python3 --with=files/docker/systemctl3.py
todo/test_%:             ; ./testsuite.py   "$(notdir $@)" -vv --todo
15.2/test_%:             ; ./testsuite.py   "$(notdir $@)" -vv --image=opensuse/leap:15.2
15.1/test_%:             ; ./testsuite.py   "$(notdir $@)" -vv --image=opensuse/leap:15.1
15.0/test_%:             ; ./testsuite.py   "$(notdir $@)" -vv --image=opensuse/leap:15.0
42.3/test_%:             ; ./testsuite.py   "$(notdir $@)" -vv --image=opensuse:42.3
42.2/test_%:             ; ./testsuite.py   "$(notdir $@)" -vv --image=opensuse:42.2
19.10/test_%:            ; ./testsuite.py   "$(notdir $@)" -vv --image=ubuntu:19.10
18.04/test_%:            ; ./testsuite.py   "$(notdir $@)" -vv --image=ubuntu:18.04
16.04/test_%:            ; ./testsuite.py   "$(notdir $@)" -vv --image=ubuntu:16.04
8.1/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:8.1.1911
8.0/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:8.0.1905
7.7/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:7.7.1908
7.6/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:7.6.1810
7.5/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:7.5.1804
7.4/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:7.4.1708
7.3/test_%:              ; ./testsuite.py   "$(notdir $@)" -vv --image=centos:7.3.1611
15.2/st_%:  ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=opensuse/leap:15.2 $(WITH3)
15.1/st_%:  ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=opensuse/leap:15.1 $(WITH3)
15.0/st_%:  ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=opensuse/leap:15.0 $(WITH3)
42.3/st_%:  ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=opensuse:42.3      $(WITH3)
42.2/st_%:  ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=opensuse:42.2      $(WITH3)
18.04/st_%: ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=ubuntu:18.04       $(WITH3)
16.04/st_%: ; $(MAKE) 3 && ./testsuite.py "te$(notdir $@)" -vv --image=ubuntu:16.04       $(WITH3)

test3list = st_[567]
testslist = test_[567]
tests: ; $(MAKE) "test_[1234]"
.PHONY: tests
15.2/tests:  ; $(MAKE) "15.2/$(testslist)"
15.1/tests:  ; $(MAKE) "15.1/$(testslist)"
15.0/tests:  ; $(MAKE) "15.0/$(testslist)"
42.3/tests:  ; $(MAKE) "42.3/$(testslist)"
42.2/tests:  ; $(MAKE) "42.2/$(testslist)"
19.10/tests: ; $(MAKE) "19.10/$(testslist)"
18.04/tests: ; $(MAKE) "19.04/$(testslist)"
16.04/tests: ; $(MAKE) "16.04/$(testslist)"
8.1/tests:   ; $(MAKE) "8.1/$(testslist)"
8.0/tests:   ; $(MAKE) "8.0/$(testslist)"
7.7/tests:   ; $(MAKE) "7.7/$(testslist)"
7.6/tests:   ; $(MAKE) "7.6/$(testslist)"
7.5/tests:   ; $(MAKE) "7.5/$(testslist)"
7.4/tests:   ; $(MAKE) "7.4/$(testslist)"
7.3/tests:   ; $(MAKE) "7.3/$(testslist)"
15.2/test3:  ; $(MAKE) "15.2/$(test3list)"
15.1/test3:  ; $(MAKE) "15.1/$(test3list)"
15.0/test3:  ; $(MAKE) "15.0/$(test3list)"
42.3/test3:  ; $(MAKE) "42.3/$(test3list)"
42.2/test3:  ; $(MAKE) "42.2/$(test3list)"
18.04/test3: ; $(MAKE) "19.04/$(test3list)"
16.04/test3: ; $(MAKE) "16.04/$(test3list)"

nightrun: checkall
	$(MAKE) checks
checkall: checkall2019
checkall2018: $(MAKE) 
	$(MAKE) -j1 tests
	$(MAKE) -j1 7.5/tests 7.4/tests 7.3/tests
	$(MAKE) -j1 18.04/tests 16.04/tests
	$(MAKE) -j1 15.0/tests 42.3/tests
	$(MAKE) -j1 18.04/test3 16.04/test3
	$(MAKE) -j1 15.0/test3 42.3/test3
checkall2019:
	$(MAKE) -j1 tests
	$(MAKE) -j1 7.7/tests 7.5/tests 7.4/tests 7.3/tests
	$(MAKE) -j1 18.04/tests 16.04/tests
	$(MAKE) -j1 15.1/tests 15.0/tests 42.3/tests
	$(MAKE) -j1 18.04/test3 16.04/test3
	$(MAKE) -j1 15.1/test3 15.0/test3 42.3/test3

check: check2019
	@ echo please run 'make checks' now
19 check2019: ; ./testsuite.py -vv --opensuse=15.1 --centos=7.7 --ubuntu=18.04
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

2/est_%:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv t$(notdir $@) --sometime=666 --coverage \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python
3/est_%:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv t$(notdir $@) --sometime=666 --coverage \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

check2:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python
check3:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

checks: checks.1 checks.2 checks.3 checks.4
checks.1:
	- rm .coverage* 
checks.2:
	$(MAKE) checks2_coverage
	for i in .coverage*; do mv $$i $$i.cov2; done
checks.3:
	$(MAKE) checks3_coverage
	for i in .coverage*; do mv $$i $$i.cov3; done
checks.4:
	coverage combine && coverage report && coverage annotate
	ls -l tmp/systemctl.py,cover
	@ echo ".... are you ready for 'make checkall' ?"

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

clean:
	- rm .coverage*
	- rm -rf tmp/tmp.test_*
	- rm -rf tmp/systemctl.py

box:
	docker rm -f $@ ; docker run -d --name $@ --rm=true centos:centos7 sleep 600
	docker cp files/docker/systemctl.py box:/usr/bin/systemctl
	docker exec box systemctl daemon-reload -vvv
	@ echo : docker exec -it box bash
