FROM "ubuntu:16.04"
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1074"

ARG PYTHON=python2
ARG PYTHONPKG=python
EXPOSE 80

RUN apt-get update && apt-get install -y apache2 ${PYTHONPKG}
COPY tmp/systemctl.py /usr/bin/systemctl
RUN sed -i -e "s:/usr/bin/env python.*:/usr/bin/env ${PYTHON}:" /usr/bin/systemctl
RUN test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html

RUN systemctl enable apache2
CMD ["/usr/bin/systemctl"]
