FROM ubuntu:24.04
LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.7.1075"

ARG PASS=P@ssw0rd.9d82fd2c7c83afb7d69213088203b6c6e402da0
ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
EXPOSE 22

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ${PYTHONPKG}

COPY tmp/systemctl3.py /usr/bin/systemctl
# RUN apt-get install -y passwd
# RUN apt-cache search sshd
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server
RUN rm -fv /etc/ssh/sshd_not_to_be_run
COPY tmp/systemctl3.py /usr/bin/systemctl
RUN systemctl enable ssh
#
RUN useradd -g nogroup testuser -m
RUN echo testuser:$PASS | chpasswd
RUN tail /etc/passwd
RUN TZ=UTC date -I > /home/testuser/date.txt
RUN touch /var/log/systemctl.debug.log
CMD ["/usr/bin/systemctl"]
