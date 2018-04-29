FROM centos:centos7

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.0.2177"

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y httpd httpd-tools
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN systemctl enable httpd
RUN echo TEST_OK > /var/www/html/index.html

EXPOSE 80
CMD /usr/bin/systemctl
