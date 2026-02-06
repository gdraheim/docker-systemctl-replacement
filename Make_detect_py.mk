PY36=3 # the minimal version equal or larger than python3.6
PY39=3 # the maximum version equal or larger than python3.9

ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.9")
  PY39=3.9
endif
ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.10")
  PY39=3.10
endif
ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.11")
  PY36=3.11
  PY39=3.11
endif
ifeq ("$(wildcard /usr/bin/python3.10)","/usr/bin/python3.10")
  PY36=3.10
endif
ifeq ("$(wildcard /usr/bin/python3.9)","/usr/bin/python3.9")
  PY36=3.9
endif
ifeq ("$(wildcard /usr/bin/python3.8)","/usr/bin/python3.8")
  PY36=3.8
endif
ifeq ("$(wildcard /usr/bin/python3.7)","/usr/bin/python3.7")
  PY36=3.7
endif
ifeq ("$(wildcard /usr/bin/python3.6)","/usr/bin/python3.6")
  PY36=3.6
endif

############## https://pypi.org/...
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
# The series above tries to find such a python3.11 - with fallbacks if not found
