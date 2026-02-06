# DEVELOPMENT GUIDELINES

* workplace setup
* makefile targets
* release process

## WORKPLACE SETUP

Development can be done with a pure text editor and a terminal session.

### VSCode setup

Use python and mypy extensions for Visual Studio Code (from Microsoft).

* Control-P: "ext list"
  * look for "Python", "Pylance" (style checker), "Mypy Type Checker" (type checker)
  * optional "Makefile Tools"
* Control-P: "ext install ms-python.mypy-type-checker"
  * this one pulls the latest mypy from the visualstudio marketplace
  * https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker

The make targets are defaulting to tests with python3.6 but the mypy plugin
for vscode requires atleast python3.8. All current Linux distros provide an
additional package with a higher version number, e.g "zypper install python311".
Be sure to also install "python311-mypy" or compile "pip3 install mypy". 
Implant the paths to those tools into the workspace settings = `.vscode/settings.json`

    {
        "mypy-type-checker.reportingScope": "workspace",
        "mypy-type-checker.interpreter": [
                "/usr/bin/python3.11"
        ],
        "mypy-type-checker.path": [
                "mypy-3.11"
        ],
        "mypy-type-checker.args": [
                "--strict",
                "--show-error-codes",
                "--show-error-context",
                "--no-warn-unused-ignores",
                "--ignore-missing-imports",
                "--exclude=build"
        ],
        "python.defaultInterpreterPath": "python3"
    }

The python files at the toplevel are not checked in vscode. 

### Testing setup

Common distro packages are:
* `zypper install python3 python3-pip` # atleast python3.6
* `zypper install python3-wheel python3-twine`
* `zypper install python3-coverage python3-unittest-xml-reporting`
* `zypper install python3-mypy python3-mypy_extensions python3-typing_extensions`
* `zypper install python3-autopep8`

Some tools do not get distro packages, so install them via "pip".
With having multiple python versions on a system, the tool should
be called preferably as a module: `python3 -m pip`.

* `python3 -m pip install pylint`

For ubuntu you can check the latest Github workflows under
* `grep apt-get .github/workflows/*.yml`

### Docker setup

Some tests require a working docker on the system. See the `tests/*.dockerfile`
examples as they install a lot of packages before actually running the application.
In order to speed up the process (and to avoid rate limit at docker.hub) you
should have caching proxy for rpm/deb packages. Or you can use the docker-mirror
setup that the testsuites will automatically pick up.

* (cd .. && git clone https://github.com/gdraheim/docker-mirror-packages-repo.git)

Building the repo images is a seperate step, check the docs of the project.

### Building setup

To `make build` you need strip_python3 in a parallel directory

* (cd .. && git clone https://github.com/gdraheim/strip_python3.git)
* ../strip_python3/strip3/strip_python3.py --version

## Testing targets

### static code checking

* `make type`
* `make lint`
* `make style`

### build targets

* `make install` # locally (`make ins`)
* `make uinstall` # locall (`make uns`)
* `make show` # the files from the local install
* `make build` # to prepare a pypi upload

### testing targets

You can run individual tests or a group of tests with the same prefix
via makefile:

* `make test_100` # runs test_1000 thru test_1009 in tests/testsuite.py

The tests that do not need docker are named `docker local` 

* `make local` # short for `make localtests`.

It gets more interesting with docker installed - the `testsuite.py` has
some target running a local docker container, and there are dockerfile
examples in tests that are run by `testbuilds.py`.

* `make checks`
* `make builds`

## Release Process

* `make type`
* `make lint`
* `make style`
* `make install` # locally (`make ins`)
* `make uninstall` # locally (`make uns`)
* `make checks`
* `make builds`
* `make coverage`
  * update `README.md` with the result percentage
* edit `RELEASENOTES.md`
* `make version` # implant a version representing the day of release
* `git push` # and check for the workflow results on github
* `make ins` 
* `make uns` 
* `make build`
* `make tag`
   * `git tag -F RELEASENOTES.md v1.x` # with the shown tag
* `git push --tags` # to get the new "version" visible
* `make build`
   * followed by show twine command to push to pypi.org
* update the short description on github
