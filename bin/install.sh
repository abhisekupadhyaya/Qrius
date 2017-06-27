#!/bin/bash
# PQMS installation/upgradation script

set -o pipefail

ROOT=
BIN_DIR=${ROOT}/usr/bin
QRIUS_LAUNCHER=${BIN_DIR}/qrius
QRIUS_USERCONFIG=${BIN_DIR}/qrius_userconfig
QRIUS_VIEWLOG=${BIN_DIR}/qrius_viewlog
INSTALL_DIR=${ROOT}/usr/local/xplore/Qrius
UDEV_RULES_LIBFTDI=/etc/udev/rules.d/99-libftdi.rules
APPLICATIONS_DIR=/usr/share/applications
ICONS_DIR=/usr/share/icons

get_topdir(){

	local _SCRIPT_PATH=`realpath "${BASH_SOURCE[0]}"`
	local _SCRIPT_FOLDER=`dirname "${_SCRIPT_PATH}"`
	local _TOP_DIR=`realpath "${_SCRIPT_FOLDER}/.."`
	eval  $1="${_TOP_DIR}"
}

TOP_DIR=""
get_topdir TOP_DIR

backup_previous_installation(){

	NOW=$(date +"%Y%m%d_%H%M%S")
	BACKUP_DIR="${INSTALL_DIR}_$NOW"

	echo "Taking backup to ${BACKUP_DIR}"
	mv ${INSTALL_DIR} ${BACKUP_DIR}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi
}

check_n_backup_previous_installation(){

	echo "================================"
	echo "Backing up previous installation"
	echo "================================"

	if [ -d ${INSTALL_DIR} ]; then

		backup_previous_installation
		XCODE=$?
		if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	else

		echo "No previous installation found. Skipping backup ..."
	fi

	echo ""
}

deploy_current_installation(){

	echo "=================================="
	echo "Deploying current installation ..."
	echo "=================================="

	# Creates installation folder
	echo "Creating folder ${INSTALL_DIR}"
	mkdir -p ${INSTALL_DIR}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# Copy source files
	echo "Copying source files from ${TOP_DIR} to ${INSTALL_DIR}"
	cp -r ${TOP_DIR}/* ${INSTALL_DIR}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# Delete svn related folders
	echo "Deleting svn related folders from ${INSTALL_DIR}"
	find ${INSTALL_DIR} -name ".svn" -exec rm -rf {} +
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# Set permission to all files to 644
	echo "Setting file permissions to 644 in ${INSTALL_DIR}"
	find ${INSTALL_DIR} -type f -exec chmod 644 {} +
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# Set permission to all folders to 755
	echo "Setting folder permissions to 755 in ${INSTALL_DIR}"
	find ${INSTALL_DIR} -type d -exec chmod 755 {} +
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	echo ""
}

create_launcher(){

	echo "===================="
	echo "Creating laucher    "
	echo "===================="

	echo "Creating folder ${BIN_DIR}"
	mkdir -p ${BIN_DIR}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	echo "Creating launcher ${QRIUS_LAUNCHER}"
	ln -nsf ${INSTALL_DIR}/qrius.sh ${QRIUS_LAUNCHER}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	echo "Setting launcher permission to 755"
	chmod 755 ${QRIUS_LAUNCHER}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	echo "Creating user config ${QRIUS_USERCONFIG}"
	ln -nsf ${INSTALL_DIR}/qrius_userconfig.sh ${QRIUS_USERCONFIG}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	echo "Setting launcher permission to 755"
	chmod 755 ${QRIUS_USERCONFIG}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	echo "Creating view log ${QRIUS_VIEWLOG}"
	ln -nsf ${INSTALL_DIR}/qrius_viewlog.sh ${QRIUS_VIEWLOG}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	echo "Setting launcher permission to 755"
	chmod 755 ${QRIUS_VIEWLOG}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	echo "Creating desktop applications"
	links="qrius.desktop \
	      qrius_system_config.desktop \
	      qrius_userconfig.desktop \
	      qrius_viewlog.desktop"

	for lnk in ${links}
		do
			ln -nsf ${INSTALL_DIR}/resources/${lnk} ${APPLICATIONS_DIR}/${lnk}
			XCODE=$?
			if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

			chmod 755 ${APPLICATIONS_DIR}/${lnk}
			XCODE=$?
			if [ ${XCODE} != 0 ]; then return ${XCODE}; fi
	done

	echo "Creating desktop icons"
	links="qrius.png \
	       qrius_system_config.png \
	       qrius_userconfig.png \
	       qrius_viewlog.png"

	for lnk in ${links}
		do
			ln -nsf ${INSTALL_DIR}/resources/${lnk} ${ICONS_DIR}/${lnk}
			XCODE=$?
			if [ ${XCODE} != 0 ]; then return ${XCODE}; fi
	done

	# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

	echo ""
}

configure_libftdi(){

	echo "===================="
	echo "Configuring libftdi "
	echo "===================="

	dirname ${UDEV_RULES_LIBFTDI} | xargs mkdir -p
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	touch ${UDEV_RULES_LIBFTDI}
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	grep "ATTRS{idProduct}==\"6001\"" ${UDEV_RULES_LIBFTDI} > /dev/null

	XCODE=$?
	if [ ${XCODE} == 0 ]
		then
			echo "FT232 is already there in the list of claimable interface."

		else
			echo "Adding FT232 in the list of claimable interface."
			cat ${TOP_DIR}/lib/99-libftdi.rules >> ${UDEV_RULES_LIBFTDI}
			XCODE=$?
			if [ ${XCODE} != 0 ]; then return ${XCODE}; fi
	fi

	echo ""
}

do_installation(){

	echo ""
	echo "++++++++++++++++++++"
	date
	echo "++++++++++++++++++++"

	check_n_backup_previous_installation
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	deploy_current_installation
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	configure_libftdi
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	create_launcher
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	echo "Installation successful"
}

check_identity() {

	MY_IDENTITY=$(whoami)
	if [ "${MY_IDENTITY}" != "root" ]
		then
			echo "This installer needs root permission to run."
			return 1
	fi
}

main(){

	# Check whether root
	check_identity
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# Performs installation
	do_installation 2>&1 | logger -s -t 'QriusInstaller'
}

main
