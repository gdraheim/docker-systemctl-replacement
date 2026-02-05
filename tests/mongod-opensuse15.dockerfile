FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 27017
ENV GPG --no-gpg-checks

RUN zypper $GPG install -r repo-oss -y python3 procps
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN zypper addrepo "https://repo.mongodb.org/zypper/suse/15/mongodb-org/4.4/x86_64/" mongodb
RUN zypper $GPG install -y mongodb-org
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD ["/usr/bin/systemctl"]
