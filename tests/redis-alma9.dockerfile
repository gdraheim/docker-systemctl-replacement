FROM almalinux:9.4

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.1067"


ARG PYTHON_EXE=/usr/libexec/platform-python
ENV PYTHON_EXE="${PYTHON_EXE}"
ENV SSL="--setopt sslverify=false"
ENV GPG="--nogpgcheck"
EXPOSE 6379

COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

# RUN yum install $GPG $SSL -y epel-release
RUN yum install $GPG $SSL -y redis
# RUN rpm -q --list redis

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'

RUN touch /var/log/systemctl.debug.log
RUN systemctl enable redis
CMD ["/usr/bin/systemctl"]
