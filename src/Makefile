L = systemctl-logging.c
T = systemctl-types.c
R = systemctl-regex.c
O = systemctl-options.c

build: init types
init: systemctl-types.h systemctl-options.h systemctl-init.h
	$(CC) systemctl-init.c $L $T $R $O -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-init.e
types: systemctl-types.h
	$(CC) systemctl-types-test.c $L $T -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-types-test.e

check: init types
	./systemctl-types-test.e
	./systemctl-init.e list-unit-files
	./systemctl-init.e list-units
	./systemctl-init.e status cron

systemctl-types.h: systemctl-types.c
	./makeheader.py systemctl-types.c
systemctl-init.h: systemctl-init.c
	./makeheader.py systemctl-init.c
systemctl-options.h: systemctl-options.c
	./makeheader.py systemctl-options.c

clean:
	- rm *.e

