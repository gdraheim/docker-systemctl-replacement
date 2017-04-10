FROM ubuntu:16.04

LABEL __copyright__="(C) Guido U. Draheim, for free use (CC-BY,GPL,BSD)" \
      __version__="1.0.1142"

RUN apt-get update
RUN apt-get install -y apache2 python
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl
RUN systemctl enable apache2
RUN echo TEST_OK > /var/www/html/index.html

EXPOSE 80
CMD ["/usr/bin/python","/usr/bin/systemctl","init"]
