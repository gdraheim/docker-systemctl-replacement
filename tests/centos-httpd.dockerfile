FROM centos:centos7

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y httpd httpd-tools
RUN systemctl enable httpd
RUN echo OK > /var/www/html/index.html
EXPOSE 80
CMD /usr/bin/systemctl
