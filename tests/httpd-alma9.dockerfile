FROM almalinux:9.4
LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.7.1076"

ARG PYTHON_EXE=/usr/libexec/platform-python
ENV PYTHON_EXE="${PYTHON_EXE}"
ENV SSL="--setopt sslverify=false"
ENV GPG="--nogpgcheck"
EXPOSE 80

COPY tmp/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/env python.*|${PYTHON_EXE}|" /usr/bin/systemctl3.py

RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN yum install $SSL $GPG -y httpd httpd-tools
COPY tmp/systemctl3.py /usr/bin/systemctl
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html

RUN systemctl enable httpd
CMD ["/usr/bin/systemctl"]
