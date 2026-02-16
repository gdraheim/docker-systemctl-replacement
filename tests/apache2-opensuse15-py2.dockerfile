FROM opensuse/leap:15.6
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1067"

ARG PYTHON=python
ARG PYTHONPKG=python2
ARG FRESH=--no-refresh
ENV GPG="--no-gpg-checks"
EXPOSE 80

RUN echo ========= PYTHON=${PYTHON} PYTHONPKG=${PYTHONPKG}
RUN [ -z "$FRESH" ] || zypper $GPG refresh repo-oss
RUN zypper $GPG $FRESH install -y ${PYTHONPKG}

COPY tmp/systemctl.py /usr/bin/systemctl.py
RUN sed -i -e "s:/usr/bin/env python.*:/usr/bin/env ${PYTHON}:" /usr/bin/systemctl.py
RUN head -1 /usr/bin/systemctl.py
RUN cp /usr/bin/systemctl.py /usr/bin/systemctl
RUN zypper $GPG $FRESH install -r repo-oss -y apache2 apache2-utils
RUN cp /usr/bin/systemctl.py /usr/bin/systemctl

RUN echo TEST_OK > /srv/www/htdocs/index.html

RUN systemctl enable apache2
CMD ["/usr/bin/systemctl"]
