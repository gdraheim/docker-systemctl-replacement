FROM centos:centos7

LABEL __copyright__="(C) Guido Draheim, for free use (CC-BY,GPL,BSD)" \
      __version__="1.0.1236"

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y java
COPY files/docker/systemctl.py /usr/bin/systemctl
COPY Software/ElasticSearch/*.rpm /srv
RUN yum install -y /srv/*.rpm

RUN systemctl enable elasticsearch

EXPOSE 80
CMD /usr/bin/systemctl
