FROM ubuntu:24.04
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1074"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
ARG USERPASS Redis.Foo.1
EXPOSE 6379


RUN echo ==== PYTHONPKG=${PYTHONPKG}
RUN apt-get update && apt-get install -y ${PYTHONPKG} procps
RUN test -s /usr/bin/python3 || ln -sv ${PYTHON} /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN apt-cache search redis
RUN apt-get install -y redis-server
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN dpkg-query -L redis-server

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'
RUN sed -i "s/^..requirepass foo.*/requirepass $USERPASS/" /etc/redis/redis.conf
RUN grep -8 requirepass /etc/redis/redis.conf

RUN touch /var/log/systemctl.debug.log
RUN systemctl enable redis-server
CMD ["/usr/bin/systemctl"]
