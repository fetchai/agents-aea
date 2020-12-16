# usage
# from cmd: @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/fetchai/agents-aea/master/scripts/install.ps1'))"
# from powershell: iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/fetchai/agents-aea/master/scripts/install.ps1'))

function install_python {
	echo "Installing python"
    Invoke-WebRequest https://www.python.org/ftp/python/3.8.6/python-3.8.6-amd64-webinstall.exe -OutFile python-3.8.6-amd64-webinstall.exe
    ./python-3.8.6-amd64-webinstall.exe /install /passive PrependPath=1 Include_test=0 Include_tcltk=0| Out-Null
    rm ./python-3.8.6-amd64-webinstall.exe

}

function install_aea {
	echo "Install aea"
    $output=pip install aea[all]==0.8.0 --force --no-cache-dir 2>&1 |out-string;
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
    refresh-path
    install_aea
    pause
}

main
