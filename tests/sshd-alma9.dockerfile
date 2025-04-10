FROM almalinux:9.4

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG PASSWORD=P@ssw0rd.788daa5d938373fe628f1dbe8d0c319c5606c4d3e857eb7
EXPOSE 22
ENV SSL --setopt sslverify=false
ENV GPG --nogpgcheck

# RUN yum install -y epel-release
RUN yum install $GPG $SSL -y passwd
RUN yum search $GPG $SSL sshd
RUN yum install -y $GPG $SSL openssh-server
RUN rpm -q --list openssh-server

COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py
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
RUN echo $PASSWORD | passwd --stdin testuser
RUN TZ=UTC date -I > /home/testuser/date.txt
RUN touch /var/log/systemctl.debug.log
CMD ["/usr/bin/systemctl"]
