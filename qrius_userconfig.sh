#!/bin/bash
# Qrius user configuration script

set -o pipefail

USERNAME=$1

add_to_plugdev() {

	groups ${USERNAME} | grep plugdev > /dev/null

	XCODE=(${PIPESTATUS[@]})
	if [ ${XCODE[0]} != 0 ]; then return ${XCODE[0]}; fi
	if [ ${XCODE[1]} == 0 ]

		then
			echo "User is already in plugdev group."

		else
			echo "Adding user to plugdev group."
			usermod -a -G plugdev ${USERNAME}

			XCODE=$?
			if [ ${XCODE} != 0 ]
				then
					echo "Error in adding user to plugdev group."
					return ${XCODE}
			fi
	fi
}

check_username() {

	if [ "${USERNAME}" == "" ]
		then
			read -p "Specify username: " USERNAME
	fi

	if [ "${USERNAME}" == "" ]
		then
			echo "No user name is specified!"
			return 1
	fi
}

do_userconfig() {

	echo ""
	echo "++++++++++++++++++++"
	date
	echo "++++++++++++++++++++"

	echo "============================================="
	echo "Configuring user ${USERNAME} as a Qrius user "
	echo "============================================="

	add_to_plugdev
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi
}

check_identity() {

	MY_IDENTITY=$(whoami)
	if [ "${MY_IDENTITY}" != "root" ]
		then
			echo "This installer needs root permission to run."
			return 1
	fi
}

main() {

	# Check whether root
	check_identity
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	check_username
	XCODE=$?
	if [ ${XCODE} != 0 ]; then return ${XCODE}; fi

	# Performs user configuration
	do_userconfig 2>&1 | logger -s -t "qrius_userconfig"
}

main
XCODE=$?

read -p "Press ENTER to continue ..."
exit ${XCODE}
