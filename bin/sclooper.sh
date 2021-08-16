#!/bin/bash

PLUGINNAME=REPLACELBPPLUGINDIR
PATH="/sbin:/bin:/usr/sbin:/usr/bin:$LBHOMEDIR/bin:$LBHOMEDIR/sbin"

ENVIRONMENT=$(cat /etc/environment)
export $ENVIRONMENT

while true
do
	$LBHOMEDIR/bin/plugins/${PLUGINNAME}/wrapper.sh poll > /dev/null 2>&1
	sleep 60
done
