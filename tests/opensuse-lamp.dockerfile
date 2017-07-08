FROM opensuse:42.2

LABEL __copyright__="(C) Guido Draheim, for free use (CC-BY,GPL,BSD)" \
      __version__="1.0.1276"

ENV WEB_CONF /etc/apache2/conf.d/phpMyAdmin.conf
ENV INC_CONF /etc/phpMyAdmin/config.inc.php

RUN zypper install -y python
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN zypper install -y apache2 apache2-utils mariadb mariadb-tools php5 phpMyAdmin
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN echo "<?php phpinfo(); ?>" > /srv/www/htdocs/index.php
RUN sed -i "s|ip 127.0.0.1|ip 172.0.0.0/8|" $WEB_CONF
RUN systemctl start mysql \
  ; mysqladmin -uroot password 'N0.secret' \
  ; systemctl stop mysql \
  ; sleep 3
RUN systemctl start mysql \
  ; sleep 3 \
  ; echo "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'" | mysql -uroot -pN0.secret \
  ; sleep 3 \
  ; systemctl stop mysql \
  ; sleep 3
RUN sed -i -e "/'user'/s|=.*;|='testuser_OK';|" $INC_CONF
RUN sed -i -e "/'password'/s|=.*;|='Testuser.OK';|" $INC_CONF
RUN systemctl enable apache2
RUN systemctl enable mysql

EXPOSE 80
CMD /usr/bin/systemctl
