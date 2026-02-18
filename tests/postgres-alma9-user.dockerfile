FROM almalinux:9.4
LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.7.1073"

ARG PYTHON_EXE=/usr/libexec/platform-python
ARG USERNAME=testuser_OK
ARG USERPASS=P@ssw0rd.b653db8c755f29eb5754860e5e77
ARG TESTUSER=testuser_11
ARG TESTPASS=P@ssw0rd.a68a359519169eda6db6ed2d01fb
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
ENV PYTHON_EXE="${PYTHON_EXE}"
ENV SSL="--setopt sslverify=false"
ENV GPG="--nogpgcheck"
ENV PG="/var/lib/pgsql/data"
EXPOSE 5432

COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl3.py

RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN yum install $GPG $SSL -y postgresql-server postgresql-contrib
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN yum install $GPG $SSL -y glibc-minimal-langpack procps
RUN export LC_ALL=en_US.UTF-8 ; LANG=en_US.UTF-8; postgresql-setup --initdb
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $PG/postgresql.conf
RUN sed -i -e "s/.*host.*ident/# &/" $PG/pg_hba.conf
RUN echo "host all all ${ALLOWS} md5" >> $PG/pg_hba.conf
RUN systemctl start postgresql \
   ; echo "CREATE USER ${TESTUSER} LOGIN ENCRYPTED PASSWORD '${TESTPASS}'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${USERPASS}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql

RUN systemctl enable postgresql
CMD ["/usr/bin/systemctl"]
USER postgres
# postgresql.service does already contain a "User=" entry
