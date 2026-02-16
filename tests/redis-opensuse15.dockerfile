FROM opensuse/leap:15.6
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1067"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
ARG USERPASS P@assw0rd.Redis.1
ENV GPG="--no-gpg-checks"
EXPOSE 6379

RUN echo ========= PYTHON=${PYTHON} PYTHONPKG=${PYTHONPKG}
RUN zypper $GPG install -r repo-oss -y ${PYTHONPKG} procps
RUN test -s /usr/bin/python3 || ln -sv "${PYTHON}" /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y redis
COPY tmp/systemctl3.py /usr/bin/systemctl

# initial setup
RUN cp -p /etc/redis/default.conf.example /etc/redis/default.conf
RUN runuser -u redis -- touch /var/log/redis/default.log
##ensured:# RUN chown redis:redis /etc/redis/default.conf
##ensured:# RUN chown redis:redis /var/log/redis/default.log

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/default.conf
# default was 'bind 127.0.0.1'
RUN sed -i "s/^..requirepass foo.*/requirepass $USERPASS/" /etc/redis/default.conf

RUN systemctl enable redis@default
RUN systemctl disable kbdsettings || true
RUN systemctl default-services
# TODO: the enable-command did not put it into default-services
RUN systemctl cat redis@.service

RUN touch /var/log/systemctl.debug.log
# CMD ["/usr/bin/systemctl"]
CMD ["/usr/bin/systemctl", "-1", "start", "redis@default"]
