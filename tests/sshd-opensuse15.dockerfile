FROM opensuse/leap:15.6
LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.7.1073"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
ARG USERNAME=testuser
ARG USERPASS=P@ssw0rd.e404e3ef41d5425af5ca357dbe90e346a53fb2d0a9b8e
ENV GPG="--no-gpg-checks"
EXPOSE 22

RUN echo ========= PYTHON=${PYTHON} PYTHONPKG=${PYTHONPKG}
RUN zypper $GPG install -r repo-oss -y ${PYTHONPKG} procps
RUN ls -l /usr/bin/python3 || ln -sv "${PYTHON}" /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
# RUN zypper $GPG search ssh
RUN zypper $GPG install -r repo-oss -y openssh
# RUN rpm -q --list openssh
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN systemctl enable sshd
RUN useradd -g users ${USERNAME} -m
RUN set -x; echo ${USERNAME}:${USERPASS} | chpasswd
RUN TZ=UTC date -I > /home/testuser/date.txt
CMD ["/usr/bin/systemctl"]
