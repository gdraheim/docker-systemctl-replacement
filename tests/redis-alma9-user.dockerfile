FROM almalinux:9.4

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 6379
ENV SSL --setopt sslverify=false
ENV GPG --nogpgcheck

COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

# RUN yum install $GPG $SSL -y epel-release
RUN yum install $GPG $SSL -y redis
# RUN rpm -q --list redis

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'

RUN systemctl enable redis
CMD /usr/bin/systemctl
USER redis
