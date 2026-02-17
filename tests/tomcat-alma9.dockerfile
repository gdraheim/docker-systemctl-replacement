FROM almalinux:9.4
LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.7.1072"

###################################################################
### WARNING: tomcat-webapps was removed from CENTOS 8 (07/2020) ###
###################################################################

ARG PYTHON_EXE=/usr/libexec/platform-python
ENV PYTHON_EXE="${PYTHON_EXE}"
ENV SSL="--setopt sslverify=false"
ENV GPG="--nogpgcheck"
EXPOSE 8080

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl
# RUN yum install $GPG $SSL -y dnf-plugins-core
# RUN yum config-manager --set-enabled PowerTools
# RUN yum install $GPG $SSL -y epel-release
# RUN yum repolist

RUN yum search $GPG $SSL tomcat
RUN yum install $GPG $SSL -y tomcat tomcat-webapps 
RUN yum install $GPG $SSL -y procps

RUN systemctl enable tomcat
CMD ["/usr/bin/systemctl"]
