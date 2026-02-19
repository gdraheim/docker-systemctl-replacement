FROM almalinux:9.4
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1074"

###############################################################################
### WARNING: the phpmyadmin package has not been ported to EPEL 8 (07/2020) ###
###############################################################################

ARG USERNAME=testuser_ok
ARG USERPASS=P@ssw0rd.548e779ca48f8c10ed3271298be06742d8ba598gsdrd
ARG TESTPASS=P@ssw0rd.UQN2pMWSUbl4gQU.P5hvJuOhjx.s90b4qCnG2idtc30.
ARG LISTEN=172.0.0.0/8
ARG VER=4.9.7
ARG PYTHON_EXE=/usr/libexec/platform-python
ENV PYTHON_EXE="${PYTHON_EXE}"
ENV SSL="--setopt sslverify=false"
ENV GPG="--nogpgcheck"
ENV WEB_CONF="/etc/httpd/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/usr/share/phpmyadmin/config.inc.php"
ENV INDEX_PHP="/var/www/html/index.php"
EXPOSE 80

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl
RUN yum install $GPG $SSL -y dnf-plugins-core
# RUN yum config-manager --set-enabled PowerTools
RUN yum install $GG $SSL -y epel-release
# RUN echo 'sslverify=false' >> /etc/yum.conf
RUN yum repolist

RUN yum search $GPG $SSL php
RUN yum install $GPG $SSL -y httpd httpd-tools mariadb-server mariadb php php-json php-mysqlnd
RUN mkdir /etc/systemd/system/mariadb.service.d ; \
   { echo '[Service]' \
   ; echo 'PIDFile=/run/mariadb/mariadb.pid' \
   ; } > /etc/systemd/system/mariadb.service.d/pidfile.conf

RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN systemctl start mariadb -vvv \
  ; mysqladmin -uroot password ${TESTPASS} \
  ; echo "CREATE USER ${USERNAME} IDENTIFIED BY '${USERPASS}'" | mysql -uroot -p${TESTPASS} \
  ; systemctl stop mariadb -vvv 

# phpMyAdmin the hard way
RUN yum install $GPG $SSL -y wget unzip
RUN wget https://files.phpmyadmin.net/phpMyAdmin/$VER/phpMyAdmin-$VER-all-languages.zip
RUN unzip phpMyAdmin-$VER-all-languages.zip
RUN mv phpMyAdmin-$VER-all-languages /usr/share/phpmyadmin
RUN cd /usr/share/phpmyadmin && mv config.sample.inc.php config.inc.php
RUN systemctl start mariadb -vvv \
  ; cat /usr/share/phpmyadmin/sql/create_tables.sql | mysql -uroot -p${TESTPASS} \
  ; systemctl stop mariadb -vvv 
RUN mkdir /usr/share/phpmyadmin/tmp \
 ; chown -R apache:apache /usr/share/phpmyadmin \
 ; chmod 777 /usr/share/phpmyadmin/tmp 
RUN { echo "Alias /phpMyAdmin /usr/share/phpmyadmin" \
    ; echo "<Directory /usr/share/phpmyadmin/>" \
    ; echo " <RequireAny>" \
    ; echo "  Require all granted" \
    ; echo " </RequireAny>" \
    ; echo "</Directory>" \
    ; } > ${WEB_CONF}

RUN sed -i -e "/'user'/s|=.*;|='${USERNAME}';|" \
           -e "/'password'/s|=.*;|='${PASSWORD}';|" ${INC_CONF}

# it does not work without php-fpm (which also requires php-json)
RUN sed -i "s/^listen.allowed/;listen.allowed/" /etc/php-fpm.d/www.conf
RUN systemctl enable php-fpm

RUN systemctl enable mariadb
RUN systemctl enable httpd
CMD ["/usr/bin/systemctl"]
