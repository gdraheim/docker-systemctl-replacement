FROM almalinux:9.4

###################################################################
### WARNING: tomcat-webapps was removed from CENTOS 8 (07/2020) ###
###################################################################

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 8080
ENV SSL --setopt sslverify=false
ENV GPG --nogpgcheck

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl
# RUN yum install $GPG $SSL -y dnf-plugins-core
# RUN yum config-manager --set-enabled PowerTools
# RUN yum install $GPG $SSL -y epel-release
# RUN yum repolist

RUN yum search $GPG $SSL tomcat
RUN yum install $GPG $SSL -y tomcat tomcat-webapps 
RUN yum install $GPG $SSL -y procps

RUN systemctl enable tomcat
CMD ["/usr/bin/systemctl"]
