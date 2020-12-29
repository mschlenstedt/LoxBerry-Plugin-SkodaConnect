#!/bin/bash

PLUGINNAME=REPLACELBPPLUGINDIR
PATH="/sbin:/bin:/usr/sbin:/usr/bin:$LBHOMEDIR/bin:$LBHOMEDIR/sbin"

ENVIRONMENT=$(cat /etc/environment)
export $ENVIRONMENT

# Logfile
. $LBHOMEDIR/libs/bashlib/loxberry_log.sh
PACKAGE=${PLUGINNAME}
NAME=${PLUGINNAME}_MQTT
LOGDIR=$LBPLOG/${PLUGINNAME}

LOGSTART "sc2mqtt"

# Debug output
#STDERR=0
#DEBUG=0
if [[ ${LOGLEVEL} -eq 7 ]]; then
	LOGINF "Debugging is enabled! This will produce A LOT messages in your logfile!"
	STDERR=1
	DEBUG=1
fi


case "$1" in
  start|restart)

	if [[ $1 -eq "restart" ]]; then
		LOGINF "Stopping sc2mqtt..."
		pkill -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/sc2mqtt.py" >> ${FILENAME} 2>&1
	fi

	if [ "$(pgrep -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/sc2mqtt.py")" ]; then
		LOGERR "sc2mqtt.py already running."
		LOGEND "sc2mqtt"
		exit 1
	fi

	LOGINF "Starting sc2mqtt..."
	if [[ ${DEBUG} -eq 1 ]]; then
		$LBHOMEDIR/bin/plugins/${PLUGINNAME}/sc2mqtt.py --logfile ${FILENAME} --loglevel DEBUG --configfile $LBHOMEDIR/config/plugins/${PLUGINNAME}/config.json > /dev/null 2>&1 &
	else
		$LBHOMEDIR/bin/plugins/${PLUGINNAME}/sc2mqtt.py --logfile ${FILENAME} --loglevel ERROR --configfile $LBHOMEDIR/config/plugins/${PLUGINNAME}/config.json > /dev/null 2>&1 &

	fi
	LOGEND "sc2mqtt"
        exit 0
        ;;

  stop)

	LOGINF "Stopping sc2mqtt..."
	pkill -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/sc2mqtt.py" >> ${FILENAME} 2>&1

	if [ "$(pgrep -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/sc2mqtt.py")" ]; then
		LOGERR "sc2mqtt.py could not be stopped."
	else
		LOGOK "sc2mqtt.py stopped successfully."
	fi

	LOGEND "sc2mqtt"
        exit 0
        ;;

  *)
        echo "Usage: $0 [start|stop]" >&2
	LOGINF "No command given. Exiting."
	LOGEND "sc2mqtt"
        exit 3
  ;;

esac

LOGEND "sc2mqtt"
