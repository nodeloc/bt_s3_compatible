#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

if [ -d "/www/server/panel/pyenv" ];then
  btpip install boto3
else
  pip install boto3
fi
Install_S3Compatible()
{
	mkdir -p /www/server/panel/plugin/s3compatible
	cd /www/server/panel/plugin/s3compatible
	echo 'Successify'
}

Uninstall_S3Compatible()
{
	rm -rf /www/server/panel/plugin/s3compatible
	echo 'Successify'
}


action=$1
if [ "${1}" == 'install' ];then
	Install_S3Compatible
else
	Uninstall_S3Compatible
fi
