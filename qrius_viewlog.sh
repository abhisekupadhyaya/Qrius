#!/bin/bash
# Qrius log viewer

LOGFILE=`realpath ${HOME}/.quazar/Qrius/latest.log`
gedit -s ${LOGFILE} +
