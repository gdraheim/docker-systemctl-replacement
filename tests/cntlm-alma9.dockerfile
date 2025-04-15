FROM almalinux:9.4

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG ALLOWS=172.0.0.0/8
EXPOSE 3128
ARG PYTHON_EXE=/usr/libexec/platform-python
ENV PYTHON_EXE ${PYTHON_EXE}
ENV SSL --setopt sslverify=false
ENV GPG --nogpgcheck

COPY tmp/systemctl.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl
RUN yum install $GPG $SSL -y dnf-plugins-core
# RUN yum config-manager --set-enabled PowerTools
RUN yum install $GPG $SSL -y epel-release
RUN yum repolist

RUN yum search $GPG $SSL cntlm
RUN yum install $GPG $SSL -y cntlm 
RUN : \
  ; sed -i -e "s/^Listen.*/Listen 0.0.0.0:3128/" /etc/cntlm.conf \
  ; sed -i -e "/Deny/a\\" -e "Allow 127.0.0.1" /etc/cntlm.conf \
  ; sed -i -e "/Deny/a\\" -e "Allow ${ALLOWS}" /etc/cntlm.conf \
  ; sed -i -e "/NoProxy/a\\" -e "NoProxy ${ALLOWS}, www.google.com" /etc/cntlm.conf \
  ; :
RUN : \
  ; mkdir /etc/systemd/system/cntlm.service.d \
  ; { echo "[Service]"; echo "PIDFile=/run/cntlm/cntlmd.pid"; } \
        > /etc/systemd/system/cntlm.service.d/pidfile.conf

RUN systemctl enable cntlm
CMD /usr/bin/systemctl
