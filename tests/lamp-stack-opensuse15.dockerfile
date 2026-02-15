FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"

ENV WEB_CONF="/etc/apache2/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/etc/phpMyAdmin/config.inc.php"
ENV INDEX_PHP="/srv/www/htdocs/index.php"
ARG USERNAME=testuser_ok
ARG USERPASS=P@ssw0rd.dgPwzyiScdd5GPEvBAbOlWRuKD5RIneJ
ARG TESTPASS=P@ssw0rd.KFXnlRDnf.FW6U6r75RfLctUQdIaukm2
ARG LISTEN=172.0.0.0/8
ARG PYTHON="python3"
ARG PYTHONPKG=${PYTHON}
ENV GPG="--no-gpg-checks"
EXPOSE 80

RUN echo ========= PYTHON=${PYTHON} PYTHONPKG=${PYTHONPKG}
COPY tmp/systemctl3.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y ${PYTHONPKG}
RUN zypper $GPG install -r repo-oss -y apache2 apache2-utils mariadb-server mariadb-tools 
COPY tmp/systemctl3.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y php7 php7-mysql apache2-mod_php7 phpMyAdmin
RUN zypper $GPG install -r repo-oss -y phpMyAdmin-apache || true
# when phpmyadmin was moved to /usr/share the file phpMyAdmin.conf was moved to its own package phpMyAdmin-apache
# RUN a2enmod php7

RUN find /etc/apache2 -name "*.conf"
RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN sed -i "s|ip 127.0.0.1|ip ${LISTEN}|" ${WEB_CONF}

RUN systemctl start mysql -vvv \
  ; mysqladmin -uroot password ${TESTPASS} \
  ; echo "CREATE USER ${USERNAME} IDENTIFIED BY '${PASSWORD}'" | mysql -uroot -p${TESTPASS} \
  ; systemctl stop mysql -vvv 
RUN sed -i -e "/'user'/s|=.*;|='${USERNAME}';|" \
           -e "/'password'/s|=.*;|='${PASSWORD}';|" ${INC_CONF}

RUN systemctl enable mysql
RUN systemctl enable apache2
CMD ["/usr/bin/systemctl"]
