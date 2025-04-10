FROM ubuntu:18.04

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 6379
ARG PASSWORD Redis.Foo.1

RUN apt-get update
RUN apt-get install -y python3 procps
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN apt-cache search redis
RUN apt-get install -y redis-server
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN dpkg-query -L redis-server

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'
RUN sed -i "s/^..requirepass foo.*/requirepass $PASSWORD/" /etc/redis/redis.conf
RUN grep -8 requirepass /etc/redis/redis.conf

RUN touch /var/log/systemctl.debug.log
RUN systemctl enable redis
CMD ["/usr/bin/systemctl"]
# CMD ["/usr/bin/systemctl", "start", "redis"]