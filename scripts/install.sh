#!/bin/bash
### usage
# mac/linux: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.sh)"

function bad_os_type() {
	echo "OS $OSTYPE is not supported!"
	exit 1
}

function check_linux() {
	# check any deb distribution!
	is_ubuntu=`cat /etc/issue|grep -i Ubuntu`
	if  [[ -z $is_ubuntu ]];
	then
		echo "Only ubuntu, macos are supported at the moment with this script. please use install.ps1 for windows 10"
		exit 1
	fi
	install_on_ubuntu
}


function is_python3(){
	return `which python3`
}

function is_python_version_ok() {
	if which python3 2>&1 >/dev/null;
	then
		version=`python3 -V 2>/dev/null`
		if [[ -z `echo $version|grep -E 'Python 3\.[(6789]\.[0-9]+'` ]];
		then
			echo "Python3 version: ${version} is not supported. Supported versions are 3.6, 3.7, 3.8."
			return 1
		fi
		return 0
	else
		echo "Python is not installed"
		return 1
	fi
}


function install_aea (){
	echo "Install AEA"
	output=$(pip3 install --user aea[all]==1.1.0 --force --no-cache-dir)
	if [[  $? -ne 0 ]];
	then
		echo "$output"
		echo 'Failed to install aea'
		exit 1
	fi
	touch ~/.profile
	py_user_base=`python3 -m site --user-base`
	echo  >>~/.bashrc
	echo 'export PATH=$PATH'":${py_user_base}/bin" >>~/.bashrc 
	echo  >>~/.zshrc
	echo 'export PATH=$PATH'":${py_user_base}/bin" >>~/.zshrc
	source ~/.bashrc  # sometimes ~/.local/bin is not in PATH
	output=`aea --help 2>&1`
	if [[  $? -ne 0 ]];
	then
		echo "$output"
		echo 'Test run of aea failed!'
		exit 1
	fi
	echo "AEA successfully installed!"
	echo "It's recommended to open a new shell to work with AEA."
}

function install_ubuntu_deps(){
	# always install it cause python3-dev can be missing! also it's not consuming much time.
	echo "Install python3 and dependencies"
	output=$(sudo bash -c "apt update &&  apt install python3 python3-pip python3-dev -y" 2>&1)
	if [[  $? -ne 0 ]];
	then
		echo "$output"
		echo -n '\n\nFailed to install required packages!'
		exit 1
	fi

}

function check_python_version(){
	output=$(is_python_version_ok)
	if [[ $? -eq 1 ]];
	then
		echo "$output"
		echo "Can not install supported python version. probably distribution is too old. Exit."
		exit 1
	fi
}

function install_on_ubuntu(){
	install_ubuntu_deps
	check_python_version
	install_aea
}

function ensure_brew(){
	output=`which brew`
	if [[ $? -ne 0 ]];
	then
		echo "Installing homebrew. Please pay attention, it can ask for the password and aggree to install xcode tools."
		/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
		if [[ $? -eq 0 ]];
		then
			echo "Homebrew was installed!"
		else
			echo "Homebrew failed to install!"
		fi
	fi
}

function mac_install_python(){
	output=`is_python_version_ok`
	if [[ $? -eq 0 ]];
	then
		echo "Python supported version already installed!"
		return 0
	fi

	ensure_brew
	echo "Install python3.8. It takes long time."
	output=$(brew install python@3.8 2>&1)
	if [[ $? -eq 0 ]];
	then
		echo "Python was successfully installed!"
		return 0
	else
		echo "$output"
		echo "Python failed to install!"
		exit 1
	fi
}

function install_on_mac(){
	mac_install_python
	check_python_version
	install_aea
}

function main(){
	echo "Welcome to AEA installer!"
	case "$OSTYPE" in
	  darwin*)  install_on_mac ;;
	  linux*)   check_linux ;;
	  *)        bad_os_type ;;
	esac
}

main
