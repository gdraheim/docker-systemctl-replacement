L = systemctl-logging.c
T = systemctl-types.c
S = systemctl-shlex.c
R = systemctl-regex.c
O = systemctl-options.c

build: init types
init: systemctl-types.h systemctl-options.h systemctl-init.h systemctl-shlex.h
	$(CC) systemctl-init.c $L $T $S $R $O -g -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-init.e
types: systemctl-types.h
	$(CC) systemctl-types-test.c $L $T $S -g -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-types-test.e

check: init types
	./systemctl-types-test.e
	./systemctl-init.e list-unit-files -v
	./systemctl-init.e list-units -vv
	./systemctl-init.e status cron
s: init
	./systemctl-init.e start z_a.service


systemctl-types.h: systemctl-types.c
	./makeheader.py systemctl-types.c
systemctl-init.h: systemctl-init.c
	./makeheader.py systemctl-init.c
systemctl-options.h: systemctl-options.c
	./makeheader.py systemctl-options.c
systemctl-shlex.h: systemctl-shlex.c
	./makeheader.py systemctl-shlex.c

clean:
	- rm *.e

