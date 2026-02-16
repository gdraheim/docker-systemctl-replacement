FROM ubuntu:18.04
LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.7.1071"

ARG PYTHON=python3
ARG PYTHONPKG=${PYTHON}
ARG USERNAME=testuser_OK
ARG USERPASS=P@ssw0rd.5724647877c4fdb1e4a966386f5bdc7f0
ARG TESTUSER=testuser_11
ARG TESTPASS=P@ssw0rd.6e3591c3eda9c854d5bc35e5b832db5cf
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
ENV PG="/var/lib/postgresql/10/main"
ENV CNF_FILE="/etc/postgresql/10/main/postgresql.conf"
ENV HBA_FILE="/etc/postgresql/10/main/pg_hba.conf"
ENV LOG_FILE="/var/log/postgresql/postgresql-10-main.log"
ENV POSTGRES="postgresql@10-main"
EXPOSE 5432

RUN apt-get update && apt-get install -y ${PYTHONPKG}
RUN test -s /usr/bin/python3 || ln -sv ${PYTHON} /usr/bin/python3

COPY tmp/systemctl3.py /usr/bin/systemctl
RUN test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

RUN apt-cache search postgres
RUN apt-get install -y postgresql postgresql-contrib
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN pg_conftool show all
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $CNF_FILE
RUN sed -i -e "s/.*host.*ident/# &/" $HBA_FILE
RUN echo "host all all ${ALLOWS} md5" >> $HBA_FILE
# RUN systemctl start $POSTGRES -vvvv ; cat $LOG_FILE

RUN systemctl start $POSTGRES \
   ; echo "CREATE USER ${TESTUSER} LOGIN ENCRYPTED PASSWORD '${TESTPASS}'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${USERPASS}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop $POSTGRES

RUN systemctl enable $POSTGRES
RUN rm -f /etc/init.d/postgresql /etc/init.d/sysstat /etc/init.d/cron
CMD ["/usr/bin/systemctl"]
