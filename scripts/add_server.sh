#!/bin/bash
# -c is the config directory to look into
# -o is the output directory to dump the final file into
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
  if [ "${APP}a" != "a" -a "${APP}" != "${CONFIG_DIR}" ]
  then
    grep "^${SERVERNAME}$" ${ENDPOINT}/servers 
    # only add if it isnt already there
    if [ $? -ne 1 ]
    then
      echo "Server already added"
      exit 1
    fi
  fi
done

# directory must exist
if [ -e ${CONFIG_DIR}/${APPNAME}/servers ]
then
  echo "$SERVERNAME" >>   ${CONFIG_DIR}/${APPNAME}/servers
  exit 0
else
  echo "You need to create the app first using add_app.sh"
  exit 1
fi
