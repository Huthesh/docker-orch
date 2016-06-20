#!/bin/bash
# -c is the config directory to look into
# -o is the output directory to dump the final file into
TEMP=`getopt -o c:o:p: -n make_config.sh -- "$@"`

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$TEMP"

#default values
CONFIG_DIR="config/"
OUTPUT_DIR="output/"
PORT=9001

while true ; do
    case "$1" in
        -c) CONFIG_DIR=$2; shift 2;;
        -o) OUTPUT_DIR=$2; shift 2 ;;
        -p) PORT=$2; shift 2 ;;
        --) shift ; break ;;
        *) echo "Internal error!" ; exit 1 ;;
    esac
done

# remove trailing /
CONFIG_DIR=${CONFIG_DIR%/}
OUTPUT_DIR=${OUTPUT_DIR%/}

echo "CONFIG_DIR ${CONFIG_DIR}"
echo "OUTPUT_DIR ${OUTPUT_DIR}"
# clean out the output dir
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

cat ${CONFIG_DIR}/global > ${OUTPUT_DIR}/haproxy.cfg

FRONTEND="${OUTPUT_DIR}/frontend"
BACKEND="${OUTPUT_DIR}/backend"
echo "frontend web" > ${FRONTEND}
echo "  bind *:${PORT}" >> ${FRONTEND}
echo > $BACKEND
echo >> $BACKEND

APPS=`find $CONFIG_DIR -type d`
echo $APPS
for ENDPOINT in $APPS
do
  APP=`echo $ENDPOINT | sed "s@^${CONFIG_DIR}/@@g"` 
  if [ "${APP}a" != "a" -a "${APP}" != "${CONFIG_DIR}" ]
  then
    URL=`head -n 1 ${ENDPOINT}/url`
    echo "  acl ${APP} path_beg -i ${URL}" >> ${FRONTEND}
    echo "use_backend srvs_${APP}  if ${APP}" >> ${BACKEND}
  fi
done

echo >> ${BACKEND}
echo >> ${BACKEND}
echo "#Now for the backends" >> ${BACKEND}
echo >> ${BACKEND}
echo >> ${BACKEND}

# DO THE LOOP AGAIN TO MAKE THE SERVER LISTS
for ENDPOINT in $APPS
do
  APP=`echo $ENDPOINT | sed "s@^${CONFIG_DIR}\/@@g"` 
  if [ "${APP}a" != "a" -a "${APP}" != "${CONFIG_DIR}" ]
  then
    echo "backend srvs_${APP}" >> ${BACKEND}
    echo "  balance roundrobin" >> ${BACKEND}
    HOST=1
    for SERVER in `cat ${ENDPOINT}/servers`
    do
      if [ "${SERVER}a" != "a" ]
      then
        echo "  server host${HOST} ${SERVER}" >> ${BACKEND}
        HOST=`expr $HOST + 1`
      fi
    done
    echo >> ${BACKEND}
  fi
done


cat ${FRONTEND} ${BACKEND} >> ${OUTPUT_DIR}/haproxy.cfg
exit 0
