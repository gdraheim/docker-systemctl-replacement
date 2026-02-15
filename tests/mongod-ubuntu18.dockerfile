FROM ubuntu:18.04

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
EXPOSE 27017

RUN echo ==== PYTHONPKG=${PYTHONPKG}
RUN apt-get update && apt-get install -y ${PYTHONPKG} procps
RUN test -s /usr/bin/python3 || ln -sv ${PYTHON} /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

RUN apt-get install -y wget gnupg
RUN wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.4 multiverse" \
    | tee /etc/apt/sources.list.d/mongodb-org-4.4.list
RUN apt-get update
RUN apt-get install -y mongodb-org
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf
RUN sed -i -e "/processManagement/a\\" -e "  pidFilePath: /var/run/mongodb/mongod.pid" /etc/mongod.conf
RUN sed -i -e "/PIDFile=/a\\" -e "RuntimeDirectory=mongodb" /lib/systemd/system/mongod.service
# systemctl3.py can not find the child process being the new MAINPID but mongodb can tell about it

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD ["/usr/bin/systemctl"]
# CMD /usr/bin/systemctl init mongod
