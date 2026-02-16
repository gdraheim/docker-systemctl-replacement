FROM ubuntu:18.04

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.1067"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
EXPOSE 6379

RUN echo ==== PYTHONPKG=${PYTHONPKG}
RUN apt-get update && apt-get install -y ${PYTHONPKG} procps
RUN test -s /usr/bin/python3 || ln -sv ${PYTHON} /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN apt-cache search redis
RUN apt-get install -y redis-server
COPY tmp/systemctl3.py /usr/bin/systemctl

# RUN dpkg-query -L redis-server
RUN chown redis /var/log # FIXME /var/log/journal(/redis.service.log)

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'

RUN touch /var/log/systemctl.debug.log
RUN systemctl enable redis
CMD ["/usr/bin/systemctl"]
USER redis
