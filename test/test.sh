#!/bin/bash
if [ "${1}a" = "a" ]
then
  echo "Usage $0 <config directory>"
  exit 2
fi

rm -rf $1
mkdir $1
cp config/global $1/
# add a host
echo "Add a host"
python scripts/mod_config.py -c $1 -o addhost -h localhost -v "range:9010-9020"
if [ $? -ne 0 ]
then
  exit $?
fi
# add an app
echo "Add app1 with one host"
SERV11=`python scripts/mod_config.py -c $1 -o addapp -a app1 -v "url:/app1/"`
python scripts/mod_config.py -c $1 -o cfgserver -a app1 -h $SERV11 -v "instance:80800" -v "version:1"
if [ $? -ne 0 ]
then
  exit $?
fi

echo "Add app2 with one host"
SERV21=`python scripts/mod_config.py -c $1 -o addapp -a app2 -v "url:/app2/"`
python scripts/mod_config.py -c $1 -o cfgserver -a app2 -h $SERV21 -v "instance:80805" -v "version:1"
if [ $? -ne 0 ]
then
  exit $?
fi


echo "Add a server to app1"
SERV12=`python scripts/mod_config.py -c $1 -o addserver -a app1`
python scripts/mod_config.py -c $1 -o cfgserver -a app1 -h $SERV12 -v "instance:80801" -v "version:1"
if [ $? -ne 0 ]
then
  exit $?
fi

echo "Add a server to app2"
SERV22=`python scripts/mod_config.py -c $1 -o addserver -a app2`
python scripts/mod_config.py -c $1 -o cfgserver -a app2 -h $SERV22 -v "instance:80802" -v "version:2"
if [ $? -ne 0 ]
then
  exit $?
fi


echo "list servers on app1"
python scripts/mod_config.py -c $1 -o listservers -v "app:app1" 



echo "list servers on app1"
python scripts/mod_config.py -c $1 -o listservers -v "app:app2"


echo "list servers app1:version 1"
python scripts/mod_config.py -c $1 -o listservers -v "app:app1" -v "version:1"

echo "list servers app1:version 2"
python scripts/mod_config.py -c $1 -o listservers -v "app:app1" -v "version:2"

echo "list servers app2:version 1"
python scripts/mod_config.py -c $1 -o listservers -v "app:app2" -v "version:1"

echo "list servers app2:version 2"
python scripts/mod_config.py -c $1 -o listservers -v "app:app2" -v "version:2"

echo "deleing $SERV21"
python scripts/mod_config.py -c $1 -o rmserver -h $SERV21 -a app2
echo "deleing $SERV12"
python scripts/mod_config.py -c $1 -o rmserver -h $SERV12 -a app1
echo "list servers on app1"
python scripts/mod_config.py -c $1 -o listservers -v "app:app1" 



echo "list servers on app1"
python scripts/mod_config.py -c $1 -o listservers -v "app:app2"


