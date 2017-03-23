F= files/docker/systemctl.py
B= 2016

version:
	@ Y=`date +%Y` ; X=$$(expr $$Y - $B); D=`date +%W%u` ; sed -i \
	-e "/^__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$D\"/" \
	-e "/^__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $B-$$Y/" \
	$F
	@ grep ^__version__ $F

