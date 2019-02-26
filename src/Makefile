L = systemctl-logging.c

build: init test
init:
	$(CC) systemctl-init.c $L -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-init.e
test:
	$(CC) systemctl-init-data-test.c $L -fsanitize=address -fno-omit-frame-pointer \
	   -o systemctl-init-data-test.e

check: init test
	./systemctl-init-data-test.e
	./systemctl-init.e list-units
	./systemctl-init.e list-unit-files

clean:
	- rm *.e

