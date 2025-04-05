F= files/docker/systemctl3.py
B= 2024
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'


UBUNTU=ubuntu:24.04
PYTHON=python3
PYTHON2 = python2
PYTHON3 = python3
PYTHON39 = python3.11
PYTHON_VERSION = 3.7
COVERAGE3 = $(PYTHON3) -m coverage
TWINE = twine
TWINE39 = twine-3.11
GIT=git
VERFILES = files/docker/systemctl3.py testsuite.py pyproject.toml
CONTAINER = docker-systemctl-

verfiles:
	@ grep -l __version__ */*.??* */*/*.??* | { while read f; do echo $$f; done; } 

version:
	@ grep -l __version__ $(VERFILES) | { while read f; do : \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $B) \
	; D=`date +%W$(DAY) -d "$(FOR)"` ; sed -i \
	-e "/^ *version = /s/[.]-*[0123456789][0123456789][0123456789]*/.$$X$$D/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $B-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep ^__version__ $(VERFILES)
	@ grep ^version.= $(VERFILES)
	@ $(GIT) add $(VERFILES) || true
	@ ver=`cat files/docker/systemctl3.py | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"

help:
	python files/docker/systemctl3.py help

alltests: CH CP UA DJ

CH centos-httpd.dockerfile: ; ./testsuite.py test_6001
CP centos-postgres.dockerfile: ; ./testsuite.py test_6002
UA ubuntu-apache2.dockerfile: ; ./testsuite.py test_6005
DJ docker-jenkins: ; ./testsuite.py test_900*

VV=-vv
COVERAGE=--coverage
est_%: ; rm .coverage*; rm -rf tmp/tmp.t$(notdir $@) ; ./testsuite.py "t$(notdir $@)" $(VV) $V --coverage --keep
test_%: ; ./testsuite.py "$(notdir $@)" $(VV) $V
real_%: ; ./testsuite.py "$(notdir $@)" $(VV) $V

test: ; $(MAKE) type && $(MAKE) tests && $(MAKE) coverage

WITH3 = --python=/usr/bin/python3 --with=files/docker/systemctl3.py
test_%/todo:             ; ./testsuite.py   "$(dir $@)" -vv --todo
test_%/15.6:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse/leap:$(notdir $@)
test_%/15.4:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse/leap:$(notdir $@)
test_%/15.3:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse/leap:$(notdir $@)
test_%/15.2:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse/leap:$(notdir $@)
test_%/15.1:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse/leap:$(notdir $@)
test_%/15.0:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse/leap:$(notdir $@)
test_%/42.3:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse:$(notdir $@)
test_%/42.2:             ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=opensuse:$(notdir $@)
test_%/24.04:            ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=ubuntu:$(notdir $@)
test_%/22.04:            ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=ubuntu:$(notdir $@)
test_%/20.04:            ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=ubuntu:$(notdir $@)
test_%/19.10:            ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=ubuntu:$(notdir $@)
test_%/19.04:            ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=ubuntu:$(notdir $@)
test_%/16.04:            ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=ubuntu:$(notdir $@)
test_%/9.4:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=almalinux:$(notdir $@)
test_%/9.3:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=almalinux:$(notdir $@)
test_%/9.1:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=almalinux:$(notdir $@)
test_%/8.1:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:8.1.1911
test_%/8.0:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:8.0.1905
test_%/7.7:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:7.7.1908
test_%/7.6:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:7.6.1810
test_%/7.5:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:7.5.1804
test_%/7.4:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:7.4.1708
test_%/7.3:              ; ./testsuite.py   "$(dir $@)" -vv $(FORCE) --image=centos:7.3.1611

basetests = test_[1234]
test2list = st_[567]
testslist = test_[567]
tests: ; $(MAKE) "${basetests}"
.PHONY: tests
tests/15.6:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/15.5:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/15.4:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/15.2:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/15.1:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/15.0:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/42.3:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/42.2:  ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/24.04: ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/22.04: ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/20.04: ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/19.10: ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/18.04: ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/16.04: ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/9.4:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/9.3:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/9.1:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/8.5:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/8.1:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/8.0:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/7.9:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/7.7:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/7.6:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/7.5:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/7.4:   ; $(MAKE) "$(testslist)/$(notdir $@)"
tests/7.3:   ; $(MAKE) "$(testslist)/$(notdir $@)"
test2/15.2:  ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/15.1:  ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/15.0:  ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/42.3:  ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/42.2:  ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/22.04: ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/20.04: ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/18.04: ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/16.04: ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/8.5:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/8.1:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/8.0:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/7.9:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/7.7:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/7.6:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/7.5:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/7.4:   ; $(MAKE) "$(test2list)/$(notdir $@)"
test2/7.3:   ; $(MAKE) "$(test2list)/$(notdir $@)"

nightrun: checkall
	$(MAKE) checks
checkall: checkall2025
checkall2024:
	$(MAKE) -j1 9.3/tests   8.5/tests   7.9/tests
	$(MAKE) -j1 24.04/tests 22.04/test2 18.04/tests
	$(MAKE) -j1 15.6/tests  15.5/tests  15.4/tests  15.2/tests
checkall2025:
	$(MAKE) -j1 tests/9.4
	$(MAKE) -j1 tests/24.04 tests/22.04 tests/20.04
	$(MAKE) -j1 tests/15.6  tests/15.4


check: check2025
	@ echo please run 'make checks' now
24 check2024: ; ./testsuite.py -vv --opensuse=15.6 --ubuntu=ubuntu:24.04 --centos=almalinux:9.3
25 check2025: ; ./testsuite.py -vv --opensuse=15.6 --ubuntu=ubuntu:24.04 --centos=almalinux:9.4

# native operating system does not have python2 anymore
test_%/27:
	$(MAKE) tmp_systemctl_py_2
	docker rm -f $(CONTAINER)-python$(notdir $@)
	docker run -d --name=$(CONTAINER)-python$(notdir $@) python$(notdir $@)/test sleep 9999
	docker exec $(CONTAINER)-python$(notdir $@) mkdir -p $(PWD)/tmp
	docker cp testsuite.py $(CONTAINER)-python$(notdir $@):/
	docker cp reply.py $(CONTAINER)-python$(notdir $@):/
	docker cp tmp/systemctl.py $(CONTAINER)-python$(notdir $@):/$(PWD)/tmp/
	docker exec $(CONTAINER)-python$(notdir $@) chmod +x /$(PWD)/tmp/systemctl.py
	docker exec $(CONTAINER)-python$(notdir $@) /testsuite.py -vv $(dir $@) --sometime=666 \
	  '--with=/$(PWD)/tmp/systemctl.py' --python=/usr/bin/python2 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || docker cp $(CONTAINER)-python$(notdir $@):/.coverage .coverage.cov1
	docker rm -f $(CONTAINER)-python$(notdir $@)
test_%/36:
	$(MAKE) tmp_systemctl_py_3
	docker rm -f $(CONTAINER)-python$(notdir $@)
	docker run -d --name=$(CONTAINER)-python36 python$(notdir $@)/test sleep 9999
	docker exec $(CONTAINER)-python$(notdir $@) mkdir -p $(PWD)/tmp
	docker cp testsuite.py $(CONTAINER)-python$(notdir $@):/
	docker cp reply.py $(CONTAINER)-python$(notdir $@):/
	docker cp tmp/systemctl.py $(CONTAINER)-python$(notdir $@):/$(PWD)/tmp/
	docker exec $(CONTAINER)-python$(notdir $@) chmod +x /$(PWD)/tmp/systemctl.py
	docker exec $(CONTAINER)-python$(notdir $@) /testsuite.py -vv $(dir $@) --sometime=666 \
	  '--with=/$(PWD)/tmp/systemctl.py' --python=/usr/bin/python3 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || docker cp $(CONTAINER)-python$(notdir):/.coverage .coverage.cov1
	docker rm -f $(CONTAINER)-python$(notdir $@)


test_%/2:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv $(dir $@) --sometime=666 \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python2
test_%/3:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv $(dir $@) --sometime=666 \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

est_%/2:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv t$(dir $@) --sometime=666 --coverage \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python2
est_%/3:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv t$(dir $@) --sometime=666 --coverage \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

check2:
	$(MAKE) tmp_systemctl_py_2
	./testsuite.py -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python2
check3:
	$(MAKE) tmp_systemctl_py_3
	./testsuite.py -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

checks: checks27 checks36 coverage
	: ready for make checkall

checks27:  
	$(MAKE) "test_[12345]/27" 
checks36:  
	$(MAKE) "test_[12345]/36" 

coverage: coverage3
	$(PYTHON) -m coverage combine && \
	$(PYTHON) -m coverage report && \
	$(PYTHON) -m coverage annotate
	- $(PYTHON) -m coverage xml -o tmp/coverage.xml
	- $(PYTHON) -m coverage html -d tmp/htmlcov
	ls -l tmp/systemctl.py,cover
coverage2: 
	$(MAKE) tmp_systemctl_py_2
	rm .coverage* ; ./testsuite.py -vv --coverage ${basetests} --xmlresults=TEST-systemctl-python2.xml \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python2
coverage3:
	$(MAKE) tmp_systemctl_py_3
	rm .coverage* ; ./testsuite.py -vv --coverage ${basetests} --xmlresults=TEST-systemctl-python3.xml \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

p2: tmp_systemctl_py_2
p3: tmp_systemctl_py_3


tmp_systemctl_py_2:
	@ test -d tmp || mkdir tmp
	@ $(MAKE) tmp/systemctl_2.py
	@ cp tmp/systemctl_2.py tmp/systemctl.py
	@ sed -i -e "s:/usr/bin/python3:/usr/bin/python2:" -e "s:/env python3:/env python2:" tmp/systemctl.py
#	cp -v ../docker-systemctl-replacement-master/files/docker/systemctl.py tmp/systemctl.py
tmp_systemctl_py_3:
	@ test -d tmp || mkdir tmp
	@ cp files/docker/systemctl3.py tmp/systemctl.py
tmp_ubuntu:
	if docker ps | grep $(UBU); then : ; else : \
	; docker run --name $(UBU) -d $(UBUNTU) sleep 3333 \
	; docker exec $(UBU) apt-get update -y --fix-missing \
	; docker exec $(UBU) apt-get install -y --fix-broken --ignore-missing python3-coverage mypy \
	; fi
	docker cp files $(UBU):/root/
	docker cp testsuite.py $(UBU):/root/ 
	docker cp reply.py $(UBU):/root/ 
UBU=test_ubuntu
test_%/ubu:
	$(MAKE) tmp_ubuntu
	docker exec $(UBU) python3 /root/testsuite.py -C /root -vv $(notdir $@)

clean:
	- rm .coverage*
	- rm -rf tmp/tmp.test_*
	- rm -rf tmp/systemctl.py
	- rm -rf tmp.* types/tmp.*
	- rm -rf .mypy_cache files/docker/.mypy_cache

copy:
	cp -v ../docker-mirror-packages-repo/docker_mirror.py .
	cp -v ../docker-mirror-packages-repo/docker_mirror.pyi .
	cp -v ../docker-mirror-packages-repo/docker_image.py .
	@ grep __version__ docker_mirror.py | sed -e "s/__version__/: git commit -m 'docker_mirror/" -e "s/\$$/' docker*.py*/"

dockerfiles:
	for dockerfile in centos7-lamp-stack.dockerfile opensuse15-lamp-stack.dockerfile \
	; do test -f ../docker-systemctl-images/$$dockerfile || continue \
	; echo "###################################################################################################" > test-$$dockerfile \
	; echo "## this file is a copy from gdraheim/docker-systemctl-images where more real world examples are :)"  >> test-$$dockerfile \
	; echo "## https://github.com/gdraheim/docker-systemctl-images/blob/develop/$$dockerfile" >> test-$$dockerfile \
	; echo "###################################################################################################" >> test-$$dockerfile \
	; cat ../docker-systemctl-images/$$dockerfile >> test-$$dockerfile \
	; wc -l test-$$dockerfile \
	; done

python27: python27/test
python36: python36/test
python39: python39/test
python310: python310/test
python311: python311/test
python312: python312/test

python27/testt: ; ./docker_local_image.py FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc python2" TEST "python2 --version"
python36/testt: ; ./docker_local_image.py FROM ubuntu:18.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
python310/test: ; ./docker_local_image.py FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
python312/test: ; ./docker_local_image.py FROM ubuntu:24.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"

python27/test:  ; ./docker_local_image.py FROM opensuse/leap:15.6 INTO $@ INSTALL "python3 procps psmisc python2" TEST "python2 --version"
python36/test:  ; ./docker_local_image.py FROM opensuse/leap:15.6 INTO $@ INSTALL "python3 procps psmisc" TEST "python3 --version"
python39/test:  ; ./docker_local_image.py FROM opensuse/leap:15.5 INTO $@ INSTALL "python39 procps psmisc" SYMLINK /usr/bin/python3.9:python3 TEST "python3 --version" -vv
python311/test: ; ./docker_local_image.py FROM opensuse/leap:15.6 INTO $@ INSTALL "python311 procps psmisc" SYMLINK /usr/bin/python3.11:python3 TEST "python3 --version"

python: python27/test python36/test

############## https://pypi.org/...

src/systemctl.py:
	test -d $(dir $@) || mkdir -v $(dir $@)
	$(PYTHON39) $(STRIPHINTS3) files/docker/systemctl3.py -o $@
src/systemctl3.py:
	cp files/docker/systemctl3.py $@
src/README.md: README.md Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	cat README.md | sed -e "/\\/badge/d" -e /^---/q > $@

.PHONY: build
src-files:
	$(MAKE) $(PARALLEL) src/README.md src/systemctl.py src/systemctl3.py
src-remove:
	- rm -v src/README.md src/systemctl.py src/systemctl3.py
	- rmdir src

PIP3 = pip3
build:
	rm -rf build dist *.egg-info
	$(MAKE) src-files
	# pip install --root=~/local . -v
	$(PYTHON39) -m build
	$(MAKE) src-remove
	$(TWINE39) check dist/*
	: $(TWINE39) upload dist/*

ins install:
	$(MAKE) src-files
	$(PIP3) install --no-compile --user .
	$(MAKE) src-remove
	$(MAKE) show | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"

uns uninstall: 
	test -d tmp || mkdir -v tmp
	set -x; $(PIP3) uninstall -y `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//'  pyproject.toml`

show:
	@ $(PIP3) show --files `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//' pyproject.toml` \
	| sed -e "s:[^ ]*/[.][.]/\\([a-z][a-z]*\\)/:~/.local/\\1/:"

####### autopep8
AUTOPEP8=autopep8
AUTOPEP8_WITH=
autopep8: ; $${PKG:-zypper} install -y python3-autopep8
%.py.pep8: %.py
	$(AUTOPEP8) $(AUTOPEP8_WITH) ${@:.pep8=} --in-place
	git --no-pager diff ${@:.pep8=}
%.pyi.pep8: %.pyi
	$(AUTOPEP8) $(AUTOPEP8_WITH) ${@:.pep8=} --in-place
	git --no-pager diff ${@:.pep8=}
%.py.style: %.py
	$(AUTOPEP8) $(AUTOPEP8_WITH) ${@:.style=} --diff
%.pyi.style: %.pyi
	$(AUTOPEP8) $(AUTOPEP8_WITH) ${@:.style=} --diff
pep8 style:
	$(MAKE) files/docker/systemctl3.py.pep8
	$(MAKE) testsuite.py.pep8
pep style.d: 
	$(MAKE) files/docker/systemctl3.py.style
	$(MAKE) testsuite.py.style

# https://github.com/nvbn/py-backwards

STRIPHINTS_GIT_URL = https://github.com/abarker/strip-hints.git
STRIPHINTS_GIT = ../striphints
STRIPHINTS = $(STRIPHINTS_GIT)/bin/strip_hints.py
striphints.git:
	set -ex ; if test -d $(STRIPHINTS_GIT); then cd $(STRIPHINTS_GIT) && git pull; else : \
	; cd $(dir $(STRIPHINTS_GIT)) && git clone $(STRIPHINTS_GIT_URL) $(notdir $(STRIPHINTS_GIT)) \
	; fi
	echo "def test(a: str) -> str: return a" > tmp.striphints.py
	$(PYTHON3) $(STRIPHINTS) --to-empty tmp.striphints.py | tee tmp.striphints.py.out
	test "def test(a )  : return a" = "`cat tmp.striphints.py.out`"
	rm tmp.striphints.*

STRIP_PYTHON3_GIT_URL = https://github.com/abarker/strip-hints.git
STRIP_PYTHON3_GIT = ../strip_python3
STRIPHINTS3 = $(STRIP_PYTHON3_GIT)/src/strip_python3.py
striphints3.git:
	set -ex ; if test -d $(STRIP_PYHTON3_GIT); then cd $(STRIP_PYTHON3_GIT) && git pull; else : \
	; cd $(dir $(STRIPHINTS_GIT)) && git clone $(STRIP_PYTHON3_GIT_URL) $(notdir $(STRIP_PYTHON3_GIT)) \
	; fi
	echo "def test(a: str) -> str: return a" > tmp.striphints.py
	$(PYTHON39) $(STRIPHINTS3) tmp.striphints.py -o tmp.striphints.py.out -vv
	cat tmp.striphints.py.out | tr '\\\n' '|' && echo
	test "def test(a):|    return a|" = "`cat tmp.striphints.py.out | tr '\\\\\\n' '|'`"
	rm tmp.striphints.*

tmp/systemctl_2.py: files/docker/systemctl3.py $(STRIPHINTS3)
	@ $(PYTHON39) $(STRIPHINTS3) files/docker/systemctl3.py -o $@ $V

MYPY = mypy
MYPY_WITH = --strict --show-error-codes --show-error-context 
MYPY_OPTIONS = --no-warn-unused-ignores --python-version $(PYTHON_VERSION)
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec
	$(MAKE) striphints.git
type:
	$(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) files/docker/systemctl3.py

####### box test
box:
	docker rm -f $@ ; docker run -d --name $@ --rm=true centos:centos7 sleep 600
	docker cp files/docker/systemctl.py box:/usr/bin/systemctl
	docker exec box systemctl daemon-reload -vvv
	@ echo : docker exec -it box bash
