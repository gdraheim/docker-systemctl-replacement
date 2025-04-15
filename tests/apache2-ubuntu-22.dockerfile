FROM "ubuntu:22.04"

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 80
ARG PYTHON=python2
ENV PYTHON ${PYTHON}
ARG PYTHON2=python2
ENV PYTHON2 ${PYTHON2}

RUN apt-get update
RUN apt-get install -y apache2 ${PYTHON2}
COPY tmp/systemctl.py /usr/bin/systemctl
RUN sed -i -e "s:/usr/bin/env python.*:/usr/bin/env ${PYTHON}:" /usr/bin/systemctl
RUN test -e /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html

RUN systemctl enable apache2
CMD ["/usr/bin/systemctl"]
