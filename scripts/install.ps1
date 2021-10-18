# usage
# from cmd: @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.ps1'))"
# from powershell: iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/fetchai/agents-aea/main/scripts/install.ps1'))

function install_python {
	echo "Installing python"
    Invoke-WebRequest https://www.python.org/ftp/python/3.8.6/python-3.8.6-amd64-webinstall.exe -OutFile python-3.8.6-amd64-webinstall.exe
    ./python-3.8.6-amd64-webinstall.exe /install /passive PrependPath=1 Include_test=0 Include_tcltk=0| Out-Null
    rm ./python-3.8.6-amd64-webinstall.exe

}

function install_build_tools {
	$output=pip install wheel --force --no-cache-dir 2>&1 |out-string;
	$output=pip wheel cytoolz --no-cache-dir 2>&1 |out-string;
    if ($LastExitCode -ne 0) {
    	echo "Installing visual studio build tools"
	    Invoke-WebRequest https://download.microsoft.com/download/5/f/7/5f7acaeb-8363-451f-9425-68a90f98b238/visualcppbuildtools_full.exe -OutFile visualcppbuildtools_full.exe
	    ./visualcppbuildtools_full.exe /NoRestart /Passive | Out-Null
	    rm ./visualcppbuildtools_full.exe
	} else{
		echo "Visual studio build tools are already installed"

	}

}


function instal_choco_golang_gcc {
   echo "Choco, golang and gcc will be installed"
   echo "You'll be asked for admin shell"
   sleep 5
   Start-Process powershell -Verb runAs -ArgumentList "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); choco install -y golang mingw"
}
function install_aea {
	echo "Install aea"
    $output=pip install aea[all]==1.1.0 --force --no-cache-dir 2>&1 |out-string;
    if ($LastExitCode -ne 0) {
        echo $output
        echo "AEA install failed!"
        exit 1
	}

    aea --help 2>&1 |out-null;
    if ($LastExitCode -eq 0) {
        echo "AEA successfully installed"
    }else{
        echo "AEA installed but can not be runned!"
    }
}

function refresh-path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") +
        ";" +
    [System.Environment]::GetEnvironmentVariable("Path","User")
}

function check_python {
	try{
	    if (((python -V)|Out-String) -match "Python 3\.[678]\.") {
	        echo "Python installed and supported!"
	    }else{
	        install_python
	    }
	}catch{
	    install_python
	}
}

function main{
    refresh-path
    check_python
    install_build_tools
    refresh-path
    install_aea
    instal_choco_golang_gcc
    pause
}

main
