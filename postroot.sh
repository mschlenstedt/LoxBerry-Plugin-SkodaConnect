#!/bin/bash

ARGV0=$0 # Zero argument is shell command
ARGV1=$1 # First argument is temp folder during install
ARGV2=$2 # Second argument is Plugin-Name for scipts etc.
ARGV3=$3 # Third argument is Plugin installation folder
ARGV4=$4 # Forth argument is Plugin version
ARGV5=$5 # Fifth argument is Base folder of LoxBerry

echo "<INFO> Upgrading pip3..."
pip3 install --upgrade pip

echo "<INFO> Installing nest-asyncio..."
pip3 install nest_asyncio

# Exit with Status 0
exit 0
