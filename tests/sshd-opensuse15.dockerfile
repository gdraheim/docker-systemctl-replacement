FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG PASS=P@ssw0rd.e404e3ef41d5425af5ca357dbe90e346a53fb2d0a9b8e
ENV GPG="--no-gpg-checks"
EXPOSE 22

RUN zypper $GPG install -r repo-oss -y python3 procps
COPY tmp/systemctl3.py /usr/bin/systemctl
# RUN zypper $GPG search ssh
RUN zypper $GPG install -r repo-oss -y openssh
# RUN rpm -q --list openssh
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN systemctl enable sshd
RUN useradd -g users testuser -m
RUN set -x; echo testuser:$PASS | chpasswd
RUN TZ=UTC date -I > /home/testuser/date.txt
CMD ["/usr/bin/systemctl"]
