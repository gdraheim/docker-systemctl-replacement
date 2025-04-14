FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 80
ARG PYTHON=python3
ENV PYTHON ${PYTHON}
ARG PYTHON3=python3
ENV PYTHON3 ${PYTHON3}
ENV GPG --no-gpg-checks

RUN zypper $GPG install -r repo-oss -y ${PYTHON3}
COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s:/usr/bin/env python.*:/usr/bin/env ${PYTHON}:" /usr/bin/systemctl3.py
RUN head -1 /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y apache2 apache2-utils
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /srv/www/htdocs/index.html

RUN systemctl enable apache2
CMD /usr/bin/systemctl
