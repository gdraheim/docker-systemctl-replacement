L = systemctl-logging.c

build: init types
init:
	$(CC) systemctl-init.c $L -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-init.e
types:
	$(CC) systemctl-types-test.c $L -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-types-test.e

check: init types
	./systemctl-types-test.e
	./systemctl-init.e list-unit-files
	./systemctl-init.e list-units

clean:
	- rm *.e

