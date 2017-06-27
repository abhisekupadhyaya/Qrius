#!/bin/bash
# Qrius launch script

LOGFILE=${HOME}/.quazar/Qrius/log/`date +%Y%m%d`.log
LLOGFILE=${HOME}/.quazar/Qrius/latest.log

get_topdir(){

	local _SCRIPT_PATH=`realpath "${BASH_SOURCE[0]}"`
	local _SCRIPT_FOLDER=`dirname "${_SCRIPT_PATH}"`
	local _TOP_DIR=`realpath "${_SCRIPT_FOLDER}"`
	eval  $1="${_TOP_DIR}"
}

TOP_DIR=''
get_topdir TOP_DIR
dirname ${LOGFILE} | xargs mkdir -p
touch ${LOGFILE}
ln -nsf ${LOGFILE} ${LLOGFILE}

echo                                         | tee -a ${LOGFILE}
echo '+++++++++++++++++++++++++++++++++++++' | tee -a ${LOGFILE}
date                                         | tee -a ${LOGFILE}
echo '+++++++++++++++++++++++++++++++++++++' | tee -a ${LOGFILE}
echo                                         | tee -a ${LOGFILE}

stdbuf --output=L --error=L \
	python2 ${TOP_DIR}/main.py 2>&1 | tee -a ${LOGFILE}
