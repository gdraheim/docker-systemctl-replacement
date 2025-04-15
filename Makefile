F= systemctl2/systemctl3.py
ORIGYEAR=2016
BASEYEAR=2024
FOR=today
DAY=%u
# 'make version FOR=yesterday' or 'make version DAY=0'


_36=3
_39=3
ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.9")
  _39=3.9
endif
ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.10")
  _39=3.10
endif
ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.11")
  _36=3.11
  _39=3.11
endif
ifeq ("$(wildcard /usr/bin/python3.10)","/usr/bin/python3.10")
  _36=3.10
endif
ifeq ("$(wildcard /usr/bin/python3.9)","/usr/bin/python3.9")
  _36=3.9
endif
ifeq ("$(wildcard /usr/bin/python3.8)","/usr/bin/python3.8")
  _36=3.8
endif
ifeq ("$(wildcard /usr/bin/python3.7)","/usr/bin/python3.7")
  _36=3.7
endif
ifeq ("$(wildcard /usr/bin/python3.6)","/usr/bin/python3.6")
  _36=3.6
endif

PYTHON=python$(_36)
PYTHON39 = python$(_39)
PYTHON_VERSION = 3.7
COVERAGE = $(PYTHON) -m coverage
TWINE = twine-$(_36)
TWINE39 = twine-$(_39)
GIT=git
VERFILES = systemctl2/systemctl3.py tests/*tests*.py pyproject.toml
CONTAINER = docker-systemctl
LOCALMIRRORS=/dock
UBUNTU=ubuntu:24.04
DOCKER=docker

LOCAL_PY = tests/localtests2.py
LOCAL = $(PYTHON) $(LOCAL_PY) $(LOCAL_OPTIONS)
TESTS_PY = tests/dockertests3.py
TESTS = $(PYTHON) $(TESTS_PY) $(TESTS_OPTIONS)
BUILD_PY = tests/buildtests4.py
BUILD = $(PYTHON) $(BUILD_PY) -C tests $(BUILD_OPTIONS)

echo:
	echo PYTHON=$(PYTHON)

verfiles:
	@ grep -l __version__ */*.??* */*/*.??* | { while read f; do echo $$f; done; } 

# make version FOR=yesterday # "FOR=2 days ago" # FOR=tomorrow # "FOR=2 days"
version:
	@ grep -l __version__ $(VERFILES) | { while read f; do : \
	; B="$(BASEYEAR)"; C=$$B; test -z "$(ORIGYEAR)" || C="$(ORIGYEAR)" \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $$B) \
	; D=`date +%W$(DAY) -d "$(FOR)"` ; sed -i \
	-e "/^ *version = /s/[.]-*[0123456789][0123456789][0123456789]*/.$$X$$D/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $$C-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep ^__version__ $(VERFILES)
	@ grep ^version.= $(VERFILES)
	@ $(GIT) add $(VERFILES) || true
	@ ver=`cat systemctl2/systemctl3.py | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"

help:
	python systemctl2/systemctl3.py help

alltests: CH CP UA DJ

CH centos-httpd.dockerfile: ; $(TESTS) test_36001
CP centos-postgres.dockerfile: ; $(TESTS) test_36002
UA ubuntu-apache2.dockerfile: ; $(TESTS) test_36005
DJ docker-jenkins: ; $(TESTS) test_3900*

VV=-vv
COVERAGE=--coverage
est_2%: ; rm .coverage*; rm -rf tmp/tmp.t$(notdir $@) ; $(TESTS) "t$(notdir $@)" $(VV) $V --coverage --keep
test_2%: ; $(LOCAL) "$(notdir $@)" $(VV) $V
real_2%: ; $(LOCAL) "$(notdir $@)" $(VV) $V
est_3%: ; rm .coverage*; rm -rf tmp/tmp.t$(notdir $@) ; $(TESTS) "t$(notdir $@)" $(VV) $V --coverage --keep
test_3%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_3%: ; $(TESTS) "$(notdir $@)" $(VV) $V

test: ; $(MAKE) type && $(MAKE) tests && $(MAKE) coverage

BASE312 = opensuse/leap:15.6
BASE311 = opensuse/leap:15.6

WITH3 = --python=/usr/bin/python3 --with=systemctl2/systemctl3.py
test_3%/todo:             ; $(TESTS)   "$(dir $@)" $(VV) --todo
test_3%/s:                ; $(TESTS)   "$(dir $@)" $(VV)
test_3%/3.12:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
test_3%/3.11:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
test_3%/15.6:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
test_3%/15.4:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
test_3%/15.3:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
test_3%/15.2:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
test_3%/15.1:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
test_3%/15.0:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
test_3%/42.3:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse:$(notdir $@)
test_3%/42.2:             ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=opensuse:$(notdir $@)
test_3%/24.04:            ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
test_3%/22.04:            ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
test_3%/20.04:            ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
test_3%/19.10:            ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
test_3%/19.04:            ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
test_3%/16.04:            ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
test_3%/9.4:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=almalinux:$(notdir $@)
test_3%/9.3:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=almalinux:$(notdir $@)
test_3%/9.1:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=almalinux:$(notdir $@)
test_3%/8.1:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:8.1.1911
test_3%/8.0:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:8.0.1905
test_3%/7.7:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:7.7.1908
test_3%/7.6:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:7.6.1810
test_3%/7.5:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:7.5.1804
test_3%/7.4:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:7.4.1708
test_3%/7.3:              ; $(TESTS)   "$(dir $@)" $(VV) $(FORCE) --image=centos:7.3.1611

tests/todo:             ; $(TESTS)    $(VV) --todo
tests/3.12:             ; $(TESTS)    $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
tests/3.11:             ; $(TESTS)    $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
tests/15.6:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
tests/15.4:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
tests/15.3:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
tests/15.2:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
tests/15.1:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
tests/15.0:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse/leap:$(notdir $@)
tests/42.3:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse:$(notdir $@)
tests/42.2:             ; $(TESTS)    $(VV) $(FORCE) --image=opensuse:$(notdir $@)
tests/24.04:            ; $(TESTS)    $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
tests/22.04:            ; $(TESTS)    $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
tests/20.04:            ; $(TESTS)    $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
tests/19.10:            ; $(TESTS)    $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
tests/19.04:            ; $(TESTS)    $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
tests/16.04:            ; $(TESTS)    $(VV) $(FORCE) --image=ubuntu:$(notdir $@)
tests/9.4:              ; $(TESTS)    $(VV) $(FORCE) --image=almalinux:$(notdir $@)
tests/9.3:              ; $(TESTS)    $(VV) $(FORCE) --image=almalinux:$(notdir $@)
tests/9.1:              ; $(TESTS)    $(VV) $(FORCE) --image=almalinux:$(notdir $@)
tests/8.1:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:8.1.1911
tests/8.0:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:8.0.1905
tests/7.7:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:7.7.1908
tests/7.6:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:7.6.1810
tests/7.5:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:7.5.1804
tests/7.4:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:7.4.1708
tests/7.3:              ; $(TESTS)    $(VV) $(FORCE) --image=centos:7.3.1611
tests: ; $(LOCAL) $(VV) $V
.PHONY: tests

test_4%/s: ; $(BUILD) "$(dir $@)" $(VV) $V 
test_4%/2: ; $(BUILD) "$(dir $@)" $(VV) $V --python=python$(notdir $@)
test_4%/3: ; $(BUILD) "$(dir $@)" $(VV) $V --python=python$(notdir $@)
test_4%/3.6: ; $(BUILD) "$(dir $@)" $(VV) $V --python=python$(notdir $@)
test_4%/3.11: ; $(BUILD) "$(dir $@)" $(VV) $V --python=python$(notdir $@)
test_4%/3.12: ; $(BUILD) "$(dir $@)" $(VV) $V --python=python$(notdir $@)

test_5%/s:  ; tests/setuptests5.py "$(dir $@)" $(VV) $(FORCE)
test_5%/2:  ; tests/setuptests5.py "$(dir $@)" $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
test_5%/3:  ; tests/setuptests5.py "$(dir $@)" $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
test_5%/3.12:  ; tests/setuptests5.py "$(dir $@)" $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)
test_5%/3.11:  ; tests/setuptests5.py "$(dir $@)" $(VV) $(FORCE) --image=$(BASE$(subst .,,$(notdir $@))) --python=python$(notdir $@)

check5: ; $(MAKE) test_5*/s
check52: ; $(MAKE) test_5*/2
check53: ; $(MAKE) test_5*/3
check5311: ; $(MAKE) test_5*/3.11
check5312: ; $(MAKE) test_5*/3.12
checks5: ; $(MAKE) check5 && $(MAKE) check5311 && $(MAKE) check5312

check4: ; $(MAKE) test_4*/s
check42: ; $(MAKE) test_4*/2
check43: ; $(MAKE) test_4*/3
check4311: ; $(MAKE) test_4*/3.11
check4312: ; $(MAKE) test_4*/3.12
checks4: ; $(MAKE) check4 && $(MAKE) check42 && $(MAKE) check43 && $(MAKE) check4311 && $(MAKE) check4312

nightrun: checkall
	$(MAKE) checks
checkall: checkall2025
checkall2025:
	$(MAKE) -j1 tests/9.4
	$(MAKE) -j1 tests/24.04 tests/22.04 tests/20.04
	$(MAKE) -j1 tests/15.6  tests/15.4
checks3:
	$(MAKE) -j1 tests/9.4
	$(MAKE) -j1 tests/24.04
	$(MAKE) -j1 tests/15.6

checks: ; $(MAKE) checks2 checks3 checks4 checks5
	@ echo please run 'make checkall' now
check: ; $(MAKE) check2 check3 check4 check5
	@ echo please run 'make checks' now
check3:
	@ if test -d $(LOCALMIRRORS); \
	then $(MAKE) check2025 "OPTIONS=--failfast --localmirrors" ; \
	else $(MAKE) check2025 "OPTIONS=--failfast" ; fi
24 check2024: ; $(TESTS) -vv --opensuse=15.6 --ubuntu=ubuntu:24.04 --centos=almalinux:9.3 --docker=$(DOCKER) $(OPTIONS)
25 check2025: ; $(TESTS) -vv --opensuse=15.6 --ubuntu=ubuntu:24.04 --centos=almalinux:9.4 --docker=$(DOCKER) $(OPTIONS)

test_2%/2: ; $(MAKE) $(dir $@)27
test_2%/3: ; $(MAKE) $(dir $@)36
test_2%/3.11: ; $(MAKE) $(dir $@)311

# native operating system does not have python2 anymore
test%/27:
	$(MAKE) tmp_systemctl_py_2
	test -z `$(DOCKER) ps -a -q -f name=$(CONTAINER)-python$(notdir $@)` || $(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p $(PWD)/tmp
	$(DOCKER) cp tests $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp tmp/systemctl.py $(CONTAINER)-python$(notdir $@):/$(PWD)/tmp/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /$(PWD)/tmp/systemctl.py
	[[ "$@" != test_1* ]] || : ignored "$@"
	[[ "$@" != test_2* ]] || $(DOCKER) exec $(CONTAINER)-python$(notdir $@) /$(LOCAL_PY) $(LOCAL_OPTIONS) -vv $(dir $@) \
	  '--with=/$(PWD)/tmp/systemctl.py' --python=/usr/bin/python2 $(COVERAGE1) $V
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/36:
	$(MAKE) tmp_systemctl_py_3
	test -z `docker ps -a -q -f name=$(CONTAINER)-python$(notdir $@)` || $(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p $(PWD)/tmp
	$(DOCKER) cp tests $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp tmp/systemctl.py $(CONTAINER)-python$(notdir $@):/$(PWD)/tmp/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /$(PWD)/tmp/systemctl.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) /$(LOCAL_PY) $(LOCAL_OPTIONS) -vv $(dir $@) \
	  '--with=/$(PWD)/tmp/systemctl.py' --python=/usr/bin/python3 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir):/.coverage .coverage.cov1
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
test%/311:
	$(MAKE) tmp_systemctl_py_3
	test -z `docker ps -a -q -f name=$(CONTAINER)-python$(notdir $@)` || $(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)
	$(DOCKER) run -d --name=$(CONTAINER)-python$(notdir $@) $(CONTAINER)/test$(notdir $@) sleep 9999
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) mkdir -p $(PWD)/tmp
	$(DOCKER) cp tests $(CONTAINER)-python$(notdir $@):/
	$(DOCKER) cp tmp/systemctl.py $(CONTAINER)-python$(notdir $@):/$(PWD)/tmp/
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) chmod +x /$(PWD)/tmp/systemctl.py
	$(DOCKER) exec $(CONTAINER)-python$(notdir $@) /$(LOCAL_PY) $(LOCAL_OPTIONS) -vv $(dir $@) \
	  '--with=/$(PWD)/tmp/systemctl.py' --python=/usr/bin/python3 $(COVERAGE1) $V
	- test -z "$(COVERAGE1)" || $(DOCKER) cp $(CONTAINER)-python$(notdir):/.coverage .coverage.cov1
	$(DOCKER) rm -f $(CONTAINER)-python$(notdir $@)

checks2: check2 check27 check36 coverage
	: ready for make checkall

# using local python3 at whatever version it just has
check2: ; $(LOCAL) -vv

# new-style .... run local tests in a container for python2
check27: ; $(MAKE) "test_2/27" 
check36: ; $(MAKE) "test_2/36" 
check311: ; $(MAKE) "test_2/311" 

# old-style .... we do not have python2 on the local system
check_2:
	$(MAKE) tmp_systemctl_py_2
	$(LOCAL) -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python2
check_3:
	$(MAKE) tmp_systemctl_py_3
	$(LOCAL) -vv \
	  '--with=tmp/systemctl.py' --python=/usr/bin/python3

coverage0: ; rm .coverage* ; $(MAKE) tmp_systemctl_py_3
coverage2: coverage0 ; $(LOCAL) -vv --coverage --python=$(PYTHON) --with=tmp/systemctl.py
coverage3: coverage0 ; $(TESTS) -vv --coverage --python=$(PYTHON) --with=tmp/systemctl.py
coverage: ; $(MAKE) -j1 _coverage
_coverage: coverage0 coverage2 coverage3 coverages
coverages:
	$(PYTHON) -m coverage combine && \
	$(PYTHON) -m coverage report && \
	$(PYTHON) -m coverage annotate
	- $(PYTHON) -m coverage xml -o tmp/coverage.xml
	- $(PYTHON) -m coverage html -d tmp/htmlcov
	ls -l tmp/systemctl.py,cover

p2: tmp_systemctl_py_2
p3: tmp_systemctl_py_3


tmp_systemctl_py_2:
	@ test -d tmp || mkdir tmp
	@ $(MAKE) tmp/systemctl_2.py
	@ cp tmp/systemctl_2.py tmp/systemctl.py
	@ sed -i -e "s:/usr/bin/python3:/usr/bin/python2:" -e "s:/env python3:/env python2:" tmp/systemctl.py
tmp_systemctl_py_3:
	@ test -d tmp || mkdir tmp
	@ cp systemctl2/systemctl3.py tmp/systemctl.py
tmp_ubuntu:
	if $(DOCKER) ps | grep $(UBU); then : ; else : \
	; $(DOCKER) run --name $(UBU) -d $(UBUNTU) sleep 3333 \
	; $(DOCKER) exec $(UBU) apt-get update -y --fix-missing \
	; $(DOCKER) exec $(UBU) apt-get install -y --fix-broken --ignore-missing python3-coverage mypy \
	; fi
	$(DOCKER) cp files $(UBU):/root/
	$(DOCKER) cp testsuite.py $(UBU):/root/ 
	$(DOCKER) cp reply.py $(UBU):/root/ 
UBU=test_ubuntu
test_%/ubu:
	$(MAKE) tmp_ubuntu
	$(DOCKER) exec $(UBU) python3 /root/$(LOCAL_PY) $(LOCAL_OPTIONS) -C /root -vv $(notdir $@)

clean:
	- rm .coverage*
	- rm -rf tmp/tmp.test_*
	- rm -rf tmp/systemctl.py
	- rm -rf tmp.* types/tmp.*
	- rm -rf .mypy_cache systemctl2/.mypy_cache

copy:
	cp -v ../docker-mirror-packages-repo/docker_mirror.py tests/
	cp -v ../docker-mirror-packages-repo/docker_mirror.pyi tests/
	cp -v ../docker-mirror-packages-repo/docker_image.py tests/
	@ grep __version__ tests/docker_mirror.py | sed -e "s|__version__|: git commit -m 'docker_mirror|" -e "s|\$$|' tests/docker*.py*|"

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

python27: $(CONTAINER)/test27
python36: $(CONTAINER)/test36
python39: $(CONTAINER)/test39
python310: $(CONTAINER)/test310
python311: $(CONTAINER)/test311
python312: $(CONTAINER)/test312

$(CONTAINER)/test27u: ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc python2" TEST "python2 --version"
$(CONTAINER)/test36u: ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM ubuntu:18.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
$(CONTAINER)/test310u: ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM ubuntu:22.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"
$(CONTAINER)/test312u: ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM ubuntu:24.04 INTO $@ INSTALL "python3 psmisc" TEST "python3 --version"

$(CONTAINER)/test27:  ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM opensuse/leap:15.6 INTO $@ INSTALL "python3 procps psmisc python2" TEST "python2 --version"
$(CONTAINER)/test36:  ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM opensuse/leap:15.6 INTO $@ INSTALL "python3 procps psmisc" TEST "python3 --version"
$(CONTAINER)/test39:  ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM opensuse/leap:15.5 INTO $@ INSTALL "python39 procps psmisc" SYMLINK /usr/bin/python3.9:python3 TEST "python3 --version" -vv
$(CONTAINER)/test311: ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM opensuse/leap:15.6 INTO $@ INSTALL "python311 python311-pip procps psmisc" SYMLINK /usr/bin/python3.11:python3 TEST "python3 --version"
$(CONTAINER)/test312: ; tests/docker_image.py --docker=$(DOCKER) $(OPTIONS) FROM opensuse/leap:15.6 INTO $@ INSTALL "python312 python312-pip procps psmisc" SYMLINK /usr/bin/python3.12:python3 TEST "python3 --version"


python: 
	@ if test -d $(LOCALMIRRORS); \
	then $(MAKE) $(CONTAINER)/test27 $(CONTAINER)/test36 OPTIONS=--localmirrors ; \
	else $(MAKE) $(CONTAINER)/test27 $(CONTAINER)/test36; fi

####### autopep8
AUTOPEP8=autopep8
AUTOPEP8_WITH=
PYLINT = pylint
PYLINT_OPTIONS =

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
%.py.lint:
	$(PYLINT) $(PYLINT_OPTIONS) $(@:.lint=)
lint:
	$(MAKE) systemctl2/systemctl3.py.lint
	$(MAKE) tests/localtests2.py.lint
	$(MAKE) tests/dockertests3.py.lint
	$(MAKE) tests/buildtests4.py.lint
	$(MAKE) tests/setuptests5.py.lint

pep8 style:
	$(MAKE) systemctl2/systemctl3.py.pep8
	$(MAKE) tests/localtests2.py.pep8
pep style.d: 
	$(MAKE) systemctl2/systemctl3.py.style
	$(MAKE) tests/localtests2.py.style

# https://github.com/nvbn/py-backwards

STRIPHINTS_GIT_URL = https://github.com/abarker/strip-hints.git
STRIPHINTS_GIT = ../striphints
STRIPHINTS = $(STRIPHINTS_GIT)/bin/strip_hints.py
striphints.git:
	set -ex ; if test -d $(STRIPHINTS_GIT); then cd $(STRIPHINTS_GIT) && git pull; else : \
	; cd $(dir $(STRIPHINTS_GIT)) && git clone $(STRIPHINTS_GIT_URL) $(notdir $(STRIPHINTS_GIT)) \
	; fi
	echo "def test(a: str) -> str: return a" > tmp.striphints.py
	$(PYTHON) $(STRIPHINTS) --to-empty tmp.striphints.py | tee tmp.striphints.py.out
	test "def test(a )  : return a" = "`cat tmp.striphints.py.out`"
	rm tmp.striphints.*

STRIP_PYTHON3_GIT_URL = https://github.com/abarker/strip-hints.git
STRIP_PYTHON3_GIT = ../strip_python3
STRIP_PYTHON3 = $(STRIP_PYTHON3_GIT)/strip3/strip_python3.py
STRIPHINTS3 = $(PYTHON39) $(STRIP_PYTHON3) $(STRIP_PYTHON3_OPTIONS)
striphints3.git:
	set -ex ; if test -d $(STRIP_PYTHON3_GIT); then cd $(STRIP_PYTHON3_GIT) && git pull; else : \
	; cd $(dir $(STRIPHINTS_GIT)) && git clone $(STRIP_PYTHON3_GIT_URL) $(notdir $(STRIP_PYTHON3_GIT)) \
	; fi
	echo "def test(a: str) -> str: return a" > tmp.striphints.py
	$(STRIPHINTS3) tmp.striphints.py -o tmp.striphints.py.out -vv
	cat tmp.striphints.py.out | tr '\\\n' '|' && echo
	test "def test(a):|    return a|" = "`cat tmp.striphints.py.out | tr '\\\\\\n' '|'`"
	rm tmp.striphints.*

tmp/systemctl_2.py: systemctl2/systemctl3.py $(STRIP_PYTHON3)
	@ $(STRIPHINTS3) systemctl2/systemctl3.py -o $@ $V

MYPY = mypy
MYPY_WITH = --strict --show-error-codes --show-error-context 
MYPY_OPTIONS = --no-warn-unused-ignores --python-version $(PYTHON_VERSION)
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec
	$(MAKE) striphints.git
type:
	$(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) systemctl2/systemctl3.py

############## https://pypi.org/...
si: setuptools/15.6
setuptools/15.6:
	zypper install -y rpm-build
	zypper source-install -y python-setuptools==67.7.2 python-setuptools-wheel==67.7.2
	cd /usr/src/packages && rpmbuild -ba SPECS/python-setuptools.spec
	cd /usr/src/packages && rpm -ivh RPMS/x86_64/python-setuptools*.rpm
# on opensuse15 we see that python3.6 and python3.9 have setuptools at 44.2.1 which is not
# good enough for pyproject.toml projects without any setup.py. python3.11 and python3.12
# however are using setuptools 67.7.2 and 68.1.2 which is >= 61.0 being required. The
# source-install rpm-build fails however as setuptools-67 require python-base >= 3.7. That
# makes systemctl3 > 2.x to be usable with python3.6 but it can not be installed via pip.
# Henceforth the "make build" diverts to a PYTHON39=python3.11 setup on opensuse15 systems.

2: share/README.md systemctl2/systemctl.py
systemctl2/systemctl.py: systemctl2/systemctl3.py $(STRIP_PYTHON3) Makefile
	: STRIPHINTS3 implies the usage of "PYTHON39=$(PYTHON39)"
	$(STRIPHINTS3) "$<" --old-python -y -o "$@"
share/README.md: README.md Makefile
	- test -d $(dir $@) || mkdir -v $(dir $@)
	cat "$<" | sed -e "/\\/badge/d" -e /^---/q > "$@"
buildclean bb:
	ls systemctl2/
	- rm -r systemctl2/*.egg-info src/__pycache__
	@ test ! -f share/README.md || rm -v share/README.md
	@ test ! -f systemctl2/systemctl.py || rm -v systemctl2/systemctl.py* 
	ls systemctl2/
distclean dd:
	- rm -rf build dist *.egg-info src/*.egg-info

fix-metadata-version:
	ls dist/*
	rm -rf dist.tmp; mkdir dist.tmp
	cd dist.tmp; for z in ../dist/*; do case "$$z" in *.whl) unzip $$z ;; *) tar xzvf $$z;; esac \
	; ( find . -name PKG-INFO ; find . -name METADATA ) | while read f; do echo FOUND $$f; sed -i -e "s/Metadata-Version: 2.4/Metadata-Version: 2.2/" $$f; done \
	; case "$$z" in *.whl) zip -r $$z * ;; *) tar czvf $$z *;; esac ; ls -l $$z; done

PIP3 = $(PYTHON) -m pip

.PHONY: build
build:  ; $(MAKE) build3 PYTHON=$(PYTHON39) TWINE=$(TWINE39)
build3:
	$(MAKE) distclean
	$(MAKE) share/README.md && $(MAKE) systemctl2/systemctl.py
	# pip install --root=~/local . -v
	$(PYTHON) -m build
	$(MAKE) buildclean
	$(MAKE) fix-metadata-version
	$(TWINE) check dist/*
	: $(TWINE) upload dist/*

ins install: ;	$(MAKE) install3 PYTHON=$(PYTHON39)
install3:
	$(MAKE) distclean
	$(MAKE) share/README.md && $(MAKE) systemctl2/systemctl.py
	$(PIP3) install --no-compile --user .
	$(MAKE) buildclean
	$(MAKE) show3 | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"

uns uninstall: ; $(MAKE) uninstall3 PYTHON=$(PYTHON39)
uninstall3:
	test -d tmp || mkdir -v tmp
	set -x; $(PIP3) uninstall -y `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//'  pyproject.toml`

show: ;	$(MAKE) show3 PYTHON=$(PYTHON39)
show3:
	@ $(PIP3) show --files `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//' pyproject.toml` \
	| sed -e "s:[^ ]*/[.][.]/\\([a-z][a-z]*\\)/:~/.local/\\1/:"


####### box test
box:
	docker rm -f $@ ; docker run -d --name $@ --rm=true centos:centos7 sleep 600
	docker cp src/systemctl.py box:/usr/bin/systemctl
	docker exec box systemctl daemon-reload -vvv
	@ echo : docker exec -it box bash
