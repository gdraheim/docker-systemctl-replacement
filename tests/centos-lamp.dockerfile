FROM centos:centos7

ENV WEB_CONF /etc/httpd/conf.d/phpMyAdmin.conf
ENV INC_CONF /etc/phpMyAdmin/config.inc.php

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y epel-release && yum repolist
RUN yum install -y httpd httpd-tools mariadb-server mariadb php phpmyadmin
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN echo "<?php phpinfo(); ?>" > /var/www/html/index.php
RUN sed -i "s|ip 127.0.0.1|ip 172.0.0.0/8|" $WEB_CONF
RUN systemctl start mariadb \
  ; mysqladmin -uroot password 'N0.secret' \
  ; systemctl stop mariadb \
  ; sleep 3
RUN systemctl start mariadb \
  ; sleep 3 \
  ; echo "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'" | mysql -uroot -pN0.secret \
  ; sleep 3 \
  ; systemctl stop mariadb \
  ; sleep 3
RUN sed -i -e "/'user'/s|=.*;|='testuser_OK';|" $INC_CONF
RUN sed -i -e "/'password'/s|=.*;|='Testuser.OK';|" $INC_CONF
RUN systemctl enable httpd
RUN systemctl enable mariadb
EXPOSE 80
CMD /usr/bin/systemctl
