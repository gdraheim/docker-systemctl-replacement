FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 80
ARG PYTHON=python
ENV PYTHON ${PYTHON}
ARG PYTHON2=python2
ENV PYTHON2 ${PYTHON2}
ENV GPG --no-gpg-checks

RUN echo PYTHON=${PYTHON} PYTHON2=${PYTHON2}
RUN zypper $GPG install -y ${PYTHON2}
COPY tmp/systemctl.py /usr/bin/systemctl.py
RUN sed -i -e "s:/usr/bin/env python.*:/usr/bin/env ${PYTHON}:" /usr/bin/systemctl.py
RUN head -1 /usr/bin/systemctl.py
RUN cp /usr/bin/systemctl.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y apache2 apache2-utils
RUN cp /usr/bin/systemctl.py /usr/bin/systemctl

RUN echo TEST_OK > /srv/www/htdocs/index.html

RUN systemctl enable apache2
CMD /usr/bin/systemctl
