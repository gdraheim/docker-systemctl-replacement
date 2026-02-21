FROM opensuse/leap:15.6
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1076"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
ENV GPG="--no-gpg-checks"
EXPOSE 27017

RUN echo ========= PYTHON=${PYTHON} PYTHONPKG=${PYTHONPKG}
RUN zypper $GPG install -r repo-oss -y ${PYTHONPKG} procps
RUN test -s /usr/bin/python3 || ln -sv "${PYTHON}" /usr/bin/python3
COPY tmp/systemctl3.py /usr/bin/systemctl

# mongodb pulls in python3-base anyway
RUN zypper addrepo "https://repo.mongodb.org/zypper/suse/15/mongodb-org/4.4/x86_64/" mongodb
RUN zypper $GPG install -y mongodb-org
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD ["/usr/bin/systemctl"]
