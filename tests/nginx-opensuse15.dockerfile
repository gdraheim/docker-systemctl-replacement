FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
ENV GPG="--no-gpg-checks"
EXPOSE 80

RUN echo ========= PYTHON=${PYTHON} PYTHONPKG=${PYTHONPKG}
RUN zypper $GPG install -r repo-oss -y ${PYTHONPKG}
RUN test -s /usr/bin/python3 || ln -sv "${PYTHON}" /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y nginx 
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /srv/www/htdocs/index.html

RUN systemctl enable nginx
CMD ["/usr/bin/systemctl"]
