FROM opensuse/leap:15.6

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 80
ENV GPG --no-gpg-checks

RUN zypper $GPG install -r repo-oss -y python3
COPY tmp/systemctl3.py /usr/bin/systemctl
RUN zypper $GPG install -r repo-oss -y nginx 
COPY tmp/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /srv/www/htdocs/index.html

RUN systemctl enable nginx
CMD /usr/bin/systemctl
