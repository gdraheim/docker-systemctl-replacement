FROM almalinux:9.4
LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.7.1067"

ARG PASS=P@ssw0rd.788daa5d938373fe628f1dbe8d0c319c5606c4d3e857eb7
ARG PYTHON_EXE=/usr/libexec/platform-python
ENV PYTHON_EXE=${PYTHON_EXE}
ENV SSL="--setopt sslverify=false"
ENV GPG="--nogpgcheck"
EXPOSE 22

# RUN yum install -y epel-release
RUN yum install $GPG $SSL -y passwd
# RUN yum search $GPG $SSL sshd
RUN yum install -y $GPG $SSL openssh-server
RUN rpm -q --list openssh-server

COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

# > systemctl cat sshd
# Wants=sshd-keygen.target

RUN systemctl enable sshd-keygen.target --force
RUN systemctl enable sshd
RUN rm -vf /run/nologin

#

RUN yum install $GPG $SSL -y procps
RUN yum install $GPG $SSL -y openssh-clients
RUN rpm -q --list openssh-clients
RUN useradd -g nobody testuser
RUN echo $PASS | passwd --stdin testuser
RUN TZ=UTC date -I > /home/testuser/date.txt
RUN touch /var/log/systemctl.debug.log
CMD ["/usr/bin/systemctl"]
