F= files/docker/systemctl.py
ORIGYEAR=2016
BASEYEAR=2025
FOR=today
# 'make version FOR=yesterday' or 'make version DAY=0'

-include Make_detect_py.mk

UBUNTU=ubuntu:18.04
PYTHON2 = python2
PYTHON3 = python3
PYTHON39 = python$(PY39)
PYTHON_VERSION = 3.9
COVERAGE3 = $(PYTHON3) -m coverage
GIT=git
VERFILES = files/docker/systemctl3.py tests/testsuite.py pyproject.toml
VV=-vv

verfiles:
	@ grep -l __version__ */*.??* */*/*.??* | { while read f; do echo $$f; done; } 

version:
	@ grep -l __version__ $(VERFILES) | { while read f; do : \
	; B="$(BASEYEAR)"; C=$$B; test -z "$(ORIGYEAR)" || C="$(ORIGYEAR)" \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $$B) \
	; W=`date +%W -d "$(FOR)"` \
	; D=`date +%u -d "$(FOR)"` ; sed -i \
	-e "/^ *version = /s/[.]-*[0123456789][0123456789][0123456789]*/.$$X$$W$$D/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$W$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$W$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $$C-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep ^__version__ $(VERFILES)
	@ grep ^version.= $(VERFILES)
	@ $(GIT) add $(VERFILES) || true
	@ ver=`cat files/docker/systemctl3.py | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"

help:
	$(PYTHON3) files/docker/systemctl3.py help

.PHONY: build tests src files notes tmp

DOCKTEST_PY = tests/testsuite.py
DOCKTEST = $(PYTHON3) $(DOCKTEST_PY) $(TESTS_OPTIONS)
BASETEST_PY = tests/basetests.py
BASETEST = $(PYTHON3) $(BASETEST_PY) $(BASETEST_OPTIONS)
BUILD_PY = tests/buildtests.py
BUILD = $(PYTHON3) $(BUILD_PY) -C tests $(BUILD_OPTIONS)

TESTS = $(DOCKTEST)
# python2 is not available on standard Linux distros after 2024 (so these are obsolete make targets)
WITH2 = --python=/usr/bin/python2 --with=tmp/systemctl.py
WITH3 = --python=/usr/bin/python3 --with=files/docker/systemctl3.py
todo/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) --todo
15.6/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.6
15.5/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.5
15.4/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.4
15.2/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.2
15.1/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.1
15.0/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.0
42.3/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse:42.3
42.2/test_%:             ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=opensuse:42.2
24.04/test_%:            ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:24.04
22.04/test_%:            ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:22.04
20.04/test_%:            ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:20.04
19.10/test_%:            ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:19.10
18.04/test_%:            ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:18.04
16.04/test_%:            ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:16.04
9.4/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=almalinux:9.4
9.3/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=almalinux:9.3
9.1/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=almalinux:9.1
8.1/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:8.1.1911
8.0/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:8.0.1905
7.7/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:7.7.1908
7.6/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:7.6.1810
7.5/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:7.5.1804
7.4/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:7.4.1708
7.3/test_%:              ; $(TESTS)   "$(notdir $@)" $(VV) $(FORCE) --image=centos:7.3.1611
15.4/st_%:  ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.4 $(WITH2)
15.2/st_%:  ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.2 $(WITH2)
15.1/st_%:  ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.1 $(WITH2)
15.0/st_%:  ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=opensuse/leap:15.0 $(WITH2)
42.3/st_%:  ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=opensuse:42.3      $(WITH2)
42.2/st_%:  ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=opensuse:42.2      $(WITH2)
22.04/st_%: ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:22.04       $(WITH2)
20.04/st_%: ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:20.04       $(WITH2)
18.04/st_%: ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:18.04       $(WITH2)
16.04/st_%: ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=ubuntu:16.04       $(WITH2)
8.1/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:8.1.1911    $(WITH2)
8.0/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:8.0.1905    $(WITH2)
7.7/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:7.7.1908    $(WITH2)
7.6/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:7.6.1810    $(WITH2)
7.5/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:7.5.1804    $(WITH2)
7.4/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:7.4.1708    $(WITH2)
7.3/st_%:   ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $(FORCE) --image=centos:7.3.1611    $(WITH2)

# testbuilds run with a stripped systemctl.py variant to cover both python2/python3 example (meanwhile testing strip_python3 to work correctly)
builds testbuilds: ; $(MAKE) tmp/systemctl.py tmp/systemctl3.py; $(BUILD) $(VV) $V $E --systemctl=tmp/systemctl.py --systemctl3=tmp/systemctl3.py
build3 testonly3: ; $(BUILD) $(VV) $V $E # defaults to files/docker/systemctl3.py # skipping python2 tests and the stripping tool
local3: ; $(MAKE) builds3 E=--local
t_%: ; $(MAKE) $@/s
t_%/s: ; $(MAKE) tmp/systemctl.py tmp/systemctl3.py; $(BUILD) "tes$(dir $@)" $(VV) $V $E --systemctl=tmp/systemctl.py --systemctl3=tmp/systemctl3.py
t_%/9: ; $(BUILD) "tes$(dir $@)" $(VV) $V $E --python=$(PYTHON39)
t_%/3: ; $(BUILD) "tes$(dir $@)" $(VV) $V $E --python=python$(notdir $@)
t_%/3.6: ; $(BUILD) "tes$(dir $@)" $(VV) $V $E --python=python$(notdir $@)
t_%/3.11: ; $(BUILD) "tes$(dir $@)" $(VV) $V $E --python=python$(notdir $@)
t_%/3.12: ; $(BUILD) "tes$(dir $@)" $(VV) $V $E --python=python$(notdir $@)
# 'make test9' or 'make test_9*' if you want to testbuilds to use the unstripped python3 script (same as 'make build3')

COVERAGE=--coverage
est_%: ; rm .coverage*; rm -rf tmp/tmp.t$(notdir $@) ; $(TESTS) "t$(notdir $@)" $(VV)  $V --coverage --keep
st_%: ; $(MAKE) 2 && $(TESTS) "te$(notdir $@)" $(VV) $V $(WITH2)
test_1%: ; $(BASETEST) "$(notdir $@)" $(VV) $V
test_2%: ; $(BASETEST) "$(notdir $@)" $(VV) $V
test_3%: ; $(BASETEST) "$(notdir $@)" $(VV) $V
test_4%: ; $(BASETEST) "$(notdir $@)" $(VV) $V
test_5%: ; $(BASETEST) "$(notdir $@)" $(VV) $V
test_6%: ; $(TESTS) "$(notdir $@)" $(VV) $V
test_7%: ; $(TESTS) "$(notdir $@)" $(VV) $V
test_8%: ; $(TESTS) "$(notdir $@)" $(VV) $V
test_9%: ; $(BUILD) "$(notdir $@)" $(VV) $V
real_1%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_2%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_3%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_4%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_5%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_6%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_7%: ; $(TESTS) "$(notdir $@)" $(VV) $V
real_8%: ; $(TESTS) "$(notdir $@)" $(VV) $V
t1 test1: ; $(MAKE) test_1*
t2 test2: ; $(MAKE) test_2*
t3 test3: ; $(MAKE) test_3*
t4 test4: ; $(MAKE) test_4*
t9 test9: ; $(MAKE) test_9*

basetestlist = test_[1234]
dockertestlist = test_[567]
dockertestlist2 = st_[567]
base basetests: ; $(MAKE) test_1* test_2* test_3* test_4*
docker dockertests: ; $(MAKE) test_5* test_6* test_7*
15.6/tests:  ; $(MAKE) "15.6/$(dockertestslist)"
15.5/tests:  ; $(MAKE) "15.5/$(dockertestlist)"
15.4/tests:  ; $(MAKE) "15.4/$(dockertestlist)"
15.2/tests:  ; $(MAKE) "15.2/$(dockertestlist)"
15.1/tests:  ; $(MAKE) "15.1/$(dockertestlist)"
15.0/tests:  ; $(MAKE) "15.0/$(dockertestlist)"
42.3/tests:  ; $(MAKE) "42.3/$(dockertestlist)"
42.2/tests:  ; $(MAKE) "42.2/$(dockertestlist)"
22.04/tests: ; $(MAKE) "22.04/$(dockertestlist)"
20.04/tests: ; $(MAKE) "20.04/$(dockertestlist)"
19.10/tests: ; $(MAKE) "19.10/$(dockertestlist)"
18.04/tests: ; $(MAKE) "18.04/$(dockertestlist)"
16.04/tests: ; $(MAKE) "16.04/$(dockertestlist)"
9.4/tests:   ; $(MAKE) "9.4/$(dockertestlist)"
9.3/tests:   ; $(MAKE) "9.3/$(dockertestlist)"
9.1/tests:   ; $(MAKE) "9.1/$(dockertestlist)"
8.5/tests:   ; $(MAKE) "8.5/$(dockertestlist)"
8.1/tests:   ; $(MAKE) "8.1/$(dockertestlist)"
8.0/tests:   ; $(MAKE) "8.0/$(dockertestlist)"
7.9/tests:   ; $(MAKE) "7.9/$(dockertestlist)"
7.7/tests:   ; $(MAKE) "7.7/$(dockertestlist)"
7.6/tests:   ; $(MAKE) "7.6/$(dockertestlist)"
7.5/tests:   ; $(MAKE) "7.5/$(dockertestlist)"
7.4/tests:   ; $(MAKE) "7.4/$(dockertestlist)"
7.3/tests:   ; $(MAKE) "7.3/$(dockertestlist)"
# python2 has been phased out by newer distros
15.2/test2:  ; $(MAKE) "15.2/$(dockertestlist2)"
15.1/test2:  ; $(MAKE) "15.1/$(dockertestlist2)"
15.0/test2:  ; $(MAKE) "15.0/$(dockertestlist2)"
42.3/test2:  ; $(MAKE) "42.3/$(dockertestlist2)"
42.2/test2:  ; $(MAKE) "42.2/$(dockertestlist2)"
22.04/test2: ; $(MAKE) "22.04/$(dockertestlist2)"
20.04/test2: ; $(MAKE) "20.04/$(dockertestlist2)"
18.04/test2: ; $(MAKE) "18.04/$(dockertestlist2)"
16.04/test2: ; $(MAKE) "16.04/$(dockertestlist2)"
8.5/test2:   ; $(MAKE) "8.5/$(dockertestlist2)"
8.1/test2:   ; $(MAKE) "8.1/$(dockertestlist2)"
8.0/test2:   ; $(MAKE) "8.0/$(dockertestlist2)"
7.9/test2:   ; $(MAKE) "7.9/$(dockertestlist2)"
7.7/test2:   ; $(MAKE) "7.7/$(dockertestlist2)"
7.6/test2:   ; $(MAKE) "7.6/$(dockertestlist2)"
7.5/test2:   ; $(MAKE) "7.5/$(dockertestlist2)"
7.4/test2:   ; $(MAKE) "7.4/$(dockertestlist2)"
7.3/test2:   ; $(MAKE) "7.3/$(dockertestlist2)"

check: check2025
	@ echo please run 'make checks' now
25 check2025: ; $(TESTS) $(VV) --opensuse=15.6 --ubuntu=ubuntu:24.04 --centos=almalinux:9.4
24 check2024: ; $(TESTS) $(VV) --opensuse=15.6 --ubuntu=ubuntu:24.04 --centos=almalinux:9.3
23 check2023: ; $(TESTS) $(VV) --opensuse=15.5 --ubuntu=ubuntu:22.04 --centos=almalinux:9.1
22 check2022: ; $(TESTS) $(VV) --opensuse=15.3 --ubuntu=ubuntu:22.04 --centos=almalinux:9.1
19 check2019: ; $(TESTS) $(VV) --opensuse=15.1 --ubuntu=ubuntu:18.04 --centos=centos:7.7
18 check2018: ; $(TESTS) $(VV) --opensuse=15.0 --ubuntu=ubuntu:18.04 --centos=centos:7.5
17 check2017: ; $(TESTS) $(VV) --opensuse=42.3 --ubuntu=ubuntu:16.04 --centos=centos:7.4
16 check2016: ; $(TESTS) $(VV) --opensuse=42.2 --ubuntu=ubuntu:16.04 --centos=centos:7.3

nightrun: checkall
	$(MAKE) checks
checkall: checkall2019
checkall2: checkall2024.2
checkall2024:
	$(MAKE) -j1 tests checkall2023.3 checkall2023.2
checkall2024.3:
	$(MAKE) -j1 9.3/tests   8.5/tests   7.9/tests
	$(MAKE) -j1 24.04/tests 22.04/test2 18.04/tests
	$(MAKE) -j1 15.6/tests  15.5/tests  15.4/tests  15.2/tests
checkall2024.2:
	: $(MAKE) -j1             8.5/test2   7.9/test2
	$(MAKE) -j1             22.04/test2 18.04/test2
	$(MAKE) -j1 15.6/test2  15.5/test2  15.4/test2  15.2/test2
checkall2023:
	$(MAKE) -j1 tests checkall2023.3 checkall2023.2
checkall2023.3:
	$(MAKE) -j1 9.1/tests 8.5/tests 7.9/tests
	$(MAKE) -j1 22.04/test2 20.04/tests 18.04/tests
	$(MAKE) -j1 15.5/tests 15.4/tests 15.2/tests
checkall2023.2:
	$(MAKE) -j1           8.5/test2 7.9/test2
	$(MAKE) -j1 22.04/test2 20.04/test2 18.04/test2
	$(MAKE) -j1 15.5/test2 15.4/test2 15.2/test2
checkall2019:
	$(MAKE) -j1 tests checkall2019.3 checkall2019.2
checkall2019.3:
	$(MAKE) -j1 8.0/tests
	$(MAKE) -j1 18.04/tests 16.04/tests
	$(MAKE) -j1 15.1/tests 15.0/tests 42.3/tests
checkall2019.2:
	$(MAKE) -j1 7.7/test2 7.5/test2 7.4/test2 7.3/test2
	$(MAKE) -j1 18.04/test2 16.04/test2
	$(MAKE) -j1 15.1/test2 15.0/test2 42.3/test2
checkall2018:
	$(MAKE) -j1 tests
	$(MAKE) -j1 7.5/tests 7.4/tests 7.3/tests
	$(MAKE) -j1 18.04/tests 16.04/tests
	$(MAKE) -j1 15.0/tests 42.3/tests
	$(MAKE) -j1 18.04/test2 16.04/test2
	$(MAKE) -j1 15.0/test2 42.3/test2

# with python2 being usually not available the coverage is actually just python3 tests now
COVERAGETESTS = test
COVERSRC=src/systemctl3.py
coverage:
	- rm .coverage*
	$(MAKE) $(COVERSRC)
	touch $(COVERSRC)
	$(BASETEST) $(VV) --coverage $(COVERAGETESTS) --with=$(COVERSRC)
	$(DOCKTEST) $(VV) --coverage $(COVERAGETESTS) --with=$(COVERSRC)
	$(PYTHON3) -m coverage combine && \
	$(PYTHON3) -m coverage report && \
	$(PYTHON3) -m coverage annotate
	- $(PYTHON3) -m coverage xml -o tmp/coverage.xml
	ls -l $(COVERSRC),cover
	@ echo = $$(expr $$(expr $$(stat -c %Y $(COVERSRC),cover) - $$(stat -c %Y $(COVERSRC))) / 60) "mins"
coveragetime mins:
	echo === $$(expr $$(expr $$(stat -c %Y $(COVERSRC),cover) - $$(stat -c %Y $(COVERSRC))) / 60) "mins"
coverage2: ; $(MAKE) coverage COVERAGESRC=tmp/systemctl.py # stripped
coverage3: ; $(MAKE) coverage COVERAGESRC=tmp/systemctl3.py # stripped

# these should show different coverage percentage results
coveragetest1: ; $(MAKE) coverage COVERAGETESTS=test_101*; 
coveragetest2: ; $(MAKE) coverage COVERAGETESTS=test_5002
coveragetest3: ; $(MAKE) coverage COVERAGETESTS=test_101*,test_5002

tmp_ubuntu:
	if docker ps | grep $(UBU); then : ; else : \
	; docker run --name $(UBU) -d $(UBUNTU) sleep 3333 \
	; docker exec $(UBU) apt-get update -y --fix-missing \
	; docker exec $(UBU) apt-get install -y --fix-broken --ignore-missing python3-coverage mypy \
	; fi
	docker cp files $(UBU):/root/
	docker cp tests/testsuite.py $(UBU):/root/ 
	docker cp tests/reply.py $(UBU):/root/ 
UBU=test_ubuntu
ubu/test_%:
	$(MAKE) tmp_ubuntu
	docker exec $(UBU) python3 /root/testsuite.py -C /root $(VV) $(notdir $@)
ubu/st_%:
	$(MAKE) tmp_ubuntu
	docker exec $(UBU) python3 /root/testsuite.py -C /root $(VV) te$(notdir $@)

clean:
	- rm .coverage*
	- rm -rf tmp/tmp.test_*
	- rm -rf tmp/systemctl.py
	- rm -rf tmp.* types/tmp.*
	- rm -rf .mypy_cache files/docker/.mypy_cache
	- rm -rf src
	- rm -rf build

copy:
	cp -v ../docker-mirror-packages-repo/docker_mirror.py tests/
	cp -v ../docker-mirror-packages-repo/docker_mirror.pyi tests/

############## https://pypi.org/...

src/README.md: README.md Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	cat README.md | sed -e "/\\/badge/d" -e /^---/q > $@

src/py.typed: files/docker/py.typed
	test -d $(dir $@) || mkdir -v $(dir $@)
	cp $< $@
src/systemctl3.py: files/docker/systemctl3.py
	test -d $(dir $@) || mkdir -v $(dir $@)
	cp $< $@
src/journalctl3.py: files/docker/journalctl3.py
	test -d $(dir $@) || mkdir -v $(dir $@)
	cp $< $@
src/__main__.py: Makefile
	{ echo '#! /usr/bin/env python3'; echo 'import sys' \
	; echo 'from .systemctl3 import main'; echo 'sys.exit(main())' \
	; } > $@

# package sources - both stripped and unstripped python scripts and a README without github badges
SRC= src/README.md src/systemctl3.py src/journalctl3.py src/py.typed src/systemctl.py src/journalctl.py src/__main__.py
src: src/README.md src/systemctl3.py src/journalctl3.py src/py.typed src/systemctl.py src/journalctl.py src/__main__.py

buildclean bb rm-src:
	- rm -r src/*.egg-info src/__pycache__
	@ for src in $(SRC); do test ! -f $$src || rm -v $$src*; done
distclean dd:
	- rm -rf build dist *.egg-info src/*.egg-info

# packaging needs python3.9+ for strip_python3 to work (should actually be common after 2025)
PIP3 = $(PYTHON3) -m pip
TWINE3 = $(PYTHON3) -m twine

pkg package:  ; $(MAKE) pkg9 PYTHON3=$(PYTHON39)
pkg9 package3:
	$(MAKE) distclean
	$(MAKE) $(SRC)
	# pip install --root=~/local . -v
	$(PYTHON3) -m build
	$(MAKE) buildclean
	$(MAKE) fix-metadata-version
	$(TWINE3) check dist/*
	: $(TWINE3) upload dist/*

ins install: ;	$(MAKE) install3 PYTHON3=$(PYTHON39)
install3:
	$(MAKE) distclean
	$(MAKE) $(SRC)
	$(PIP3) install --no-compile --user .
	$(MAKE) buildclean
	$(MAKE) show3 | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"

uns uninstall: ; $(MAKE) uninstall3 PYTHON3=$(PYTHON39)
uninstall3:
	test -d tmp || mkdir -v tmp
	set -x; $(PIP3) uninstall -y `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//'  pyproject.toml`

show: ;	$(MAKE) show3 PYTHON3=$(PYTHON39)
show3:
	@ $(PIP3) show --files `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//' pyproject.toml` \
	| sed -e "s:[^ ]*/[.][.]/\\([a-z][a-z]*\\)/:~/.local/\\1/:"

tag:
	@ ver=`sed -e '/^version *=/!d' -e 's/version *= *"//' -e 's/".*//' pyproject.toml` \
	; rev=`$(GIT) rev-parse --short HEAD` \
	; if test -f tmp.changes.txt \
        ; then echo ": ${GIT} tag -F tmp.changes.txt v$$ver $$rev" \
	; elif test -f RELEASENOTES.md \
        ; then echo ": ${GIT} tag -F RELEASENOTES.md v$$ver $$rev" \
        ; else echo ": ${GIT} tag v$$ver $$rev"; fi 

fix-metadata-version:
	ls dist/*
	rm -rf dist.tmp; mkdir dist.tmp
	cd dist.tmp; for z in ../dist/*; do case "$$z" in *.whl) unzip $$z ;; *) tar xzvf $$z;; esac \
	; ( find . -name PKG-INFO ; find . -name METADATA ) | while read f; do echo FOUND $$f; sed -i -e "s/Metadata-Version: 2.4/Metadata-Version: 2.2/" $$f; done \
	; case "$$z" in *.whl) zip -r $$z * ;; *) tar czvf $$z *;; esac ; ls -l $$z; done

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
	$(MAKE) files/docker/systemctl3.py.lint
	$(MAKE) tests/testsuite.py.lint
pep8 style:
	$(MAKE) files/docker/systemctl3.py.pep8
	$(MAKE) types/systemctl3.pyi.pep8
	$(MAKE) testsuite.py.pep8
pep style.d: 
	$(MAKE) files/docker/systemctl3.py.style
	$(MAKE) types/systemctl3.pyi.style
	$(MAKE) testsuite.py.style

####### strip-hints
STRIPHINTS_GIT_URL = https://github.com/abarker/strip-hints.git
STRIP_HINTS = ../strip-hints
STRIP_HINTS_PY = $(STRIP_HINTS)/bin/strip_hints.py
striphints.git:
	set -ex ; if test -d $(STRIPHINTS_GIT); then cd $(STRIPHINTS_GIT) && git pull; else : \
	; cd $(dir $(STRIPHINTS_GIT)) && git clone $(STRIPHINTS_GIT_URL) $(notdir $(STRIPHINTS_GIT)) \
	; fi
	echo "def test(a: str) -> str: return a" > tmp.striphints.py
	$(PYTHON) $(STRIPHINTS) --to-empty tmp.striphints.py | tee tmp.striphints.py.out
	test "def test(a )  : return a" = "`cat tmp.striphints.py.out`"
	rm tmp.striphints.*

STRIP_PYTHON3_GIT_URL = https://github.com/gdraheim/strip_python3
STRIP_PYTHON3_GIT = ../strip_python3
STRIP_PYTHON3_PY = $(STRIP_PYTHON3_GIT)/tool/strip_python3.py
ifeq ("$(wildcard $(STRIP_PYTHON3_PY))", "$(STRIP_PYTHON3_PY)")
STRIP_PYTHON3_SRC = $(STRIP_PYTHON3_PY)
STRIP_PYTHON3_RUN = $(STRIP_PYTHON3_PY)
else
STRIP_PYTHON3_SRC =
STRIP_PYTHON3_RUN = -m strip_python3
endif
STRIP_PYTHON3 = $(PYTHON39) $(STRIP_PYTHON3_RUN) $(STRIP_PYTHON3_OPTIONS)
strip_python3.git:
	set -ex ; if test -d $(STRIP_PYTHON3_GIT); then cd $(STRIP_PYTHON3_GIT) && git pull; else : \
	; cd $(dir $(STRIPHINTS_GIT)) && git clone $(STRIP_PYTHON3_GIT_URL) $(notdir $(STRIP_PYTHON3_GIT)) \
	; fi
	echo "def test(a: str) -> str: return a" > tmp.strip_python3.py
	$(PYTHON39) $(STRIP_PYTHON3_PY) tmp.strip_python3.py -o tmp.strip_python3.py.out $(VV)
	cat tmp.strip_python3.py.out | tr '\\\n' '|' && echo
	test "def test(a):|    return a|" = "`cat tmp.strip_python3.py.out | tr '\\\\\\n' '|'`"
	rm tmp.strip_python3.*
strip_python3:
	$(PYTHON39) -m pip install $@

1: src/systemctl.py
src/systemctl.py: files/docker/systemctl3.py $(STRIP_PYTHON3_SRC) Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	@ $(STRIP_PYTHON3) $< -o $@ $V --old-python --make-pyi
	chmod +x $@
src/journalctl.py: files/docker/journalctl3.py $(STRIP_PYTHON3_SRC) Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	@ $(STRIP_PYTHON3) $< -o $@ $V --old-python --make-pyi
	chmod +x $@

strip: tmp/systemctl_2.py
tmp/systemctl_2.py: files/docker/systemctl3.py $(STRIP_PYTHON3_SRC) Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	@ $(STRIP_PYTHON3) $< -o $@ $V --old-python
	chmod +x $@

2: tmp/systemctl.py
tmp/systemctl.py: files/docker/systemctl3.py $(STRIP_PYTHON3_SRC) Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	$(STRIP_PYTHON3) $< -o $@ $V --no-comments --run-python=python2
	chmod +x $@
3: tmp/systemctl3.py
tmp/systemctl3.py: files/docker/systemctl3.py $(STRIP_PYTHON3_SRC) Makefile
	test -d $(dir $@) || mkdir -v $(dir $@)
	@ $(STRIP_PYTHON3) $< -o $@ $V --no-comments --run-python=python3
	chmod +x $@

MYPY = mypy
MYPY_WITH = --strict --show-error-codes --show-error-context 
MYPY_OPTIONS = --no-warn-unused-ignores --python-version $(PYTHON_VERSION)
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec
	cd .. && git clone git@github.com:ambv/retype.git
	cd ../retype && git checkout 17.12.0

type:; $(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) files/docker/systemctl3.py
ttype:; $(MYPY) $(MYPY_WITH) $(MYPY_OPTIONS) testsuite.py

####### box test
box:
	docker rm -f $@ ; docker run -d --name $@ --rm=true centos:centos7 sleep 600
	docker cp files/docker/systemctl.py box:/usr/bin/systemctl
	docker exec box systemctl daemon-reload $(VV)
	@ echo : docker exec -it box bash

-include Makefile.tmp.mk
