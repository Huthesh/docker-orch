#!/bin/bash
# -c is the config directory to look into
# -o is the output directory to dump the final file into

# I want plain grep here
unalias grep

TEMP=`getopt -o c:s:a: -n make_config.sh -- "$@"`

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

#default values
CONFIG_DIR="config/"
SERVERNAME=""
APPNAME=""
while true ; do
    case "$1" in
        -c) CONFIG_DIR=$2; shift 2;;
        -s) SERVERNAME=$2; shift 2 ;;
        -a) APPNAME=$2; shift 2 ;;
        --) shift ; break ;;
        *) echo "Internal error!" ; exit 1 ;;
    esac
done

if [ "${SERVERNAME}a" == "a" -o "${APPNAME}a" == "a" ]
then
  echo "Usage: $0 -s <servername> -a <appname> -c <configdir(optional)>"
  exit 1
fi

# remove trailing /
CONFIG_DIR=${CONFIG_DIR%/}

echo "CONFIG_DIR ${CONFIG_DIR}"

APPS=`find $CONFIG_DIR -type d`
echo $APPS
for ENDPOINT in $APPS
do
  APP=`echo $ENDPOINT | sed "s@^${CONFIG_DIR}/@@g"` 
  if [ "${APP}" == "${APPNAME}" ]
  then
    grep "^${SERVERNAME}$" ${ENDPOINT}/servers 
    # only remove if it is there
    if [ $? -eq 0 ]
    then
      TEMPFILE=`mktemp`
      cat ${ENDPOINT}/servers | grep -v "^${SERVERNAME}$" > $TEMPFILE
      mv $TEMPFILE ${ENDPOINT}/servers
      exit 0
    fi
  fi
done

echo "Server not found in app"
exit 1
