FROM centos:centos7

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.0.2177"

ENV PG /var/lib/pgsql/data

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y postgresql-server postgresql-utils
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN postgresql-setup initdb
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '*'/" $PG/postgresql.conf
RUN sed -i -e "s/.*host.*ident/# &/" $PG/pg_hba.conf
RUN echo "host all all 0.0.0.0/0 md5" >> $PG/pg_hba.conf
RUN systemctl start postgresql \
   ; echo "CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD 'Testuser.11'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER testuser_OK LOGIN ENCRYPTED PASSWORD 'Testuser.OK'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql
RUN systemctl enable postgresql

EXPOSE 5432
CMD /usr/bin/systemctl
