FROM ubuntu:18.04

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG PASS=P@ssw0rd.9d82fd2c7c83afb7d69213088203b6c6e402da0
ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
EXPOSE 22

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ${PYTHONPKG}
COPY tmp/systemctl3.py /usr/bin/systemctl
RUN test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

# RUN apt-get install -y passwd
# RUN apt-cache search sshd
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server
RUN rm -fv /etc/ssh/sshd_not_to_be_run
RUN systemctl enable ssh
#
RUN useradd -g nogroup testuser -m
RUN echo testuser:$PASS | chpasswd
RUN tail /etc/passwd
RUN TZ=UTC date -I > /home/testuser/date.txt
CMD ["/usr/bin/systemctl"]
