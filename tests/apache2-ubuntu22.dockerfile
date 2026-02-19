FROM ubuntu:22.04
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1074"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
EXPOSE 80

RUN echo ==== PYTHONPKG=${PYTHONPKG}
RUN apt-get update && apt-get install -y apache2 ${PYTHONPKG}
RUN test -s /usr/bin/python3 || ln -sv ${PYTHON} /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN test -e /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html

RUN systemctl enable apache2
CMD ["/usr/bin/systemctl"]
